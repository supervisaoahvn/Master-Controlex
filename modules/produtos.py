import streamlit as st
import pandas as pd

def render(conn, cur, empresa_id):

    st.subheader("Produtos")

    nome = st.text_input("Nome")
    sku = st.text_input("SKU")
    qtd = st.number_input("Quantidade", min_value=0)

    if st.button("Salvar"):
        cur.execute("""
            INSERT INTO produtos (nome, sku, quantidade, empresa_id)
            VALUES (%s,%s,%s,%s)
        """, (nome, sku, qtd, empresa_id))
        conn.commit()
        st.success("Salvo")

    df = pd.read_sql(f"SELECT * FROM produtos WHERE empresa_id={empresa_id}", conn)
    st.dataframe(df)