"""API da nave e da Terra (FastAPI). Cada rota devolve só o que aquela
superfície pode ver: relógio, painel de bordo, Houston e família.

Rodar, na pasta 8-backend:  uvicorn app.main:app --port 8000
As telas ficam em http://127.0.0.1:8000/ (pasta 9-frontend servida aqui).
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import hitl, ia
from .config import FRONT, MEDICO_TERRA, MISSOES, MODELOS, ORDEM, ORDEM_PERMANENTE, TRIPULACAO, autonomia, nome_de
from .nave import cosmo, dialogo, registro, trilha
from .nave.motor import FINAIS, PIN_MEDICO, Recusa
from .nave.simulador import Simulador
from .terra import familia

estado = {"sim": None}


def sim() -> Simulador:
    return estado["sim"]


def iniciar(caminho_banco=None) -> Simulador:
    if not (MODELOS / "registro.json").exists():
        raise RuntimeError("Modelos não treinados. Rode antes: python -m treino.pipeline")
    registro.conectar(caminho_banco, limpar_operacional=True)
    trilha.iniciar()
    s = Simulador()
    s.motor.rotular = hitl.rotular
    s.decidir_modelo = hitl._decidir
    estado["sim"] = s
    return s


@asynccontextmanager
async def ciclo_de_vida(app):
    iniciar()
    async def laco():
        while True:
            await asyncio.sleep(1.0)
            try:
                await asyncio.to_thread(sim().passo)
            except Exception:  # um passo com erro não pode parar o relógio da nave
                logging.getLogger("astrohealth").exception("falha num passo do simulador")
    tarefa = asyncio.create_task(laco()) if os.environ.get("ASTRO_SEM_RELOGIO") != "1" else None
    yield
    if tarefa:
        tarefa.cancel()


app = FastAPI(title="AstroHealth OS · API", version="0.1", lifespan=ciclo_de_vida)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def sem_cache(request, call_next):
    """As telas mudam durante o hackathon: o navegador sempre revalida HTML, JS e CSS."""
    resposta = await call_next(request)
    resposta.headers["Cache-Control"] = "no-cache"
    return resposta


# ------------------------------------------------------------------ formatos
def _ev(ev: dict) -> dict:
    t = sim().relogio()
    escondidos = ("vetores", "m1_atributos", "m2_atributos", "ar_t", "exame_t", "cai_t")
    return dict(id=ev["id"], classe=ev["classe"], tipo=ev["tipo"], tripulante_id=ev["tripulante_id"],
                nome=TRIPULACAO[ev["tripulante_id"]]["nome"], estado=ev["estado"], nivel_autonomia=ev["nivel_autonomia"],
                responsavel_papel=ev["responsavel_papel"], responsavel_id=ev["responsavel_id"],
                responsavel_nome=nome_de(ev["responsavel_id"]), prazo_em=ev["prazo_em"],
                medico_local=ev["medico_local"], medico_id=ev["medico_id"], medico_nome=nome_de(ev["medico_id"]),
                prazo_restante_s=None if ev["prazo_t"] is None else max(0, round(ev["prazo_t"] - t)),
                gerado_em=ev["gerado_em"], sugestao=ev["sugestao"], decisoes=ev["decisoes"], historico=ev["historico"],
                escalonamentos=ev["escalonamentos"], consentido=ev["consentido"],
                dados={k: v for k, v in ev["dados"].items() if k not in escondidos})


def _missao() -> dict:
    s = sim()
    return dict(hora_nave=s.agora_iso(), cabine=s.cabine, **dict(s.link.resumo(), autonomia=autonomia(s.link.missao, s.medico_local)),
                equipe=s.equipe(), versoes=ia.versoes(),
                ordem_permanente=dict(ORDEM_PERMANENTE, assinada_por_nome=nome_de(ORDEM_PERMANENTE["assinada_por"]),
                                      em_vigor=s.medico_local == "terra", vale_agora=s.medico_local == "terra" and s.link.blackout),
                perfis={k: v["rotulo"] for k, v in MISSOES.items()},
                aviso="Protótipo experimental com dados simulados. Não é dispositivo médico.")


def _visivel_bordo(e) -> bool:
    """Privado só aparece no painel de bordo com consentimento e se o médico está a
    bordo. Com o médico na Terra, o que a pessoa compartilha vai só para a médica de
    voo: o CMO não vê."""
    if not e["privado"]:
        return e["classe"] == "evento" or e["consentido"]
    return e["consentido"] and e["medico_local"] == "bordo"


def _hormonal_bordo(tid: str, compartilhados: list) -> dict | None:
    """ADR-013 e ADR-014 no painel de bordo. Sem calendário, ou sem médico a bordo
    (o CMO não vê saúde reprodutiva), não vai nada. Com médico a bordo, o painel sabe
    só que é privado, até ela compartilhar pelo relógio; aí vê os sintomas e o pedido
    de cuidado leve. Método e fase nunca saem daqui."""
    s = sim()
    if s.medico_local != "bordo" or not s.pessoas[tid]["analise"]["ficha"]["calendario"]:
        return None
    if any(e["tipo"] == "ciclo" and e["tripulante_id"] == tid for e in compartilhados):
        return dict(compartilhado=True, resumo="pode ter cólica, inchaço ou humor mais baixo e pediu cuidado leve")
    return dict(compartilhado=False)


def _pessoa(tid):
    if tid not in TRIPULACAO:
        raise HTTPException(404, "tripulante não existe")
    return tid


def _trilha_bordo(limite=25) -> dict:
    """Trilha da Cosmo de bordo: chat do painel e sugestões dos eventos que o painel pode ver.
    O chat do relógio é da pessoa e não aparece aqui."""
    s = sim()

    def pode(r):
        if r["superficie"] != "bordo":
            return False
        ev = s.motor.eventos.get(r["evento_id"]) if r["evento_id"] else None
        return r["evento_id"] is None or (ev is not None and _visivel_bordo(ev))
    regs = trilha.listar(pode)
    return dict(resumo=trilha.resumo(regs), registros=regs[:limite])


def _trilha_houston(limite=25) -> dict:
    """Houston vê a própria Cosmo Terra e, pelo link, a trilha das sugestões de bordo
    que já chegaram (métricas e passos, sem a pergunta de ninguém)."""
    chegou = {}
    for p in sim().link.entregues("houston"):
        t = ((p["carga"].get("mensagem") or {}).get("sugestao") or {}).get("trilha")
        if t and t["id"] not in chegou:
            chegou[t["id"]] = dict(t, recebido_em=p["entregue_em"], via_link=True)
    proprios = trilha.listar(lambda r: r["superficie"] == "houston")
    regs = sorted(list(chegou.values()) + proprios, key=lambda r: r.get("recebido_em") or r["quando"], reverse=True)
    return dict(resumo=trilha.resumo(proprios), resumo_bordo=trilha.resumo(list(chegou.values())), registros=regs[:limite])


# ------------------------------------------------------------------ missão e simulador
@app.get("/api/missao")
def missao():
    return _missao()


class Cenario(BaseModel):
    cenario: str
    tripulante_id: str | None = None


@app.post("/api/simulador/cenario")
def cenario(c: Cenario):
    try:
        return sim().injetar(c.cenario, c.tripulante_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/simulador/reiniciar")
def reiniciar():
    with sim().trava:  # espera o passo em curso antes de trocar o banco e o simulador
        iniciar()
    return dict(ok=True, hora_nave=sim().agora_iso())


@app.get("/api/simulador/estado")
def estado_simulador():
    s = sim()
    return dict(hora_nave=s.agora_iso(), fases={t: s.pessoas[t]["fase"] for t in ORDEM}, cabine=s.cabine, equipe=s.equipe(),
                blackout=s.link.blackout, missao=s.link.missao, banco_ecg=s.banco_info,
                abertos=[dict(id=e["id"], tipo=e["tipo"], tripulante_id=e["tripulante_id"], estado=e["estado"],
                              responsavel_id=e["responsavel_id"]) for e in s.motor.abertos()])


# ------------------------------------------------------------------ painel de bordo (oficial médico)
@app.get("/api/bordo")
def bordo():
    """Visão do oficial médico (ou do CMO, com o médico na Terra): sinais de todos,
    eventos clínicos e só os avisos privados que a pessoa autorizou para ele."""
    s = sim()
    with s.trava:
        evs = list(s.motor.eventos.values())
        visiveis = [e for e in evs if e["classe"] == "evento" and _visivel_bordo(e)]
        compartilhados = [e for e in evs if e["classe"] == "aviso" and _visivel_bordo(e)]
        tripulantes = [dict(s.clinico(t), saude_hormonal=_hormonal_bordo(t, compartilhados)) for t in ORDEM]
        return dict(missao=_missao(), tripulantes=tripulantes,
                    eventos=[_ev(e) for e in sorted(visiveis, key=lambda e: (e["estado"] in FINAIS, -e["gerado_t"]))][:12],
                    avisos_compartilhados=[_ev(e) for e in compartilhados][-6:],
                    sombra=ia.placar_sombra(), trilha_cosmo=_trilha_bordo())


@app.get("/api/tripulantes/{tid}/ecg")
def ecg(tid: str):
    return sim().ecg(_pessoa(tid))


@app.get("/api/eventos/{evento_id}/explicacao")
def explicacao(evento_id: str):
    s = sim()
    ev = s.motor.eventos.get(evento_id)
    if not ev:
        raise HTTPException(404, "evento não existe")
    return cosmo.explicar(ev, s.pessoas[ev["tripulante_id"]]["analise"])


# ------------------------------------------------------------------ relógio (a própria pessoa)
@app.get("/api/tripulantes/{tid}/relogio")
def relogio(tid: str):
    """Visão do pulso: os próprios sinais, o que espera uma resposta dessa pessoa
    e os avisos privados dela. Nada aqui é de outro tripulante, exceto a decisão
    que cabe a ela como comandante."""
    s = sim()
    tid = _pessoa(tid)
    with s.trava:
        c = s.clinico(tid)
        a = s.pessoas[tid]["analise"]
        todos = list(s.motor.eventos.values())
        pend = [e for e in todos if e["estado"] not in FINAIS and e["responsavel_id"] == tid
                and (e["tripulante_id"] == tid or e["responsavel_papel"] != "astronauta")]
        meus = [e for e in todos if e["estado"] not in FINAIS and e["tripulante_id"] == tid and e not in pend
                and e["tipo"] in ("arritmia", "sensor_suspeito", "bem_estar", "dor_de_cabeca")]
        emergencia = any(e["tipo"] == "arritmia" for e in pend + meus)
        faixas = [m["faixa"] for m in c["metricas"].values()]
        ciclo = a["ciclo"]
        return dict(eu={k: c[k] for k in ("tripulante_id", "nome", "papel", "gerada_em", "estado", "homeostase", "qualidade",
                                          "fc", "spo2", "hrv", "temp_pele", "respiracao", "agua_ml_dia", "agua_meta",
                                          "sono_min_noite", "estresse", "dose_msv_dia", "metricas", "sexo")},
                    contagem=dict(otimos=faixas.count("padrao"), atencao=faixas.count("atencao"), criticos=faixas.count("critico")),
                    pendencias=[_ev(e) for e in sorted(pend, key=lambda e: e["nivel_autonomia"] * -1)],
                    acompanhando=[_ev(e) for e in meus],
                    emergencia=emergencia,
                    ciclo=None if not ciclo else dict(na_janela=ciclo["na_janela"], aviso_dias=ciclo["aviso_dias"],
                                                      metodo=a["ficha"].get("metodo"), privado=True),
                    calendario=a["ficha"]["calendario"],
                    jogo=None if emergencia else s.jogo,  # o jogo some na emergência
                    mensagens=s.mensagens[-4:][::-1] if tid == "sarah" else [],
                    avisos=list(s.pessoas[tid]["avisos"])[::-1], link=s.link.resumo(), cabine=s.cabine, equipe=s.equipe())


class Decisao(BaseModel):
    evento_id: str
    humano_id: str
    acao: str
    dose: str | None = None
    pin: str | None = None
    detalhe: dict | None = None


@app.post("/api/decisoes")
def decidir(d: Decisao):
    """Única rota que muda o estado de um evento, e só com um humano identificado."""
    s = sim()
    with s.trava:
        try:
            return _ev(s.motor.decidir(d.evento_id, d.humano_id, d.acao, d.dose, d.pin, d.detalhe))
        except Recusa as e:
            raise HTTPException(403, str(e))


class Habito(BaseModel):
    tripulante_id: str


@app.post("/api/habitos/agua")
def agua(h: Habito):
    return dict(agua_ml_dia=sim().beber(_pessoa(h.tripulante_id)))


@app.post("/api/habitos/respiracao")
def respiracao(h: Habito):
    s = sim()
    with s.trava:
        if _pessoa(h.tripulante_id) == "sarah":
            s.missao_feita("respiracao", "Escudo mental")
        s.avisar(h.tripulante_id, "Respiração concluída")
    return dict(ok=True)


class Recado(BaseModel):
    tripulante_id: str
    tipo: str  # sos | sincronia | recado_familia | incentivo


@app.post("/api/relogio/enviar")
def relogio_enviar(r: Recado):
    s = sim()
    nome = TRIPULACAO[_pessoa(r.tripulante_id)]["nome"]
    opcoes = dict(sos=(f"SOS de {nome}: rajada de ECG bruto + sinais", 1, ["houston"], None, 3.2),
                  sincronia=("Telemetria contínua: agregado de 1 minuto", 2, ["houston"], None, 1.8),
                  recado_familia=(f"Recado de {nome} para a família", 3, ["familia"], f"Recado da {nome}: \"Tudo bem por aqui. Saudades de vocês!\"", 0.1),
                  incentivo=(f"Incentivo de {nome} para o Lucas", 4, ["familia"], f"A {nome} mandou um incentivo: \"Arrasou na corrida, filho!\"", 0.1))
    if r.tipo not in opcoes:
        raise HTTPException(400, "tipo desconhecido")
    rot, prio, dest, frase, mb = opcoes[r.tipo]
    with s.trava:
        p = s.link.enviar("up", rot, prioridade=prio, destinos=dest, frase_familia=frase, gerado_em=s.agora_iso(), tamanho_mb=mb)
        if r.tipo == "sos":  # nível 4: o SOS vai para a frente da fila, e isso fica registrado
            registro.auditar("pacote", p["id"], None, "fila P1", r.tripulante_id, dict(acao="SOS na frente da fila"))
        return s.link.publico(p)


# ------------------------------------------------------------------ Cosmo (só leitura)
class Pergunta(BaseModel):
    pergunta: str
    superficie: str = "relogio"
    tripulante_id: str | None = None


def _visao(superficie: str, tid: str | None) -> dict:
    """O que a Cosmo pode ler para responder nessa superfície. Bordo: o agora, sem
    dado privado não consentido. Houston: só o retrato atrasado e os eventos cujo
    pacote já chegou. Relógio: só o que é da própria pessoa."""
    s = sim()
    tid = _pessoa(tid or "sarah")
    v = dict(superficie=superficie, foco=tid, hora=s.agora_iso(), link=dict(s.link.resumo(), autonomia=autonomia(s.link.missao, s.medico_local)),
             versoes=ia.versoes(), avisos=[], sombra={}, equipe=s.equipe(), decisoes_terra=_decisoes_terra(),
             decisoes_modelo=_decisoes_modelo())
    r = s.retrato_terra()
    v["familia"] = familia.feed(s.link, r, v["link"])["frase"]
    if superficie == "houston":
        v.update(tripulantes=[] if r is None else [r["tripulantes"][t] for t in ORDEM], cabine=None if r is None else r["cabine"],
                 dado_de=None if r is None else r["gerada_em"], recebidos=len(s.link.entregues("houston")),
                 eventos=[dict(e, decisoes=[e["decisao"]] if e.get("decisao") else [],
                               dados=dict(seguras=e.get("acoes_seguras"), medicacao=e.get("medicacao")),
                               prazo_restante_s=None, responsavel_nome=None) for e in _eventos_houston()],
                 serie_fc=[] if r is None else [h["tripulantes"][tid]["fc"] for h in s.historico if r["t"] - 60 <= h["t"] <= r["t"]])
        return v
    evs = list(s.motor.eventos.values())
    if superficie == "relogio":
        vis = [e for e in evs if e["estado"] not in FINAIS and (e["tripulante_id"] == tid or e["responsavel_id"] == tid)
               and (e["tripulante_id"] == tid or not e["privado"])]
        v["tripulantes"] = [s.clinico(tid)]
    else:
        vis = [e for e in evs if e["classe"] == "evento" and _visivel_bordo(e)]
        v.update(tripulantes=[s.clinico(t) for t in ORDEM], sombra=ia.placar_sombra(),
                 avisos=[_ev(e) for e in evs if e["classe"] == "aviso" and _visivel_bordo(e)])
    v.update(eventos=[_ev(e) for e in sorted(vis, key=lambda e: (e["estado"] in FINAIS, -e["gerado_t"]))][:8], cabine=s.cabine,
             serie_fc=[h["tripulantes"][tid]["fc"] for h in list(s.historico)[-60:]])
    return v


@app.post("/api/cosmo/chat")
def chat(p: Pergunta):
    """A Cosmo só lê a visão da superfície. Esta rota não muda estado nenhum."""
    with sim().trava:
        visao = _visao(p.superficie, p.tripulante_id)
    return dialogo.conversar(p.pergunta, visao)


@app.get("/api/cosmo/trilha")
def cosmo_trilha(superficie: str = "bordo", limite: int = 25):
    """Trilha mínima da Cosmo (ADR-018): tokens, latência, custo, decisão e passos."""
    with sim().trava:
        if superficie == "houston":
            return _trilha_houston(limite)
        return _trilha_bordo(limite)


@app.get("/api/cosmo/perguntas")
def perguntas(superficie: str = "bordo", tripulante_id: str | None = None):
    """Perguntas principais para o chat, com as do cenário em curso na frente."""
    with sim().trava:
        return dialogo.sugestoes(_visao(superficie, tripulante_id))


# ------------------------------------------------------------------ Terra: Houston
def _eventos_houston() -> list:
    """Houston só conhece um evento pelo último pacote que já chegou."""
    ultimo = {}
    for p in sim().link.entregues("houston"):
        m = p["carga"].get("mensagem")
        if m:
            ultimo[m["evento"]["id"]] = dict(m["evento"], sugestao=m.get("sugestao"), decisao=m.get("decisao"),
                                             acoes_seguras=m.get("acoes_seguras"), medicacao=m.get("medicacao"),
                                             recebido_em=p["entregue_em"], enviado_em=p["gerado_em"],
                                             nome=TRIPULACAO[m["evento"]["tripulante_id"]]["nome"])
    return list(ultimo.values())[::-1]


def _compartilhados_terra() -> list:
    """O que a pessoa autorizou só para a médica de voo. O resto de Houston não vê."""
    vistos = {}
    for p in sim().link.entregues("medico_terra"):
        c = p["carga"]["privado"]
        vistos[c["evento_id"]] = dict(c, recebido_em=p["entregue_em"])
    return list(vistos.values())[::-1]


def _decisoes_terra() -> list:
    s = sim()
    por_id = {p["id"]: p for p in s.link.pacotes}
    return [dict(d, falta_s=s.link.publico(por_id[d["pacote_id"]])["falta_s"] if d["pacote_id"] in por_id else None,
                 pacote_estado=por_id[d["pacote_id"]]["estado"] if d["pacote_id"] in por_id else "entregue")
            for d in s.decisoes_terra][::-1]


def _decisoes_modelo() -> list:
    s = sim()
    por_id = {p["id"]: p for p in s.link.pacotes}
    return [dict(d, falta_s=s.link.publico(por_id[d["pacote_id"]])["falta_s"] if d["pacote_id"] in por_id else None,
                 pacote_estado=por_id[d["pacote_id"]]["estado"] if d["pacote_id"] in por_id else "entregue")
            for d in s.decisoes_modelo][::-1]


@app.get("/api/houston/console")
def houston():
    s = sim()
    with s.trava:
        r = s.retrato_terra()
        recebidos = [s.link.publico(p) for p in s.link.entregues("houston")][-8:][::-1]
        descendo = [s.link.publico(p) for p in s.link.pacotes if p["direcao"] == "down" and p["de"] == "houston"][-4:][::-1]
        pareceres = {e["id"]: e["dados"].get("parecer") for e in s.motor.eventos.values()}
        minhas = _decisoes_terra()
        return dict(missao=_missao(), dado_de=None if r is None else r["gerada_em"],
                    tripulantes=[] if r is None else [r["tripulantes"][t] for t in ORDEM],
                    cabine=None if r is None else r["cabine"], recebidos=recebidos, enviados=descendo,
                    eventos=[dict(e, parecer_entregue=bool(pareceres.get(e["id"])),
                                  minhas_decisoes=[d for d in minhas if d["evento_id"] == e["id"]]) for e in _eventos_houston()],
                    compartilhados=[dict(c, minhas_decisoes=[d for d in minhas if d["evento_id"] == c["evento_id"]])
                                    for c in _compartilhados_terra()],
                    decisoes_terra=minhas, trilha_cosmo=_trilha_houston())


# Decisões que a médica de voo toma do console quando não há médico a bordo.
ACOES_TERRA = dict(arritmia={"confirmar", "recusar", "liberar_medicacao"},
                   dor_de_cabeca={"confirmar", "aprovar_exame", "recusar"}, bem_estar={"marcar_conversa"})
ROTULO_TERRA = dict(confirmar="protocolo confirmado", recusar="recusado: falso alarme", liberar_medicacao="antiarrítmico liberado, dose definida",
                    aprovar_exame="ultrassom ocular aprovado", marcar_conversa="conversa privada marcada")


class DecisaoTerra(BaseModel):
    evento_id: str
    acao: str
    dose: str | None = None
    pin: str | None = None
    detalhe: dict | None = None


@app.post("/api/houston/decisao")
def houston_decisao(d: DecisaoTerra):
    """Sem médico a bordo, a Dra. Rivera decide daqui. A decisão viaja pelo link e só
    vale quando chega à nave; até lá, o CMO segue com as ações seguras."""
    s = sim()
    with s.trava:
        conhecido = {e["id"]: e for e in _eventos_houston()}
        conhecido.update({c["evento_id"]: dict(id=c["evento_id"], tipo=c["tipo"], estado="em_execucao", medico_local="terra",
                                               nome=c["nome"]) for c in _compartilhados_terra()})
        e = conhecido.get(d.evento_id)
        if not e:
            raise HTTPException(409, "Houston ainda não recebeu esse evento")
        if e.get("medico_local") != "terra":
            raise HTTPException(409, "Este evento nasceu com médico a bordo: quem decide é o Dr. Marcus. Daqui vai parecer, não comando.")
        if d.acao not in ACOES_TERRA.get(e["tipo"], set()):
            raise HTTPException(400, f"'{d.acao}' não é decisão de Houston para {e['tipo']}")
        if s.link.blackout:
            raise HTTPException(409, "Sem sinal: a decisão não tem como chegar. A bordo, o CMO segue só os protocolos pré-aprovados; "
                                     "a liberação de medicação fica bloqueada até o contato voltar e, na FA, vale a ordem permanente "
                                     f"{ORDEM_PERMANENTE['id']} que você assinou antes do voo.")
        if e["estado"] in FINAIS:
            raise HTTPException(409, "Pelo último pacote, esse evento já foi encerrado a bordo")
        if (e.get("medicacao") or {}).get("via") == "ordem_permanente":
            raise HTTPException(409, f"Sem sinal, o CMO já usou a ordem permanente {ORDEM_PERMANENTE['id']} neste evento: "
                                     "a dose foi aplicada. Daqui vai parecer, para revisão.")
        minhas = [x for x in s.decisoes_terra if x["evento_id"] == d.evento_id and x["estado"] != "não aplicada"]
        if any(x["acao"] == d.acao for x in minhas):
            raise HTTPException(409, "Essa decisão já foi enviada")
        if d.acao in ("confirmar", "recusar") and any(x["acao"] in ("confirmar", "recusar") for x in minhas):
            raise HTTPException(409, "A conduta deste evento já foi enviada; a próxima mudança é um novo evento ou um parecer")
        if d.acao == "liberar_medicacao":
            if not any(x["acao"] == "confirmar" for x in minhas) and e["estado"] != "em_execucao":
                raise HTTPException(409, "Confirme o protocolo antes: medicação é sempre um passo separado, depois da conduta")
            if not (d.dose or "").strip():
                raise HTTPException(400, "A dose é definida pela médica")
            if d.pin != PIN_MEDICO:
                raise HTTPException(403, "PIN da médica inválido")
        agora = s.agora_iso()
        pac = s.link.enviar("down", f"Decisão da {MEDICO_TERRA['nome']}: {ROTULO_TERRA[d.acao]} · {e['nome']}",
                            prioridade=1 if e["tipo"] == "arritmia" else 2, destinos=["tripulacao"], de="houston", tamanho_mb=0.05,
                            carga=dict(tipo="decisao", evento_id=d.evento_id, acao=d.acao, dose=d.dose, pin=d.pin,
                                       detalhe=d.detalhe, humano_id=MEDICO_TERRA["id"]), gerado_em=agora)
        s.decisoes_terra.append(dict(pacote_id=pac["id"], evento_id=d.evento_id, tipo=e["tipo"], nome=e["nome"], acao=d.acao,
                                     rotulo=ROTULO_TERRA[d.acao], dose=d.dose, enviada_em=agora, estado="a caminho",
                                     chegou_em=None, motivo=None))
        registro.auditar("decisao_terra", d.evento_id, None, "a caminho", MEDICO_TERRA["id"], dict(acao=d.acao, dose=d.dose, pacote=pac["id"]), agora)
        return s.link.publico(pac)


@app.get("/api/houston/serie/{tid}")
def serie(tid: str, segundos: int = 60):
    s = sim()
    with s.trava:
        r = s.retrato_terra()
        if r is None:
            return []
        return [dict(gerada_em=h["gerada_em"], fc=h["tripulantes"][_pessoa(tid)]["fc"])
                for h in s.historico if r["t"] - segundos <= h["t"] <= r["t"]]


class Parecer(BaseModel):
    evento_id: str
    texto: str
    de: str | None = None


@app.post("/api/houston/parecer")
def parecer(p: Parecer):
    """Parecer é revisão, não comando: viaja com o atraso da missão e não muda estado."""
    s = sim()
    with s.trava:
        if p.evento_id not in {e["id"] for e in _eventos_houston()}:
            raise HTTPException(409, "Houston ainda não recebeu esse evento")
        p.de = p.de or (f"{MEDICO_TERRA['nome']} · Houston" if s.medico_local == "terra" else "Flight surgeon · Houston")
        pac = s.link.enviar("down", f"Parecer de Houston: {p.texto}", prioridade=1, destinos=["tripulacao"], de="houston",
                            carga=dict(tipo="parecer", evento_id=p.evento_id, texto=p.texto, de=p.de), gerado_em=s.agora_iso())
        return s.link.publico(pac)


# ------------------------------------------------------------------ Terra: família
@app.get("/api/familia/feed")
def feed():
    s = sim()
    with s.trava:
        f = familia.feed(s.link, s.retrato_terra(), s.link.resumo())
        j = s.jogo
        f["elo"] = dict(estufa_nivel=j["nivel"], estufa_pct=j["pct"], brinde=j["brinde"],
                        corrida="A corrida Terra–órbita está quase completa." if j["corrida_km"] < j["corrida_meta"] else "Corrida Terra–órbita concluída!")
        f["enviadas"] = [s.link.publico(p) for p in s.link.pacotes if p["direcao"] == "down" and p["de"] == "familia"][-5:][::-1]
        return f


class AcaoFamilia(BaseModel):
    tipo: str  # brinde | corrida | mensagem
    texto: str | None = None


@app.post("/api/familia/acao")
def acao_familia(a: AcaoFamilia):
    s = sim()
    rotulos = dict(brinde="Convite da Ana: brinde hídrico", corrida="Lucas registrou uma corrida",
                   mensagem=a.texto or "Áudio do Lucas: \"Boa noite, mãe! Corri hoje.\"")
    if a.tipo not in rotulos:
        raise HTTPException(400, "tipo desconhecido")
    with s.trava:
        if a.tipo == "brinde":
            s.jogo["brinde"] = "enviado"
        p = s.link.enviar("down", rotulos[a.tipo], prioridade=4, destinos=["astronauta"], de="familia",
                          carga=dict(tipo=a.tipo, de="família", km=5), gerado_em=s.agora_iso())
        return s.link.publico(p)


# ------------------------------------------------------------------ auditoria
@app.get("/api/auditoria")
def auditoria(limite: int = 40):
    return dict(cadeia=registro.verificar_cadeia(),
                registros=registro.listar("SELECT * FROM auditoria ORDER BY seq DESC LIMIT ?", (limite,)))


# ------------------------------------------------------------------ dados e IA (human-in-the-loop)
@app.get("/api/ia/painel")
def ia_painel():
    return dict(hitl.painel(), equipe=sim().equipe(), decisoes_modelo=_decisoes_modelo())


@app.get("/api/ia/analise/{tid}")
def ia_analise(tid: str):
    """A saída crua do `ia.analisar` para a última leitura, no formato dos contratos."""
    a = sim().pessoas[_pessoa(tid)]["analise"]
    limpa = lambda m: None if m is None else {k: v for k, v in m.items() if not k.startswith("_")}
    return dict(a, m1=limpa(a["m1"]), m2=limpa(a["m2"]))


class Treino(BaseModel):
    peca: str
    humano_id: str


@app.post("/api/ia/retreinar")
def ia_retreinar(t: Treino):
    s = sim()
    try:
        with s.trava:
            return hitl.retreinar(t.peca, t.humano_id, medico=s.motor.medico())
    except hitl.Negado as e:
        raise HTTPException(409, str(e))


@app.post("/api/ia/modelos/{peca}/{acao}")
def ia_modelo(peca: str, acao: str, t: Treino):
    s = sim()
    if acao not in ("aprovar", "rejeitar"):
        raise HTTPException(404, "ação desconhecida")
    try:
        with s.trava:
            m = s.motor.medico()
            if m != MEDICO_TERRA["id"]:
                return hitl.aprovar(peca, t.humano_id, m) if acao == "aprovar" else hitl.rejeitar(peca, t.humano_id, m)
            versao = hitl.checar(peca, t.humano_id, m)
    except hitl.Negado as e:
        raise HTTPException(403, str(e))
    # Sem médico a bordo, a decisão da médica de voo viaja pelo link (P4) e só vale quando chega (ADR-017).
    with s.trava:
        if any(d["peca"] == peca and d["estado"] == "a caminho" for d in s.decisoes_modelo):
            raise HTTPException(409, "Já há uma decisão sua sobre esta peça a caminho da nave")
        agora = s.agora_iso()
        rotulo = f"{'aprovar' if acao == 'aprovar' else 'rejeitar'} {versao}"
        pac = s.link.enviar("down", f"Decisão da {MEDICO_TERRA['nome']}: {rotulo}", prioridade=4, destinos=["tripulacao"],
                            de="houston", tamanho_mb=0.01, gerado_em=agora,
                            carga=dict(tipo="modelo", peca=peca, acao=acao, versao=versao, humano_id=m))
        s.decisoes_modelo.append(dict(pacote_id=pac["id"], peca=peca, versao=versao, acao=acao, rotulo=rotulo, enviada_em=agora,
                                      estado="a caminho", chegou_em=None, motivo=None))
        registro.auditar("modelo_terra", versao, None, "a caminho", m, dict(acao=acao, peca=peca, pacote=pac["id"]), agora)
        return dict(peca=peca, versao=versao, estado="a caminho", pacote=s.link.publico(pac))


if FRONT.exists():
    app.mount("/", StaticFiles(directory=str(FRONT), html=True), name="telas")
