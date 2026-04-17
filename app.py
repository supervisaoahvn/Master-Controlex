import streamlit as st
from db import conectar
from auth import login, criar_usuario
import pandas as pd

st.set_page_config(page_title="Inventário PRO V8", layout="wide")

# ================= ESTILO =================
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
}
.stButton>button {
    width: 100%;
    border-radius: 10px;
    height: 45px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

conn = conectar()
cur = conn.cursor()

# ================= LOGIN =================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:

    st.title("🚀 Inventário PRO")
    st.caption("Sistema profissional de controle de estoque")

    aba1, aba2 = st.tabs(["🔐 Login", "🆕 Criar Conta"])

    # LOGIN
    with aba1:
        user = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            dados = login(user, senha)

            if dados:
                st.session_state.logado = True
                st.session_state.empresa_id = dados["empresa_id"]
                st.success("Login realizado!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")

    # CADASTRO
    with aba2:
        empresa = st.text_input("Nome da empresa")
        user = st.text_input("Novo usuário")
        senha = st.text_input("Nova senha", type="password")

        if st.button("Criar conta"):
            cur.execute("INSERT INTO empresas (nome) VALUES (%s) RETURNING id", (empresa,))
            empresa_id = cur.fetchone()[0]

            criar_usuario(user, senha, empresa_id)

            conn.commit()
            st.success("Conta criada com sucesso!")

    st.stop()

# ================= PROTEÇÃO =================
if "empresa_id" not in st.session_state:
    st.error("Sessão inválida")
    st.stop()

empresa_id = st.session_state.empresa_id

# ================= APP =================
st.title("📦 Inventário PRO")

menu = st.sidebar.radio("Menu", [
    "📊 Dashboard",
    "📦 Produtos",
    "🔄 Movimentação",
    "📈 Relatórios",
    "🏢 Departamentos",
    "🚚 Fornecedores",
    "👤 Funcionários"
])

# ================= DASHBOARD =================
if menu == "📊 Dashboard":

    df = pd.read_sql("SELECT * FROM produtos WHERE empresa_id=%s", conn, params=(empresa_id,))

    st.subheader("📊 Visão Geral")

    col1, col2, col3 = st.columns(3)

    col1.metric("Produtos", len(df))
    col2.metric("Estoque total", int(df["quantidade"].sum()) if not df.empty else 0)

    valor = (df["quantidade"] * df["preco_custo"]).sum() if "preco_custo" in df.columns else 0
    col3.metric("Valor total", f"R$ {valor:.2f}")

    st.divider()
    st.dataframe(df, use_container_width=True)

# ================= PRODUTOS =================
elif menu == "📦 Produtos":

    col1, col2 = st.columns([1,2])

    with col1:
        st.subheader("Novo Produto")

        nome = st.text_input("Nome")
        sku = st.text_input("SKU")
        qtd = st.number_input("Quantidade", min_value=0)

        forn_df = pd.read_sql("SELECT id, nome FROM fornecedores WHERE empresa_id=%s", conn, params=(empresa_id,))
        fornecedor = st.selectbox("Fornecedor", forn_df["nome"] if not forn_df.empty else [])

        if st.button("Salvar produto"):

            # evitar duplicado
            cur.execute("SELECT id FROM produtos WHERE sku=%s AND empresa_id=%s", (sku, empresa_id))
            if cur.fetchone():
                st.warning("SKU já existe!")
                st.stop()

            fornecedor_id = None
            if fornecedor:
                cur.execute("SELECT id FROM fornecedores WHERE nome=%s AND empresa_id=%s", (fornecedor, empresa_id))
                fornecedor_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO produtos (nome, sku, quantidade, fornecedor_id, empresa_id)
                VALUES (%s,%s,%s,%s,%s)
            """, (nome, sku, qtd, fornecedor_id, empresa_id))

            conn.commit()
            st.success("Produto cadastrado!")
            st.rerun()

    with col2:
        df = pd.read_sql("SELECT * FROM produtos WHERE empresa_id=%s", conn, params=(empresa_id,))
        st.dataframe(df, use_container_width=True)

# ================= MOVIMENTAÇÃO =================
elif menu == "🔄 Movimentação":

    tipo = st.radio("Tipo", ["Entrada", "Saída"])

    prod_df = pd.read_sql("SELECT id, nome, quantidade FROM produtos WHERE empresa_id=%s", conn, params=(empresa_id,))
    produto = st.selectbox("Produto", prod_df["nome"])

    qtd = st.number_input("Quantidade", min_value=1)

    if st.button("Registrar movimentação"):

        cur.execute("SELECT id FROM produtos WHERE nome=%s AND empresa_id=%s", (produto, empresa_id))
        produto_id = cur.fetchone()[0]

        # valida estoque
        if tipo == "Saída":
            cur.execute("SELECT quantidade FROM produtos WHERE id=%s", (produto_id,))
            atual = cur.fetchone()[0]

            if qtd > atual:
                st.error("Estoque insuficiente!")
                st.stop()

        # atualiza estoque
        if tipo == "Entrada":
            cur.execute("UPDATE produtos SET quantidade = quantidade + %s WHERE id=%s", (qtd, produto_id))
        else:
            cur.execute("UPDATE produtos SET quantidade = quantidade - %s WHERE id=%s", (qtd, produto_id))

        # registra
        cur.execute("""
            INSERT INTO movimentacoes (produto_id, tipo, quantidade, empresa_id)
            VALUES (%s,%s,%s,%s)
        """, (produto_id, tipo, qtd, empresa_id))

        conn.commit()
        st.success("Movimentação registrada!")
        st.rerun()

# ================= RELATÓRIOS =================
elif menu == "📈 Relatórios":

    df = pd.read_sql("""
        SELECT m.*, p.nome as produto
        FROM movimentacoes m
        JOIN produtos p ON p.id = m.produto_id
        WHERE m.empresa_id=%s
        ORDER BY data DESC
    """, conn, params=(empresa_id,))

    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode()
    st.download_button("📥 Baixar CSV", csv, "relatorio.csv")

# ================= CADASTROS =================
elif menu == "🚚 Fornecedores":

    nome = st.text_input("Nome do fornecedor")

    if st.button("Salvar fornecedor"):
        cur.execute("INSERT INTO fornecedores (nome, empresa_id) VALUES (%s,%s)", (nome, empresa_id))
        conn.commit()
        st.rerun()

    st.dataframe(pd.read_sql("SELECT * FROM fornecedores WHERE empresa_id=%s", conn, params=(empresa_id,)))

elif menu == "🏢 Departamentos":

    nome = st.text_input("Nome do departamento")

    if st.button("Salvar departamento"):
        cur.execute("INSERT INTO departamentos (nome, empresa_id) VALUES (%s,%s)", (nome, empresa_id))
        conn.commit()
        st.rerun()

    st.dataframe(pd.read_sql("SELECT * FROM departamentos WHERE empresa_id=%s", conn, params=(empresa_id,)))

elif menu == "👤 Funcionários":

    nome = st.text_input("Nome do funcionário")

    if st.button("Salvar funcionário"):
        cur.execute("INSERT INTO funcionarios (nome, empresa_id) VALUES (%s,%s)", (nome, empresa_id))
        conn.commit()
        st.rerun()

    st.dataframe(pd.read_sql("SELECT * FROM funcionarios WHERE empresa_id=%s", conn, params=(empresa_id,)))