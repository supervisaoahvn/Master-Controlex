import streamlit as st
import pandas as pd

def render(conn, cur, empresa_id):

    st.subheader("📦 Solicitação de Estoque")

    produtos = pd.read_sql(f"""
        SELECT id, nome, quantidade, estoque_minimo
        FROM produtos WHERE empresa_id={empresa_id}
    """, conn)

    produto = st.selectbox("Produto", produtos["nome"])

    linha = produtos[produtos["nome"] == produto].iloc[0]

    sugestao = max(linha["estoque_minimo"] - linha["quantidade"], 0)

    st.info(f"Sugestão automática: {sugestao}")

    qtd = st.number_input("Quantidade", value=int(sugestao))

    if st.button("Solicitar"):
        cur.execute("""
            INSERT INTO solicitacoes (produto_id, quantidade, empresa_id)
            VALUES (%s,%s,%s)
        """, (linha["id"], qtd, empresa_id))
        conn.commit()
        st.success("Solicitação criada")

    st.markdown("---")

    hist = pd.read_sql(f"""
        SELECT s.*, p.nome
        FROM solicitacoes s
        JOIN produtos p ON p.id = s.produto_id
        WHERE s.empresa_id={empresa_id}
        ORDER BY data DESC
    """, conn)

    st.subheader("📜 Histórico de Solicitações")
    st.dataframe(hist)