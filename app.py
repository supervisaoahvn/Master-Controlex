import streamlit as st
from db import conectar
from auth import login
import pandas as pd

st.set_page_config(page_title="Inventário PRO", layout="wide")

# LOGIN
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login")

    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if login(user, senha):
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Login inválido")

    st.stop()

# APP
st.title("📦 Sistema de Inventário")

menu = st.sidebar.radio(
    "📂 Menu",
    ["📊 Dashboard", "📦 Produtos", "🔄 Movimentação"]
)

conn = conectar()
cur = conn.cursor()

# DASHBOARD
if menu == "📊 Dashboard":
    df = pd.read_sql("SELECT * FROM produtos", conn)

    st.subheader("📊 Visão Geral")

    col1, col2 = st.columns(2)

    col1.metric("📦 Total itens", df["quantidade"].sum())

    if "preco_custo" in df.columns:
        valor = (df["quantidade"] * df["preco_custo"]).sum()
        col2.metric("💰 Valor estoque", f"{valor:.2f}")

    st.divider()
    st.dataframe(df, use_container_width=True)

# PRODUTOS
elif menu == "📦 Produtos":

    col1, col2 = st.columns([1,2])

    with col1:
        st.subheader("➕ Novo")

        nome = st.text_input("Nome")
        sku = st.text_input("SKU")
        qtd = st.number_input("Qtd", min_value=0)

        if st.button("Salvar"):
            cur.execute(
                "INSERT INTO produtos (nome, sku, quantidade) VALUES (%s,%s,%s)",
                (nome, sku, qtd)
            )
            conn.commit()
            st.success("Produto cadastrado!")
            st.rerun()

    with col2:
        st.subheader("📦 Produtos")

        busca = st.text_input("🔍 Buscar")

        query = "SELECT * FROM produtos"
        if busca:
            query += f" WHERE nome ILIKE '%{busca}%'"
        query += " ORDER BY nome"

        df = pd.read_sql(query, conn)
        st.dataframe(df, use_container_width=True)

# MOVIMENTAÇÃO
elif menu == "🔄 Movimentação":

    df = pd.read_sql("SELECT id, nome, quantidade FROM produtos ORDER BY nome", conn)

    col1, col2, col3 = st.columns([2,1,1])

    produto = col1.selectbox("Produto", df["nome"])
    qtd = col2.number_input("Qtd", min_value=1)
    tipo = col3.selectbox("Tipo", ["+", "-"])

    if st.button("Confirmar", use_container_width=True):

        cur.execute("SELECT id, quantidade FROM produtos WHERE nome=%s", (produto,))
        produto_id, atual = cur.fetchone()

        if tipo == "-" and qtd > atual:
            st.error("Estoque insuficiente!")
        else:
            if tipo == "+":
                cur.execute(
                    "UPDATE produtos SET quantidade = quantidade + %s WHERE id=%s",
                    (qtd, produto_id)
                )
            else:
                cur.execute(
                    "UPDATE produtos SET quantidade = quantidade - %s WHERE id=%s",
                    (qtd, produto_id)
                )

            conn.commit()
            st.success("✔ Atualizado")
            st.rerun()