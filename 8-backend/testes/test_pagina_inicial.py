"""A raiz do site abre o Vue (v2) quando o build existe, como na imagem do Render;
sem o build, mostra a sala de simulação antiga."""
from app import main


def test_raiz_vai_para_o_vue_quando_o_v2_existe(api, tmp_path, monkeypatch):
    (tmp_path / "v2").mkdir()
    (tmp_path / "v2" / "index.html").write_text("<!doctype html><title>v2</title>", encoding="utf-8")
    (tmp_path / "index.html").write_text("<!doctype html><title>antiga</title>", encoding="utf-8")
    monkeypatch.setattr(main, "FRONT", tmp_path)
    r = api.get("/", follow_redirects=False)
    assert r.status_code in (302, 307) and r.headers["location"] == "/v2/"


def test_sem_o_v2_a_raiz_mostra_a_sala_antiga(api, tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text("<!doctype html><title>antiga</title>", encoding="utf-8")
    monkeypatch.setattr(main, "FRONT", tmp_path)
    r = api.get("/")
    assert r.status_code == 200 and "antiga" in r.text
