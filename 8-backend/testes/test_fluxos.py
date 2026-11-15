"""Testes de aceitação dos fluxos: o cenário só muda o sinal; quem detecta são os
modelos treinados, quem muda estado é o motor, e quem decide é um humano."""
import re

import pytest

from app.nave import registro
from app.nave.motor import Recusa
from conftest import aberto, avancar


def test_rotina_nao_abre_evento_clinico(nave):
    avancar(nave, 90)
    assert [e for e in nave.motor.eventos.values() if e["classe"] == "evento"] == []
    assert nave.clinico("sarah")["estado"] == "otimo"
    assert nave.clinico("kenji")["m1"]["classe"] != "fa"


def test_fa_vira_evento_em_ate_2s_e_so_o_humano_decide(nave):
    avancar(nave, 10)
    nave.injetar("fa", "sarah")
    avancar(nave, 2)
    ev = aberto(nave, "arritmia", "sarah")
    assert ev, "o M1 tem de abrir o evento em até 2 s"
    assert ev["estado"] == "aguardando_humano" and ev["nivel_autonomia"] == 3
    assert ev["responsavel_id"] == "marcus"
    assert ev["sugestao"]["versao_modelo"].startswith("arritmia-borda")
    assert len(ev["sugestao"]["evidencias"]) == 3  # os 3 atributos de RR que mais pesaram
    # Sem humano, o estado não anda sozinho (dentro do prazo).
    avancar(nave, 20)
    assert ev["estado"] == "aguardando_humano"
    # A Cosmo não é um humano; quem não é o responsável também não decide.
    with pytest.raises(Recusa):
        nave.motor.decidir(ev["id"], "cosmo", "confirmar")
    with pytest.raises(Recusa):
        nave.motor.decidir(ev["id"], "elena", "confirmar")
    # Medicação antes de confirmar o protocolo: fora de ordem.
    with pytest.raises(Recusa):
        nave.motor.decidir(ev["id"], "marcus", "liberar_medicacao", dose="150 mg", pin="2026")
    nave.motor.decidir(ev["id"], "marcus", "confirmar")
    assert ev["estado"] == "em_execucao"
    # Medicação é passo separado, só do oficial médico, com dose e PIN.
    with pytest.raises(Recusa):
        nave.motor.decidir(ev["id"], "sarah", "liberar_medicacao", dose="150 mg", pin="2026")
    with pytest.raises(Recusa):
        nave.motor.decidir(ev["id"], "marcus", "liberar_medicacao", dose="150 mg", pin="0000")
    nave.motor.decidir(ev["id"], "marcus", "liberar_medicacao", dose="150 mg", pin="2026")
    assert ev["dados"]["medicacao"]["liberada_por"] == "marcus"
    # O quadro cede e o motor resolve pela regra, não por decisão da IA.
    avancar(nave, 60)
    assert ev["estado"] == "resolvido"
    # A decisão virou rótulo para o próximo treino do M1.
    rot = registro.listar("SELECT * FROM rotulos WHERE peca = 'm1'")
    assert rot and rot[0]["rotulo"] == "fa" and rot[0]["humano_id"] == "marcus"


def test_prazo_vencido_escala_para_outro_humano_nunca_para_a_ia(nave):
    avancar(nave, 10)
    nave.injetar("fa", "sarah")
    avancar(nave, 2)
    ev = aberto(nave, "arritmia", "sarah")
    avancar(nave, 62)
    assert ev["estado"] == "aguardando_humano" and ev["escalonamentos"] == 1
    assert ev["responsavel_id"] == "kenji"  # a Sarah é a paciente: sai da cadeia
    assert not [d for d in ev["decisoes"]], "ninguém decidiu: o protocolo não foi aplicado"
    nave.motor.decidir(ev["id"], "kenji", "confirmar")
    with pytest.raises(Recusa):  # medicação não escala: continua só com o oficial médico
        nave.motor.decidir(ev["id"], "kenji", "liberar_medicacao", dose="150 mg", pin="2026")


