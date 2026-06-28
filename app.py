"""
app.py
-------
Aplicação principal do Zyncash, construída com Streamlit.

Como rodar:
    streamlit run app.py

Fluxo do app:
1. Tela de login (campo de e-mail/senha em destaque; "Criar conta" como ação secundária)
2. Formulário para registrar entradas e saídas do dia, com campo de valor com máscara monetária
3. Tabela de lançamentos com indicador colorido (bolinha) por tipo, e opção de editar/excluir
4. Menu de opções (⋮) no canto superior direito com: resumo filtrado, gráficos filtrados,
   download de PDF (tabela e gráficos separados) e caixa de sugestões
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

import database as db
import analise
import relatorio_pdf

# ---------- Configuração inicial da página ----------
st.set_page_config(page_title="Zyncash", layout="wide")

# Garante que as tabelas do banco existem (só cria na primeira vez)
db.criar_tabelas()

# Categorias sugeridas — o usuário também pode digitar uma categoria livre
CATEGORIAS_SUGERIDAS = [
    "Combustível", "Manutenção", "Alimentação", "Trabalho",
    "Aluguel/Moradia", "Transporte", "Lazer", "Outros",
]


# ======================================================================
# Funções auxiliares gerais
# ======================================================================

def usuario_logado() -> bool:
    return st.session_state.get("usuario_id") is not None


def formatar_real(valor: float) -> str:
    """Formata um número como moeda brasileira: 1234.5 -> 'R$ 1.234,50'."""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


# ======================================================================
# Tela de login / cadastro
# ======================================================================

def tela_login():
    st.title("Zyncash")
    st.caption("Pequenas decisões diárias constroem grandes resultados.")
    st.write("")

    # Login em primeiro plano — simples, direto, sem abas que possam confundir.
    col_esquerda, col_centro, col_direita = st.columns([1, 2, 1])
    with col_centro:
        st.subheader("Entrar")
        email = st.text_input("E-mail", key="login_email")
        senha = st.text_input("Senha", type="password", key="login_senha")

        if st.button("Entrar", use_container_width=True, type="primary"):
            usuario = db.autenticar_usuario(email, senha)
            if usuario:
                st.session_state["usuario_id"] = usuario["id"]
                st.session_state["usuario_nome"] = usuario["nome"]
                st.rerun()
            else:
                st.error("E-mail ou senha incorretos.")

        st.write("")
        st.divider()
        st.write("Ainda não tem uma conta?")

        if st.button("Criar conta", use_container_width=True):
            st.session_state["mostrar_cadastro"] = True
            st.rerun()

    if st.session_state.get("mostrar_cadastro"):
        with col_centro:
            st.write("")
            st.subheader("Criar conta")
            nome = st.text_input("Nome", key="cad_nome")
            email_novo = st.text_input("E-mail", key="cad_email")
            senha_nova = st.text_input("Crie uma senha", type="password", key="cad_senha")

            if st.button("Confirmar cadastro", use_container_width=True, type="primary"):
                if not nome or not email_novo or not senha_nova:
                    st.warning("Preencha todos os campos.")
                else:
                    sucesso, mensagem = db.criar_usuario(nome, email_novo, senha_nova)
                    if sucesso:
                        st.success(mensagem + " Agora você já pode entrar.")
                        st.session_state["mostrar_cadastro"] = False
                    else:
                        st.error(mensagem)

            if st.button("Cancelar", use_container_width=True):
                st.session_state["mostrar_cadastro"] = False
                st.rerun()


# ======================================================================
# Campo de valor com máscara monetária (estilo caixa eletrônico)
# ======================================================================

# ======================================================================
# Campo de valor com máscara monetária (estilo caixa eletrônico)
# ======================================================================

def _formatar_campo_valor(key_atual: str):
    """
    Callback chamado pelo Streamlit (via on_change) sempre que o conteúdo do campo
    muda. É o único momento em que é permitido alterar st.session_state de um
    widget que já existe — por isso a reformatação acontece aqui, e não durante
    o desenho normal da tela.
    """
    texto_digitado = st.session_state.get(key_atual, "")
    apenas_digitos = "".join(filter(str.isdigit, texto_digitado))

    if not apenas_digitos:
        st.session_state[key_atual] = ""
        return

    valor_numerico = int(apenas_digitos) / 100
    st.session_state[key_atual] = formatar_real(valor_numerico)


def campo_valor_monetario(label: str, key_base: str, valor_inicial_centavos: int = 0) -> tuple[float, str]:
    """
    Mostra um campo de valor que formata o que o usuário digita como dinheiro
    (ex: digitar '1050' mostra 'R$ 10,50'), tudo dentro do mesmo campo de texto.

    Para evitar o erro do Streamlit "valor não pode ser alterado após o widget
    já existir", este campo usa uma key dinâmica (contador, trocado sempre que o
    formulário é limpo) e reformata o valor através de um callback (on_change),
    que é o mecanismo correto e suportado pelo Streamlit para esse caso.

    Retorna uma tupla (valor_numerico, key_atual_usada).
    """
    contador = st.session_state.get(f"{key_base}_contador", 0)
    key_atual = f"{key_base}_{contador}"

    if key_atual not in st.session_state and valor_inicial_centavos:
        st.session_state[key_atual] = formatar_real(valor_inicial_centavos / 100)

    st.markdown(f"**{label}**")
    st.text_input(
        label="valor_oculto",
        key=key_atual,
        placeholder="R$ 0,00",
        label_visibility="collapsed",
        on_change=_formatar_campo_valor,
        args=(key_atual,),
    )

    valor_texto = st.session_state.get(key_atual, "")
    apenas_digitos = "".join(filter(str.isdigit, valor_texto))
    valor_numerico = int(apenas_digitos) / 100 if apenas_digitos else 0.0

    return valor_numerico, key_atual


def limpar_campo_valor(key_base: str):
    """Avança o contador de uma key dinâmica, fazendo o próximo campo nascer vazio."""
    contador_atual = st.session_state.get(f"{key_base}_contador", 0)
    st.session_state[f"{key_base}_contador"] = contador_atual + 1


# ======================================================================
# Formulário de novo lançamento
# ======================================================================

def formulario_lancamento(usuario_id: int):
    st.subheader("Novo Lançamento")

    contador_desc = st.session_state.get("descricao_novo_contador", 0)
    key_descricao = f"descricao_novo_{contador_desc}"

    col1, col2 = st.columns(2)
    with col1:
        data_lanc = st.date_input(
            "Data", value=date.today(), key="data_novo", format="DD/MM/YYYY"
        )
        tipo = st.radio("Tipo", ["entrada", "saida"], horizontal=True,
                         format_func=lambda t: "Entrada" if t == "entrada" else "Saída",
                         key="tipo_novo")
    with col2:
        categoria = st.selectbox("Categoria", CATEGORIAS_SUGERIDAS, key="categoria_novo")
        valor, key_valor_usada = campo_valor_monetario("Valor (R$)", key_base="valor_novo_lancamento")

    descricao = st.text_input("Descrição (ex: gasolina, gás, roupa)", key=key_descricao)
    enviado = st.button("Adicionar lançamento")

    if enviado:
        if valor <= 0:
            st.warning("Informe um valor maior que zero.")
        else:
            descricao_final = descricao.strip().capitalize() if descricao.strip() else "Sem descrição"
            db.inserir_lancamento(
                usuario_id, data_lanc.isoformat(), descricao_final, categoria, tipo, valor
            )
            st.success("Lançamento adicionado!")
            limpar_campo_valor("valor_novo_lancamento")
            st.session_state["descricao_novo_contador"] = contador_desc + 1
            st.rerun()


# ======================================================================
# Tabela de lançamentos (com bolinha colorida) + editar/excluir
# ======================================================================

# Definição de todas as colunas possíveis na tabela, na ordem de exibição.
COLUNAS_TABELA = ["Tipo", "Data", "Descrição", "Categoria", "Valor", "Ações"]
LARGURAS_COLUNAS = {
    "Tipo": 0.6, "Data": 1.2, "Descrição": 2.2,
    "Categoria": 1.5, "Valor": 1.3, "Ações": 1.2,
}


def _aplicar_estilo_tabela():
    """Insere um CSS simples para desenhar linhas e colunas (grade) na tabela manual."""
    st.markdown(
        """
        <style>
        .zyncash-linha {
            border-bottom: 1px solid rgba(49, 51, 63, 0.2);
            padding: 0.4rem 0;
        }
        .zyncash-cabecalho {
            border-bottom: 2px solid rgba(49, 51, 63, 0.4);
            padding-bottom: 0.4rem;
            font-weight: 600;
        }
        div[data-testid="column"] {
            border-right: 1px solid rgba(49, 51, 63, 0.12);
            padding-right: 0.6rem;
        }
        div[data-testid="column"]:last-child {
            border-right: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def tabela_lancamentos(df: pd.DataFrame, usuario_id: int):
    st.subheader("Lançamentos")

    if df.empty:
        st.info("Nenhum lançamento ainda. Use o formulário acima para começar.")
        return

    colunas_visiveis = st.multiselect(
        "Colunas visíveis",
        options=[c for c in COLUNAS_TABELA if c != "Ações"],
        default=[c for c in COLUNAS_TABELA if c != "Ações"],
        key="colunas_visiveis_tabela",
    )
    colunas_exibidas = colunas_visiveis + ["Ações"]

    _aplicar_estilo_tabela()

    larguras = [LARGURAS_COLUNAS[c] for c in colunas_exibidas]
    colunas_cabecalho = st.columns(larguras)
    for col, nome in zip(colunas_cabecalho, colunas_exibidas):
        col.markdown(f"<div class='zyncash-cabecalho'>{nome}</div>", unsafe_allow_html=True)

    for _, linha in df.iterrows():
        colunas_linha = st.columns(larguras)
        indice = 0

        if "Tipo" in colunas_exibidas:
            bolinha = "🟢" if linha["tipo"] == "entrada" else "🔴"
            colunas_linha[indice].markdown(
                f"<div class='zyncash-linha' style='font-size:18px'>{bolinha}</div>",
                unsafe_allow_html=True,
            )
            indice += 1

        if "Data" in colunas_exibidas:
            colunas_linha[indice].markdown(
                f"<div class='zyncash-linha'>{linha['data'].strftime('%d/%m/%Y')}</div>",
                unsafe_allow_html=True,
            )
            indice += 1

        if "Descrição" in colunas_exibidas:
            colunas_linha[indice].markdown(
                f"<div class='zyncash-linha'>{str(linha['descricao']).capitalize()}</div>",
                unsafe_allow_html=True,
            )
            indice += 1

        if "Categoria" in colunas_exibidas:
            colunas_linha[indice].markdown(
                f"<div class='zyncash-linha'>{str(linha['categoria']).capitalize()}</div>",
                unsafe_allow_html=True,
            )
            indice += 1

        if "Valor" in colunas_exibidas:
            colunas_linha[indice].markdown(
                f"<div class='zyncash-linha'>{formatar_real(linha['valor'])}</div>",
                unsafe_allow_html=True,
            )
            indice += 1

        with colunas_linha[indice]:
            sub_col1, sub_col2 = st.columns(2)
            if sub_col1.button("✏️", key=f"editar_{linha['id']}", help="Editar lançamento"):
                st.session_state["editando_id"] = int(linha["id"])
                st.rerun()
            if sub_col2.button("🗑️", key=f"excluir_{linha['id']}", help="Excluir lançamento"):
                db.excluir_lancamento(int(linha["id"]), usuario_id)
                st.rerun()

    # Formulário de edição, exibido apenas quando o usuário clicou em "editar"
    if st.session_state.get("editando_id"):
        formulario_edicao(st.session_state["editando_id"], usuario_id)


def formulario_edicao(lancamento_id: int, usuario_id: int):
    lancamento = db.buscar_lancamento(lancamento_id, usuario_id)
    if lancamento is None:
        st.session_state["editando_id"] = None
        return

    st.divider()
    st.subheader("Editar lançamento")

    col1, col2 = st.columns(2)
    with col1:
        data_edit = st.date_input(
            "Data", value=pd.to_datetime(lancamento["data"]).date(),
            key=f"data_edicao_{lancamento_id}", format="DD/MM/YYYY",
        )
        tipo_edit = st.radio(
            "Tipo", ["entrada", "saida"], horizontal=True,
            format_func=lambda t: "Entrada" if t == "entrada" else "Saída",
            index=0 if lancamento["tipo"] == "entrada" else 1,
            key=f"tipo_edicao_{lancamento_id}",
        )
    with col2:
        categorias_disponiveis = CATEGORIAS_SUGERIDAS.copy()
        if lancamento["categoria"] not in categorias_disponiveis:
            categorias_disponiveis.append(lancamento["categoria"])
        categoria_edit = st.selectbox(
            "Categoria", categorias_disponiveis,
            index=categorias_disponiveis.index(lancamento["categoria"]),
            key=f"categoria_edicao_{lancamento_id}",
        )
        valor_edit, key_valor_edicao = campo_valor_monetario(
            "Valor (R$)", key_base=f"valor_edicao_{lancamento_id}",
            valor_inicial_centavos=int(round(lancamento["valor"] * 100)),
        )

    descricao_edit = st.text_input(
        "Descrição", value=lancamento["descricao"], key=f"descricao_edicao_{lancamento_id}"
    )

    col_salvar, col_cancelar = st.columns(2)
    if col_salvar.button("Salvar alterações", type="primary", use_container_width=True):
        if valor_edit <= 0:
            st.warning("Informe um valor maior que zero.")
        else:
            descricao_final = descricao_edit.strip().capitalize() if descricao_edit.strip() else "Sem descrição"
            db.atualizar_lancamento(
                lancamento_id, usuario_id, data_edit.isoformat(),
                descricao_final, categoria_edit, tipo_edit, valor_edit,
            )
            st.session_state["editando_id"] = None
            st.success("Lançamento atualizado!")
            st.rerun()

    if col_cancelar.button("Cancelar", use_container_width=True):
        st.session_state["editando_id"] = None
        st.rerun()


# ======================================================================
# Menu de opções (⋮): resumo, gráficos, PDFs e sugestões
# ======================================================================

def menu_opcoes(df: pd.DataFrame, usuario_id: int, usuario_nome: str):
    with st.popover("⋮", use_container_width=False):
        aba_resumo, aba_graficos, aba_download, aba_sugestao = st.tabs(
            ["Resumo", "Gráficos", "Download", "Sugestões"]
        )

        # ---------- Resumo filtrado ----------
        with aba_resumo:
            periodo = st.selectbox(
                "Filtrar por período", ["todos", "dia", "semana", "mes"],
                format_func=lambda p: {"todos": "Sem filtro", "dia": "Hoje",
                                        "semana": "Últimos 7 dias", "mes": "Últimos 30 dias"}[p],
                key="periodo_resumo",
            )
            df_filtrado = analise.filtrar_por_periodo(df, periodo)
            resumo = analise.resumo_geral(df_filtrado)

            st.metric("Total recebido", formatar_real(resumo["total_entradas"]))
            st.metric("Total gasto", formatar_real(resumo["total_saidas"]))
            st.metric("Lucro líquido", formatar_real(resumo["lucro"]))

        # ---------- Gráficos filtrados ----------
        with aba_graficos:
            periodo_g = st.selectbox(
                "Filtrar por período", ["todos", "dia", "semana", "mes"],
                format_func=lambda p: {"todos": "Sem filtro", "dia": "Hoje",
                                        "semana": "Últimos 7 dias", "mes": "Últimos 30 dias"}[p],
                key="periodo_grafico",
            )
            df_filtrado_g = analise.filtrar_por_periodo(df, periodo_g)

            if df_filtrado_g.empty:
                st.info("Sem lançamentos no período selecionado.")
            else:
                por_dia = analise.resumo_por_dia(df_filtrado_g)
                fig, ax = plt.subplots(figsize=(6, 3))
                cores = ["#2ecc71" if v >= 0 else "#e74c3c" for v in por_dia["saldo"]]
                ax.bar(por_dia["data"].astype(str), por_dia["saldo"], color=cores)
                ax.set_ylabel("Saldo (R$)")
                ax.set_title("Saldo por dia")
                ax.grid(axis="y", linestyle="--", alpha=0.3)
                plt.xticks(rotation=0, ha="center")
                fig.tight_layout()
                st.pyplot(fig)

                gastos = analise.gastos_por_categoria(df_filtrado_g)
                if not gastos.empty:
                    fig2, ax2 = plt.subplots(figsize=(5, 5))
                    ax2.pie(gastos["total"], labels=gastos["categoria"], autopct="%1.1f%%", startangle=90)
                    ax2.set_title("Gastos por categoria")
                    st.pyplot(fig2)

        # ---------- Download de PDFs ----------
        with aba_download:
            st.write("Baixe seus dados em PDF:")

            pdf_tabela_bytes = relatorio_pdf.gerar_pdf_tabela(df)
            st.download_button(
                "📄 Baixar tabela de lançamentos (PDF)",
                data=pdf_tabela_bytes,
                file_name="zyncash_lancamentos.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

            pdf_graficos_bytes = relatorio_pdf.gerar_pdf_graficos(df)
            st.download_button(
                "📊 Baixar gráficos (PDF)",
                data=pdf_graficos_bytes,
                file_name="zyncash_graficos.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        # ---------- Caixa de sugestões ----------
        with aba_sugestao:
            st.write("Tem alguma ideia para melhorar o Zyncash? Conte para a gente:")
            mensagem = st.text_area("Sua sugestão", key="texto_sugestao")
            if st.button("Enviar sugestão", use_container_width=True):
                if mensagem.strip():
                    db.salvar_sugestao(usuario_id, usuario_nome, mensagem.strip())
                    st.success("Sugestão enviada, muito obrigada!")
                    st.session_state["texto_sugestao"] = ""
                else:
                    st.warning("Escreva sua sugestão antes de enviar.")


# ======================================================================
# Aplicação principal
# ======================================================================

def main():
    if not usuario_logado():
        tela_login()
        return

    st.sidebar.title(f"Olá, {st.session_state['usuario_nome']} ")
    if st.sidebar.button("Sair"):
        st.session_state.clear()
        st.rerun()

    usuario_id = st.session_state["usuario_id"]
    usuario_nome = st.session_state["usuario_nome"]

    lancamentos = db.listar_lancamentos(usuario_id)
    df = analise.lancamentos_para_dataframe(lancamentos)

    col_titulo, col_menu = st.columns([10, 1])
    with col_titulo:
        st.title("Zyncash")
        st.caption("Pequenas decisões diárias constroem grandes resultados.")
    with col_menu:
        st.write("")
        menu_opcoes(df, usuario_id, usuario_nome)

    formulario_lancamento(usuario_id)
    st.divider()
    tabela_lancamentos(df, usuario_id)


if __name__ == "__main__":
    main()