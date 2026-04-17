import psycopg2
import os

def conectar():
    return psycopg2.connect(
        os.getenv("DATABASE_URL"),
        sslmode="require"
    )