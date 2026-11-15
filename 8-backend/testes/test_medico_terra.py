"""Hipótese da missão sem médico a bordo: o Marcus é oficial de saúde (CMO) e só
inicia as ações seguras pré-aprovadas; quem confirma o protocolo, aprova exame e
libera medicação é a Dra. Rivera, no console de Houston, e a decisão dela só vale
quando o pacote chega à nave."""
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


def _houston_ve(api, evento_id):
    return next((e for e in api.get("/api/houston/console").json()["eventos"] if e["id"] == evento_id), None)


def _fa_sem_medico(nave, api, missao="mars"):
    api.post("/api/simulador/cenario", json=dict(cenario=missao))
    r = api.post("/api/simulador/cenario", json=dict(cenario="medico_terra")).json()
    assert r["cenario"] == "medico_terra"
    avancar(nave, 10)
    nave.injetar("fa", "sarah")
    avancar(nave, 2)
    ev = aberto(nave, "arritmia", "sarah")
    assert ev, "o M1 continua abrindo o evento a bordo, com ou sem médico"
    return ev


def test_troca_de_hipotese_muda_nomes_e_autonomia(nave, api):
    m = api.get("/api/missao").json()
    assert m["equipe"]["local"] == "bordo" and m["equipe"]["medico_nome"] == "Dr. Marcus"
    api.post("/api/simulador/cenario", json=dict(cenario="medico_terra"))
    m = api.get("/api/missao").json()
    assert m["equipe"]["local"] == "terra" and m["equipe"]["medico_nome"] == "Dra. Rivera"
    assert m["equipe"]["marcus"] == dict(nome="Marcus", papel="Oficial de saúde (CMO)")
    assert "Dra. Rivera" in m["autonomia"] and "CMO" in m["autonomia"]
    bordo = api.get("/api/bordo").json()
    assert next(t for t in bordo["tripulantes"] if t["tripulante_id"] == "marcus")["papel"] == "Oficial de saúde (CMO)"
    api.post("/api/simulador/cenario", json=dict(cenario="medico_bordo"))
    assert api.get("/api/missao").json()["equipe"]["medico_nome"] == "Dr. Marcus"


