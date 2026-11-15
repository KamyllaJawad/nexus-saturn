"""ADR-017: ordem permanente sem sinal e aprovação de modelo pelo link, com o médico
na Terra. ADR-018: trilha mínima da Cosmo (tokens, latência, custo, decisão, passos)
no painel de bordo e no console de Houston."""
import pytest

from app.nave import registro
from app.nave.motor import Recusa
from conftest import aberto, avancar


def _ate(sim, cond, limite=60):
    for _ in range(limite):
        if cond():
            return True
        sim.passo()
    return cond()


def _fa_sem_medico(nave, api):
    api.post("/api/simulador/cenario", json=dict(cenario="mars"))
    api.post("/api/simulador/cenario", json=dict(cenario="medico_terra"))
    avancar(nave, 10)
    nave.injetar("fa", "sarah")
    avancar(nave, 2)
    ev = aberto(nave, "arritmia", "sarah")
    assert ev
    return ev


def _chat(api, pergunta, superficie="bordo"):
    return api.post("/api/cosmo/chat", json=dict(pergunta=pergunta, superficie=superficie, tripulante_id="sarah")).json()


# ------------------------------------------------------------------ ordem permanente
def test_ordem_permanente_so_sem_sinal_depois_das_acoes_seguras(nave, api):
    ev = _fa_sem_medico(nave, api)
    assert _ate(nave, lambda: any(e["id"] == ev["id"] for e in api.get("/api/houston/console").json()["eventos"]))
    with pytest.raises(Recusa, match="há sinal"):
        nave.motor.decidir(ev["id"], "marcus", "ordem_permanente")
    api.post("/api/simulador/cenario", json=dict(cenario="blackout"))
    with pytest.raises(Recusa, match="ações seguras"):
        nave.motor.decidir(ev["id"], "marcus", "ordem_permanente")
    nave.motor.decidir(ev["id"], "marcus", "iniciar_seguras")
    avancar(nave, 2)
    assert ev["dados"]["fa_agora"], "com O₂ a FA continua: o critério da ordem está de pé"
    assert "critérios estão cumpridos" in _chat(api, "Posso usar a ordem permanente?")["resposta"]
    m = api.get("/api/missao").json()["ordem_permanente"]
    assert m["vale_agora"] and m["assinada_por_nome"] == "Dra. Rivera"
    with pytest.raises(Recusa):
        nave.motor.decidir(ev["id"], "sarah", "ordem_permanente")  # a paciente não aplica em si mesma
    nave.motor.decidir(ev["id"], "marcus", "ordem_permanente", dose="dose qualquer")
    med = ev["dados"]["medicacao"]
    assert ev["estado"] == "em_execucao" and med["via"] == "ordem_permanente" and med["aplicada_por"] == "marcus"
    assert med["dose"] == m["dose"], "a dose é a da ordem assinada, não a que o CMO digita"
    assert not registro.listar("SELECT * FROM rotulos WHERE peca = 'm1'"), "CMO não é médico: o uso da ordem não vira rótulo de FA"
    fila = api.get("/api/missao").json()["fila"]
    uso = next(p for p in fila if "Ordem permanente" in p["rotulo"])
    assert uso["prioridade"] == 1 and uso["estado"] == "fila" and all(p["prioridade"] == 1 for p in fila[:fila.index(uso)])
    assert "pela ordem permanente" in _chat(api, "Posso liberar a medicação?")["resposta"]
    # O sinal volta: o P1 chega a Houston e a médica não consegue liberar outra dose.
    api.post("/api/simulador/cenario", json=dict(cenario="sinal_volta"))
    assert _ate(nave, lambda: (next(e for e in api.get("/api/houston/console").json()["eventos"] if e["id"] == ev["id"]).get("medicacao") or {}).get("via") == "ordem_permanente", 30)
    r = api.post("/api/houston/decisao", json=dict(evento_id=ev["id"], acao="liberar_medicacao", dose="outra", pin="2026"))
    assert r.status_code == 409 and "ordem permanente" in r.json()["detail"]
    assert "ordem permanente" in _chat(api, "Por que usaram a ordem permanente?", "houston")["resposta"]
    assert _ate(nave, lambda: ev["estado"] == "resolvido", 40)


