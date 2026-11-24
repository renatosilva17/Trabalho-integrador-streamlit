import sqlite3
import hashlib

def gerar_hash_senha(senha):
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

def init_db():
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            perfil TEXT NOT NULL
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha_hash, perfil) 
            VALUES (?, ?, ?, ?)
        """, ("Carlos Gerente", "gerente@dragonhot.com", gerar_hash_senha("admin123"), "Gerente"))
        
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha_hash, perfil) 
            VALUES (?, ?, ?, ?)
        """, ("Roberto Chapa", "chapa@dragonhot.com", gerar_hash_senha("chapa123"), "Chapa"))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()