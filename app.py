"""
app.py 
------ 
Aplicação principal do Zyncash, construída com Streamlit.

Como rodar:
    streamlit run app.py

Fluxo do app:
1. Tela de login/cadastro (cada usuário só vê seus próprios dados)
2. Formulário para registrar entradas e saídas do dia
3. Tabela colorida (verde = entrada, vermelho = saída)
4. Dashboard com totais, gráficos e resumo por semana/mês
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

import database as db
import analise

# ---------- Configuração inicial da página ----------
st.set_page_config(page_title="Zyncash", layout="wide")

# Garante que as tabelas do banco existem (só cria na primeira vez)
db.criar_tabelas()

# Categorias sugeridas — o usuário também pode digitar uma categoria livre
CATEGORIAS_SUGERIDAS = [
    "Combustível", "Manutenção", "Alimentação", "Trabalho",
    "Aluguel/Moradia", "Transporte", "Lazer", "Outros",
]


# ---------- Controle de sessão (login) ----------
def usuario_logado():
    return st.session_state.get("usuario_id") is not None


def tela_login():
    st.title(" Zyncash")
    st.caption("Pequenas decisões diárias constroem grandes resultados.")

    aba_login, aba_cadastro = st.tabs(["Entrar", "Criar conta"])

    with aba_login:
        with st.form("form_login"):
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            enviado = st.form_submit_button("Entrar")

            if enviado:
                usuario = db.autenticar_usuario(email, senha)
                if usuario:
                    st.session_state["usuario_id"] = usuario["id"]
                    st.session_state["usuario_nome"] = usuario["nome"]
                    st.rerun()
                else:
                    st.error("E-mail ou senha incorretos.")

    with aba_cadastro:
        with st.form("form_cadastro"):
            nome = st.text_input("Nome")
            email_novo = st.text_input("E-mail para cadastro")
            senha_nova = st.text_input("Crie uma senha", type="password")
            enviado_cad = st.form_submit_button("Criar conta")

            if enviado_cad:
                if not nome or not email_novo or not senha_nova:
                    st.warning("Preencha todos os campos.")
                else:
                    sucesso, mensagem = db.criar_usuario(nome, email_novo, senha_nova)
                    if sucesso:
                        st.success(mensagem + " Agora entre na aba 'Entrar'.")
                    else:
                        st.error(mensagem)


# ---------- Formulário de novo lançamento ----------
def formulario_lancamento(usuario_id: int):
    st.subheader("Registre novo Lançamento")

    with st.form("form_lancamento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data_lanc = st.date_input("Data", value=date.today())
            tipo = st.radio("Tipo", ["entrada", "saida"], horizontal=True,
                             format_func=lambda t: "Entrada" if t == "entrada" else "Saída")
        with col2:
            categoria = st.selectbox("Categoria", CATEGORIAS_SUGERIDAS)
            valor = st.number_input("Valor (R$)", min_value=0.0, step=1.0, format="%.2f")

        descricao = st.text_input("Descrição (ex: gasolina, gás, roupa)")
        enviado = st.form_submit_button("Adicionar lançamento")

        if enviado:
            if valor <= 0 or not descricao.strip():
                st.warning("Preencha a descrição e um valor maior que zero.")
            else:
                db.inserir_lancamento(
                    usuario_id, data_lanc.isoformat(), descricao.strip(), categoria, tipo, valor
                )
                st.success("Lançamento adicionado!")


# ---------- Tabela colorida ----------
def tabela_colorida(df: pd.DataFrame):
    st.subheader("Lançamentos")

    if df.empty:
        st.info("Nenhum lançamento ainda. Use o formulário acima para começar.")
        return

    def cor_linha(linha):
        cor = "#d4f7d4" if linha["tipo"] == "entrada" else "#f7d4d4"
        return [f"background-color: {cor}"] * len(linha)

    tabela_exibicao = df[["data", "descricao", "categoria", "tipo", "valor"]].copy()
    tabela_exibicao["data"] = tabela_exibicao["data"].dt.strftime("%d/%m/%Y")
    tabela_exibicao["valor"] = tabela_exibicao["valor"].apply(lambda v: f"R$ {v:,.2f}")
    tabela_exibicao["tipo"] = tabela_exibicao["tipo"].map({"entrada": "Entrada", "saida": "Saída"})

    estilizada = tabela_exibicao.style.apply(cor_linha, axis=1)
    st.dataframe(estilizada, use_container_width=True, hide_index=True)


# ---------- Dashboard com métricas e gráficos ----------
def dashboard(df: pd.DataFrame):
    st.subheader("Resumo")

    resumo = analise.resumo_geral(df)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total recebido", f"R$ {resumo['total_entradas']:,.2f}")
    col2.metric("Total gasto", f"R$ {resumo['total_saidas']:,.2f}")
    col3.metric("Lucro líquido", f"R$ {resumo['lucro']:,.2f}")

    if df.empty:
        return

    aba_dia, aba_semana, aba_mes, aba_categoria = st.tabs(
        ["Por dia", "Por semana", "Por mês", "Gastos por categoria"]
    )

    with aba_dia:
        por_dia = analise.resumo_por_dia(df)
        fig, ax = plt.subplots(figsize=(8, 3))
        cores = ["#2ecc71" if v >= 0 else "#e74c3c" for v in por_dia["saldo"]]
        ax.bar(por_dia["data"].astype(str), por_dia["saldo"], color=cores)
        ax.set_ylabel("Saldo (R$)")
        ax.set_title("Saldo por dia")
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        plt.xticks(rotation=0, ha="center")
        fig.tight_layout()
        st.pyplot(fig)

    with aba_semana:
        por_semana = analise.resumo_por_semana(df)
        fig, ax = plt.subplots(figsize=(8, 3))
        cores = ["#2ecc71" if v >= 0 else "#e74c3c" for v in por_semana["saldo"]]
        ax.bar(por_semana["semana"], por_semana["saldo"], color=cores)
        ax.set_ylabel("Saldo (R$)")
        ax.set_title("Saldo por semana")
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        plt.xticks(rotation=0, ha="center")
        fig.tight_layout()
        st.pyplot(fig)

    with aba_mes:
        por_mes = analise.resumo_por_mes(df)
        fig, ax = plt.subplots(figsize=(8, 3))
        cores = ["#2ecc71" if v >= 0 else "#e74c3c" for v in por_mes["saldo"]]
        ax.bar(por_mes["mes"], por_mes["saldo"], color=cores)
        ax.set_ylabel("Saldo (R$)")
        ax.set_title("Saldo por mês")
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        plt.xticks(rotation=0, ha="center")
        fig.tight_layout()
        st.pyplot(fig)

    with aba_categoria:
        gastos = analise.gastos_por_categoria(df)
        if gastos.empty:
            st.info("Nenhum gasto registrado ainda.")
        else:
            fig, ax = plt.subplots(figsize=(6, 6))
            ax.pie(gastos["total"], labels=gastos["categoria"], autopct="%1.1f%%", startangle=90)
            ax.set_title("Distribuição de gastos por categoria")
            st.pyplot(fig)


# ---------- Permitir excluir lançamentos ----------
def secao_exclusao(df: pd.DataFrame, usuario_id: int):
    if df.empty:
        return
    with st.expander("Excluir um lançamento"):
        opcoes = {
            f"{row['data'].strftime('%d/%m/%Y')} — {row['descricao']} (R$ {row['valor']:.2f})": row["id"]
            for _, row in df.iterrows()
        }
        escolha = st.selectbox("Selecione o lançamento", list(opcoes.keys()))
        if st.button("Excluir"):
            db.excluir_lancamento(opcoes[escolha], usuario_id)
            st.success("Lançamento excluído.")
            st.rerun()


# ---------- Aplicação principal ----------
def main():
    if not usuario_logado():
        tela_login()
        return

    st.sidebar.title(f"Olá, {st.session_state['usuario_nome']} ")
    if st.sidebar.button("Sair"):
        st.session_state.clear()
        st.rerun()

    st.title(" Zyncash")
    st.caption("Pequenas decisões diárias constroem grandes resultados.")

    usuario_id = st.session_state["usuario_id"]

    formulario_lancamento(usuario_id)
    st.divider()

    lancamentos = db.listar_lancamentos(usuario_id)
    df = analise.lancamentos_para_dataframe(lancamentos)

    tabela_colorida(df)
    secao_exclusao(df, usuario_id)
    st.divider()
    dashboard(df)


if __name__ == "__main__":
    main()