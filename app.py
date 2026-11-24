import streamlit as st
import sqlite3
import hashlib
import pillow_avif
from PIL import Image

# 1. Inicializa o estado da sessão
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

# 2. Recupera o login caso a página seja recarregada (F5)
if st.session_state.usuario_logado is None and "user" in st.query_params:
    email_salvo = st.query_params["user"]
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nome, perfil FROM usuarios WHERE email = ?", (email_salvo,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        st.session_state.usuario_logado = {
            "nome": user_data[0],
            "perfil": user_data[1]
        }

# 3. Configuração da página (deve vir antes de qualquer elemento visual)
layout_atual = "centered" if st.session_state.usuario_logado is None else "wide"

st.set_page_config(
    page_title="Dragon-Hot — Acesso ao Sistema",
    page_icon="imagens/logo_dragon.png.png",
    layout=layout_atual
)

# --- FUNÇÕES DE BANCO DE DADOS ---
def verificar_credenciais(email, senha):
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    senha_hash = hashlib.sha256(senha.encode('utf-8')).hexdigest()
    
    cursor.execute("""
        SELECT nome, perfil FROM usuarios 
        WHERE email = ? AND senha_hash = ?
    """, (email, senha_hash))
    
    usuario = cursor.fetchone()
    conn.close()
    return usuario

def buscar_pedidos_por_status(status):
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, numero_pedido, cliente, horario, tipo_entrega, itens, observacoes 
        FROM pedidos WHERE status = ?
    """, (status,))
    pedidos = cursor.fetchall()
    conn.close()
    return pedidos

def atualizar_status_pedido(pedido_id, novo_status):
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    conn.commit()
    conn.close()

def garantir_pedidos_teste():
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
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
cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status IN ('RECEBIDO', 'EM_PREPARO', 'PRONTO')")
    if cursor.fetchone()[0] == 0:
        pedidos_exemplo = [
            ("#103", "Lucas Araujo", "14:05", "Delivery", "1x Dog Duplo Prensado\n**SEM PURÊ DE BATATA**\n+ Extras: Cheddar", "Obs: Bem prensado", "RECEBIDO"),
            ("#105", "Luisa Prado", "15:20", "Delivery", "2x Dog Tradicional\n+ Extras: Bacon", "", "EM_PREPARO"),
            ("#102", "Luisa Prado", "15:20", "Delivery", "1x Dog Frango Catupiry", "", "PRONTO")
        ]
        cursor.executemany("""
            INSERT INTO pedidos (numero_pedido, cliente, horario, tipo_entrega, itens, observacoes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, pedidos_exemplo)
        conn.commit()
    conn.close()

garantir_pedidos_teste()

# --- TELA DE LOGIN ---
if st.session_state.usuario_logado is None:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        imagem = Image.open("imagens/logo_dragon.png.avif")
        st.image(imagem, use_container_width=True)

    st.markdown("<h3 style='text-align: center; color: gray;'>Acesso ao Sistema Interno</h3>", unsafe_allow_html=True)

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
                    st.query_params["user"] = email_input  
                    st.success(f"Bem-vindo, {user_data[0]}! Redirecionando...")
                    st.rerun()
                else:
                    st.error("E-mail ou senha incorretos.")
            else:
                st.warning("Por favor, preencha todos os campos.")

    with st.expander("ℹ️ Credenciais para Teste"):
        st.write("**Gerente:** `gerente@dragonhot.com` | Senha: `admin123`")
        st.write("**Chapa:** `chapa@dragonhot.com` | Senha: `chapa123`")