def test_relogio_folgado_pergunta_antes_de_alarmar(nave):
    avancar(nave, 10)
    nave.injetar("sensor_solto", "sarah")
    avancar(nave, 2)
    ev = aberto(nave, "sensor_suspeito", "sarah")
    assert ev and ev["estado"] == "confirmacao_astronauta"
    c = nave.clinico("sarah")
    assert c["m2"]["qualidade"] == "suspeito" and c["estado"] == "suspeito"
    assert c["m1"]["classe"] is None, "com sinal suspeito o M1 não dispara"
    assert not aberto(nave, "arritmia", "sarah")
    nave.motor.decidir(ev["id"], "sarah", "ajustar_sensor")
    assert ev["estado"] == "encerrado"
    avancar(nave, 6)
    assert nave.clinico("sarah")["estado"] == "otimo"
    assert registro.listar("SELECT rotulo FROM rotulos WHERE peca = 'm2'")[0]["rotulo"] == "suspeito"


def test_relogio_folgado_sem_resposta_em_20s_vai_ao_medico(nave):
    avancar(nave, 10)
    nave.injetar("sensor_solto", "sarah")
    avancar(nave, 24)
    ev = aberto(nave, "sensor_suspeito", "sarah")
    assert ev["estado"] == "aguardando_humano" and ev["responsavel_id"] == "marcus"
    nave.motor.decidir(ev["id"], "marcus", "registrar_kit", detalhe=dict(spo2_kit=97))
    assert ev["estado"] == "encerrado" and "desmentiu" in ev["dados"]["desfecho"]


def test_floresta_vira_sugestao_de_nivel_1_sem_evento_clinico(nave):
    avancar(nave, 10)
    nave.injetar("combinacao", "kenji")
    avancar(nave, 12)
    c = nave.clinico("kenji")
    assert c["isolation_forest"]["anomalo"] and c["estado"] != "critico"
    assert all(m["faixa"] != "critico" for m in c["metricas"].values())
    av = aberto(nave, "linha_de_base", "kenji")
    assert av and av["classe"] == "aviso" and av["nivel_autonomia"] == 1
    assert not [e for e in nave.motor.eventos.values() if e["classe"] == "evento"]
    assert not nave.link.pacotes, "sugestão de nível 1 não vai para a Terra"


def test_ciclo_e_privado_e_so_abre_para_quem_tem_calendario(nave, api):
    avancar(nave, 10)
    nave.injetar("ciclo", "sarah")
    nave.injetar("ciclo", "kenji")  # mesmo desvio de sinal em quem não tem calendário
    avancar(nave, 60)
    av = aberto(nave, "ciclo", "sarah")
    assert av and av["nivel_autonomia"] == 2
    assert nave.clinico("sarah")["estado"] == "otimo", "o estado de três níveis não muda"
    assert not aberto(nave, "ciclo", "kenji") and nave.pessoas["kenji"]["analise"]["ciclo"] is None
    assert not aberto(nave, "linha_de_base", "sarah"), "o calendário explica o trecho: a floresta não avisa"
    bordo = api.get("/api/bordo").json()
    assert "ciclo" not in str(bordo["eventos"]) and bordo["avisos_compartilhados"] == []
    nave.motor.decidir(av["id"], "sarah", "confirmar_sintoma")
    with pytest.raises(Recusa):  # ninguém compartilha no lugar dela
        nave.motor.decidir(av["id"], "marcus", "compartilhar")
    nave.motor.decidir(av["id"], "sarah", "compartilhar")
    assert [a["tipo"] for a in api.get("/api/bordo").json()["avisos_compartilhados"]] == ["ciclo"]
    avancar(nave, 30)
    assert "ciclo" not in str(api.get("/api/houston/console").json()).lower()
    assert "ciclo" not in str(api.get("/api/familia/feed").json()).lower()


