def pode(nivel, acao):
    regras = {
        "dono": ["tudo"],
        "admin": ["criar", "editar"],
        "operador": ["movimentar"]
    }

    return "tudo" in regras.get(nivel, []) or acao in regras.get(nivel, [])