"""
analise.py 
------ 
Funções de análise de dados sobre os lançamentos financeiros.
Recebe os dados do banco (via pandas) e calcula totais, agrupamentos
por período (dia/semana/mês) e estatísticas por categoria.
"""

import pandas as pd


def lancamentos_para_dataframe(lancamentos) -> pd.DataFrame:
    """
    Converte o resultado do banco (lista de sqlite3.Row) em um DataFrame do pandas,
    já com a coluna de valor assinado (positivo para entrada, negativo para saída).
    """
    dados = [dict(row) for row in lancamentos]
    df = pd.DataFrame(dados)

    if df.empty:
        return pd.DataFrame(columns=["id", "data", "descricao", "categoria", "tipo", "valor", "valor_assinado"])

    df["data"] = pd.to_datetime(df["data"])
    df["valor_assinado"] = df.apply(
        lambda linha: linha["valor"] if linha["tipo"] == "entrada" else -linha["valor"],
        axis=1,
    )
    return df


def resumo_geral(df: pd.DataFrame) -> dict:
    """Retorna totais gerais: total de entradas, total de saídas e lucro líquido."""
    if df.empty:
        return {"total_entradas": 0.0, "total_saidas": 0.0, "lucro": 0.0}

    total_entradas = df.loc[df["tipo"] == "entrada", "valor"].sum()
    total_saidas = df.loc[df["tipo"] == "saida", "valor"].sum()
    return {
        "total_entradas": round(total_entradas, 2),
        "total_saidas": round(total_saidas, 2),
        "lucro": round(total_entradas - total_saidas, 2),
    }


def resumo_por_dia(df: pd.DataFrame) -> pd.DataFrame:
    """Agrupa os lançamentos por dia, somando o saldo (valor_assinado) de cada um."""
    if df.empty:
        return pd.DataFrame(columns=["data", "saldo"])
    agrupado = df.groupby(df["data"].dt.date)["valor_assinado"].sum().reset_index()
    agrupado.columns = ["data", "saldo"]
    return agrupado.sort_values("data")


def resumo_por_semana(df: pd.DataFrame) -> pd.DataFrame:
    """Agrupa os lançamentos por semana (semana do ano), somando o saldo."""
    if df.empty:
        return pd.DataFrame(columns=["semana", "saldo"])
    semana = df["data"].dt.to_period("W").astype(str)
    agrupado = df.groupby(semana)["valor_assinado"].sum().reset_index()
    agrupado.columns = ["semana", "saldo"]
    return agrupado


def resumo_por_mes(df: pd.DataFrame) -> pd.DataFrame:
    """Agrupa os lançamentos por mês, somando o saldo."""
    if df.empty:
        return pd.DataFrame(columns=["mes", "saldo"])
    mes = df["data"].dt.to_period("M").astype(str)
    agrupado = df.groupby(mes)["valor_assinado"].sum().reset_index()
    agrupado.columns = ["mes", "saldo"]
    return agrupado


def gastos_por_categoria(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna o total de saídas (gastos) agrupado por categoria, do maior para o menor."""
    if df.empty:
        return pd.DataFrame(columns=["categoria", "total"])
    saidas = df[df["tipo"] == "saida"]
    agrupado = saidas.groupby("categoria")["valor"].sum().reset_index()
    agrupado.columns = ["categoria", "total"]
    return agrupado.sort_values("total", ascending=False)


def dia_mais_lucrativo(df: pd.DataFrame):
    """Retorna a data e o saldo do dia com maior lucro líquido."""
    por_dia = resumo_por_dia(df)
    if por_dia.empty:
        return None, 0.0
    linha = por_dia.loc[por_dia["saldo"].idxmax()]
    return linha["data"], round(linha["saldo"], 2)