def test_fa_sem_medico_cmo_faz_acoes_seguras_e_a_terra_decide(nave, api):
    ev = _fa_sem_medico(nave, api)
    assert ev["medico_local"] == "terra" and ev["medico_id"] == "rivera"
    assert ev["responsavel_id"] == "marcus" and ev["responsavel_papel"] == "cmo"
    # O CMO não confirma protocolo nem assume; a médica da Terra não decide pela rota de bordo.
    for quem, acao in (("marcus", "confirmar"), ("marcus", "assumir"), ("rivera", "confirmar"), ("cosmo", "confirmar")):
        with pytest.raises(Recusa):
            nave.motor.decidir(ev["id"], quem, acao)
    r = api.post("/api/decisoes", json=dict(evento_id=ev["id"], humano_id="rivera", acao="confirmar"))
    assert r.status_code == 403 and "console de Houston" in r.json()["detail"]
    # Ações seguras pré-aprovadas: não esperam o atraso.
    spo2_antes = nave.clinico("sarah")["spo2"]
    nave.motor.decidir(ev["id"], "marcus", "iniciar_seguras")
    assert ev["estado"] == "aguardando_humano" and ev["dados"]["seguras"]["por"] == "marcus"
    assert ev["responsavel_id"] == "rivera" and ev["prazo_t"] is None, "agora espera a Terra, sem escalar para a IA"
    avancar(nave, 12)
    assert nave.pessoas["sarah"]["fase"] == "fa_o2" and nave.clinico("sarah")["spo2"] > spo2_antes
    assert ev["estado"] == "aguardando_humano", "sem a decisão da Terra, o protocolo não anda"
    # Houston só decide sobre o que já chegou.
    assert _ate(nave, lambda: _houston_ve(api, ev["id"]) is not None)
    he = _houston_ve(api, ev["id"])
    assert he["medico_local"] == "terra"
    # Medicação antes da conduta: fora de ordem, também na Terra.
    r = api.post("/api/houston/decisao", json=dict(evento_id=ev["id"], acao="liberar_medicacao", dose="150 mg", pin="2026"))
    assert r.status_code == 409
    r = api.post("/api/houston/decisao", json=dict(evento_id=ev["id"], acao="confirmar"))
    assert r.status_code == 200 and r.json()["direcao"] == "down"
    assert api.post("/api/houston/decisao", json=dict(evento_id=ev["id"], acao="recusar")).status_code == 409
    assert ev["estado"] == "aguardando_humano", "a decisão viaja: só vale quando chega"
    assert _ate(nave, lambda: ev["estado"] == "em_execucao", 20)
    d = ev["decisoes"][-1]
    assert d["humano_id"] == "rivera" and d["acao"] == "confirmar" and d["via"] == "link"
    # Medicação: dose e PIN da médica; o CMO aplica quando a liberação chega.
    assert api.post("/api/houston/decisao", json=dict(evento_id=ev["id"], acao="liberar_medicacao", dose="150 mg", pin="0000")).status_code == 403
    assert api.post("/api/houston/decisao", json=dict(evento_id=ev["id"], acao="liberar_medicacao", dose="", pin="2026")).status_code == 400
    assert api.post("/api/houston/decisao", json=dict(evento_id=ev["id"], acao="liberar_medicacao", dose="150 mg", pin="2026")).status_code == 200
    with pytest.raises(Recusa):
        nave.motor.decidir(ev["id"], "marcus", "aplicar_medicacao")  # ainda não chegou
    with pytest.raises(Recusa):
        nave.motor.decidir(ev["id"], "marcus", "liberar_medicacao", dose="150 mg", pin="2026")  # o CMO não libera
    assert _ate(nave, lambda: bool(ev["dados"].get("medicacao")), 20)
    assert ev["dados"]["medicacao"]["liberada_por"] == "rivera" and ev["dados"]["medicacao"]["aplicada"] is False
    with pytest.raises(Recusa):
        nave.motor.decidir(ev["id"], "sarah", "aplicar_medicacao")  # a paciente não aplica a própria dose
    nave.motor.decidir(ev["id"], "marcus", "aplicar_medicacao")
    assert ev["dados"]["medicacao"]["aplicada_por"] == "marcus"
    # O que Houston mandou fica rastreado; a regra de resolução é a mesma.
    minhas = api.get("/api/houston/console").json()["decisoes_terra"]
    assert {x["acao"]: x["estado"] for x in minhas} == dict(confirmar="aplicada", liberar_medicacao="aplicada")
    avancar(nave, 60)
    assert ev["estado"] == "resolvido"
    rot = registro.listar("SELECT * FROM rotulos WHERE peca = 'm1'")
    assert rot and rot[0]["humano_id"] == "rivera", "a decisão da Terra também vira rótulo para o treino"
    assert registro.listar("SELECT * FROM auditoria WHERE entidade = 'decisao_terra' AND para_estado = 'aplicada'")


def test_cmo_que_nao_responde_escala_a_bordo_nunca_para_a_ia(nave, api):
    ev = _fa_sem_medico(nave, api)
    avancar(nave, 62)
    assert ev["escalonamentos"] == 1 and ev["responsavel_id"] == "kenji" and ev["responsavel_papel"] == "cmo"
    with pytest.raises(Recusa):
        nave.motor.decidir(ev["id"], "marcus", "iniciar_seguras")  # agora é o Kenji
    nave.motor.decidir(ev["id"], "kenji", "iniciar_seguras")
    assert ev["responsavel_id"] == "rivera"


def test_sem_sinal_e_sem_medico_medicacao_fica_bloqueada(nave, api):
    ev = _fa_sem_medico(nave, api)
    assert _ate(nave, lambda: _houston_ve(api, ev["id"]) is not None)
    api.post("/api/simulador/cenario", json=dict(cenario="blackout"))
    nave.motor.decidir(ev["id"], "marcus", "iniciar_seguras")  # as ações seguras não dependem do link
    r = api.post("/api/houston/decisao", json=dict(evento_id=ev["id"], acao="confirmar"))
    assert r.status_code == 409 and "bloqueada" in r.json()["detail"]
    chat = api.post("/api/cosmo/chat", json=dict(pergunta="Posso liberar a medicação?", superficie="bordo", tripulante_id="sarah")).json()
    assert "bloqueada" in chat["resposta"]
    avancar(nave, 30)
    assert ev["estado"] == "aguardando_humano" and not ev["dados"].get("medicacao")
    api.post("/api/simulador/cenario", json=dict(cenario="sinal_volta"))
    assert api.post("/api/houston/decisao", json=dict(evento_id=ev["id"], acao="confirmar")).status_code == 200
    assert _ate(nave, lambda: ev["estado"] == "em_execucao", 20)


