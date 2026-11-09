"""Regras exploratórias de RH e tratamento que preserva os valores recebidos."""

from datetime import date, datetime
from numbers import Real
from pathlib import Path
import json
import math
import re
import unicodedata

import numpy as np
import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
COLUNAS_OBRIGATORIAS = [
    "Cód Funcionário", "Cargo", "Tipo Contrato", "Escolaridade", "Situação",
    "Data Admissão", "Data Afastamento", "Data Nascimento", "Valor Salário",
]
PROGRAMAS = [
    "Conecta Carreira", "DataDrive", "Crescer Juntos",
    "Direcionamento Head", "Liderança Sustentável",
]
COLUNAS_PONTOS = [
    "pontos_conecta_carreira", "pontos_datadrive", "pontos_crescer_juntos",
    "pontos_direcionamento_head", "pontos_lideranca_sustentavel",
]


def normalizar_texto(valor):
    if pd.isna(valor):
        return ""
    texto = unicodedata.normalize("NFKD", str(valor).strip())
    texto = "".join(letra for letra in texto if not unicodedata.combining(letra))
    return re.sub(r"\s+", " ", texto).upper()


def carregar_csv(caminho):
    """Lê UTF-8 ou Windows-1252 sem presumir que salários são texto brasileiro."""
    try:
        dados = pd.read_csv(caminho, dtype="string", encoding="utf-8-sig")
    except UnicodeDecodeError:
        dados = pd.read_csv(caminho, dtype="string", encoding="cp1252")
    dados.columns = dados.columns.str.strip()
    return dados


def converter_salario(valor):
    """Aceita números, decimal com ponto e moeda brasileira com vírgula."""
    if pd.isna(valor):
        return np.nan
    if isinstance(valor, Real):
        return float(valor) if math.isfinite(valor) else np.nan
    texto = str(valor).strip().replace("R$", "").replace("\xa0", "")
    texto = texto.replace(" ", "")
    if re.fullmatch(r"[+-]?\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?", texto):
        texto = texto.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"[+-]?\d+(?:,\d{1,2})?", texto):
        texto = texto.replace(",", ".")
    elif not re.fullmatch(r"[+-]?\d+\.\d{1,2}", texto):
        return np.nan
    return float(texto)


def converter_data(valor):
    if pd.isna(valor) or str(valor).strip() == "":
        return pd.NaT
    if isinstance(valor, (datetime, date, pd.Timestamp)):
        return pd.Timestamp(valor).normalize().tz_localize(None)
    texto = str(valor).strip()
    try:
        if re.match(r"^\d{4}-\d{2}-\d{2}(?:$|[ T])", texto):
            return pd.Timestamp(datetime.fromisoformat(texto).date())
        return pd.Timestamp(datetime.strptime(texto, "%d/%m/%Y"))
    except ValueError:
        return pd.NaT


def anos_completos(inicios, fins):
    """Conta aniversários completos, incluindo o dia do aniversário."""
    antes_aniversario = (fins.dt.month < inicios.dt.month) | (
        (fins.dt.month == inicios.dt.month) & (fins.dt.day < inicios.dt.day)
    )
    anos = fins.dt.year - inicios.dt.year - antes_aniversario.astype(int)
    return anos.where(inicios.notna() & fins.notna()).astype("Int64")


def carregar_mapeamentos():
    config = json.loads((RAIZ / "config/mapeamentos.json").read_text(encoding="utf-8"))
    setores = {}
    for setor, cargos in config["setores_por_cargo"].items():
        for cargo in cargos:
            setores.setdefault(normalizar_texto(cargo), set()).add(setor)
    # Um cargo com duas classificações precisa de conferência do domínio.
    mapa_setores = {
        cargo: next(iter(opcoes)) for cargo, opcoes in setores.items() if len(opcoes) == 1
    }
    escolaridade = {
        normalizar_texto(descricao): grupo
        for descricao, grupo in config["escolaridade_por_descricao"].items()
    }
    return mapa_setores, escolaridade


