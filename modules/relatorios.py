import streamlit as st
import pandas as pd
import io
from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib.pagesizes import letter

def render(conn, empresa_id):

    st.subheader("📊 Relatórios")

    df = pd.read_sql(f"""
        SELECT m.*, p.nome as produto, d.nome as departamento
        FROM movimentacoes m
        JOIN produtos p ON p.id = m.produto_id
        LEFT JOIN departamentos d ON d.id = m.departamento_id
        WHERE m.empresa_id={empresa_id}
        ORDER BY data DESC
    """, conn)

    busca = st.text_input("Buscar produto")

    if busca:
        df = df[df["produto"].str.contains(busca, case=False)]

    st.dataframe(df)

    st.download_button("⬇️ CSV", df.to_csv(index=False), "relatorio.csv")

    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    st.download_button("⬇️ Excel", buffer.getvalue(), "relatorio.xlsx")

    def gerar_pdf(df):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        data = [df.columns.tolist()] + df.values.tolist()
        table = Table(data)
        doc.build([table])
        buffer.seek(0)
        return buffer

    st.download_button(
        "📄 PDF",
        gerar_pdf(df),
        file_name="relatorio.pdf"
    )