def test_com_medico_a_bordo_houston_nao_decide(nave, api):
    avancar(nave, 10)
    nave.injetar("fa", "sarah")
    avancar(nave, 2)
    ev = aberto(nave, "arritmia", "sarah")
    assert _ate(nave, lambda: _houston_ve(api, ev["id"]) is not None)
    r = api.post("/api/houston/decisao", json=dict(evento_id=ev["id"], acao="confirmar"))
    assert r.status_code == 409 and "parecer" in r.json()["detail"]
    with pytest.raises(Recusa):
        nave.motor.decidir(ev["id"], "marcus", "iniciar_seguras")
    # Trocar a hipótese no meio não muda a regra de um evento aberto.
    api.post("/api/simulador/cenario", json=dict(cenario="medico_terra"))
    assert ev["medico_local"] == "bordo"
    nave.motor.decidir(ev["id"], "marcus", "confirmar")
    assert ev["estado"] == "em_execucao"


def test_dor_de_cabeca_sem_medico_ar_a_bordo_exame_pela_terra(nave, api):
    api.post("/api/simulador/cenario", json=dict(cenario="medico_terra"))
    avancar(nave, 3)
    api.post("/api/simulador/cenario", json=dict(cenario="dor_de_cabeca", tripulante_id="kenji"))
    ev = aberto(nave, "dor_de_cabeca", "kenji")
    assert ev["responsavel_id"] == "marcus" and ev["responsavel_papel"] == "cmo"
    with pytest.raises(Recusa):
        nave.motor.decidir(ev["id"], "marcus", "aprovar_exame")
    nave.motor.decidir(ev["id"], "marcus", "iniciar_seguras")
    avancar(nave, 8)
    assert ev["dados"]["ar"] == "feito" and nave.cabine["co2"] < 3, "o ajuste do ar não espera a Terra"
    assert ev["estado"] == "aguardando_humano"
    assert _ate(nave, lambda: _houston_ve(api, ev["id"]) is not None)
    assert api.post("/api/houston/decisao", json=dict(evento_id=ev["id"], acao="aprovar_exame")).status_code == 200
    assert _ate(nave, lambda: ev["estado"] == "resolvido", 40)
    assert any(d["humano_id"] == "rivera" and d["acao"] == "aprovar_exame" for d in ev["decisoes"])


def test_privado_vai_so_para_a_medica_da_terra_e_o_cmo_nao_ve(nave, api):
    api.post("/api/simulador/cenario", json=dict(cenario="medico_terra"))
    avancar(nave, 3)
    api.post("/api/simulador/cenario", json=dict(cenario="humor", tripulante_id="sarah"))
    ev = aberto(nave, "bem_estar", "sarah")
    nave.motor.decidir(ev["id"], "sarah", "compartilhar")
    assert ev["consentido"] and ev["responsavel_id"] == "rivera"
    cons = registro.listar("SELECT * FROM consentimentos")
    assert cons[-1]["destinatario"] == "medico_terra"
    # O CMO, no painel de bordo, não vê; nem o chat de bordo.
    bordo = api.get("/api/bordo").json()
    assert not any(e["tipo"] == "bem_estar" for e in bordo["eventos"])
    chat = api.post("/api/cosmo/chat", json=dict(pergunta="O que Sarah compartilhou sobre bem-estar?", superficie="bordo", tripulante_id="sarah")).json()
    assert "sono mais curto" not in chat["resposta"]
    # Só a médica da Terra recebe, com o atraso, fora da lista geral de Houston.
    assert _ate(nave, lambda: bool(api.get("/api/houston/console").json()["compartilhados"]), 20)
    h = api.get("/api/houston/console").json()
    c = h["compartilhados"][0]
    assert c["tipo"] == "bem_estar" and "sono mais curto" in c["resumo"]
    assert not any(e["tipo"] == "bem_estar" for e in h["eventos"])
    assert "sono mais curto" not in str(api.get("/api/familia/feed").json())
    assert api.post("/api/houston/decisao", json=dict(evento_id=ev["id"], acao="marcar_conversa", detalhe=dict(hora="19:00"))).status_code == 200
    assert _ate(nave, lambda: ev["estado"] == "resolvido", 20)
    assert ev["dados"]["conversa"] == "19:00"