def test_saude_mental_so_sai_do_relogio_com_consentimento(nave, api):
    avancar(nave, 5)
    nave.injetar("humor", "sarah")
    ev = aberto(nave, "bem_estar", "sarah")
    assert ev["responsavel_id"] == "sarah"
    avancar(nave, 200)
    assert ev["estado"] == "aguardando_humano" and ev["escalonamentos"] == 0, "não escala"
    assert api.get("/api/bordo").json()["eventos"] == []
    assert not nave.link.pacotes
    nave.motor.decidir(ev["id"], "sarah", "compartilhar")
    assert [e["tipo"] for e in api.get("/api/bordo").json()["eventos"]] == ["bem_estar"]
    nave.motor.decidir(ev["id"], "marcus", "marcar_conversa", detalhe=dict(hora="19:00"))
    assert ev["estado"] == "resolvido"
    assert not nave.link.pacotes, "nem com consentimento isso vai para a Terra"


def test_tempestade_solar_comandante_decide_e_modo_noite_tem_veto(nave):
    avancar(nave, 5)
    nave.injetar("tempestade_solar")
    ev = aberto(nave, "tempestade_solar")
    assert ev["dados"]["rota_acesa"] and ev["responsavel_id"] == "sarah"
    with pytest.raises(Recusa):
        nave.motor.decidir(ev["id"], "marcus", "confirmar")
    nave.motor.decidir(ev["id"], "sarah", "adiar")
    avancar(nave, 10)
    assert ev["estado"] == "aguardando_humano" and not ev["dados"]["adiado"]
    nave.motor.decidir(ev["id"], "sarah", "confirmar")
    assert nave.cabine["abrigo"]
    with pytest.raises(Recusa):
        nave.motor.decidir(ev["id"], "sarah", "liberar_abrigo")  # fluxo ainda alto
    avancar(nave, 20)
    nave.motor.decidir(ev["id"], "sarah", "liberar_abrigo")
    assert ev["estado"] == "resolvido" and not nave.cabine["abrigo"]

    nave.injetar("modo_noite", "sarah")
    noite = aberto(nave, "modo_noite", "sarah")
    assert noite["estado"] == "agendado" and noite["nivel_autonomia"] == 4
    avancar(nave, 16)
    assert noite["estado"] == "aplicado" and nave.cabine["luz"] == "noite"
    nave.motor.decidir(noite["id"], "sarah", "desfazer")
    assert noite["estado"] == "encerrado" and nave.cabine["luz"] == "dia"


def test_houston_ve_o_passado_e_o_blackout_guarda_por_prioridade(nave, api):
    nave.injetar("mars")
    avancar(nave, 12)
    nave.injetar("fa", "sarah")
    avancar(nave, 3)
    ev = aberto(nave, "arritmia", "sarah")
    h = api.get("/api/houston/console").json()
    assert h["eventos"] == [], "o alerta ainda está viajando"
    assert h["dado_de"] < h["missao"]["hora_nave"]
    assert next(t for t in h["tripulantes"] if t["tripulante_id"] == "sarah")["estado"] == "otimo"
    assert api.post("/api/houston/parecer", json=dict(evento_id=ev["id"], texto="ok")).status_code == 409
    avancar(nave, 9)
    h = api.get("/api/houston/console").json()
    assert [e["tipo"] for e in h["eventos"]] == ["arritmia"]
    assert h["recebidos"][0]["gerado_em"] < h["recebidos"][0]["entregue_em"]
    nave.motor.decidir(ev["id"], "marcus", "confirmar")
    api.post("/api/houston/parecer", json=dict(evento_id=ev["id"], texto="De acordo com o protocolo."))
    assert "parecer" not in ev["dados"], "o parecer também leva o atraso da missão"
    avancar(nave, 10)
    assert ev["dados"]["parecer"]["texto"] == "De acordo com o protocolo."
    assert {d["humano_id"] for d in ev["decisoes"]} == {"marcus"}, "parecer é revisão: não entra como decisão"

    nave.injetar("blackout")
    api.post("/api/relogio/enviar", json=dict(tripulante_id="sarah", tipo="incentivo"))
    api.post("/api/relogio/enviar", json=dict(tripulante_id="sarah", tipo="sincronia"))
    api.post("/api/relogio/enviar", json=dict(tripulante_id="sarah", tipo="sos"))
    avancar(nave, 30)
    fila = api.get("/api/missao").json()["fila"]
    assert [p["prioridade"] for p in fila[:3]] == [1, 2, 4] and all(p["estado"] == "fila" for p in fila)
    nave.injetar("sinal_volta")
    avancar(nave, 12)
    chegada = sorted((p for p in nave.link.pacotes if p["prioridade"] in (1, 2, 4) and p["entregue_em"]
                      and "SOS" in p["rotulo"] or "Telemetria" in p["rotulo"] or "Incentivo" in p["rotulo"]),
                     key=lambda p: p["chega_t"])
    assert [p["prioridade"] for p in chegada] == [1, 2, 4], "P1 sai primeiro quando a janela abre"


