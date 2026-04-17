import streamlit as st
from db import conectar
from auth import login, criar_usuario
import pandas as pd
import plotly.express as px
import io
from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib.pagesizes import letter

st.set_page_config(page_title="Inventário PRO V11 MAX", layout="wide")

conn = conectar()
cur = conn.cursor()

# ================= ESTILO =================
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

    st.stop()

empresa_id = st.session_state.empresa_id
nivel = st.session_state.nivel

# ================= MENU =================
menu = st.sidebar.radio("Menu", [
    "Dashboard",
    "Produtos",
    "Movimentação",
    "Departamentos",
    "Fornecedores",
    "Usuários",
    "Relatórios"
])

if st.sidebar.button("🚪 Sair"):
    st.session_state.clear()
    st.rerun()

# ================= DASHBOARD =================
if menu == "Dashboard":

    df = pd.read_sql(f"SELECT * FROM produtos WHERE empresa_id = {empresa_id}", conn)
    mov = pd.read_sql(f"SELECT * FROM movimentacoes WHERE empresa_id = {empresa_id}", conn)

    st.title("📊 Dashboard PRO MAX")

    col1, col2 = st.columns(2)
    col1.metric("Total Produtos", len(df))
    col2.metric("Estoque Total", int(df["quantidade"].sum()))

    if not df.empty:
        fig = px.bar(df, x="nome", y="quantidade", title="Estoque por Produto")
        st.plotly_chart(fig, use_container_width=True)

    # ranking produtos
    saidas = mov[mov["tipo"] == "Saída"]
    if not saidas.empty:
        ranking = saidas.groupby("produto_id")["quantidade"].sum().reset_index()
        nomes = pd.read_sql(f"SELECT id, nome FROM produtos WHERE empresa_id = {empresa_id}", conn)
        ranking = ranking.merge(nomes, left_on="produto_id", right_on="id")

        fig2 = px.bar(ranking, x="nome", y="quantidade", title="Produtos mais consumidos")
        st.plotly_chart(fig2, use_container_width=True)

    # consumo por departamento
    dep_rank = pd.read_sql(f"""
        SELECT d.nome, SUM(m.quantidade) as total
        FROM movimentacoes m
        JOIN departamentos d ON d.id = m.departamento_id
        WHERE m.empresa_id = {empresa_id}
        GROUP BY d.nome
        ORDER BY total DESC
    """, conn)

    if not dep_rank.empty:
        fig_dep = px.bar(dep_rank, x="nome", y="total", title="Consumo por Departamento")
        st.plotly_chart(fig_dep, use_container_width=True)

# ================= PRODUTOS =================
elif menu == "Produtos":

    if nivel == "operador":
        st.warning("Operador não pode cadastrar produtos")
        st.stop()

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

    df = pd.read_sql(f"SELECT * FROM produtos WHERE empresa_id = {empresa_id}", conn)
    st.dataframe(df)

# ================= MOVIMENTAÇÃO =================
elif menu == "Movimentação":

    tipo = st.radio("Tipo", ["Entrada", "Saída"])

    df = pd.read_sql(f"SELECT id, nome FROM produtos WHERE empresa_id = {empresa_id}", conn)
    produto = st.selectbox("Produto", df["nome"])
    qtd = st.number_input("Quantidade", min_value=1)

    deps = pd.read_sql(f"SELECT id, nome FROM departamentos WHERE empresa_id = {empresa_id}", conn)
    dep_nome = st.selectbox("Departamento", deps["nome"])
    dep_id = deps[deps["nome"] == dep_nome]["id"].values[0]

    if st.button("Movimentar"):

        cur.execute("SELECT id FROM produtos WHERE nome=%s", (produto,))
        produto_id = cur.fetchone()[0]

        if tipo == "Saída":
            cur.execute("SELECT quantidade FROM produtos WHERE id=%s", (produto_id,))
            atual = cur.fetchone()[0]

            if qtd > atual:
                st.error("❌ Estoque insuficiente!")
                st.stop()

        cur.execute("""
            INSERT INTO movimentacoes 
            (produto_id, tipo, quantidade, empresa_id, usuario_id, departamento_id)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (produto_id, tipo, qtd, empresa_id, st.session_state.usuario_id, dep_id))

        if tipo == "Entrada":
            cur.execute("UPDATE produtos SET quantidade = quantidade + %s WHERE id=%s", (qtd, produto_id))
        else:
            cur.execute("UPDATE produtos SET quantidade = quantidade - %s WHERE id=%s", (qtd, produto_id))

        conn.commit()
        st.success("Movimentado!")
        st.rerun()

# ================= DEPARTAMENTOS =================
elif menu == "Departamentos":

    st.subheader("Cadastro de Departamentos")

    nome = st.text_input("Nome")

    if st.button("Salvar"):
        cur.execute("""
            INSERT INTO departamentos (nome, empresa_id)
            VALUES (%s,%s)
        """, (nome, empresa_id))
        conn.commit()
        st.success("Salvo!")

    df = pd.read_sql(f"SELECT * FROM departamentos WHERE empresa_id = {empresa_id}", conn)
    st.dataframe(df)

# ================= FORNECEDORES =================
elif menu == "Fornecedores":

    st.subheader("Cadastro de Fornecedores")

    nome = st.text_input("Nome")
    tel = st.text_input("Telefone")
    end = st.text_input("Endereço")
    doc = st.text_input("CNPJ/CPF")

    if st.button("Salvar"):
        cur.execute("""
            INSERT INTO fornecedores (nome, telefone, endereco, documento, empresa_id)
            VALUES (%s,%s,%s,%s,%s)
        """, (nome, tel, end, doc, empresa_id))
        conn.commit()
        st.success("Salvo!")

    df = pd.read_sql(f"SELECT * FROM fornecedores WHERE empresa_id = {empresa_id}", conn)
    st.dataframe(df)

# ================= USUÁRIOS =================
elif menu == "Usuários":

    if nivel != "admin":
        st.warning("Apenas admin pode acessar")
        st.stop()

    st.subheader("Criar Usuário")

    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    nivel = st.selectbox("Nível", ["admin", "operador"])

    if st.button("Criar"):
        criar_usuario(user, senha, nivel, empresa_id)
        st.success("Usuário criado!")

# ================= RELATÓRIOS =================
elif menu == "Relatórios":

    st.subheader("📊 Relatórios PRO")

    df = pd.read_sql(f"""
        SELECT m.*, p.nome as produto, d.nome as departamento
        FROM movimentacoes m
        JOIN produtos p ON p.id = m.produto_id
        LEFT JOIN departamentos d ON d.id = m.departamento_id
        WHERE m.empresa_id = {empresa_id}
        ORDER BY data DESC
    """, conn)

    busca = st.text_input("Buscar produto")
    if busca:
        df = df[df["produto"].str.contains(busca, case=False)]

    data_ini = st.date_input("Data inicial")
    data_fim = st.date_input("Data final")

    if data_ini and data_fim:
        df = df[(df["data"] >= str(data_ini)) & (df["data"] <= str(data_fim))]

    st.dataframe(df)

    st.download_button("⬇️ CSV", df.to_csv(index=False), "relatorio.csv")

    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    st.download_button("⬇️ Excel", buffer.getvalue(), "relatorio.xlsx")

    def gerar_pdf(df):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        data = [df.columns.tolist()] + df.values.tolist()
        table = Table(data)
        doc.build([table])
        buffer.seek(0)
        return buffer

    pdf = gerar_pdf(df)

    st.download_button(
        "📄 Exportar PDF",
        pdf,
        file_name="relatorio.pdf",
        mime="application/pdf"
    )