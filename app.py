import streamlit as st
from db import conectar
from auth import login
from modules import (
    dashboard,
    produtos,
    movimentacao,
    departamentos,
    fornecedores,
    relatorios,
    solicitacoes
)
st.set_page_config(layout="wide")

conn = conectar()
cur = conn.cursor()

# LOGIN
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    user = st.text_input("User")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        dados = login(user, senha)
        if dados:
            st.session_state.logado = True
            st.session_state.usuario_id = dados["id"]
            st.session_state.empresa_id = dados["empresa_id"]
            st.rerun()
    st.stop()

empresa_id = st.session_state.empresa_id
user_id = st.session_state.usuario_id

menu = st.sidebar.radio("Menu", [
    "Dashboard",
    "Produtos",
    "Movimentação",
    "Departamentos",
    "Fornecedores",
    "Solicitações",
    "Relatórios"
])
])

if menu == "Dashboard":
    dashboard.render(conn, empresa_id)

elif menu == "Produtos":
    produtos.render(conn, cur, empresa_id)

elif menu == "Movimentação":
    movimentacao.render(conn, cur, empresa_id, st.session_state.usuario_id)

elif menu == "Departamentos":
    departamentos.render(conn, cur, empresa_id)

elif menu == "Fornecedores":
    fornecedores.render(conn, cur, empresa_id)

elif menu == "Solicitações":
    solicitacoes.render(conn, cur, empresa_id)

elif menu == "Relatórios":
    relatorios.render(conn, empresa_id)