"""Os modelos em serviço: formato do contrato, metas medidas e inferência rápida
igual à do scikit-learn."""
import json

import numpy as np

from app import ia, sinais
from app.config import MODELOS, SINAIS_IF
from conftest import avancar


def test_inferencia_rapida_igual_ao_scikit_learn(nave):
    rng = np.random.default_rng(1)
    m1, m2 = ia._ativos["m1"], ia._ativos["m2"]
    X1 = rng.normal(size=(20, len(m1["atributos"]))) * 50
    assert np.allclose(ia.proba(m1["modelo"], X1), m1["modelo"].predict_proba(X1), atol=1e-9)
    X2 = rng.normal(size=(20, len(m2["atributos"])))
    assert np.allclose(ia.proba(m2["modelo"], X2), m2["modelo"].predict_proba(X2), atol=1e-9)
    for tid, m in ia._ativos["m3-if"]["tripulantes"].items():
        med, mad = np.array(m["mediana"]), np.array(m["mad"])
        E = sinais.expandir_if(med + rng.normal(size=(30, len(SINAIS_IF))) * 3, med, mad)
        assert np.allclose(ia.escore_floresta(m["pipeline"], E), -m["pipeline"].score_samples(E), atol=1e-9), tid


def test_analise_segue_o_contrato_e_registra_versoes(nave):
    avancar(nave, 6)
    a = nave.pessoas["sarah"]["analise"]
    assert set(a) >= {"tripulante_id", "ficha", "m1", "m2", "m3", "ciclo"}
    assert a["m1"]["versao_modelo"].startswith("arritmia-borda") and a["m2"]["versao_modelo"].startswith("qualidade")
    assert a["m3"]["versao_z"] == "m3-z-0.1" and a["m3"]["estado"] in ("otimo", "atencao", "critico", "suspeito")
    f = a["m3"]["isolation_forest"]
    assert set(f) >= {"anomalo", "score", "limiar", "evidencias", "versao_modelo"}
    assert all(set(v) == {"z", "faixa"} for v in a["m3"]["metricas"].values())
    assert a["ficha"]["calendario"] is True and a["ciclo"]["compartilhado"] is False
    k = nave.pessoas["kenji"]["analise"]
    assert k["ficha"]["calendario"] is False and k["ciclo"] is None


def test_metas_medidas_no_relatorio_de_treino():
    """Não fixa número bonito: confere o que o relatório diz e cobra as metas que
    o treino declara ter batido. O F1 do M1 é reportado como saiu."""
    r = json.loads((MODELOS / "relatorio.json").read_text(encoding="utf-8"))["modelos"]
    m1, m2, m3 = r["m1"]["metricas"], r["m2"]["metricas"], r["m3-if"]["metricas"]
    assert m1["bateu_meta"] == (m1["f1_fa"] >= 0.75)
    assert m1["n_teste"] > 1000 and sum(map(sum, m1["matriz_confusao"]["valores"])) == m1["n_teste"]
    assert m2["recall_suspeito"] >= 0.9, "meta do M2: preferimos perguntar demais a alarmar errado"
    for t, v in m3["por_tripulante"].items():
        assert v["alarmes_fora_da_amostra_por_dia"] <= 1.0, t
        assert v["recall_desvio_em_3_sinais"] >= 0.9, t
    assert m3["episodios_excluidos"]["acima_do_limiar"] == m3["episodios_excluidos"]["total"]
