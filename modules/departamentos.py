import streamlit as st
import pandas as pd

def render(conn, cur, empresa_id):

    st.subheader("🏢 Departamentos")

    nome = st.text_input("Nome do departamento")

    if st.button("Salvar"):
        cur.execute("""
            INSERT INTO departamentos (nome, empresa_id)
            VALUES (%s,%s)
        """, (nome, empresa_id))
        conn.commit()
        st.success("Departamento criado")

    df = pd.read_sql(f"""
        SELECT * FROM departamentos WHERE empresa_id={empresa_id}
    """, conn)

    st.dataframe(df)