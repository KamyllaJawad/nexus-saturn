"""Testes das regras determinísticas (não precisam do Ollama):  python -m unittest test_ia -v"""
import unittest

import ia


def dia(data, **kw):
    return {"data": data, **kw}


class TestRegras(unittest.TestCase):
    def avaliar(self, dias, **kw):
        return ia.avaliar_prevencao(dias, usar_rag=False, explicar=False, **kw)

    def ids(self, r):
        return {a["id"] for a in r["alertas"]}

    def test_sono_3_dias_abaixo_de_6h_gera_alerta(self):
        r = self.avaliar([dia("2026-01-01", sono_h=7), dia("2026-01-02", sono_h=5.5),
                          dia("2026-01-03", sono_h=5), dia("2026-01-04", sono_h=5.9)])
        self.assertIn("sono_baixo", self.ids(r))

    def test_sono_2_dias_nao_gera(self):
        r = self.avaliar([dia("2026-01-01", sono_h=7), dia("2026-01-02", sono_h=5), dia("2026-01-03", sono_h=5)])
        self.assertNotIn("sono_baixo", self.ids(r))

    def test_dia_bom_no_fim_quebra_a_sequencia(self):
        r = self.avaliar([dia("2026-01-01", sono_h=5), dia("2026-01-02", sono_h=5),
                          dia("2026-01-03", sono_h=5), dia("2026-01-04", sono_h=7)])
        self.assertNotIn("sono_baixo", self.ids(r))

    def test_dado_ausente_quebra_a_sequencia(self):
        r = self.avaliar([dia("2026-01-01", sono_h=5), dia("2026-01-02"), dia("2026-01-03", sono_h=5)])
        self.assertNotIn("sono_baixo", self.ids(r))

    def test_nivel_sobe_com_a_persistencia(self):
        dias = [dia(f"2026-01-0{i}", sono_h=5) for i in range(1, 6)]
        self.assertEqual(self.avaliar(dias)["alertas"][0]["nivel"], "alerta")

    def test_saude_mental_exige_consentimento(self):
        dias = [dia(f"2026-01-0{i}", humor=1) for i in range(1, 4)]
        self.assertNotIn("humor_baixo", self.ids(self.avaliar(dias)))
        r = self.avaliar(dias, consentimento_saude_mental=True)
        a = [x for x in r["alertas"] if x["id"] == "humor_baixo"][0]
        self.assertFalse(a["compartilhavel_com_terra"])
        self.assertEqual(a["orientacao"], [])
        self.assertIsNone(a["explicacao"])

    def test_autonomia_nunca_passa_de_2(self):
        dias = [dia(f"2026-01-0{i}", sono_h=4, agua_ml=500, exercicio_min=0) for i in range(1, 7)]
        for a in self.avaliar(dias)["alertas"]:
            self.assertLessEqual(a["autonomia"], 2)
            self.assertEqual(a["status"], "pendente_revisao_humana")

    def test_fc_precisa_de_linha_de_base(self):
        r = self.avaliar([dia("2026-01-01", fc_repouso=80), dia("2026-01-02", fc_repouso=90), dia("2026-01-03", fc_repouso=95)])
        self.assertNotIn("fc_repouso_subindo", self.ids(r))

    def test_fc_acima_da_base(self):
        dias = [dia(f"2026-01-0{i}", fc_repouso=58) for i in range(1, 5)] + \
               [dia(f"2026-01-0{i}", fc_repouso=68) for i in range(5, 8)]
        self.assertIn("fc_repouso_subindo", self.ids(self.avaliar(dias)))

    def test_filtro_de_farmaco(self):
        self.assertEqual(ia._filtrar_farmaco("Tome 500 mg de ibuprofeno"), ia._SEGURO)
        self.assertEqual(ia._filtrar_farmaco("Beba água e caminhe na esteira."), "Beba água e caminhe na esteira.")


if __name__ == "__main__":
    unittest.main()

