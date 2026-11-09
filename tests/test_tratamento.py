"""Regressões dos erros identificados no protótipo, usando somente dados fictícios."""

import unittest

import pandas as pd

from src.gerar_dados_sinteticos import gerar_base
from src.rh_programas import (
    carregar_mapeamentos, converter_data, converter_salario, simular_programas, tratar_base,
)


class TratamentoTest(unittest.TestCase):
    def setUp(self):
        self.fonte = gerar_base()
        self.base, self.relatorio = tratar_base(self.fonte, "2026-11-09")

    def test_salarios_numericos_e_brasileiros(self):
        for valor, esperado in [(10000.0, 10000), ("10000.0", 10000),
                                ("R$ 1.234,56", 1234.56), ("1.500", 1500),
                                ("18500.0", 18500), ("950,50", 950.5)]:
            with self.subTest(valor=valor):
                self.assertEqual(converter_salario(valor), esperado)
        self.assertTrue(pd.isna(converter_salario("não informado")))

    def test_escolaridade_usa_descricao(self):
        self.assertEqual(self.base.loc[0, "escolaridade_simplificada"], "Médio")
        self.assertEqual(self.base.loc[1, "escolaridade_simplificada"], "Superior")
        _, mapa = carregar_mapeamentos()
        self.assertEqual(mapa["ENSINO FUNDAMENTAL COMPLETO"], "Fundamental")

    def test_origem_preservada_sem_imputacao_ou_teto(self):
        pd.testing.assert_frame_equal(self.fonte.iloc[:240].reset_index(drop=True),
                                      self.base[self.fonte.columns])
        self.assertTrue(pd.isna(self.base.loc[5, "data_nascimento"]))
        self.assertTrue(pd.isna(self.base.loc[14, "data_admissao"]))
        self.assertTrue(pd.isna(self.base.loc[6, "tempo_casa_anos"]))
        self.assertEqual(self.base.loc[1, "salario_numerico"], 18500)
        self.assertEqual(self.base.loc[4, "salario_numerico"], 60000)
        self.assertTrue(self.base.loc[4, "qualidade_salario_suspeito"])

    def test_setor_antes_de_agrupar_cargo_raro(self):
        self.assertEqual(self.base.loc[18, "cargo_agrupado"], "Outros")
        self.assertEqual(self.base.loc[18, "setor"], "Produção")
        self.assertTrue(self.base.loc[10, "qualidade_setor"])

    def test_datas_invalidas_e_aniversario(self):
        self.assertTrue(pd.isna(converter_data("31/02/2026")))
        fonte = self.fonte.iloc[:2].copy()
        fonte["Data Nascimento"] = ["2000-11-10", "2000-11-09"]
        base, _ = tratar_base(fonte, "2026-11-09")
        self.assertEqual(base["idade"].tolist(), [25, 26])
        self.assertTrue(self.base.loc[8, "qualidade_data_futura"])
        self.assertTrue(self.base.loc[15, "qualidade_cronologia"])

    def test_ferias_nao_encerram_tempo_de_casa(self):
        fonte = self.fonte.iloc[[17]].copy()
        fonte["Data Admissão"] = "2024-10-01"
        fonte["Data Afastamento"] = "2025-02-01"
        base, _ = tratar_base(fonte, "2026-11-09")
        self.assertEqual(base.loc[0, "tempo_casa_anos"], 2)

    def test_duplicatas_e_fonte_ja_processada(self):
        self.assertEqual(self.relatorio["duplicatas_exatas_removidas"], 1)
        fonte = self.fonte.iloc[:2].copy()
        fonte.loc[1, "Cód Funcionário"] = fonte.loc[0, "Cód Funcionário"]
        with self.assertRaisesRegex(ValueError, "único"):
            tratar_base(fonte, "2026-11-09")
        with self.assertRaisesRegex(ValueError, "já contém"):
            tratar_base(self.fonte.assign(Programa="exemplo"), "2026-11-09")

    def test_publico_pendencias_e_empate_explicito(self):
        simulacao = simular_programas(self.base)
        self.assertTrue(simulacao.loc[simulacao.situacao_vinculo.eq("Sem vínculo"),
                                       "programa_sugerido"].eq("Não simulado").all())
        self.assertEqual(simulacao.loc[2, "status_simulacao"], "Revisar dados")
        fonte = self.fonte.iloc[:1].copy()
        fonte["Tipo Contrato"] = "Empregado"
        fonte["Cargo"] = "ASSISTENTE ADMINISTRATIVO"
        fonte["Escolaridade"] = "Superior Completo"
        fonte["Data Nascimento"] = "1996-01-01"
        fonte["Data Admissão"] = "2022-01-01"
        fonte["Valor Salário"] = 8000
        base, _ = tratar_base(fonte, "2026-11-09")
        resultado = simular_programas(base).iloc[0]
        self.assertTrue(resultado.houve_empate)
        self.assertIn("DataDrive", resultado.programas_empatados)
        self.assertIn("Direcionamento Head", resultado.programas_empatados)
        self.assertEqual(resultado.programa_sugerido, "DataDrive")
        self.assertTrue(resultado.justificativa)

    def test_reexecucao_deterministica(self):
        repetida, _ = tratar_base(self.fonte, "2026-11-09")
        pd.testing.assert_frame_equal(simular_programas(self.base), simular_programas(repetida))


if __name__ == "__main__":
    unittest.main()
