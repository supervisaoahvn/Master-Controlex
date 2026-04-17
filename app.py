import streamlit as st
import pandas as pd
import plotly.express as px
from db import conectar
from auth import login, criar_usuario

st.set_page_config(page_title="Inventário PRO V11 MAX", layout="wide")

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
nivel = st.session_state.nivel

# ================= MENU =================
menu = st.sidebar.radio("Menu", [
    "Dashboard",
    "Produtos",
    "Movimentação",
    "Fornecedores",
    "Relatórios"
])

# ================= DASHBOARD =================
if menu == "Dashboard":

    df = pd.read_sql(f"""
        SELECT * FROM produtos WHERE empresa_id = {empresa_id}
    """, conn)

    mov = pd.read_sql(f"""
        SELECT * FROM movimentacoes WHERE empresa_id = {empresa_id}
    """, conn)

    st.title("📊 Dashboard PRO MAX")

    # KPIs
    col1, col2 = st.columns(2)
    col1.metric("Total Estoque", int(df["quantidade"].sum()))

    valor = (df["quantidade"] * df.get("preco_custo", 0)).sum()
    col2.metric("Valor Total", f"{valor:.2f}")

    # 🚨 ALERTA ESTOQUE
    alerta = df[df["quantidade"] <= df["estoque_minimo"]]
    if not alerta.empty:
        st.error("⚠️ Produtos com estoque baixo!")
        st.dataframe(alerta)

    # 📊 PIZZA (distribuição)
    fig_pizza = px.pie(df, names="nome", values="quantidade", title="Distribuição Estoque")
    st.plotly_chart(fig_pizza, use_container_width=True)

    # 📈 MONTANHA
    fig_area = px.area(df, x="nome", y="quantidade", title="Estoque por Produto")
    st.plotly_chart(fig_area, use_container_width=True)

    # 🏆 PRODUTOS MAIS MOVIMENTADOS
    ranking = pd.read_sql(f"""
        SELECT p.nome, SUM(m.quantidade) as total
        FROM movimentacoes m
        JOIN produtos p ON p.id = m.produto_id
        WHERE m.empresa_id = {empresa_id}
        GROUP BY p.nome
        ORDER BY total DESC
        LIMIT 10
    """, conn)

    fig_rank = px.bar(ranking, x="nome", y="total", title="Top Produtos")
    st.plotly_chart(fig_rank, use_container_width=True)

    # 👥 USUÁRIOS MAIS ATIVOS
    users = pd.read_sql(f"""
        SELECT u.usuario, SUM(m.quantidade) as total
        FROM movimentacoes m
        JOIN usuarios u ON u.id = m.usuario_id
        WHERE m.empresa_id = {empresa_id}
        GROUP BY u.usuario
        ORDER BY total DESC
    """, conn)

    fig_users = px.bar(users, x="usuario", y="total", title="Usuários Ativos")
    st.plotly_chart(fig_users, use_container_width=True)

# ================= PRODUTOS =================
elif menu == "Produtos":

    if nivel == "operador":
        st.warning("Operador não pode cadastrar produtos")
        st.stop()

    nome = st.text_input("Nome")
    sku = st.text_input("SKU")
    qtd = st.number_input("Quantidade", min_value=0)
    minimo = st.number_input("Estoque mínimo", min_value=0)

    if st.button("Salvar"):
        cur.execute("""
            INSERT INTO produtos (nome, sku, quantidade, estoque_minimo, empresa_id)
            VALUES (%s,%s,%s,%s,%s)
        """, (nome, sku, qtd, minimo, empresa_id))
        conn.commit()
        st.success("Salvo!")

# ================= MOVIMENTAÇÃO =================
elif menu == "Movimentação":

    df = pd.read_sql(f"""
        SELECT id, nome FROM produtos WHERE empresa_id = {empresa_id}
    """, conn)

    produto = st.selectbox("Produto", df["nome"])
    qtd = st.number_input("Quantidade", min_value=1)
    tipo = st.radio("Tipo", ["Entrada", "Saída"])

    if st.button("Movimentar"):

        cur.execute("SELECT id FROM produtos WHERE nome=%s", (produto,))
        produto_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO movimentacoes (produto_id, tipo, quantidade, empresa_id, usuario_id)
            VALUES (%s,%s,%s,%s,%s)
        """, (produto_id, tipo, qtd, empresa_id, st.session_state.usuario_id))

        if tipo == "Entrada":
            cur.execute("UPDATE produtos SET quantidade = quantidade + %s WHERE id=%s", (qtd, produto_id))
        else:
            cur.execute("UPDATE produtos SET quantidade = quantidade - %s WHERE id=%s", (qtd, produto_id))

        conn.commit()
        st.success("Movimentado!")
        st.rerun()

# ================= RELATÓRIOS =================
elif menu == "Relatórios":

    df = pd.read_sql(f"""
        SELECT m.*, p.nome as produto
        FROM movimentacoes m
        JOIN produtos p ON p.id = m.produto_id
        WHERE m.empresa_id = {empresa_id}
    """, conn)

    produto = st.selectbox("Filtro Produto", ["Todos"] + df["produto"].unique().tolist())

    if produto != "Todos":
        df = df[df["produto"] == produto]

    st.dataframe(df)

    st.download_button("Exportar CSV", df.to_csv(index=False), "relatorio.csv")