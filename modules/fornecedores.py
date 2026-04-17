import streamlit as st
import pandas as pd

def render(conn, cur, empresa_id):

    st.subheader("🚚 Fornecedores")

    nome = st.text_input("Nome")
    telefone = st.text_input("Telefone")
    endereco = st.text_input("Endereço")
    documento = st.text_input("CNPJ/CPF")

    if st.button("Salvar"):
        cur.execute("""
            INSERT INTO fornecedores 
            (nome, telefone, endereco, documento, empresa_id)
            VALUES (%s,%s,%s,%s,%s)
        """, (nome, telefone, endereco, documento, empresa_id))
        conn.commit()
        st.success("Fornecedor salvo")

    df = pd.read_sql(f"""
        SELECT * FROM fornecedores WHERE empresa_id={empresa_id}
    """, conn)

    st.dataframe(df)