import streamlit as st
import pandas as pd
import plotly.express as px
from utils.alerts import estoque_baixo

def render(conn, empresa_id):

    df = pd.read_sql(f"SELECT * FROM produtos WHERE empresa_id = {empresa_id}", conn)
    mov = pd.read_sql(f"SELECT * FROM movimentacoes WHERE empresa_id = {empresa_id}", conn)

    st.markdown('<div class="section-title">🚀 Dashboard PRO ULTRA</div>', unsafe_allow_html=True)

    total_prod = len(df)
    estoque_total = int(df["quantidade"].sum()) if not df.empty else 0

    entradas = mov[mov["tipo"] == "Entrada"]["quantidade"].sum() if not mov.empty else 0
    saidas = mov[mov["tipo"] == "Saída"]["quantidade"].sum() if not mov.empty else 0

    c1, c2, c3, c4 = st.columns(4)

    c1.markdown(f'<div class="metric-card"><div class="metric-title">Produtos</div><div class="metric-value">{total_prod}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-title">Estoque</div><div class="metric-value">{estoque_total}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-title">Entradas</div><div class="metric-value">{entradas}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-title">Saídas</div><div class="metric-value">{saidas}</div></div>', unsafe_allow_html=True)

    st.markdown("## 📦 Estoque por Produto")

    if not df.empty:
        fig = px.bar(
            df,
            x="nome",
            y="quantidade",
            color="quantidade",
            color_continuous_scale="blues"
        )

        fig.update_layout(
            plot_bgcolor="#0f172a",
            paper_bgcolor="#0f172a",
            font_color="white"
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("## 🥧 Distribuição de Movimentações")

    if not mov.empty:
        pie = px.pie(
            mov,
            names="tipo",
            values="quantidade",
            hole=0.4
        )

        pie.update_layout(
            paper_bgcolor="#0f172a",
            font_color="white"
        )

        st.plotly_chart(pie, use_container_width=True)

    st.markdown("## 🏆 Top Produtos Consumidos")

    if not mov.empty:
        ranking = mov[mov["tipo"] == "Saída"] \
            .groupby("produto_id")["quantidade"] \
            .sum().reset_index()

        nomes = pd.read_sql(f"SELECT id, nome FROM produtos WHERE empresa_id = {empresa_id}", conn)
        ranking = ranking.merge(nomes, left_on="produto_id", right_on="id")

        ranking = ranking.sort_values("quantidade", ascending=False).head(5)

        fig_rank = px.bar(
            ranking,
            x="nome",
            y="quantidade",
            color="quantidade",
            color_continuous_scale="reds"
        )

        fig_rank.update_layout(
            paper_bgcolor="#0f172a",
            font_color="white"
        )

        st.plotly_chart(fig_rank, use_container_width=True)

    alertas = estoque_baixo(conn, empresa_id)

    if not alertas.empty:
        st.error("⚠️ Produtos com estoque baixo")
        st.dataframe(alertas)