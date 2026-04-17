def load_css(file):
    with open(file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("styles/base.css")
load_css("styles/dashboard.css")
import streamlit as st
from db import conectar
from auth import criar_usuario, login
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
# ================= LOGIN =================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:

    aba = st.radio("Acesso", ["Login", "Cadastrar"])

    if aba == "Login":
        st.title("🔐 Login")

        user = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            dados = login(user, senha)

            if dados:
                st.session_state.logado = True
                st.session_state.usuario_id = dados["id"]
                st.session_state.nivel = dados["nivel"]
                st.session_state.empresa_id = dados["empresa_id"]

                st.success("Login OK")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")

    else:
        st.title("🆕 Criar Conta")

        user = st.text_input("Novo usuário")
        senha = st.text_input("Senha", type="password")
        nivel = st.selectbox("Nível", ["admin", "operador"])

        if st.button("Criar usuário"):
            criar_usuario(user, senha, nivel, 1)
            st.success("Usuário criado!")

    st.stop()  # 🔥 ESSA LINHA É CRÍTICA

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