import psycopg2
import os

def conectar():
    return psycopg2.connect(
        os.environ["DATABASE_URL"]
    )