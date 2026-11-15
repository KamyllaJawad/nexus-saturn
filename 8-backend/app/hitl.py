"""Human-in-the-loop dos modelos (ADR-010).

1. Cada decisão humana vira um rótulo (tabela `rotulos`, só inclusão).
2. O retreino em lote junta o ouro com esses rótulos e gera um candidato.
3. O candidato entra em modo sombra: roda em cada leitura, sem agir, e é
   comparado com o modelo em serviço.
4. Só o médico da missão promove ou rejeita: o oficial médico a bordo ou, sem
   médico a bordo, a médica de voo. A troca fica na auditoria. Da Terra, a decisão
   viaja pelo link e só vale quando chega, para a versão que ela viu (ADR-017).
"""
import csv
import json

from treino import pipeline

from . import ia
from .config import BRONZE, MODELOS, OURO, PRATA, TRIPULACAO, nome_de
from .nave import registro

PECAS = {"m1": "M1 · fibrilação atrial", "m2": "M2 · qualidade de sinal", "m3-if": "M3 · Isolation Forest"}
MEDICO = "marcus"


class Negado(Exception):
    pass


def rotular(peca, tripulante_id, rotulo, humano_id, origem, dados):
    versao = ia.versoes()["ativos"].get(peca)
    registro.incluir("rotulos", peca=peca, tripulante_id=tripulante_id, rotulo=rotulo, humano_id=humano_id,
                     origem=origem, versao_modelo=versao, dados=dados, criado_em=registro.agora_iso())
    registro.auditar("rotulo", origem, None, rotulo, humano_id, dict(peca=peca, tripulante=tripulante_id, versao_modelo=versao))


def rotulos(peca=None) -> list:
    linhas = registro.listar("SELECT id, peca, tripulante_id, rotulo, humano_id, origem, versao_modelo, criado_em, dados FROM rotulos"
                             + (" WHERE peca = ?" if peca else "") + " ORDER BY id DESC", (peca,) if peca else ())
    for l in linhas:
        l["dados"] = json.loads(l["dados"])
    return linhas


def _para_treino(peca) -> list:
    saida = []
    for r in rotulos(peca):
        if peca == "m3-if":
            saida += [dict(tripulante_id=r["tripulante_id"], rotulo=r["rotulo"], vetor=v) for v in r["dados"]["vetores"]]
        else:
            saida.append(dict(rotulo=r["rotulo"], atributos=r["dados"]["atributos"]))
    return saida


def _resumo(art) -> dict:
    m = art["metricas"]
    if art["peca"] == "m1":
        chaves = ["f1_fa", "f1_fa_ic95", "precisao_fa", "recall_fa", "limiar_fa", "rotulos_humanos", "bateu_meta"]
    elif art["peca"] == "m2":
        chaves = ["recall_suspeito", "precisao_suspeito", "falso_suspeito_em_bom", "estimador_escolhido", "rotulos_humanos", "bateu_meta"]
    else:
        return dict(versao=art["versao"], treinado_em=art["treinado_em"], bateu_meta=m["bateu_meta"],
                    por_tripulante={t: {k: v[k] for k in ("limiar", "alarmes_fora_da_amostra_por_dia", "recall_desvio_em_3_sinais", "rotulos_humanos")}
                                    for t, v in m["por_tripulante"].items()})
    return dict(versao=art["versao"], treinado_em=art["treinado_em"], **{k: m[k] for k in chaves})


def retreinar(peca: str, humano_id: str, medico: str = MEDICO) -> dict:
    """Treina um candidato com o ouro + rótulos humanos e o coloca em modo sombra."""
    if peca not in PECAS:
        raise Negado("peça desconhecida")
    if humano_id not in TRIPULACAO and humano_id != medico:
        raise Negado("o retreino é pedido por um humano")
    humanos = _para_treino(peca)
    if not humanos:
        raise Negado("ainda não há rótulo humano para esta peça: responda a um aviso ou decida um evento primeiro")
    reg = pipeline.ler_registro()
    ja = [h["versao"] for h in reg["historico"] if h["peca"] == peca]
    versao = pipeline.proxima_versao(sorted(ja, key=lambda v: int(v.rpartition(".")[2]))[-1])
    lote = f"bordo-{registro.agora_iso()}"
    art = pipeline.TREINADORES[peca](versao=versao, rotulos_humanos=humanos, lote=lote)
    reg["sombra"][peca] = pipeline.salvar(art, "candidatos")
    reg["historico"].append(dict(versao=versao, peca=peca, estado="sombra", lote=lote, treinado_em=art["treinado_em"],
                                 pedido_por=humano_id, rotulos_humanos=len(humanos)))
    pipeline.gravar_registro(reg)
    ia.zerar_sombra(peca)
    ia.carregar()
    registro.auditar("modelo", versao, None, "sombra", humano_id, dict(peca=peca, rotulos_humanos=len(humanos), lote=lote))
    return dict(peca=peca, candidato=_resumo(art), ativo=_resumo(ia._ativos[peca]), rotulos_usados=len(humanos))


