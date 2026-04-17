import streamlit as st
from db import conectar
from auth import login
import pandas as pd

st.set_page_config(page_title="Inventário PRO 4.0", layout="wide")

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
st.title("📦 Inventário PRO 4.0")

menu = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Produtos", "Movimentação", "Relatórios"]
)

conn = conectar()
cur = conn.cursor()

# ================= DASHBOARD =================
if menu == "Dashboard":

    df = pd.read_sql("SELECT * FROM produtos", conn)

    col1, col2 = st.columns(2)

    col1.metric("Itens em estoque", int(df["quantidade"].sum()))

    valor = (df["quantidade"] * df["preco_custo"]).sum()
    col2.metric("Valor total", f"R$ {valor:.2f}")

    st.subheader("📊 Estoque por Produto")
    st.bar_chart(df.set_index("nome")["quantidade"])

    # ALERTA
    baixo = df[df["quantidade"] <= df["estoque_minimo"]]

    if not baixo.empty:
        st.error("⚠ Estoque baixo")
        st.dataframe(baixo)


# ================= PRODUTOS =================
elif menu == "Produtos":

    st.subheader("Cadastro")

    nome = st.text_input("Nome")
    sku = st.text_input("SKU")
    qtd = st.number_input("Quantidade", 0)
    custo = st.number_input("Preço custo", 0.0)
    minimo = st.number_input("Estoque mínimo", 0)

    forn_df = pd.read_sql("SELECT nome FROM fornecedores", conn)

    if not forn_df.empty:
        fornecedor = st.selectbox("Fornecedor", forn_df["nome"])

    if st.button("Salvar"):

        cur.execute("SELECT id FROM produtos WHERE sku=%s", (sku,))
        if cur.fetchone():
            st.error("SKU já existe")
            st.stop()

        cur.execute("SELECT id FROM fornecedores WHERE nome=%s", (fornecedor,))
        fornecedor_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO produtos (nome, sku, quantidade, preco_custo, estoque_minimo, fornecedor_id)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (nome, sku, qtd, custo, minimo, fornecedor_id))

        conn.commit()
        st.success("Salvo")
        st.rerun()

    st.divider()

    df = pd.read_sql("SELECT * FROM produtos", conn)
    st.dataframe(df)


# ================= MOVIMENTAÇÃO =================
elif menu == "Movimentação":

    tipo = st.radio("Tipo", ["Entrada", "Saída"])

    df = pd.read_sql("SELECT id, nome, quantidade FROM produtos", conn)
    produto = st.selectbox("Produto", df["nome"])

    qtd = st.number_input("Quantidade", 1)

    if st.button("Registrar"):

        cur.execute("SELECT id, quantidade FROM produtos WHERE nome=%s", (produto,))
        produto_id, estoque = cur.fetchone()

        if tipo == "Saída" and qtd > estoque:
            st.error("Sem estoque")
            st.stop()

        if tipo == "Entrada":
            cur.execute("UPDATE produtos SET quantidade = quantidade + %s WHERE id=%s", (qtd, produto_id))
        else:
            cur.execute("UPDATE produtos SET quantidade = quantidade - %s WHERE id=%s", (qtd, produto_id))

        cur.execute("""
            INSERT INTO movimentacoes (produto_id, tipo, quantidade)
            VALUES (%s,%s,%s)
        """, (produto_id, tipo, qtd))

        conn.commit()
        st.success("OK")
        st.rerun()


# ================= RELATÓRIOS =================
elif menu == "Relatórios":

    st.subheader("📊 Consumo")

    df = pd.read_sql("""
        SELECT tipo, SUM(quantidade) as total
        FROM movimentacoes
        GROUP BY tipo
    """, conn)

    st.dataframe(df)
    st.bar_chart(df.set_index("tipo"))

    # EXPORTAR CSV
    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="📥 Baixar CSV",
        data=csv,
        file_name="relatorio.csv",
        mime="text/csv"
    )