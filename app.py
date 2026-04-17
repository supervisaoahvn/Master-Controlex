import streamlit as st
from db import conectar
from auth import login, criar_usuario
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Inventário PRO V9", layout="wide")

conn = conectar()
cur = conn.cursor()
st.markdown("""
<style>
.stButton>button {
    border-radius: 8px;
    height: 45px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)
# ================= LOGIN =================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:

    aba = st.radio("Acesso", ["Login", "Cadastrar"])

    # LOGIN
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

                st.success("Login realizado!")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")

    # CADASTRO
    else:
        st.title("🆕 Criar Conta")

        user = st.text_input("Novo usuário")
        senha = st.text_input("Senha", type="password")
        nivel = st.selectbox("Nível", ["admin", "operador"])

        if st.button("Criar usuário"):
            criar_usuario(user, senha, nivel, 1)
            st.success("Usuário criado!")

    st.stop()

# ================= APP =================
empresa_id = st.session_state.empresa_id

# ================= MENU =================
menu = st.sidebar.radio("Menu", [
    "Dashboard",
    "Produtos",
    "Movimentação",
    "Usuários",
    "Relatórios",
])

# LOGOUT (fica sempre visível)
if st.sidebar.button("🚪 Sair"):
    st.session_state.clear()
    st.rerun()

# ================= DASHBOARD =================

if menu == "Dashboard":

    df = pd.read_sql(f"""
        SELECT * FROM produtos
        WHERE empresa_id = {empresa_id}
    """, conn)

    mov = pd.read_sql(f"""
        SELECT * FROM movimentacoes
        WHERE empresa_id = {empresa_id}
    """, conn)

    st.subheader("📊 Dashboard PRO")

    col1, col2 = st.columns(2)

    col1.metric("Total Produtos", len(df))
    col2.metric("Estoque Total", int(df["quantidade"].sum()))

    # 🔥 gráfico estoque
    if not df.empty:
        fig = px.bar(df, x="nome", y="quantidade", title="Estoque por Produto")
        st.plotly_chart(fig, use_container_width=True)

    # 🔥 ranking consumo
    saidas = mov[mov["tipo"] == "Saída"]

    if not saidas.empty:
        ranking = saidas.groupby("produto_id")["quantidade"].sum().reset_index()

        nomes = pd.read_sql(f"""
    SELECT id, nome FROM produtos WHERE empresa_id = {empresa_id}
""", conn)
        ranking = ranking.merge(nomes, left_on="produto_id", right_on="id")

        fig2 = px.bar(ranking, x="nome", y="quantidade", title="Produtos mais consumidos")
        st.plotly_chart(fig2, use_container_width=True)


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

    # 🔥 valida estoque
    if tipo == "Saída":
        cur.execute("SELECT quantidade FROM produtos WHERE id=%s", (produto_id,))
        atual = cur.fetchone()[0]

        if qtd > atual:
            st.error("❌ Estoque insuficiente!")
            st.stop()

    # 🔥 registra movimentação
    cur.execute("""
        INSERT INTO movimentacoes (produto_id, tipo, quantidade, empresa_id)
        VALUES (%s,%s,%s,%s)
    """, (produto_id, tipo, qtd, empresa_id))

    # 🔥 atualiza estoque
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

# ================= RELATORIOS =================
elif menu == "Relatórios":

    df = pd.read_sql(f"""
        SELECT m.*, p.nome as produto
        FROM movimentacoes m
        JOIN produtos p ON p.id = m.produto_id
        WHERE m.empresa_id = {empresa_id}
        ORDER BY data DESC
    """, conn)

    st.subheader("📈 Relatórios")

    st.dataframe(df, use_container_width=True)

    # CSV
    csv = df.to_csv(index=False).encode()
    st.download_button("📥 Baixar CSV", csv, "relatorio.csv")

    # EXCEL (correto em memória)
    from io import BytesIO
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    st.download_button("📥 Baixar Excel", buffer.getvalue(), "relatorio.xlsx")