from db import conectar

def login(username, senha):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, empresa_id 
        FROM usuarios 
        WHERE username=%s AND senha=%s
    """, (username, senha))

    user = cur.fetchone()

    if user:
        return {
            "user_id": user[0],
            "empresa_id": user[1]
        }

    return None