def tratar_base(dados, data_referencia, frequencia_minima_cargo=5):
    """Retorna uma cópia tratada e contagens de qualidade, sem imputar valores."""
    referencia = pd.Timestamp(data_referencia)
    if pd.isna(referencia) or referencia.tz is not None:
        raise ValueError("Informe uma data de referência válida, sem fuso horário.")
    referencia = referencia.normalize()
    if frequencia_minima_cargo < 1:
        raise ValueError("A frequência mínima de cargo deve ser positiva.")
    base = dados.copy(deep=True)
    base.columns = base.columns.str.strip()
    if base.columns.duplicated().any():
        raise ValueError("Há nomes de colunas duplicados após remover espaços.")
    faltantes = sorted(set(COLUNAS_OBRIGATORIAS) - set(base.columns))
    if faltantes:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(faltantes)}")
    derivadas = {"Programa", "score_retencao", "idade", "programa_sugerido"}
    if derivadas.intersection(base.columns):
        raise ValueError(
            "A entrada já contém colunas de tratamento. Use a fonte original. "
            "Datas imputadas e salários limitados anteriormente não podem ser recuperados."
        )
    quantidade_original = len(base)
    base = base.drop_duplicates().reset_index(drop=True)
    ids = base["Cód Funcionário"].astype("string").str.strip()
    if ids.isna().any() or ids.eq("").any() or ids.duplicated().any():
        raise ValueError("A base deve ter um ID preenchido e único por pessoa.")

    mapa_setores, mapa_escolaridade = carregar_mapeamentos()
    base["id_pessoa"] = ids
    base["cargo_normalizado"] = base["Cargo"].map(normalizar_texto)
    base["setor"] = base["cargo_normalizado"].map(mapa_setores).fillna("Não mapeado")
    frequencias = base["cargo_normalizado"].value_counts()
    base["cargo_agrupado"] = base["cargo_normalizado"].where(
        base["cargo_normalizado"].map(frequencias).ge(frequencia_minima_cargo), "Outros"
    )
    base["escolaridade_simplificada"] = (
        base["Escolaridade"].map(normalizar_texto).map(mapa_escolaridade).fillna("Não informada")
    )
    base["contrato"] = base["Tipo Contrato"].map(normalizar_texto).map({
        "EMPREGADO": "Empregado", "APRENDIZ": "Aprendiz",
        "ESTAGIARIO": "Estagiário", "DIRETOR": "Diretor",
    }).fillna("Não informado")
    situacoes = {
        "ATIVO": "Com vínculo", "TRABALHANDO": "Com vínculo", "FERIAS": "Com vínculo",
        "LICENCA MATERNIDADE": "Com vínculo", "AUXILIO DOENCA": "Com vínculo",
        "ACIDENTE TRABALHO": "Com vínculo", "LIC. S/ REMUNERACAO": "Com vínculo",
        "DEMITIDO": "Sem vínculo", "DESLIGADO": "Sem vínculo",
    }
    base["situacao_vinculo"] = (
        base["Situação"].map(normalizar_texto).map(situacoes).fillna("Não informada")
    )
    base["qualidade_setor"] = base["setor"].eq("Não mapeado")
    base["qualidade_escolaridade"] = base["escolaridade_simplificada"].eq("Não informada")
    base["qualidade_contrato"] = base["contrato"].eq("Não informado")
    base["qualidade_situacao"] = base["situacao_vinculo"].eq("Não informada")

    for original, destino in [
        ("Data Admissão", "data_admissao"), ("Data Afastamento", "data_afastamento"),
        ("Data Nascimento", "data_nascimento"),
    ]:
        base[destino] = pd.to_datetime(base[original].map(converter_data))
        preenchida = base[original].notna() & base[original].astype("string").str.strip().ne("")
        base[f"qualidade_{destino}"] = preenchida & base[destino].isna()
    base["qualidade_admissao_ausente"] = base["data_admissao"].isna()
    base["qualidade_nascimento_ausente"] = base["data_nascimento"].isna()
    base["qualidade_desligamento_ausente"] = (
        base["situacao_vinculo"].eq("Sem vínculo") & base["data_afastamento"].isna()
    )
    base["qualidade_data_futura"] = (
        base[["data_admissao", "data_nascimento", "data_afastamento"]].gt(referencia).any(axis=1)
    )
    base["qualidade_cronologia"] = (
        base["data_admissao"].lt(base["data_nascimento"])
        | base["data_afastamento"].lt(base["data_admissao"])
    )
    referencias = pd.Series(referencia, index=base.index, dtype="datetime64[ns]")
    base["idade"] = anos_completos(base["data_nascimento"], referencias)
    base["qualidade_idade"] = base["idade"].lt(16).fillna(False) | base["idade"].gt(100).fillna(False)
    base["faixa_etaria"] = pd.cut(
        base["idade"].astype(float), [15, 25, 40, 55, np.inf],
        labels=["16–25", "26–40", "41–55", "Acima de 55"],
    )
    fim_vinculo = referencias.where(
        base["situacao_vinculo"].eq("Com vínculo"), base["data_afastamento"]
    )
    fim_vinculo = fim_vinculo.mask(base["situacao_vinculo"].eq("Não informada"))
    valido = (
        base["data_admissao"].le(fim_vinculo) & fim_vinculo.le(referencia)
        & ~base["qualidade_cronologia"]
    )
    base["tempo_casa_anos"] = anos_completos(base["data_admissao"], fim_vinculo).where(valido)
    base["salario_numerico"] = base["Valor Salário"].map(converter_salario).astype(float)
    base["qualidade_salario"] = (
        base["salario_numerico"].isna() | base["salario_numerico"].le(0)
    )
    # Limites de conferência são parâmetros ilustrativos, sem alterar o salário.
    base["qualidade_salario_suspeito"] = (
        base["salario_numerico"].lt(600) | base["salario_numerico"].gt(50000)
    )
    base["faixa_salarial"] = pd.cut(
        base["salario_numerico"], [0, 1500, 3000, 6000, 10000, np.inf],
        labels=["Até 1.500", "1.500–3.000", "3.000–6.000", "6.000–10.000", "Acima de 10.000"],
    )
    flags = [coluna for coluna in base if coluna.startswith("qualidade_")]
    base["revisar_dados"] = base[flags].any(axis=1)
    relatorio = {"linhas_recebidas": quantidade_original, "linhas_tratadas": len(base),
                 "duplicatas_exatas_removidas": quantidade_original - len(base),
                 "pessoas_com_pendencias": int(base["revisar_dados"].sum()),
                 "data_referencia": referencia.strftime("%Y-%m-%d"),
                 "ocorrencias_por_regra": base[flags].sum().astype(int).to_dict()}
    return base, relatorio


