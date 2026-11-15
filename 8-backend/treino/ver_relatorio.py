"""Imprime o resumo de modelos/relatorio.json. Uso: python -m treino.ver_relatorio"""
import json

from app.config import MODELOS


def principal():
    r = json.loads((MODELOS / "relatorio.json").read_text(encoding="utf-8"))
    m = r["modelos"]
    e = r["lote"]["ecg"]
    print(f"Lote {r['lote']['id']} · ECG: {e['origem']} · {e['gravacoes']} gravações · classes {e['classes']}")
    print(f"Split {e['split']} · banco do simulador {e['banco_simulador']}")
    x = m["m1"]["metricas"]
    print(f"\nM1 {m['m1']['versao']} · F1 FA {x['f1_fa']} (IC95 {x['f1_fa_ic95']}, validação {x['f1_fa_validacao']}) · precisão {x['precisao_fa']} · recall {x['recall_fa']} "
          f"· limiar {x['limiar_fa']} · acurácia {x['acuracia']} · meta batida: {x['bateu_meta']}")
    print("   matriz (linhas = verdade)", x["matriz_confusao"]["rotulos"], x["matriz_confusao"]["valores"])
    print("   atributos que mais pesam:", list(x["importancias"].items())[:5])
    x = m["m2"]["metricas"]
    print(f"\nM2 {m['m2']['versao']} · {x['estimador_escolhido']} · recall suspeito {x['recall_suspeito']} "
          f"· precisão {x['precisao_suspeito']} · bom marcado como suspeito {x['falso_suspeito_em_bom']} · meta batida: {x['bateu_meta']}")
    print("   comparação na validação:", x["comparacao"])
    x = m["m3-if"]["metricas"]
    print(f"\nM3 {m['m3-if']['versao']} · persistência {x['persistencia']} · episódios excluídos {x['episodios_excluidos']} · meta batida: {x['bateu_meta']}")
    for t, v in x["por_tripulante"].items():
        print(f"   {t:7s} limiar {v['limiar']} · alarmes/dia fora da amostra {v['alarmes_fora_da_amostra_por_dia']} "
              f"· recall com desvio em 2/3/4 sinais: {v['recall_desvio_em_2_sinais']} / {v['recall_desvio_em_3_sinais']} / {v['recall_desvio_em_4_sinais']}")


if __name__ == "__main__":
    principal()
