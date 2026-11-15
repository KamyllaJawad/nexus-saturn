"""Trilha mínima da Cosmo (ADR-018). Cada vez que a Cosmo fala fica registrado:

- tokens: quanto texto entrou e saiu. Com Ollama, a contagem dele; sem LLM,
  estimativa de 4 caracteres por token (marcada como estimada);
- latência: tempo de parede da chamada, em ms, e de cada passo;
- custo: US$ pelo preço por milhão de tokens (padrão 0: tudo roda local) e a
  energia estimada no computador de bordo (latência x potência);
- decisão da Cosmo: o que ela escolheu fazer (responder, recusar agir, sugerir,
  não encontrar). Nunca é decisão clínica: `pode_agir` é sempre falso;
- passos: o caminho da pergunta até a resposta.

Só inclusão: a tabela `cosmo_trilha` não tem update, e cada registro também entra
na auditoria encadeada, só com as métricas (o texto da pergunta não vai para lá).
"""
import math
import os
import threading
import time
from collections import deque

from . import registro

WATTS = float(os.environ.get("COSMO_WATTS", "15"))                  # potência estimada do computador de bordo
USD_1M_ENTRADA = float(os.environ.get("COSMO_USD_1M_ENTRADA", "0"))  # preço por milhão de tokens; local = 0
USD_1M_SAIDA = float(os.environ.get("COSMO_USD_1M_SAIDA", "0"))

_trava = threading.Lock()
_memoria = deque(maxlen=400)   # a sessão atual; o histórico inteiro fica no SQLite
_seq = 0


def iniciar():
    """Nova sessão de simulação: a tela começa vazia, o SQLite guarda as anteriores."""
    global _seq
    with _trava:
        _memoria.clear()
        _seq = registro.listar("SELECT COUNT(*) AS n FROM cosmo_trilha")[0]["n"]


def tokens(texto) -> int:
    return math.ceil(len(texto) / 4) if texto else 0


class Passos:
    """Cronômetro de passos: cada `marcar` fecha o passo anterior com o tempo gasto."""

    def __init__(self):
        self.t0 = self._ult = time.perf_counter()
        self.lista = []

    def marcar(self, etapa: str, detalhe: str):
        agora = time.perf_counter()
        self.lista.append(dict(etapa=etapa, detalhe=detalhe, ms=round((agora - self._ult) * 1000, 2)))
        self._ult = agora

    def total_ms(self) -> float:
        return round((time.perf_counter() - self.t0) * 1000, 2)


def registrar(origem: str, superficie: str, quando: str, passos: Passos, decisao: dict, entrada: str, saida: str,
              llm: dict | None = None, evento_id=None, tripulante_id=None, pergunta=None) -> dict:
    """Fecha a chamada e devolve o registro compacto (o que vai no chat e no pacote)."""
    global _seq
    ms = passos.total_ms()
    usou_llm = bool(llm and llm.get("texto"))
    if usou_llm and llm.get("tokens_entrada") is not None:
        t_ent, t_sai, fonte = llm["tokens_entrada"], llm["tokens_saida"], f"contados pelo Ollama ({llm['modelo']})"
    else:
        t_ent, t_sai, fonte = tokens(entrada), tokens(saida), "estimados (4 caracteres por token)"
    usd = round(t_ent * USD_1M_ENTRADA / 1e6 + t_sai * USD_1M_SAIDA / 1e6, 6)
    with _trava:
        _seq += 1
        r = dict(id=f"cos-{_seq:05d}", quando=quando, origem=origem, superficie=superficie, evento_id=evento_id,
                 tripulante_id=tripulante_id, pergunta=(pergunta or "")[:160] or None, resposta=(saida or "")[:200],
                 decisao=dict(decisao, pode_agir=False),
                 tokens=dict(entrada=t_ent, saida=t_sai, total=t_ent + t_sai, fonte=fonte),
                 latencia_ms=ms,
                 custo=dict(usd=usd, energia_mwh=round(ms / 1000 * WATTS / 3.6, 4),
                            base=(f"US$ {USD_1M_ENTRADA:g}/{USD_1M_SAIDA:g} por milhão de tokens (entrada/saída); "
                                  f"energia = latência x {WATTS:g} W")),
                 modo=f"LLM local ({llm['modelo']})" if usou_llm else "regras locais (plano B)",
                 passos=passos.lista)
        _memoria.append(r)
    registro.incluir("cosmo_trilha", trilha_id=r["id"], superficie=superficie, origem=origem, evento_id=evento_id,
                     quando=quando, corpo=r)
    registro.auditar("cosmo", r["id"], None, decisao["tipo"], "cosmo",
                     dict(origem=origem, superficie=superficie, evento=evento_id, tokens=r["tokens"]["total"],
                          latencia_ms=ms, custo_usd=usd, passos=len(r["passos"])), quando)
    return r


def listar(filtro=lambda r: True) -> list:
    with _trava:
        return [r for r in reversed(_memoria) if filtro(r)]


def resumo(registros: list) -> dict:
    lat = sorted(r["latencia_ms"] for r in registros)
    por = {}
    for r in registros:
        por[r["decisao"]["tipo"]] = por.get(r["decisao"]["tipo"], 0) + 1
    return dict(chamadas=len(registros),
                tokens_entrada=sum(r["tokens"]["entrada"] for r in registros),
                tokens_saida=sum(r["tokens"]["saida"] for r in registros),
                latencia_media_ms=round(sum(lat) / len(lat), 2) if lat else 0,
                latencia_p95_ms=lat[min(len(lat) - 1, math.ceil(0.95 * len(lat)) - 1)] if lat else 0,
                custo_usd=round(sum(r["custo"]["usd"] for r in registros), 6),
                energia_mwh=round(sum(r["custo"]["energia_mwh"] for r in registros), 4),
                com_llm=sum(1 for r in registros if r["modo"].startswith("LLM")),
                por_decisao=por, watts=WATTS, usd_1m=dict(entrada=USD_1M_ENTRADA, saida=USD_1M_SAIDA))


def compacto(r: dict) -> dict:
    """O que viaja no pacote do evento para Houston: métricas e passos, sem texto livre."""
    return {k: r[k] for k in ("id", "quando", "origem", "superficie", "evento_id", "tripulante_id", "decisao", "tokens",
                              "latencia_ms", "custo", "modo", "passos", "resposta")}