def test_ciclo_compartilhado_sem_medico_a_bordo_nao_aparece_no_painel(nave, api):
    api.post("/api/simulador/cenario", json=dict(cenario="medico_terra"))
    avancar(nave, 3)
    nave.injetar("ciclo", "sarah")
    assert _ate(nave, lambda: aberto(nave, "ciclo", "sarah") is not None, 40)
    ev = aberto(nave, "ciclo", "sarah")
    nave.motor.decidir(ev["id"], "sarah", "compartilhar")
    assert not any(a["tipo"] == "ciclo" for a in api.get("/api/bordo").json()["avisos_compartilhados"])
    assert _ate(nave, lambda: any(c["tipo"] == "ciclo" for c in api.get("/api/houston/console").json()["compartilhados"]), 20)


def test_modelo_novo_sem_medico_a_bordo_e_aprovado_pela_medica(nave, api):
    api.post("/api/simulador/cenario", json=dict(cenario="medico_terra"))
    r = api.post("/api/ia/modelos/m1/aprovar", json=dict(peca="m1", humano_id="marcus"))
    assert r.status_code == 403 and "Dra. Rivera" in r.json()["detail"]
    r = api.post("/api/ia/modelos/m1/aprovar", json=dict(peca="m1", humano_id="rivera"))
    assert r.status_code == 403 and "candidato" in r.json()["detail"]  # passou do humano; falta o candidato


@pytest.mark.parametrize("superficie", ["bordo", "houston"])
def test_chat_sabe_onde_esta_o_medico(nave, api, superficie):
    ev = _fa_sem_medico(nave, api)
    nave.motor.decidir(ev["id"], "marcus", "iniciar_seguras")
    assert _ate(nave, lambda: _houston_ve(api, ev["id"]) is not None and _houston_ve(api, ev["id"]).get("acoes_seguras"))
    grupos = api.get(f"/api/cosmo/perguntas?superficie={superficie}&tripulante_id=sarah").json()
    todas = [p for g in grupos for p in g["perguntas"]]
    agora = next(g for g in grupos if g["grupo"] == "Agora")["perguntas"]
    if superficie == "houston":
        assert "O que espera a minha decisão?" in agora
    else:
        assert "Quando chega a decisão da Dra. Rivera?" in agora
    for p in todas:
        r = api.post("/api/cosmo/chat", json=dict(pergunta=p, superficie=superficie, tripulante_id="sarah")).json()
        assert r["pode_agir"] is False and len(r["resposta"]) > 20, p
    eq = api.post("/api/cosmo/chat", json=dict(pergunta="Quem é o médico desta missão?", superficie=superficie, tripulante_id="sarah")).json()
    assert "Rivera" in eq["resposta"] and "CMO" in eq["resposta"]
    med = api.post("/api/cosmo/chat", json=dict(pergunta="Posso liberar a medicação?", superficie=superficie, tripulante_id="sarah")).json()
    assert "Rivera" in med["resposta"] or superficie == "houston" and "confirme o protocolo" in med["resposta"]
    if superficie == "houston":
        pend = api.post("/api/cosmo/chat", json=dict(pergunta="O que espera a minha decisão?", superficie="houston", tripulante_id="sarah")).json()
        assert "conduta sua" in pend["resposta"] and "ações seguras" in pend["resposta"]
        api.post("/api/houston/decisao", json=dict(evento_id=ev["id"], acao="confirmar"))
        ida = api.post("/api/cosmo/chat", json=dict(pergunta="Minha decisão já chegou a bordo?", superficie="houston", tripulante_id="sarah")).json()
        assert "protocolo confirmado" in ida["resposta"] and "a caminho" in ida["resposta"]
