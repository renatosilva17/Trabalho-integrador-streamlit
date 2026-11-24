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

    # >>> NOVO: Tabela de Pedidos para a Fila da Cozinha <<<
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_pedido TEXT NOT NULL,
            cliente TEXT NOT NULL,
            horario TEXT NOT NULL,
            tipo_entrega TEXT NOT NULL,
            itens TEXT NOT NULL,
            observacoes TEXT,
            status TEXT NOT NULL
        )
    """)
    
    # Inserir usuários padrão para teste (Gerente e Chapa) caso a tabela esteja vazia
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        senha_gerente = gerar_hash_senha("admin123")
        senha_chapa = gerar_hash_senha("chapa123")
        
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha_hash, perfil) 
            VALUES (?, ?, ?, ?)
        """, ("Carlos Gerente", "gerente@dragonhot.com", senha_gerente, "Gerente"))
        
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha_hash, perfil) 
            VALUES (?, ?, ?, ?)
        """, ("Roberto Chapa", "chapa@dragonhot.com", senha_chapa, "Chapa"))
        
        conn.commit()
        print("Banco de dados inicializado com usuários padrão!")

    conn.close()

if __name__ == "__main__":
    init_db()