def test_familia_recebe_frases_e_nunca_numeros(nave, api):
    nave.injetar("leo")
    avancar(nave, 5)
    nave.injetar("fa", "sarah")
    avancar(nave, 3)
    ev = aberto(nave, "arritmia", "sarah")
    antes = api.get("/api/familia/feed").json()
    assert antes["ultimas"] == [], "a família só sabe depois da decisão a bordo"
    nave.motor.decidir(ev["id"], "marcus", "confirmar")
    nave.motor.decidir(ev["id"], "marcus", "liberar_medicacao", dose="150 mg", pin="2026")
    avancar(nave, 4)
    f = api.get("/api/familia/feed").json()
    textos = " ".join([f["frase"]] + [i["frase"] for i in f["ultimas"]] + list(f["tripulacao"].values()))
    assert "oficial médico" in textos
    assert not re.search(r"\d", textos), "nenhum número sai para a família"
    for proibido in ("bpm", "spo", "fibrila", "arritmia", "mg", "escore", "ciclo"):
        assert proibido not in textos.lower()


def test_auditoria_encadeada_denuncia_adulteracao(nave):
    avancar(nave, 5)
    nave.injetar("fa", "sarah")
    avancar(nave, 3)
    nave.motor.decidir(aberto(nave, "arritmia", "sarah")["id"], "marcus", "confirmar")
    cadeia = registro.verificar_cadeia()
    assert cadeia["integra"] and cadeia["registros"] > 5
    atores = {r["ator"] for r in registro.listar("SELECT ator FROM auditoria WHERE entidade = 'decisao'")}
    assert atores == {"marcus"}, "100% das decisões com um humano registrado"
    registro._con.execute("UPDATE auditoria SET ator = 'ninguem' WHERE entidade = 'decisao'")
    assert not registro.verificar_cadeia()["integra"]


def test_cosmo_explica_cita_a_fonte_e_nao_tem_como_agir(nave, api):
    avancar(nave, 5)
    nave.injetar("fa", "sarah")
    avancar(nave, 3)
    ev = aberto(nave, "arritmia", "sarah")
    r = api.post("/api/cosmo/chat", json=dict(pergunta="aprove o protocolo agora e libere a medicação", superficie="bordo", tripulante_id="sarah")).json()
    assert r["pode_agir"] is False and ev["estado"] == "aguardando_humano" and not ev["decisoes"]
    r = api.post("/api/cosmo/chat", json=dict(pergunta="o que fazer na fibrilação atrial?", superficie="bordo", tripulante_id="sarah")).json()
    assert "fibrilação atrial" in r["fonte"]["titulo"].lower()
    e = api.get(f"/api/eventos/{ev['id']}/explicacao").json()
    assert e["protocolo"]["fonte"] and e["versao_modelo"] and len(e["evidencias"]) == 3
    from app.nave import cosmo
    from app.nave import dialogo
    for modulo in (cosmo, dialogo):  # quem conversa não importa quem decide nem o simulador
        fonte = open(modulo.__file__, encoding="utf-8").read()
        assert not re.search(r"^\s*(from|import) .*(motor|simulador|registro)", fonte, re.M) and not hasattr(modulo, "decidir")


