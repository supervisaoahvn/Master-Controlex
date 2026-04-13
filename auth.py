from db import conectar

def login(user, senha):
    conn = conectar()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM usuarios WHERE username=%s AND senha=%s",
        (user, senha)
    )

    return cur.fetchone()
