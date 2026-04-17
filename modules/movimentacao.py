import streamlit as st
import pandas as pd

def render(conn, cur, empresa_id, user_id):

    tipo = st.radio("Tipo", ["Entrada", "Saída"])

    df = pd.read_sql(f"SELECT id, nome FROM produtos WHERE empresa_id={empresa_id}", conn)
    produto = st.selectbox("Produto", df["nome"])

    qtd = st.number_input("Quantidade", min_value=1)

    if st.button("Movimentar"):

        cur.execute("SELECT id FROM produtos WHERE nome=%s", (produto,))
        produto_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO movimentacoes (produto_id, tipo, quantidade, empresa_id, usuario_id)
            VALUES (%s,%s,%s,%s,%s)
        """, (produto_id, tipo, qtd, empresa_id, user_id))

        if tipo == "Entrada":
            cur.execute("UPDATE produtos SET quantidade = quantidade + %s WHERE id=%s", (qtd, produto_id))
        else:
            cur.execute("UPDATE produtos SET quantidade = quantidade - %s WHERE id=%s", (qtd, produto_id))

        conn.commit()
        st.success("OK")