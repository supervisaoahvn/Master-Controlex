import streamlit as st
import pandas as pd

def render(conn, cur, empresa_id):

    st.subheader("📋 Nova Ordem")

    # =====================
    # DEPARTAMENTO
    # =====================
    dept_df = pd.read_sql(
        f"SELECT id, nome FROM departamentos WHERE empresa_id={empresa_id}",
        conn
    )

    departamento_nome = st.selectbox("Departamento", dept_df["nome"])
    departamento_id = dept_df[dept_df["nome"] == departamento_nome]["id"].values[0]

    # =====================
    # PRODUTOS
    # =====================
    prod_df = pd.read_sql(
        f"SELECT id, nome FROM produtos WHERE empresa_id={empresa_id}",
        conn
    )

    produto_nome = st.selectbox("Produto", prod_df["nome"])
    produto_id = prod_df[prod_df["nome"] == produto_nome]["id"].values[0]

    quantidade = st.number_input("Quantidade", min_value=1)

    # =====================
    # CARRINHO (SESSION)
    # =====================
    if "itens" not in st.session_state:
        st.session_state.itens = []

    if st.button("➕ Adicionar"):
        st.session_state.itens.append({
            "produto_id": produto_id,
            "produto": produto_nome,
            "quantidade": quantidade
        })

    # =====================
    # LISTA
    # =====================
    if st.session_state.itens:
        st.subheader("Itens da Ordem")
        st.table(st.session_state.itens)

    # =====================
    # SALVAR ORDEM
    # =====================
    if st.button("💾 Finalizar Ordem"):

        # cria ordem
        cur.execute("""
            INSERT INTO ordens (departamento_id, empresa_id)
            VALUES (%s, %s) RETURNING id
        """, (departamento_id, empresa_id))

        ordem_id = cur.fetchone()[0]

        # salva itens
        for item in st.session_state.itens:
            cur.execute("""
                INSERT INTO ordem_itens (ordem_id, produto_id, quantidade)
                VALUES (%s,%s,%s)
            """, (ordem_id, item["produto_id"], item["quantidade"]))

            # atualiza estoque (saída automática)
            cur.execute("""
                UPDATE produtos
                SET quantidade = quantidade - %s
                WHERE id = %s
            """, (item["quantidade"], item["produto_id"]))

        conn.commit()

        st.success("Ordem criada com sucesso!")
        st.session_state.itens = []
        st.rerun()