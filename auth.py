import bcrypt
from db import conectar

def hash_senha(senha):
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

def verificar_senha(senha, hash_db):
    return bcrypt.checkpw(senha.encode(), hash_db.encode())

def login(usuario, senha):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, senha, nivel, empresa_id 
        FROM usuarios WHERE usuario=%s
    """, (usuario,))

    user = cur.fetchone()

    if user:
        uid, senha_hash, nivel, empresa_id = user
        if verificar_senha(senha, senha_hash):
            return {"id": uid, "nivel": nivel, "empresa_id": empresa_id}

    return None

def criar_usuario(usuario, senha, nivel, empresa_id):
    conn = conectar()
    cur = conn.cursor()

    senha_hash = hash_senha(senha)

    cur.execute("""
        INSERT INTO usuarios (usuario, senha, nivel, empresa_id)
        VALUES (%s,%s,%s,%s)
    """, (usuario, senha_hash, nivel, empresa_id))

    conn.commit()