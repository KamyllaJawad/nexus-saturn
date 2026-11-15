"""Os testes dirigem o simulador passo a passo (sem esperar o relógio de verdade)
e usam um banco e um registro de modelos temporários, para não tocar no que
está em serviço."""
import os
import shutil
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.environ["ASTRO_SEM_RELOGIO"] = "1"
os.environ["COSMO_OLLAMA"] = "0"


@pytest.fixture()
def nave(tmp_path, monkeypatch):
    from app import config, hitl, ia, main
    from treino import pipeline

    modelos = tmp_path / "modelos"
    shutil.copytree(config.MODELOS, modelos)
    reg = pipeline.ler_registro()
    reg["sombra"] = {}  # cada teste começa sem candidato em sombra
    for alvo in (config, ia, hitl, main, pipeline):
        if hasattr(alvo, "MODELOS"):
            monkeypatch.setattr(alvo, "MODELOS", modelos)
    pipeline.gravar_registro(dict(reg, ativos={p: a for p, a in reg["ativos"].items()}))
    sim = main.iniciar(tmp_path / "teste.db")
    yield sim
    ia._ativos.clear(); ia._sombra.clear()


@pytest.fixture()
def api(nave):
    from fastapi.testclient import TestClient
    from app import main
    return TestClient(main.app)


def avancar(sim, segundos):
    for _ in range(int(segundos)):
        sim.passo()


def aberto(sim, tipo, tid=None):
    evs = sim.motor.abertos(tid, tipo)
    return evs[0] if evs else None
