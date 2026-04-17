import streamlit as st
from db import conectar
from auth import login, criar_usuario
import pandas as pd

st.set_page_config(page_title="Inventário PRO V9", layout="wide")

conn = conectar()
cur = conn.cursor()

# ================= LOGIN =================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:

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
            st.rerun()
        else:
            st.error("Login inválido")

    st.stop()

empresa_id = st.session_state.empresa_id

# ================= MENU =================
menu = st.sidebar.radio("Menu", [
    "Dashboard",
    "Produtos",
    "Movimentação",
    "Usuários"
])

# ================= DASHBOARD =================
if menu == "Dashboard":

    df = pd.read_sql(f"""
        SELECT * FROM produtos
        WHERE empresa_id = {empresa_id}
    """, conn)

    st.subheader("📊 Dashboard")

    col1, col2 = st.columns(2)

    col1.metric("Total Itens", int(df["quantidade"].sum()))

    if "preco_custo" in df.columns:
        valor = (df["quantidade"] * df["preco_custo"]).sum()
        col2.metric("Valor Estoque", f"{valor:.2f}")

    st.bar_chart(df.set_index("nome")["quantidade"])


# ================= PRODUTOS =================
elif menu == "Produtos":

    st.subheader("Cadastro de Produtos")

    nome = st.text_input("Nome")
    sku = st.text_input("SKU")
    qtd = st.number_input("Quantidade", min_value=0)

    if st.button("Salvar"):
        cur.execute("""
            INSERT INTO produtos (nome, sku, quantidade, empresa_id)
            VALUES (%s,%s,%s,%s)
        """, (nome, sku, qtd, empresa_id))
        conn.commit()
        st.success("Salvo!")
        st.rerun()

    df = pd.read_sql(f"""
        SELECT * FROM produtos
        WHERE empresa_id = {empresa_id}
    """, conn)

    st.dataframe(df)


# ================= MOVIMENTAÇÃO =================
elif menu == "Movimentação":

    tipo = st.radio("Tipo", ["Entrada", "Saída"])

    df = pd.read_sql(f"""
        SELECT id, nome FROM produtos
        WHERE empresa_id = {empresa_id}
    """, conn)

    produto = st.selectbox("Produto", df["nome"])
    qtd = st.number_input("Quantidade", min_value=1)

    if st.button("Movimentar"):

        cur.execute("SELECT id FROM produtos WHERE nome=%s", (produto,))
        produto_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO movimentacoes (produto_id, tipo, quantidade, empresa_id)
            VALUES (%s,%s,%s,%s)
        """, (produto_id, tipo, qtd, empresa_id))

        if tipo == "Entrada":
            cur.execute("UPDATE produtos SET quantidade = quantidade + %s WHERE id=%s", (qtd, produto_id))
        else:
            cur.execute("UPDATE produtos SET quantidade = quantidade - %s WHERE id=%s", (qtd, produto_id))

        conn.commit()
        st.success("Movimentado!")
        st.rerun()


# ================= USUÁRIOS =================
elif menu == "Usuários":

    if st.session_state.nivel != "admin":
        st.warning("Apenas admin pode acessar")
        st.stop()

    st.subheader("Criar Usuário")

    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    nivel = st.selectbox("Nível", ["admin", "operador"])

    if st.button("Criar"):
        criar_usuario(user, senha, nivel, empresa_id)
        st.success("Usuário criado!")