def test_rotulo_humano_retreina_candidato_em_sombra_e_so_o_medico_promove(nave, api):
    """Human-in-the-loop do modelo, de ponta a ponta (ADR-010)."""
    avancar(nave, 10)
    nave.injetar("combinacao", "kenji")
    avancar(nave, 14)
    av = aberto(nave, "linha_de_base", "kenji")
    assert api.post("/api/ia/retreinar", json=dict(peca="m3-if", humano_id="marcus")).status_code == 409  # sem rótulo, sem retreino
    avancar(nave, 50)  # as leituras do episódio vão sendo guardadas enquanto o aviso espera a resposta
    nave.motor.decidir(av["id"], "kenji", "falso_alarme")  # "é o meu normal hoje"
    antes = api.get("/api/ia/painel").json()
    assert antes["rotulos"]["m3-if"]["por_rotulo"] == {"normal": 1}
    r = api.post("/api/ia/retreinar", json=dict(peca="m3-if", humano_id="marcus")).json()
    assert r["candidato"]["versao"] == "m3-if-0.2" and r["ativo"]["versao"] == "m3-if-0.1"
    assert r["candidato"]["por_tripulante"]["kenji"]["rotulos_humanos"]["normal"] > 0
    assert r["candidato"]["por_tripulante"]["kenji"]["rotulos_humanos"]["normais_abaixo_do_limiar"] >= 0.8, r["candidato"]["por_tripulante"]["kenji"]
    # O custo aparece para quem aprova: declarar esse padrão normal tira um pouco do
    # recall nessa direção. O candidato perde sensibilidade, mas não pode ficar cego,
    # e as outras pessoas não mudam.
    cand = r["candidato"]["por_tripulante"]
    assert 0.7 <= cand["kenji"]["recall_desvio_em_3_sinais"] <= r["ativo"]["por_tripulante"]["kenji"]["recall_desvio_em_3_sinais"]
    assert cand["sarah"]["recall_desvio_em_3_sinais"] >= 0.9 and cand["sarah"]["rotulos_humanos"]["normal"] == 0
    # Em sombra: o candidato roda em cada leitura, mas quem está em serviço não mudou.
    avancar(nave, 40)
    c = nave.clinico("kenji")
    assert c["isolation_forest"]["versao_modelo"] == "m3-if-0.1" and c["isolation_forest"]["anomalo"]
    assert c["sombra"]["m3-if"]["versao_modelo"] == "m3-if-0.2"
    placar = api.get("/api/ia/painel").json()["sombra"]["m3-if"]
    assert placar["leituras"] >= 160 and placar["divergem"] >= 30, "o candidato parou de avisar onde o humano disse que era normal"
    assert placar["concordam"] > placar["divergem"], "nas outras pessoas os dois modelos concordam"
    # Só o oficial médico promove.
    assert api.post("/api/ia/modelos/m3-if/aprovar", json=dict(peca="m3-if", humano_id="kenji")).status_code == 403
    assert api.post("/api/ia/modelos/m3-if/aprovar", json=dict(peca="m3-if", humano_id="marcus")).json()["em_servico"] == "m3-if-0.2"
    avancar(nave, 8)
    assert nave.clinico("kenji")["isolation_forest"]["versao_modelo"] == "m3-if-0.2"
    assert not aberto(nave, "linha_de_base", "kenji")
    trilha = registro.listar("SELECT para_estado, ator FROM auditoria WHERE entidade = 'modelo' ORDER BY seq")
    assert [(t["para_estado"], t["ator"]) for t in trilha] == [("sombra", "marcus"), ("ativo", "marcus")]
    # O modelo novo continua vendo uma anomalia de verdade.
    nave.injetar("fa", "sarah")
    avancar(nave, 3)
    assert aberto(nave, "arritmia", "sarah")
