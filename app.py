import streamlit as st
from db import conectar
from auth import login
import pandas as pd

st.set_page_config(page_title="Inventário PRO v5", layout="wide")

# ================= LOGIN =================
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

# ================= APP =================
st.title("📦 Inventário PRO v5")

menu = st.sidebar.radio("Menu", [
    "📊 Dashboard",
    "📦 Produtos",
    "🔄 Movimentação",
    "📈 Relatórios",
    "🏢 Departamentos",
    "🚚 Fornecedores",
    "👤 Funcionários"
])

conn = conectar()
cur = conn.cursor()

# ================= DASHBOARD =================
if menu == "📊 Dashboard":

    df = pd.read_sql("SELECT * FROM produtos", conn)
    mov = pd.read_sql("SELECT * FROM movimentacoes", conn)

    col1, col2, col3 = st.columns(3)

    col1.metric("📦 Total itens", int(df["quantidade"].sum()))
    col2.metric("📊 Produtos cadastrados", len(df))

    valor = (df["quantidade"] * df["preco_custo"]).sum()
    col3.metric("💰 Valor estoque", f"{valor:.2f}")

    st.divider()

    # 📊 consumo por produto
    saidas = mov[mov["tipo"] == "Saída"]

    if not saidas.empty:
        ranking = saidas.groupby("produto_id")["quantidade"].sum().reset_index()

        prod = pd.read_sql("SELECT id, nome FROM produtos", conn)
        ranking = ranking.merge(prod, left_on="produto_id", right_on="id")

        st.subheader("🔥 Produtos mais consumidos")
        st.bar_chart(ranking.set_index("nome")["quantidade"])

    # 📊 consumo por departamento
    if "departamento_id" in mov.columns:
        dep = pd.read_sql("SELECT * FROM departamentos", conn)

        uso_dep = mov[mov["tipo"] == "Saída"].groupby("departamento_id")["quantidade"].sum().reset_index()

        if not uso_dep.empty:
            uso_dep = uso_dep.merge(dep, left_on="departamento_id", right_on="id")

            st.subheader("🏢 Consumo por departamento")
            st.bar_chart(uso_dep.set_index("nome")["quantidade"])


