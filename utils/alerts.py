import pandas as pd

def estoque_baixo(conn, empresa_id):
    df = pd.read_sql(f"""
        SELECT nome, quantidade, estoque_minimo
        FROM produtos
        WHERE empresa_id = {empresa_id}
    """, conn)

    if "estoque_minimo" not in df.columns:
        df["estoque_minimo"] = 5

    baixo = df[df["quantidade"] <= df["estoque_minimo"]]

    return baixo