import bcrypt
from db import conectar

def login(usuario, senha):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT id, senha, nivel, empresa_id FROM usuarios WHERE usuario=%s", (usuario,))
    user = cur.fetchone()

    if user and bcrypt.checkpw(senha.encode(), user[1].encode()):
        return {
            "id": user[0],
            "nivel": user[2],
            "empresa_id": user[3]
        }
    return None


def criar_usuario(usuario, senha, nivel, empresa_id):
    conn = conectar()
    cur = conn.cursor()

    hash_senha = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

    cur.execute("""
        INSERT INTO usuarios (usuario, senha, nivel, empresa_id)
        VALUES (%s,%s,%s,%s)
    """, (usuario, hash_senha, nivel, empresa_id))

    conn.commit()