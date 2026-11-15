"""Campos do painel de bordo em Vue (9-frontend/vue): silhueta por órgão, sexo da
ficha e saúde hormonal. O servidor decide e filtra; o front só pinta."""
from app.nave.simulador import corpo
from conftest import aberto, avancar

FAIXAS = {"padrao", "atencao", "critico"}


def _pessoa(api, tid):
    return next(t for t in api.get("/api/bordo").json()["tripulantes"] if t["tripulante_id"] == tid)


def test_bordo_traz_sexo_e_corpo_com_faixas(nave, api):
    avancar(nave, 5)
    for t in api.get("/api/bordo").json()["tripulantes"]:
        assert t["sexo"] in ("feminino", "masculino")
        assert set(t["corpo"]) == {"cerebro", "coracao", "pulmoes", "rins"}
        assert set(t["corpo"].values()) <= FAIXAS


def test_fa_deixa_o_coracao_critico(nave, api):
    avancar(nave, 10)
    nave.injetar("fa", "sarah")
    avancar(nave, 2)
    assert aberto(nave, "arritmia", "sarah")
    assert _pessoa(api, "sarah")["corpo"]["coracao"] == "critico"


def test_regras_do_corpo():
    leitura = dict(estresse=40, agua_ml_dia=1000)
    metricas = dict(spo2=dict(faixa="atencao"), sono=dict(faixa="padrao"))
    c = corpo(leitura, metricas, dict(classe="normal"), agua_meta=2400)
    assert c == dict(cerebro="padrao", coracao="padrao", pulmoes="atencao", rins="critico")
    assert corpo(dict(estresse=75, agua_ml_dia=2400), {}, None, 2400)["cerebro"] == "critico"


def test_saude_hormonal_privada_ate_ela_compartilhar_e_sem_metodo(nave, api):
    avancar(nave, 10)
    assert _pessoa(api, "sarah")["saude_hormonal"] == {"compartilhado": False}
    assert _pessoa(api, "kenji")["saude_hormonal"] is None, "sem calendário, nada"
    nave.injetar("ciclo", "sarah")
    avancar(nave, 60)
    ev = aberto(nave, "ciclo", "sarah")
    assert ev
    assert _pessoa(api, "sarah")["saude_hormonal"] == {"compartilhado": False}, "aberto no relógio ainda é privado"
    nave.motor.decidir(ev["id"], "sarah", "confirmar_sintoma")
    nave.motor.decidir(ev["id"], "sarah", "compartilhar")
    h = _pessoa(api, "sarah")["saude_hormonal"]
    assert h["compartilhado"] is True and "cuidado leve" in h["resumo"]
    bordo = str(api.get("/api/bordo").json()).lower()
    assert "pilula" not in bordo and "ultima_menstruacao" not in bordo, "método e datas não chegam ao painel"


def test_sem_medico_a_bordo_o_cmo_nao_ve_saude_hormonal(nave, api):
    api.post("/api/simulador/cenario", json=dict(cenario="medico_terra"))
    avancar(nave, 5)
    assert all(t["saude_hormonal"] is None for t in api.get("/api/bordo").json()["tripulantes"])


def test_relogio_traz_o_sexo_para_o_avatar_e_nao_o_corpo(nave, api):
    avancar(nave, 3)
    eu = api.get("/api/tripulantes/elena/relogio").json()["eu"]
    assert eu["sexo"] == "feminino"
    assert "corpo" not in eu, "o relógio mostra os próprios sinais, não a silhueta do painel"
