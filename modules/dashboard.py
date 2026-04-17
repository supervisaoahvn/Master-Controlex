import streamlit as st
import pandas as pd
import plotly.express as px
from utils.alerts import estoque_baixo

def render(conn, empresa_id):

    df = pd.read_sql(f"SELECT * FROM produtos WHERE empresa_id={empresa_id}", conn)
    mov = pd.read_sql(f"SELECT * FROM movimentacoes WHERE empresa_id={empresa_id}", conn)

    st.title("🚀 Dashboard PRO")

    col1, col2 = st.columns(2)
    col1.metric("Produtos", len(df))
    col2.metric("Estoque", int(df["quantidade"].sum()))

    baixo = estoque_baixo(df)
    if not baixo.empty:
        st.error("⚠️ Estoque baixo detectado")

    fig = px.bar(df, x="nome", y="quantidade")
    st.plotly_chart(fig, use_container_width=True)