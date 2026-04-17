import bcrypt
from db import conectar

def criar_usuario(usuario, senha, empresa_id):
    conn = conectar()
    cur = conn.cursor()

    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

    cur.execute("""
        INSERT INTO usuarios (usuario, senha, empresa_id)
        VALUES (%s, %s, %s)
    """, (usuario, senha_hash, empresa_id))

    conn.commit()
    conn.close()


def login(usuario, senha):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, senha, empresa_id 
        FROM usuarios 
        WHERE usuario=%s
    """, (usuario,))

    user = cur.fetchone()
    conn.close()

    if user:
        user_id, senha_hash, empresa_id = user

        if bcrypt.checkpw(senha.encode(), senha_hash.encode()):
            return {
                "user_id": user_id,
                "empresa_id": empresa_id
            }

    return None