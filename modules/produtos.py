import streamlit as st
import pandas as pd

def render(conn, cur, empresa_id):

    st.subheader("Produtos")

    nome = st.text_input("Nome")
    sku = st.text_input("SKU")
    qtd = st.number_input("Quantidade", min_value=0)
    baixo = df[df["quantidade"] <= df["estoque_minimo"]]

    if st.button("Salvar"):
        cur.execute("""
            INSERT INTO produtos (nome, sku, quantidade, empresa_id)
            VALUES (%s,%s,%s,%s)
        """, (nome, sku, qtd, empresa_id))
        conn.commit()
        st.success("Salvo")

    df = pd.read_sql(f"SELECT * FROM produtos WHERE empresa_id={empresa_id}", conn)

    for i, row in df.iterrows():
        col1, col2, col3, col4, col5, col6 = st.columns([1,3,2,2,2,1])

        col1.write(row["id"])
        col2.write(row["nome"])
        col3.write(row["sku"])
        col4.write(row["quantidade"])
        col5.write(row["preco_custo"])

        if col6.button("🗑️", key=f"del_{row['id']}"):
            if st.confirm(f"Excluir {row['nome']}?"):
                cur.execute("DELETE FROM produtos WHERE id = %s", (row["id"],))
                conn.commit()
                st.success("Produto excluído!")
                st.rerun()
        