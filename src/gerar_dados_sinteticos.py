"""Gera perfis inteiramente fictícios, com casos de qualidade conhecidos."""

from datetime import date
from pathlib import Path
import random

import pandas as pd


def gerar_base(semente=42):
    gerador = random.Random(semente)
    cargos = [
        "ASSISTENTE ADMINISTRATIVO", "AUXILIAR DE PRODUÇÃO", "ANALISTA RECURSOS HUMANOS",
        "ANALISTA REDES E SISTEMAS PL", "VENDEDOR EM GERAL", "ASSISTENTE FINANCEIRO",
        "AUXILIAR DE LOGISTICA", "ENGENHEIRO DE MANUTENÇÃO I", "GERENTE DE MARKETING", "COMPRADOR",
    ]
    escolaridades = ["Ensino Fundamental Completo", "Ensino Médio Incompleto",
                    "Ensino Médio Completo", "Superior Incompleto", "Superior Completo",
                    "Pós-Graduação/Espec.Completo"]
    registros = []
    for numero in range(1, 241):
        contrato = gerador.choice(["Empregado", "Empregado", "Aprendiz", "Estagiário", "Diretor"])
        nascimento = date(gerador.randint(1961, 2006), gerador.randint(1, 12), gerador.randint(1, 28))
        admissao = date(gerador.randint(max(2001, nascimento.year + 18), 2025), 3, 10)
        desligado = numero % 7 == 0
        salario = gerador.choice([1250, 1800, 2800, 4500, 6800, 9800, 12500, 18500])
        if contrato in ["Aprendiz", "Estagiário"]:
            salario = gerador.choice([950, 1400, 1800])
        salario_texto = f"{salario:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
        registros.append({
            "Cód Funcionário": f"SINT-{numero:04d}",
            "Funcionário": f"Pessoa sintética {numero:04d}",
            "Cargo": cargos[(numero - 1) % len(cargos)],
            "Tipo Contrato": contrato, "Escolaridade": gerador.choice(escolaridades),
            "Situação": "Demitido" if desligado else "Trabalhando",
            "Data Admissão": admissao.isoformat(),
            "Data Afastamento": "2026-06-30" if desligado else "",
            "Data Nascimento": nascimento.isoformat(),
            "Valor Salário": f"R$ {salario_texto}" if numero % 2 else str(float(salario)),
        })
    base = pd.DataFrame(registros)
    casos = {
        0: {"Escolaridade": "Ensino Médio Completo"},
        1: {"Escolaridade": "Superior Completo", "Valor Salário": "18500.0"},
        2: {"Valor Salário": ""},
        3: {"Valor Salário": "valor inválido"},
        4: {"Valor Salário": "R$ 60.000,00"},
        5: {"Data Nascimento": ""},
        6: {"Data Afastamento": ""},
        7: {"Data Nascimento": "31/02/1990"},
        8: {"Data Admissão": "2027-01-01"},
        9: {"Cargo": "CARGO A CONFERIR"},
        10: {"Cargo": "ASSISTENTE DE EXPORTAÇÃO"},
        11: {"Situação": ""},
        12: {"Tipo Contrato": "CONTRATO A CONFERIR"},
        13: {"Escolaridade": "CURSO A CONFERIR"},
        14: {"Data Admissão": ""},
        15: {"Situação": "Demitido", "Data Afastamento": "1990-01-01"},
        16: {"Valor Salário": "R$ 450,00"},
        17: {"Situação": "Férias", "Data Afastamento": "2026-08-01"},
        18: {"Cargo": "SERRADOR I"},
    }
    for indice, ajustes in casos.items():
        for coluna, valor in ajustes.items():
            base.loc[indice, coluna] = valor
    return pd.concat([base, base.iloc[[20]]], ignore_index=True)


if __name__ == "__main__":
    destino = Path(__file__).resolve().parents[1] / "data/sinteticos/base_rh_sintetica.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    gerar_base().to_csv(destino, index=False, encoding="utf-8")
    print(f"Base fictícia salva em {destino}")
