import streamlit as st
import sqlite3
import hashlib

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Dragon-Hot — Acesso ao Sistema",
    page_icon="imagens/logo_dragon.png.png",
    layout="centered"
)

def verificar_credenciais(email, senha):
    """Verifica no banco SQLite se o usuário existe e se a senha confere (RNF05)."""
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    
    # Gera o hash SHA-256 da senha digitada para comparar com o banco
    senha_hash = hashlib.sha256(senha.encode('utf-8')).hexdigest()
    
    cursor.execute("""
        SELECT nome, perfil FROM usuarios 
        WHERE email = ? AND senha_hash = ?
    """, (email, senha_hash))
    
    usuario = cursor.fetchone()
    conn.close()
    return usuario

# Gerenciamento de sessão
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

# Se não estiver logado, exibe a Tela de Login (RF1.1)
if st.session_state.usuario_logado is None:
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.image("imagens/logo_dragon.png.png", use_container_width=True)

    st.markdown("<h3 style='text-align: center; color: gray;'>Acesso ao Sistema Interno</h3>", unsafe_allow_html=True)
    
    # Caixa de login simulando o card do wireframe
    with st.form("form_login"):
        email_input = st.text_input("E-mail ou Usuário")
        senha_input = st.text_input("Senha", type="password")
        st.write("")
        
        botao_entrar = st.form_submit_button("Entrar", use_container_width=True)
        
        if botao_entrar:
            if email_input and senha_input:
                user_data = verificar_credenciais(email_input, senha_input)
                if user_data:
                    st.session_state.usuario_logado = {
                        "nome": user_data[0],
                        "perfil": user_data[1]
                    }
                    st.success(f"Bem-vindo, {user_data[0]}! Redirecionando...")
                    st.rerun()
                else:
                    st.error("E-mail ou senha incorretos.")
            else:
                st.warning("Por favor, preencha todos os campos.")

    # Dica com os logins padrão criados no database.py
    with st.expander("ℹ️ Credenciais para Teste"):
        st.write("**Gerente:** `gerente@dragonhot.com` | Senha: `admin123`")
        st.write("**Chapa:** `chapa@dragonhot.com` | Senha: `chapa123`")

else:
    # Redirecionamento Automático por Perfil (RF1.2)
    perfil = st.session_state.usuario_logado["perfil"]
    nome = st.session_state.usuario_logado["nome"]
    
    st.sidebar.title(f"Olá, {nome}")
    st.sidebar.caption(f"Perfil: {perfil}")
    
    if st.sidebar.button("Sair da Conta", use_container_width=True):
        st.session_state.usuario_logado = None
        st.rerun()
        
    if perfil == "Gerente":
        st.title("📊 Dashboard Gerencial (Tela 4.1)")
        st.success("Você acessou com o perfil de Gerente!")
        st.write("Aqui ficarão os KPIs, gráficos e menus de gestão do cardápio, bairros e colaboradores.")
        
    elif perfil == "Chapa":
        st.title("🍳 Fila de Pedidos da Cozinha (Tela 3.1)")
        st.success("Você acessou com o perfil da Chapa!")
        st.write("Aqui ficará o quadro Kanban da fila de preparo e o controle de estoque.")