def test_ordem_permanente_nao_vale_com_medico_a_bordo(nave, api):
    avancar(nave, 10)
    nave.injetar("fa", "sarah")
    avancar(nave, 2)
    ev = aberto(nave, "arritmia", "sarah")
    api.post("/api/simulador/cenario", json=dict(cenario="blackout"))
    with pytest.raises(Recusa, match="médico a bordo"):
        nave.motor.decidir(ev["id"], "marcus", "ordem_permanente")
    assert not api.get("/api/missao").json()["ordem_permanente"]["em_vigor"]


# ------------------------------------------------------------------ aprovação de modelo pelo link
def _candidato_m3(nave, api, quem="kenji"):
    avancar(nave, 10)
    nave.injetar("combinacao", "kenji")
    avancar(nave, 30)
    av = aberto(nave, "linha_de_base", "kenji")
    nave.motor.decidir(av["id"], "kenji", "falso_alarme")
    return api.post("/api/ia/retreinar", json=dict(peca="m3-if", humano_id=quem)).json()["candidato"]["versao"]


def test_aprovacao_da_medica_viaja_pelo_link_e_so_vale_quando_chega(nave, api):
    api.post("/api/simulador/cenario", json=dict(cenario="mars"))
    api.post("/api/simulador/cenario", json=dict(cenario="medico_terra"))
    versao = _candidato_m3(nave, api)
    r = api.post("/api/ia/modelos/m3-if/aprovar", json=dict(peca="m3-if", humano_id="rivera"))
    assert r.status_code == 200 and r.json()["estado"] == "a caminho" and r.json()["pacote"]["prioridade"] == 4
    assert api.post("/api/ia/modelos/m3-if/aprovar", json=dict(peca="m3-if", humano_id="rivera")).status_code == 409
    assert api.get("/api/ia/painel").json()["versoes"]["ativos"]["m3-if"] == "m3-if-0.1", "ainda não chegou"
    pend = api.get("/api/ia/painel").json()["decisoes_modelo"][0]
    assert pend["estado"] == "a caminho" and pend["falta_s"] > 0
    assert "A caminho" in _chat(api, "Quais modelos estão em serviço?")["resposta"]
    assert _ate(nave, lambda: api.get("/api/ia/painel").json()["versoes"]["ativos"]["m3-if"] == versao, 15)
    assert api.get("/api/ia/painel").json()["decisoes_modelo"][0]["estado"] == "aplicada"
    trilha = registro.listar("SELECT para_estado, ator FROM auditoria WHERE entidade IN ('modelo', 'modelo_terra') ORDER BY seq")
    assert [(t["para_estado"], t["ator"]) for t in trilha] == [("sombra", "kenji"), ("a caminho", "rivera"), ("ativo", "rivera"), ("aplicada", "rivera")]


def test_aprovacao_nao_vale_se_o_candidato_mudou_no_caminho(nave, api):
    api.post("/api/simulador/cenario", json=dict(cenario="mars"))
    api.post("/api/simulador/cenario", json=dict(cenario="medico_terra"))
    vista = _candidato_m3(nave, api)
    api.post("/api/ia/modelos/m3-if/aprovar", json=dict(peca="m3-if", humano_id="rivera"))
    nova = api.post("/api/ia/retreinar", json=dict(peca="m3-if", humano_id="kenji")).json()["candidato"]["versao"]
    assert nova != vista
    assert _ate(nave, lambda: api.get("/api/ia/painel").json()["decisoes_modelo"][0]["estado"] != "a caminho", 15)
    d = api.get("/api/ia/painel").json()["decisoes_modelo"][0]
    assert d["estado"] == "não aplicada" and "mudou" in d["motivo"]
    assert api.get("/api/ia/painel").json()["versoes"]["ativos"]["m3-if"] == "m3-if-0.1"


