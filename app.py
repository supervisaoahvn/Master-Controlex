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

menu = st.sidebar.selectbox("Menu", ["Dashboard", "Produtos", "Movimentações"])

conn = conectar()
cur = conn.cursor()

# DASHBOARD
if menu == "Dashboard":
    df = pd.read_sql("SELECT * FROM produtos", conn)

    st.subheader("📊 Estoque Atual")
    st.dataframe(df)

    st.bar_chart(df["quantidade"])

# PRODUTOS
elif menu == "Produtos":
    st.subheader("📦 Cadastro de Produto")

    nome = st.text_input("Nome")
    sku = st.text_input("SKU")
    quantidade = st.number_input("Quantidade", min_value=0)

    if st.button("Salvar"):
        cur.execute(
            "INSERT INTO produtos (nome, sku, quantidade) VALUES (%s,%s,%s)",
            (nome, sku, quantidade)
        )
        conn.commit()
        st.success("Produto cadastrado")

# MOVIMENTAÇÃO
elif menu == "Movimentações":
    st.subheader("🔄 Entrada / Saída")

    produto_id = st.number_input("ID Produto")
    tipo = st.selectbox("Tipo", ["entrada", "saida"])
    quantidade = st.number_input("Quantidade")

    if st.button("Registrar"):
        cur.execute(
            "INSERT INTO movimentacoes (produto_id, tipo, quantidade) VALUES (%s,%s,%s)",
            (produto_id, tipo, quantidade)
        )

        if tipo == "entrada":
            cur.execute("UPDATE produtos SET quantidade = quantidade + %s WHERE id=%s",
                        (quantidade, produto_id))
        else:
            cur.execute("UPDATE produtos SET quantidade = quantidade - %s WHERE id=%s",
                        (quantidade, produto_id))

        conn.commit()
        st.success("Movimentação registrada")
