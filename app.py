import streamlit as st
from db import conectar
from auth import login
import pandas as pd

st.set_page_config(page_title="Inventário PRO V7", layout="wide")

conn = conectar()
cur = conn.cursor()

# ================= LOGIN / CADASTRO =================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:

    st.title("🚀 Inventário PRO")

    aba = st.tabs(["🔐 Login", "🆕 Criar Conta"])

    # LOGIN
    with aba[0]:
        user = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            dados = login(user, senha)

            if dados:
                st.session_state.logado = True
                st.session_state.empresa_id = dados["empresa_id"]
                st.success("Login OK")
                st.rerun()
            else:
                st.error("Login inválido")

    # CADASTRO
    with aba[1]:
        empresa = st.text_input("Empresa")
        user = st.text_input("Novo usuário")
        senha = st.text_input("Nova senha", type="password")

        if st.button("Criar conta"):
            cur.execute("INSERT INTO empresas (nome) VALUES (%s) RETURNING id", (empresa,))
            empresa_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO usuarios (username, senha, empresa_id)
                VALUES (%s,%s,%s)
            """, (user, senha, empresa_id))

            conn.commit()
            st.success("Conta criada!")

    st.stop()

# ================= APP =================
empresa_id = st.session_state.empresa_id

st.title("📦 Inventário PRO")

menu = st.sidebar.radio("Menu", [
    "Dashboard",
    "Produtos",
    "Movimentação",
    "Relatórios",
    "Departamentos",
    "Fornecedores",
    "Funcionários"
])

# ================= DASHBOARD =================
if menu == "Dashboard":

    df = pd.read_sql("SELECT * FROM produtos WHERE empresa_id=%s", conn, params=(empresa_id,))

    st.metric("Itens em estoque", int(df["quantidade"].sum()) if not df.empty else 0)

    st.dataframe(df, use_container_width=True)

# ================= PRODUTOS =================
elif menu == "Produtos":

    nome = st.text_input("Nome")
    sku = st.text_input("SKU")
    qtd = st.number_input("Quantidade", min_value=0)

    forn_df = pd.read_sql("SELECT id, nome FROM fornecedores WHERE empresa_id=%s", conn, params=(empresa_id,))

    fornecedor = st.selectbox("Fornecedor", forn_df["nome"] if not forn_df.empty else [])

    if st.button("Salvar"):
        if fornecedor:
            cur.execute("SELECT id FROM fornecedores WHERE nome=%s AND empresa_id=%s", (fornecedor, empresa_id))
            fornecedor_id = cur.fetchone()[0]
        else:
            fornecedor_id = None

        cur.execute("""
            INSERT INTO produtos (nome, sku, quantidade, fornecedor_id, empresa_id)
            VALUES (%s,%s,%s,%s,%s)
        """, (nome, sku, qtd, fornecedor_id, empresa_id))

        conn.commit()
        st.rerun()

    df = pd.read_sql("SELECT * FROM produtos WHERE empresa_id=%s", conn, params=(empresa_id,))
    st.dataframe(df)

# ================= MOVIMENTAÇÃO =================
elif menu == "Movimentação":

    tipo = st.radio("Tipo", ["Entrada", "Saída"])

    prod_df = pd.read_sql("SELECT id, nome FROM produtos WHERE empresa_id=%s", conn, params=(empresa_id,))
    produto = st.selectbox("Produto", prod_df["nome"])

    qtd = st.number_input("Quantidade", min_value=1)

    if st.button("Registrar"):

        cur.execute("SELECT id FROM produtos WHERE nome=%s AND empresa_id=%s", (produto, empresa_id))
        produto_id = cur.fetchone()[0]

        if tipo == "Entrada":
            cur.execute("UPDATE produtos SET quantidade = quantidade + %s WHERE id=%s", (qtd, produto_id))
        else:
            cur.execute("UPDATE produtos SET quantidade = quantidade - %s WHERE id=%s", (qtd, produto_id))

        cur.execute("""
            INSERT INTO movimentacoes (produto_id, tipo, quantidade, empresa_id)
            VALUES (%s,%s,%s,%s)
        """, (produto_id, tipo, qtd, empresa_id))

        conn.commit()
        st.success("OK")
        st.rerun()

# ================= RELATÓRIOS =================
elif menu == "Relatórios":

    df = pd.read_sql("""
        SELECT m.*, p.nome as produto
        FROM movimentacoes m
        JOIN produtos p ON p.id = m.produto_id
        WHERE m.empresa_id=%s
        ORDER BY data DESC
    """, conn, params=(empresa_id,))

    st.dataframe(df)

    csv = df.to_csv(index=False).encode()
    st.download_button("Baixar CSV", csv, "relatorio.csv")

# ================= CADASTROS =================
elif menu == "Fornecedores":

    nome = st.text_input("Nome")

    if st.button("Salvar"):
        cur.execute("INSERT INTO fornecedores (nome, empresa_id) VALUES (%s,%s)", (nome, empresa_id))
        conn.commit()
        st.rerun()

    st.dataframe(pd.read_sql("SELECT * FROM fornecedores WHERE empresa_id=%s", conn, params=(empresa_id,)))

elif menu == "Departamentos":

    nome = st.text_input("Nome")

    if st.button("Salvar"):
        cur.execute("INSERT INTO departamentos (nome, empresa_id) VALUES (%s,%s)", (nome, empresa_id))
        conn.commit()
        st.rerun()

    st.dataframe(pd.read_sql("SELECT * FROM departamentos WHERE empresa_id=%s", conn, params=(empresa_id,)))

elif menu == "Funcionários":

    nome = st.text_input("Nome")

    if st.button("Salvar"):
        cur.execute("INSERT INTO funcionarios (nome, empresa_id) VALUES (%s,%s)", (nome, empresa_id))
        conn.commit()
        st.rerun()

    st.dataframe(pd.read_sql("SELECT * FROM funcionarios WHERE empresa_id=%s", conn, params=(empresa_id,)))