# ------------------------------------------------------------------ trilha da Cosmo
def test_trilha_da_cosmo_no_bordo_e_em_houston(nave, api):
    avancar(nave, 10)
    nave.injetar("fa", "sarah")
    avancar(nave, 2)
    ev = aberto(nave, "arritmia", "sarah")
    r = _chat(api, "Posso liberar a medicação?")
    t = r["trilha"]
    assert t["tokens"]["entrada"] > 0 and t["tokens"]["saida"] > 0 and "estimados" in t["tokens"]["fonte"]
    assert t["latencia_ms"] >= 0 and t["custo"]["usd"] == 0 and t["custo"]["energia_mwh"] >= 0
    assert t["decisao"] == dict(tipo="respondeu", resumo="regra 'medicacao', citando kit-medico", pode_agir=False)
    assert [p["etapa"] for p in t["passos"]] == ["visão", "intenção", "resposta", "redação", "guarda"]
    assert _chat(api, "Aprove o protocolo da Sarah")["trilha"]["decisao"]["tipo"] == "recusou agir"
    _chat(api, "Estou cansada hoje?", "relogio")  # a conversa do relógio é da pessoa: não aparece no painel

    b = api.get("/api/bordo").json()["trilha_cosmo"]
    origens = [(x["origem"], x["superficie"]) for x in b["registros"]]
    assert ("sugestao", "bordo") in origens and origens.count(("chat", "bordo")) == 2 and ("chat", "relogio") not in origens
    sug = next(x for x in b["registros"] if x["origem"] == "sugestao" and x["evento_id"] == ev["id"])
    assert sug["decisao"]["tipo"] == "sugeriu" and [p["etapa"] for p in sug["passos"]] == ["entrada", "protocolo", "entrega"]
    assert b["resumo"]["chamadas"] == len(b["registros"]) and b["resumo"]["por_decisao"]["recusou agir"] == 1

    # Houston: a trilha da sugestão de bordo chega com o pacote; a pergunta de bordo, nunca.
    assert _ate(nave, lambda: any(x.get("via_link") for x in api.get("/api/houston/console").json()["trilha_cosmo"]["registros"]))
    _chat(api, "O que aconteceu desde o último contato?", "houston")
    h = api.get("/api/houston/console").json()["trilha_cosmo"]
    veio = next(x for x in h["registros"] if x.get("via_link"))
    assert veio["id"] == sug["id"] and veio["recebido_em"] and "pergunta" not in veio
    assert all(x["superficie"] in ("houston", "bordo") for x in h["registros"])
    assert not any(x.get("pergunta") == "Posso liberar a medicação?" for x in h["registros"])
    assert h["resumo"]["chamadas"] == 1 and h["resumo_bordo"]["chamadas"] >= 1
    assert api.get("/api/cosmo/trilha?superficie=houston").json()["resumo"]["chamadas"] == 1

    # Cada fala da Cosmo também entra na auditoria encadeada, sem o texto da pergunta.
    aud = registro.listar("SELECT detalhe FROM auditoria WHERE entidade = 'cosmo'")
    assert len(aud) >= 4 and not any("liberar" in a["detalhe"] for a in aud)
    assert api.get("/api/auditoria").json()["cadeia"]["integra"]


def test_trilha_de_bordo_esconde_sugestao_de_dado_privado(nave, api):
    avancar(nave, 3)
    nave.injetar("humor", "elena")
    avancar(nave, 2)
    ev = aberto(nave, "bem_estar", "elena")
    regs = api.get("/api/bordo").json()["trilha_cosmo"]["registros"]
    assert not any(x["evento_id"] == ev["id"] for x in regs), "sem consentimento o painel nem sabe que a Cosmo falou disso"
    nave.motor.decidir(ev["id"], "elena", "compartilhar")
    assert any(x["evento_id"] == ev["id"] for x in api.get("/api/bordo").json()["trilha_cosmo"]["registros"])