# --- ÁREA LOGADA ---
else:
    perfil = st.session_state.usuario_logado["perfil"]
    nome = st.session_state.usuario_logado["nome"]

    # Cabeçalho da Sidebar
    imagem_sidebar = Image.open("imagens/logo_dragon.png.avif")
    col_esq, col_centro, col_dir = st.sidebar.columns([1, 2, 1])
    with col_centro:
        st.image(imagem_sidebar, use_container_width=True)

    st.sidebar.title(f"Olá, {nome}")
    st.sidebar.caption(f"Perfil: **{perfil}**")
    st.sidebar.divider()

    # ==========================================
    # PERFIL: GERENTE
    # ==========================================
    if perfil == "Gerente":
        if st.sidebar.button("Sair da Conta", use_container_width=True):
            st.session_state.usuario_logado = None
            st.query_params.clear() 
            st.rerun()

        st.title("Dashboard Gerencial")
        st.success("Você acessou com o perfil de Gerente!")
        st.write("Aqui ficarão os KPIs, gráficos e menus de gestão do cardápio, bairros e colaboradores.")

    # ==========================================
    # PERFIL: CHAPA
    # ==========================================
    elif perfil == "Chapa":
        if "pagina_chapa" not in st.session_state:
            st.session_state.pagina_chapa = "Fila de Pedidos"

        with st.sidebar:
            if st.button("Fila de Pedidos", type="primary" if st.session_state.pagina_chapa == "Fila de Pedidos" else "secondary", use_container_width=True):
                st.session_state.pagina_chapa = "Fila de Pedidos"
                st.rerun()
                
            if st.button("Controle de Estoque", type="primary" if st.session_state.pagina_chapa == "Controle de Estoque" else "secondary", use_container_width=True):
                st.session_state.pagina_chapa = "Controle de Estoque"
                st.rerun()
                
            if st.button("Cadastrar insumo", type="primary" if st.session_state.pagina_chapa == "Cadastrar insumo" else "secondary", use_container_width=True):
                st.session_state.pagina_chapa = "Cadastrar insumo"
                st.rerun()

            st.divider()
            if st.button("Sair da Conta", use_container_width=True):
                st.session_state.usuario_logado = None
                st.query_params.clear()  
                st.rerun()

        if st.session_state.pagina_chapa == "Fila de Pedidos":
            with st.container(border=True):
                st.subheader("Fila de Pedidos da Cozinha e Expedição")
                st.caption("Clique nos botões para avançar etapas ou cancelar (estorno)")

            recebidos = buscar_pedidos_por_status("RECEBIDO")
            em_preparo = buscar_pedidos_por_status("EM_PREPARO")
            prontos = buscar_pedidos_por_status("PRONTO")

            if not recebidos and not em_preparo and not prontos:
                st.markdown("**RECEBIDOS, PREPARO, ENTREGA**")
                with st.container(border=True):
                    st.info("Nenhum pedido aguardando.\n\nChapa livre.\n\nNenhum pedido aguardando retirada.")
            
            else:
                st.markdown("**RECEBIDOS (AGUARDANDO ACEITE)**")
                with st.container(border=True):
                    if not recebidos:
                        st.write("Nenhum pedido aguardando.")
                    else:
                        for ped in recebidos:
                            p_id, num, cliente, hora, tipo, itens, obs = ped
                            with st.container(border=True):
                                col_info, col_tag = st.columns([4, 1])
                                col_info.markdown(f"#### {num}")
                                col_tag.button(tipo, key=f"tag_{p_id}", disabled=True, use_container_width=True)
                                st.caption(f"{cliente} • {hora}")
                                st.divider()
                                
                                with st.container(border=True):
                                    st.markdown(itens.replace("\n", "  \n"))
                                    if obs:
                                        st.caption(obs)
                                
                                if st.button("ACEITAR PEDIDO", key=f"aceitar_{p_id}", type="primary", use_container_width=True):
                                    atualizar_status_pedido(p_id, "EM_PREPARO")
                                    st.rerun()
                                    
                                if st.button("CANCELAR (ESTORNAR ESTOQUE)", key=f"cancelar_{p_id}", use_container_width=True):
                                    atualizar_status_pedido(p_id, "CANCELADO")
                                    st.rerun()

                st.markdown("**EM PREPARO (CHAPA)**")
                with st.container(border=True):
                    if not em_preparo:
                        st.write("Chapa livre.")
                    else:
                        for ped in em_preparo:
                            p_id, num, cliente, hora, tipo, itens, obs = ped
                            with st.container(border=True):
                                col_info, col_tag = st.columns([4, 1])
                                col_info.markdown(f"#### {num}")
                                col_tag.button(tipo, key=f"tag_{p_id}", disabled=True, use_container_width=True)
                                st.caption(f"{cliente} • {hora}")
                                st.divider()
                                
                                with st.container(border=True):
                                    st.markdown(itens.replace("\n", "  \n"))
                                    if obs:
                                        st.caption(obs)
                                
                                if st.button("CONCLUIR PREPARO", key=f"concluir_{p_id}", type="primary", use_container_width=True):
                                    atualizar_status_pedido(p_id, "PRONTO")
                                    st.rerun()

                st.markdown("**PRONTO / EM ENTREGA**")
                with st.container(border=True):
                    if not prontos:
                        st.write("Nenhum pedido aguardando retirada.")
                    else:
                        for ped in prontos:
                            p_id, num, cliente, hora, tipo, itens, obs = ped
                            with st.container(border=True):
                                col_info, col_tag = st.columns([4, 1])
                                col_info.markdown(f"#### {num}")
                                col_tag.button(tipo, key=f"tag_{p_id}", disabled=True, use_container_width=True)
                                st.caption(f"{cliente} • {hora}")
                                st.divider()
                                
                                with st.container(border=True):
                                    st.markdown(itens.replace("\n", "  \n"))
                                    if obs:
                                        st.caption(obs)
                                
                                if st.button("CONFIRMAR RETIRADA", key=f"retirar_{p_id}", type="primary", use_container_width=True):
                                    atualizar_status_pedido(p_id, "FINALIZADO")
                                    st.rerun()

        elif st.session_state.pagina_chapa == "Controle de Estoque":
            st.subheader("Controle de Estoque")
            st.info("Tela em construção.")

        elif st.session_state.pagina_chapa == "Cadastrar insumo":
            st.subheader("Cadastrar Insumo")
            st.info("Tela em construção.")