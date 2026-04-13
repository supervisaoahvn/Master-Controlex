import psycopg2
import streamlit as st

def conectar():
    return psycopg2.connect(st.secrets["DATABASE_URL"])