def pontuar_programas(pessoa):
    """Aplica as regras ilustrativas a uma linha completa e conferida."""
    pontos = {programa: 0.0 for programa in PROGRAMAS}
    motivos = {programa: [] for programa in PROGRAMAS}

    def adicionar(programa, valor, motivo):
        pontos[programa] += valor
        motivos[programa].append(f"{motivo} (+{valor:g})")

    contrato = pessoa["contrato"]
    setor = pessoa["setor"]
    idade = pessoa["idade"]
    salario = pessoa["salario_numerico"]
    escolaridade = pessoa["escolaridade_simplificada"]
    tempo = pessoa["tempo_casa_anos"]
    superior = escolaridade in ["Superior", "Pós-graduação"]
    if contrato in ["Aprendiz", "Estagiário"]:
        adicionar("Conecta Carreira", 3, "Contrato de aprendizagem ou estágio")
        if idade <= 25:
            adicionar("Conecta Carreira", 2, "Idade entre 16 e 25 anos")
        if salario <= 3000:
            adicionar("Conecta Carreira", 2, "Salário até 3.000")
        if escolaridade in ["Médio", "Fundamental"]:
            adicionar("Conecta Carreira", 1, "Escolaridade fundamental ou média")
    if contrato in ["Empregado", "Diretor"] and setor in [
        "Administrativo", "Comercial", "Financeiro", "TI", "Marketing", "RH"
    ]:
        adicionar("Direcionamento Head", 2, "Setor previsto na regra")
        if tempo > 5:
            adicionar("Direcionamento Head", 2, "Mais de 5 anos de casa")
        if idade > 40:
            adicionar("Direcionamento Head", 2, "Mais de 40 anos")
        elif idade >= 30:
            adicionar("Direcionamento Head", 1, "Idade entre 30 e 40 anos")
        if salario > 6000:
            adicionar("Direcionamento Head", 2, "Salário acima de 6.000")
        if superior:
            adicionar("Direcionamento Head", 1, "Escolaridade superior ou pós-graduação")
    if superior and tempo >= 1:
        pesos_setor = {"Administrativo": 3, "Marketing": 2, "Logística": 2, "TI": 1.5, "Financeiro": 1.5}
        adicionar("DataDrive", pesos_setor.get(setor, 1), "Setor na regra de dados")
        if idade <= 30:
            adicionar("DataDrive", 2, "Idade até 30 anos")
        if contrato in ["Empregado", "Aprendiz", "Estagiário"]:
            adicionar("DataDrive", 1, "Contrato previsto na regra")
    if contrato == "Empregado" and setor in ["Produção", "Logística", "Engenharia / Manutenção"]:
        adicionar("Crescer Juntos", 2, "Setor operacional")
        if 26 <= idade <= 35:
            adicionar("Crescer Juntos", 2, "Idade entre 26 e 35 anos")
        if 1500 < salario <= 6000:
            adicionar("Crescer Juntos", 2, "Salário acima de 1.500 e até 6.000")
        if escolaridade in ["Médio", "Superior"]:
            adicionar("Crescer Juntos", 1, "Escolaridade média ou superior")
        if tempo <= 5:
            adicionar("Crescer Juntos", 1, "Até 5 anos de casa")
    if contrato in ["Empregado", "Diretor"] and idade > 35:
        adicionar("Liderança Sustentável", 2, "Mais de 35 anos")
        if salario > 6000:
            adicionar("Liderança Sustentável", 2, "Salário acima de 6.000")
        if superior:
            adicionar("Liderança Sustentável", 1, "Escolaridade superior ou pós-graduação")
        if tempo > 10:
            adicionar("Liderança Sustentável", 2, "Mais de 10 anos de casa")
    return pontos, motivos


