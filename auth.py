from db import conectar
import bcrypt

def criar_usuario(username, senha, empresa_id):
    conn = conectar()
    cur = conn.cursor()

    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

    cur.execute("""
        INSERT INTO usuarios (username, senha, empresa_id)
        VALUES (%s, %s, %s)
    """, (username, senha_hash, empresa_id))

    conn.commit()


def login(username, senha):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, senha, empresa_id
        FROM usuarios
        WHERE username=%s
    """, (username,))

    user = cur.fetchone()

    if user:
        senha_hash = user[1].encode()

        if bcrypt.checkpw(senha.encode(), senha_hash):
            return {
                "user_id": user[0],
                "empresa_id": user[2]
            }

    return None