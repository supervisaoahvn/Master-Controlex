import streamlit as st
from db import conectar
from auth import login
import pandas as pd

st.set_page_config(page_title="Inventário PRO", layout="wide")

# ================= LOGIN =================

if "logado" not in st.session_state:
st.session_state.logado = False

if not st.session_state.logado:
st.title("🔐 Login")

```
user = st.text_input("Usuário")
senha = st.text_input("Senha", type="password")

if st.button("Entrar"):
    if login(user, senha):
        st.session_state.logado = True
        st.rerun()
    else:
        st.error("Login inválido")

st.stop()
```

# ================= APP =================

st.title("📦 Sistema de Inventário PRO")

menu = st.sidebar.radio(
"📂 Menu",
[
"📊 Dashboard",
"📦 Produtos",
"🔄 Movimentação",
"📜 Histórico",
"🏢 Departamentos",
"🚚 Fornecedores",
"👤 Funcionários"
]
)

conn = conectar()
cur = conn.cursor()

# ================= DASHBOARD =================

if menu == "📊 Dashboard":

```
df = pd.read_sql("SELECT * FROM produtos", conn)

st.subheader("📊 Visão Geral")

col1, col2 = st.columns(2)

col1.metric("📦 Total itens", int(df["quantidade"].sum()))

if "preco_custo" in df.columns:
    valor = (df["quantidade"] * df["preco_custo"]).sum()
    col2.metric("💰 Valor estoque", f"R$ {valor:.2f}")

st.divider()
st.dataframe(df, use_container_width=True)
```

# ================= PRODUTOS =================

elif menu == "📦 Produtos":

```
col1, col2 = st.columns([1,2])

with col1:
    st.subheader("➕ Novo Produto")

    nome = st.text_input("Nome")
    sku = st.text_input("SKU")
    qtd = st.number_input("Quantidade", min_value=0)

    forn_df = pd.read_sql("SELECT id, nome FROM fornecedores", conn)
    fornecedor = st.selectbox("Fornecedor", forn_df["nome"])

    if st.button("Salvar produto"):

        # evitar duplicado
        cur.execute("SELECT id FROM produtos WHERE sku=%s", (sku,))
        if cur.fetchone():
            st.error("SKU já existe!")
            st.stop()

        cur.execute("SELECT id FROM fornecedores WHERE nome=%s", (fornecedor,))
        fornecedor_id = cur.fetchone()[0]

        cur.execute(
            "INSERT INTO produtos (nome, sku, quantidade, fornecedor_id) VALUES (%s,%s,%s,%s)",
            (nome, sku, qtd, fornecedor_id)
        )
        conn.commit()

        st.success("Produto cadastrado!")
        st.rerun()

with col2:
    st.subheader("📦 Lista de Produtos")

    busca = st.text_input("🔍 Buscar produto")

    query = "SELECT * FROM produtos"
    if busca:
        query += f" WHERE nome ILIKE '%{busca}%'"
    query += " ORDER BY nome"

    df = pd.read_sql(query, conn)
    st.dataframe(df, use_container_width=True)
```

# ================= MOVIMENTAÇÃO =================

elif menu == "🔄 Movimentação":

```
tipo = st.radio("Tipo", ["Entrada", "Saída"])

prod_df = pd.read_sql("SELECT id, nome, quantidade FROM produtos ORDER BY nome", conn)
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

    # produto
    cur.execute("SELECT id, quantidade FROM produtos WHERE nome=%s", (produto,))
    res = cur.fetchone()

    if not res:
        st.error("Produto não encontrado")
        st.stop()

    produto_id, estoque_atual = res

    # entrada
    if tipo == "Entrada":
        cur.execute("SELECT id FROM fornecedores WHERE nome=%s", (fornecedor,))
        fornecedor_id = cur.fetchone()[0]

    # saída
    else:
        if qtd > estoque_atual:
            st.error("Estoque insuficiente!")
            st.stop()

        cur.execute("SELECT id FROM departamentos WHERE nome=%s", (departamento,))
        departamento_id = cur.fetchone()[0]

        cur.execute("SELECT id FROM funcionarios WHERE nome=%s", (funcionario,))
        funcionario_id = cur.fetchone()[0]

    # salvar movimentação
    cur.execute("""
        INSERT INTO movimentacoes 
        (produto_id, tipo, quantidade, fornecedor_id, departamento_id, funcionario_id)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (produto_id, tipo, qtd, fornecedor_id, departamento_id, funcionario_id))

    # atualizar estoque
    if tipo == "Entrada":
        cur.execute("UPDATE produtos SET quantidade = quantidade + %s WHERE id=%s",
                    (qtd, produto_id))
    else:
        cur.execute("UPDATE produtos SET quantidade = quantidade - %s WHERE id=%s",
                    (qtd, produto_id))

    conn.commit()
    st.success("Movimentação registrada!")
    st.rerun()
```

# ================= HISTÓRICO =================

elif menu == "📜 Histórico":

```
st.subheader("📜 Histórico de Movimentações")

df = pd.read_sql("""
    SELECT 
        m.id,
        p.nome AS produto,
        m.tipo,
        m.quantidade,
        f.nome AS fornecedor,
        d.nome AS departamento,
        fu.nome AS funcionario,
        m.data
    FROM movimentacoes m
    LEFT JOIN produtos p ON m.produto_id = p.id
    LEFT JOIN fornecedores f ON m.fornecedor_id = f.id
    LEFT JOIN departamentos d ON m.departamento_id = d.id
    LEFT JOIN funcionarios fu ON m.funcionario_id = fu.id
    ORDER BY m.data DESC
""", conn)

st.dataframe(df, use_container_width=True)
```

# ================= DEPARTAMENTOS =================

elif menu == "🏢 Departamentos":

```
st.subheader("Cadastrar Departamento")

nome = st.text_input("Nome do departamento")

if st.button("Salvar departamento"):
    cur.execute("INSERT INTO departamentos (nome) VALUES (%s)", (nome,))
    conn.commit()
    st.success("Departamento cadastrado!")
    st.rerun()

df = pd.read_sql("SELECT * FROM departamentos", conn)
st.dataframe(df)
```

# ================= FORNECEDORES =================

elif menu == "🚚 Fornecedores":

```
st.subheader("Cadastrar Fornecedor")

nome = st.text_input("Nome do fornecedor")

if st.button("Salvar fornecedor"):
    cur.execute("INSERT INTO fornecedores (nome) VALUES (%s)", (nome,))
    conn.commit()
    st.success("Fornecedor cadastrado!")
    st.rerun()

df = pd.read_sql("SELECT * FROM fornecedores", conn)
st.dataframe(df)
```

# ================= FUNCIONÁRIOS =================

elif menu == "👤 Funcionários":

```
st.subheader("Cadastrar Funcionário")

nome = st.text_input("Nome")

dep_df = pd.read_sql("SELECT id, nome FROM departamentos", conn)
departamento = st.selectbox("Departamento", dep_df["nome"])

if st.button("Salvar funcionário"):

    cur.execute("SELECT id FROM departamentos WHERE nome=%s", (departamento,))
    departamento_id = cur.fetchone()[0]

    cur.execute(
        "INSERT INTO funcionarios (nome, departamento_id) VALUES (%s,%s)",
        (nome, departamento_id)
    )

    conn.commit()
    st.success("Funcionário cadastrado!")
    st.rerun()

df = pd.read_sql("SELECT * FROM funcionarios", conn)
st.dataframe(df)
```
