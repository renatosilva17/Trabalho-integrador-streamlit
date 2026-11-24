import sqlite3
import hashlib

def gerar_hash_senha(senha):
    """Aplica o algoritmo SHA-256 para cumprir o requisito de segurança (RNF05)."""
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

def init_db():
    """Inicializa o banco de dados SQLite e cria as tabelas essenciais."""
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    
    # Tabela de Usuários / Colaboradores (Atende ao RF1.1, RF7.1 e RNF05)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            perfil TEXT NOT NULL
        )
    """)

if __name__ == "__main__":
    init_db()