def checar(peca, humano_id, medico: str = MEDICO) -> str:
    """Quem pode decidir e se há candidato. Devolve a versão em sombra."""
    if humano_id != medico:
        raise Negado(f"modelo novo só entra em uso com aprovação do médico da missão, {nome_de(medico)} (ADR-010)")
    if peca not in pipeline.ler_registro()["sombra"] or peca not in ia._sombra:
        raise Negado("não há candidato em modo sombra para esta peça")
    return ia._sombra[peca]["versao"]


def _decidir(peca, humano_id, aprovar: bool, medico: str = MEDICO, versao_vista: str | None = None) -> dict:
    atual = checar(peca, humano_id, medico)
    if versao_vista and atual != versao_vista:
        raise Negado(f"o candidato em sombra mudou de {versao_vista} para {atual} enquanto a decisão viajava")
    reg = pipeline.ler_registro()
    placar = ia.placar_sombra().get(peca, {})
    versao, anterior = ia._sombra[peca]["versao"], ia._ativos[peca]["versao"]
    arquivo = reg["sombra"].pop(peca)
    if aprovar:
        reg["ativos"][peca] = arquivo
    for h in reg["historico"]:
        if h["versao"] == versao:
            h.update(estado="ativo" if aprovar else "rejeitado", decidido_por=humano_id, decidido_em=registro.agora_iso(),
                     placar_sombra={k: placar.get(k) for k in ("leituras", "concordam", "divergem")})
        elif aprovar and h["versao"] == anterior:
            h["estado"] = "aposentado"
    pipeline.gravar_registro(reg)
    ia.carregar()
    ia.zerar_sombra(peca)
    registro.auditar("modelo", versao, "sombra", "ativo" if aprovar else "rejeitado", humano_id,
                     dict(peca=peca, substitui=anterior if aprovar else None, placar_sombra=placar.get("leituras", 0)))
    return dict(peca=peca, versao=versao, estado="ativo" if aprovar else "rejeitado", em_servico=ia.versoes()["ativos"][peca])


def aprovar(peca, humano_id, medico=MEDICO):
    return _decidir(peca, humano_id, True, medico)


def rejeitar(peca, humano_id, medico=MEDICO):
    return _decidir(peca, humano_id, False, medico)


def _linhas(caminho) -> int:
    if not caminho.exists():
        return 0
    with open(caminho, encoding="utf-8") as f:
        return max(0, sum(1 for _ in f) - 1)


def painel() -> dict:
    """Tudo o que a tela Dados e IA mostra: lakehouse, métricas reais, sombra e rótulos."""
    rel = json.loads((MODELOS / "relatorio.json").read_text(encoding="utf-8"))
    reg = pipeline.ler_registro()
    todos = rotulos()
    por_peca = {p: [r for r in todos if r["peca"] == p] for p in PECAS}
    zonas = dict(
        bronze=[dict(nome="sintetico/vitais_minuto.csv", linhas=_linhas(BRONZE / "sintetico" / "vitais_minuto.csv"), origem="sintetico"),
                dict(nome="cinc2017/training2017.zip", linhas=rel["lote"]["ecg"]["gravacoes"], origem=rel["lote"]["ecg"]["origem"]),
                dict(nome="sintetico/ficha.csv", linhas=_linhas(BRONZE / "sintetico" / "ficha.csv"), origem="ficha de solo")],
        prata=[dict(nome="vitais.csv", linhas=_linhas(PRATA / "vitais.csv")), dict(nome="ecg_atributos.csv", linhas=_linhas(PRATA / "ecg_atributos.csv"))],
        ouro=[dict(nome="m1_rr.csv", linhas=_linhas(OURO / "m1_rr.csv"), peca="m1"),
              dict(nome="m2_qualidade.csv", linhas=_linhas(OURO / "m2_qualidade.csv"), peca="m2"),
              dict(nome="m3_vitais_normais.csv", linhas=_linhas(OURO / "m3_vitais_normais.csv"), peca="m3")])
    return dict(lote=rel["lote"], zonas=zonas, relatorio=rel["modelos"], versoes=ia.versoes(),
                historico=reg["historico"][::-1], sombra=ia.placar_sombra(),
                candidatos={p: _resumo(ia._sombra[p]) for p in ia._sombra},
                ativos={p: _resumo(ia._ativos[p]) for p in PECAS},
                rotulos={p: dict(total=len(v), por_rotulo={k: sum(1 for r in v if r["rotulo"] == k) for k in {r["rotulo"] for r in v}},
                                 ultimos=[{k: r[k] for k in ("tripulante_id", "rotulo", "humano_id", "origem", "versao_modelo", "criado_em")} for r in v[:5]])
                         for p, v in por_peca.items()},
                pecas=PECAS)