# ================= PRODUTOS =================
elif menu == "📦 Produtos":

    col1, col2 = st.columns([1,2])

    with col1:
        st.subheader("Novo Produto")

        nome = st.text_input("Nome")
        sku = st.text_input("SKU")
        qtd = st.number_input("Quantidade", min_value=0)

        forn_df = pd.read_sql("SELECT id, nome FROM fornecedores", conn)

        if forn_df.empty:
            st.warning("Cadastre fornecedores primeiro")
            st.stop()

        fornecedor = st.selectbox("Fornecedor", forn_df["nome"])

        if st.button("Salvar produto"):

            cur.execute("SELECT id FROM fornecedores WHERE nome=%s", (fornecedor,))
            fornecedor_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO produtos (nome, sku, quantidade, fornecedor_id)
                VALUES (%s,%s,%s,%s)
            """, (nome, sku, qtd, fornecedor_id))

            conn.commit()
            st.success("Produto cadastrado!")
            st.rerun()

    with col2:
        df = pd.read_sql("SELECT * FROM produtos ORDER BY nome", conn)
        st.dataframe(df, use_container_width=True)


# ================= MOVIMENTAÇÃO =================
elif menu == "🔄 Movimentação":

    tipo = st.radio("Tipo", ["Entrada", "Saída"])

    prod_df = pd.read_sql("SELECT id, nome, quantidade FROM produtos", conn)

    if prod_df.empty:
        st.warning("Cadastre produtos primeiro")
        st.stop()

    produto = st.selectbox("Produto", prod_df["nome"])
    qtd = st.number_input("Quantidade", min_value=1)

    fornecedor_id = None
    departamento_id = None
    funcionario_id = None

    if tipo == "Entrada":
        forn_df = pd.read_sql("SELECT id, nome FROM fornecedores", conn)
        fornecedor = st.selectbox("Fornecedor", forn_df["nome"])

    else:
        dep_df = pd.read_sql("SELECT id, nome FROM departamentos", conn)
        departamento = st.selectbox("Departamento", dep_df["nome"])

        func_df = pd.read_sql("SELECT id, nome FROM funcionarios", conn)
        funcionario = st.selectbox("Funcionário", func_df["nome"])

    if st.button("Registrar movimentação"):

        cur.execute("SELECT id FROM produtos WHERE nome=%s", (produto,))
        produto_id = cur.fetchone()[0]

        if tipo == "Entrada":
            cur.execute("SELECT id FROM fornecedores WHERE nome=%s", (fornecedor,))
            fornecedor_id = cur.fetchone()[0]

        else:
            cur.execute("SELECT id FROM departamentos WHERE nome=%s", (departamento,))
            departamento_id = cur.fetchone()[0]

            cur.execute("SELECT id FROM funcionarios WHERE nome=%s", (funcionario,))
            funcionario_id = cur.fetchone()[0]

            # bloquear estoque negativo
            cur.execute("SELECT quantidade FROM produtos WHERE id=%s", (produto_id,))
            atual = cur.fetchone()[0]

            if qtd > atual:
                st.error("Estoque insuficiente!")
                st.stop()

        cur.execute("""
            INSERT INTO movimentacoes 
            (produto_id, tipo, quantidade, fornecedor_id, departamento_id, funcionario_id)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (produto_id, tipo, qtd, fornecedor_id, departamento_id, funcionario_id))

        if tipo == "Entrada":
            cur.execute("UPDATE produtos SET quantidade = quantidade + %s WHERE id=%s", (qtd, produto_id))
        else:
            cur.execute("UPDATE produtos SET quantidade = quantidade - %s WHERE id=%s", (qtd, produto_id))

        conn.commit()
        st.success("Movimentação registrada!")
        st.rerun()


# ================= RELATÓRIOS =================
elif menu == "📈 Relatórios":

    st.subheader("Relatórios")

    mov = pd.read_sql("""
        SELECT m.*, p.nome as produto
        FROM movimentacoes m
        JOIN produtos p ON p.id = m.produto_id
        ORDER BY data DESC
    """, conn)

    st.dataframe(mov, use_container_width=True)

    # EXPORTAR
    csv = mov.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="📥 Baixar CSV",
        data=csv,
        file_name='relatorio.csv',
        mime='text/csv'
    )


# ================= CADASTROS =================
elif menu == "🏢 Departamentos":

    nome = st.text_input("Nome do departamento")

    if st.button("Salvar"):
        cur.execute("INSERT INTO departamentos (nome) VALUES (%s)", (nome,))
        conn.commit()
        st.rerun()

    st.dataframe(pd.read_sql("SELECT * FROM departamentos", conn))


elif menu == "🚚 Fornecedores":

    nome = st.text_input("Nome do fornecedor")

    if st.button("Salvar"):
        cur.execute("INSERT INTO fornecedores (nome) VALUES (%s)", (nome,))
        conn.commit()
        st.rerun()

    st.dataframe(pd.read_sql("SELECT * FROM fornecedores", conn))


elif menu == "👤 Funcionários":

    nome = st.text_input("Nome")

    dep_df = pd.read_sql("SELECT id, nome FROM departamentos", conn)
    departamento = st.selectbox("Departamento", dep_df["nome"])

    if st.button("Salvar"):
        cur.execute("SELECT id FROM departamentos WHERE nome=%s", (departamento,))
        dep_id = cur.fetchone()[0]

        cur.execute(
            "INSERT INTO funcionarios (nome, departamento_id) VALUES (%s,%s)",
            (nome, dep_id)
        )
        conn.commit()
        st.rerun()

    st.dataframe(pd.read_sql("SELECT * FROM funcionarios", conn))