def simular_programas(base):
    """Expõe critérios e empates para estudo. Pesos dependem de validação de RH."""
    resultados = []
    for _, pessoa in base.iterrows():
        saida = {coluna: np.nan for coluna in COLUNAS_PONTOS}
        saida.update({"programa_sugerido": "Não simulado", "pontuacao_programa": np.nan,
                      "programas_empatados": "", "houve_empate": False,
                      "justificativa": "", "pontuacao_perfil_exploratorio": np.nan})
        if pessoa["situacao_vinculo"] == "Sem vínculo":
            saida["status_simulacao"] = "Fora do público de demonstração"
            saida["justificativa"] = "Registro de pessoa desligada na fotografia recebida."
        elif pessoa["revisar_dados"]:
            saida["status_simulacao"] = "Revisar dados"
            saida["justificativa"] = "; ".join(
                coluna.removeprefix("qualidade_")
                for coluna in base.columns if coluna.startswith("qualidade_") and pessoa[coluna]
            )
        else:
            pontos, motivos = pontuar_programas(pessoa)
            saida.update(dict(zip(COLUNAS_PONTOS, (pontos[p] for p in PROGRAMAS))))
            maximo = max(pontos.values())
            empatados = [programa for programa in PROGRAMAS if pontos[programa] == maximo]
            escolhido = empatados[0] if maximo > 0 else "Nenhum"
            saida.update({"programa_sugerido": escolhido, "pontuacao_programa": maximo,
                          "programas_empatados": " | ".join(empatados) if maximo > 0 else "",
                          "houve_empate": len(empatados) > 1 and maximo > 0,
                          "status_simulacao": "Simulação concluída" if maximo > 0 else "Sem correspondência",
                          "justificativa": "; ".join(motivos.get(escolhido, [])) or "Nenhuma regra pontuou."})
            perfil = (
                2 * int(pessoa["tempo_casa_anos"] >= 2)
                + 2 * int(30 <= pessoa["idade"] <= 50)
                + int(pessoa["salario_numerico"] < 3000)
                + int(pessoa["setor"] in ["Administrativo", "RH", "TI"])
                + int(pessoa["escolaridade_simplificada"] in ["Superior", "Pós-graduação"])
                + int(pessoa["contrato"] in ["Empregado", "Diretor"])
            )
            saida["pontuacao_perfil_exploratorio"] = perfil + 2 * int(perfil >= 5)
        resultados.append(saida)
    colunas = COLUNAS_PONTOS + ["programa_sugerido", "pontuacao_programa", "programas_empatados",
                               "houve_empate", "justificativa", "pontuacao_perfil_exploratorio",
                               "status_simulacao"]
    simulacao = pd.DataFrame(resultados, columns=colunas, index=base.index)
    return pd.concat([base.copy(), simulacao], axis=1)
