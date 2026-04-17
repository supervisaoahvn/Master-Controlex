import streamlit as st
from db import conectar
from auth import login, criar_usuario
import pandas as pd

st.set_page_config(page_title="Inventário PRO V12 HARDENED", layout="wide")

conn = conectar()
cur = conn.cursor()

# ================= SAFE EXECUTE =================
def safe_execute(query, params=None, fetch=False):
    try:
        cur.execute(query, params or ())
        if fetch:
            return cur.fetchall()
        conn.commit()
    except Exception as e:
        st.error(f"Erro SQL: {e}")
        return None

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
    "Departamentos",
    "Fornecedores",
    "Relatórios",
    "Logout"
])

# ================= DASHBOARD =================
if menu == "Dashboard":

    df = pd.read_sql(f"""
        SELECT * FROM produtos WHERE empresa_id = {empresa_id}
    """, conn)

    st.title("📊 Dashboard")

    if not df.empty:
        st.metric("Total Itens", int(df["quantidade"].sum()))

        if "preco_custo" in df.columns:
            valor = (df["quantidade"] * df["preco_custo"]).sum()
            st.metric("Valor Estoque", f"{valor:.2f}")

        st.bar_chart(df.set_index("nome")["quantidade"])

# ================= PRODUTOS =================
elif menu == "Produtos":

    st.subheader("Produtos")

    nome = st.text_input("Nome")
    sku = st.text_input("SKU (único)")
    qtd = st.number_input("Quantidade", min_value=0)

    if st.button("Salvar"):
        safe_execute("""
            INSERT INTO produtos (nome, sku, quantidade, empresa_id)
            VALUES (%s,%s,%s,%s)
        """, (nome, sku, qtd, empresa_id))

        st.success("Produto salvo")
        st.rerun()

    df = pd.read_sql(f"""
        SELECT * FROM produtos WHERE empresa_id = {empresa_id}
    """, conn)

    st.dataframe(df)

# ================= MOVIMENTAÇÃO =================
elif menu == "Movimentação":

    tipo = st.radio("Tipo", ["Entrada", "Saída"])

    produtos = pd.read_sql(f"""
        SELECT id, nome FROM produtos WHERE empresa_id = {empresa_id}
    """, conn)

    departamentos = pd.read_sql(f"""
        SELECT id, nome FROM departamentos WHERE empresa_id = {empresa_id}
    """, conn)

    produto_nome = st.selectbox("Produto", produtos["nome"])
    departamento_nome = st.selectbox("Departamento", departamentos["nome"])
    qtd = st.number_input("Quantidade", min_value=1)

    if st.button("Movimentar"):

        try:
            # produto
            cur.execute("SELECT id FROM produtos WHERE nome=%s", (produto_nome,))
            produto_id = cur.fetchone()[0]

            # departamento
            cur.execute("SELECT id FROM departamentos WHERE nome=%s", (departamento_nome,))
            departamento_id = cur.fetchone()[0]

            # INSERT seguro
            safe_execute("""
                INSERT INTO movimentacoes 
                (produto_id, tipo, quantidade, empresa_id, departamento_id, usuario_id)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                produto_id,
                tipo,
                qtd,
                empresa_id,
                departamento_id,
                st.session_state.usuario_id
            ))

            # Atualiza estoque
            if tipo == "Entrada":
                safe_execute("UPDATE produtos SET quantidade = quantidade + %s WHERE id=%s", (qtd, produto_id))
            else:
                safe_execute("UPDATE produtos SET quantidade = quantidade - %s WHERE id=%s", (qtd, produto_id))

            st.success("Movimentação registrada")
            st.rerun()

        except Exception as e:
            st.error(f"Erro movimentação: {e}")

# ================= DEPARTAMENTOS =================
elif menu == "Departamentos":

    nome = st.text_input("Nome do departamento")

    if st.button("Criar"):
        safe_execute("""
            INSERT INTO departamentos (nome, empresa_id)
            VALUES (%s,%s)
        """, (nome, empresa_id))
        st.success("Criado")

    df = pd.read_sql(f"""
        SELECT * FROM departamentos WHERE empresa_id = {empresa_id}
    """, conn)

    st.dataframe(df)

# ================= FORNECEDORES =================
elif menu == "Fornecedores":

    nome = st.text_input("Nome")
    telefone = st.text_input("Telefone")
    doc = st.text_input("CNPJ/CPF")

    if st.button("Salvar"):
        safe_execute("""
            INSERT INTO fornecedores (nome, telefone, documento, empresa_id)
            VALUES (%s,%s,%s,%s)
        """, (nome, telefone, doc, empresa_id))

        st.success("Fornecedor salvo")

    df = pd.read_sql(f"""
        SELECT * FROM fornecedores WHERE empresa_id = {empresa_id}
    """, conn)

    st.dataframe(df)

# ================= RELATÓRIOS =================
elif menu == "Relatórios":

    st.subheader("Relatórios")

    df = pd.read_sql(f"""
        SELECT m.*, p.nome as produto
        FROM movimentacoes m
        LEFT JOIN produtos p ON p.id = m.produto_id
        WHERE m.empresa_id = {empresa_id}
        ORDER BY m.data DESC
    """, conn)

    busca = st.text_input("Buscar produto")

    if busca:
        df = df[df["produto"].str.contains(busca, case=False)]

    st.dataframe(df)

    st.download_button("Baixar CSV", df.to_csv(index=False), "relatorio.csv")

# ================= LOGOUT =================
elif menu == "Logout":
    st.session_state.clear()
    st.rerun()