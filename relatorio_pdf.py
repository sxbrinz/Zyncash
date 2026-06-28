"""
relatorio_pdf.py
------------------
Geração de relatórios em PDF a partir dos dados financeiros do usuário.
Oferece dois relatórios independentes:
  - gerar_pdf_tabela(): só a tabela de lançamentos
  - gerar_pdf_graficos(): só os gráficos de resumo (barras por período)
"""

import io
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

import analise


def _formatar_real(valor: float) -> str:
    """Formata um número como moeda brasileira: 1234.5 -> '1.234,50'."""
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _cabecalho(elementos, styles, titulo: str):
    """Adiciona um cabeçalho padrão com o título do relatório e a data de geração."""
    elementos.append(Paragraph("Zyncash", styles["Title"]))
    elementos.append(Paragraph(titulo, styles["Heading2"]))
    data_geracao = datetime.now().strftime("%d/%m/%Y às %H:%M")
    elementos.append(Paragraph(f"Gerado em {data_geracao}", styles["Normal"]))
    elementos.append(Spacer(1, 0.5 * cm))


def gerar_pdf_tabela(df) -> bytes:
    """
    Gera um PDF contendo apenas a tabela de lançamentos (data, descrição,
    categoria, tipo e valor). Retorna os bytes do PDF, prontos para download.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elementos = []

    _cabecalho(elementos, styles, "Relatório de Lançamentos")

    if df.empty:
        elementos.append(Paragraph("Nenhum lançamento cadastrado até o momento.", styles["Normal"]))
    else:
        dados_tabela = [["Data", "Descrição", "Categoria", "Tipo", "Valor (R$)"]]
        for _, linha in df.iterrows():
            tipo_legivel = "Entrada" if linha["tipo"] == "entrada" else "Saída"
            dados_tabela.append([
                linha["data"].strftime("%d/%m/%Y"),
                str(linha["descricao"]).capitalize(),
                str(linha["categoria"]).capitalize(),
                tipo_legivel,
                f"R$ {_formatar_real(linha['valor'])}",
            ])

        tabela = Table(dados_tabela, repeatRows=1, hAlign="LEFT")
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a2332")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ("ALIGN", (4, 0), (4, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elementos.append(tabela)

        resumo = analise.resumo_geral(df)
        elementos.append(Spacer(1, 0.7 * cm))
        elementos.append(Paragraph(
            f"<b>Total recebido:</b> R$ {_formatar_real(resumo['total_entradas'])} &nbsp;&nbsp; "
            f"<b>Total gasto:</b> R$ {_formatar_real(resumo['total_saidas'])} &nbsp;&nbsp; "
            f"<b>Lucro líquido:</b> R$ {_formatar_real(resumo['lucro'])}",
            styles["Normal"],
        ))

    doc.build(elementos)
    buffer.seek(0)
    return buffer.read()


def _figura_para_imagem_reportlab(fig, largura_cm=16):
    """Converte uma figura do matplotlib em um objeto Image utilizável pelo reportlab."""
    img_buffer = io.BytesIO()
    fig.savefig(img_buffer, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    img_buffer.seek(0)
    return Image(img_buffer, width=largura_cm * cm, height=largura_cm * 0.45 * cm)


def gerar_pdf_graficos(df) -> bytes:
    """
    Gera um PDF contendo apenas os gráficos de resumo financeiro
    (saldo por dia, por semana, por mês e gastos por categoria).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elementos = []

    _cabecalho(elementos, styles, "Relatório Gráfico")

    if df.empty:
        elementos.append(Paragraph("Nenhum lançamento cadastrado até o momento.", styles["Normal"]))
        doc.build(elementos)
        buffer.seek(0)
        return buffer.read()

    resumo = analise.resumo_geral(df)
    elementos.append(Paragraph(
        f"<b>Total recebido:</b> R$ {_formatar_real(resumo['total_entradas'])} &nbsp;&nbsp; "
        f"<b>Total gasto:</b> R$ {_formatar_real(resumo['total_saidas'])} &nbsp;&nbsp; "
        f"<b>Lucro líquido:</b> R$ {_formatar_real(resumo['lucro'])}",
        styles["Normal"],
    ))
    elementos.append(Spacer(1, 0.6 * cm))

    # Gráfico 1: saldo por dia
    por_dia = analise.resumo_por_dia(df)
    if not por_dia.empty:
        fig, ax = plt.subplots(figsize=(8, 3))
        cores = ["#2ecc71" if v >= 0 else "#e74c3c" for v in por_dia["saldo"]]
        ax.bar(por_dia["data"].astype(str), por_dia["saldo"], color=cores)
        ax.set_ylabel("Saldo (R$)")
        ax.set_title("Saldo por dia")
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        plt.xticks(rotation=0, ha="center")
        fig.tight_layout()
        elementos.append(_figura_para_imagem_reportlab(fig))
        elementos.append(Spacer(1, 0.4 * cm))

    # Gráfico 2: saldo por semana
    por_semana = analise.resumo_por_semana(df)
    if not por_semana.empty:
        fig, ax = plt.subplots(figsize=(8, 3))
        cores = ["#2ecc71" if v >= 0 else "#e74c3c" for v in por_semana["saldo"]]
        ax.bar(por_semana["semana"], por_semana["saldo"], color=cores)
        ax.set_ylabel("Saldo (R$)")
        ax.set_title("Saldo por semana")
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        plt.xticks(rotation=0, ha="center")
        fig.tight_layout()
        elementos.append(_figura_para_imagem_reportlab(fig))
        elementos.append(Spacer(1, 0.4 * cm))

    # Gráfico 3: saldo por mês
    por_mes = analise.resumo_por_mes(df)
    if not por_mes.empty:
        fig, ax = plt.subplots(figsize=(8, 3))
        cores = ["#2ecc71" if v >= 0 else "#e74c3c" for v in por_mes["saldo"]]
        ax.bar(por_mes["mes"], por_mes["saldo"], color=cores)
        ax.set_ylabel("Saldo (R$)")
        ax.set_title("Saldo por mês")
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        plt.xticks(rotation=0, ha="center")
        fig.tight_layout()
        elementos.append(_figura_para_imagem_reportlab(fig))
        elementos.append(Spacer(1, 0.4 * cm))

    # Gráfico 4: gastos por categoria (pizza)
    gastos = analise.gastos_por_categoria(df)
    if not gastos.empty:
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pie(gastos["total"], labels=gastos["categoria"], autopct="%1.1f%%", startangle=90)
        ax.set_title("Distribuição de gastos por categoria")
        elementos.append(_figura_para_imagem_reportlab(fig, largura_cm=12))

    doc.build(elementos)
    buffer.seek(0)
    return buffer.read()
