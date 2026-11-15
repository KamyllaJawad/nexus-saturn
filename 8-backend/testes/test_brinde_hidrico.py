"""Brinde hídrico Terra–órbita: o convite da família viaja pelo link até o relógio
da Sarah, ela bebe a bordo e a resposta volta para a Terra. O app da família só
sabe de cada passo quando o pacote chega, com o atraso da missão."""
from conftest import avancar


def _brinde(api):
    return api.get("/api/familia/feed").json()["elo"]["brinde"]


def _ate(nave, cond, limite=40):
    for _ in range(limite):
        if cond():
            return True
        nave.passo()
    return cond()


def test_brinde_ida_e_volta_com_o_atraso_do_link(nave, api):
    avancar(nave, 3)
    assert _brinde(api) is None
    api.post("/api/familia/acao", json=dict(tipo="brinde"))
    elo = api.get("/api/familia/feed").json()["elo"]
    assert elo["brinde"] == "enviado" and elo["brinde_falta_s"] > 0, "o convite ainda está no caminho"
    assert nave.jogo["brinde"] == "enviado", "a nave ainda não recebeu"

    # O convite chega ao relógio da Sarah, que recebe o aviso.
    assert _ate(nave, lambda: _brinde(api) == "chegou")
    relogio = api.get("/api/tripulantes/sarah/relogio").json()
    assert relogio["jogo"]["brinde"] == "chegou"
    assert any("brinde" in a["texto"] for a in relogio["avisos"])

    # A Sarah bebe a bordo; a Terra ainda não sabe (a resposta está no link).
    api.post("/api/habitos/agua", json=dict(tripulante_id="sarah"))
    assert nave.jogo["brinde"] == "feito"
    assert _brinde(api) == "chegou", "a família só sabe quando a resposta atravessar o link"
    assert any("brindou" in a["texto"] for a in api.get("/api/tripulantes/sarah/relogio").json()["avisos"])

    # A resposta chega à Terra.
    assert _ate(nave, lambda: _brinde(api) == "feito")
    feed = api.get("/api/familia/feed").json()
    assert any("brindou de volta" in u["frase"] for u in feed["ultimas"])
    assert not any(ch.isdigit() for u in feed["ultimas"] for ch in u["frase"]), "a família não recebe número"


def test_brinde_no_blackout_fica_na_fila_e_segue_quando_o_sinal_volta(nave, api):
    avancar(nave, 3)
    api.post("/api/simulador/cenario", json=dict(cenario="blackout"))
    api.post("/api/familia/acao", json=dict(tipo="brinde"))
    assert _brinde(api) == "fila"
    avancar(nave, 15)
    assert _brinde(api) == "fila" and nave.jogo["brinde"] == "enviado", "sem sinal, nada atravessa"
    api.post("/api/simulador/cenario", json=dict(cenario="sinal_volta"))
    assert _ate(nave, lambda: _brinde(api) == "chegou")
