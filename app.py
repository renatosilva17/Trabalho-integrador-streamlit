import streamlit as st
import sqlite3
import hashlib
import pillow_avif
from PIL import Image

# 1. Inicializa o estado da sessão
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

# ADICIONE ESTAS DUAS LINHAS AQUI EMBAIXO:
if "pagina_gerente" not in st.session_state:
    st.session_state.pagina_gerente = "Dashboard"

if "pagina_chapa" not in st.session_state:
    st.session_state.pagina_chapa = "Fila de Pedidos"

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
    page_icon="magens/logo_dragon.png.png",
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

def garantir_estoque_teste():
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS insumos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            quantidade_atual REAL NOT NULL,
            unidade TEXT NOT NULL,
            estoque_minimo REAL NOT NULL
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM insumos")
    if cursor.fetchone()[0] == 0:
        insumos_exemplo = [
            ("Pão de Hot Dog", 45, "UN", 20),
            ("Salsicha Tradicional", 15, "UN", 30),
            ("Purê de Batata", 800, "G", 1500),
            ("Molho Cheddar", 0, "ML", 1000),
            ("Batata Palha", 2500, "G", 1000)
        ]
        cursor.executemany("""
            INSERT INTO insumos (nome, quantidade_atual, unidade, estoque_minimo)
            VALUES (?, ?, ?, ?)
        """, insumos_exemplo)
        conn.commit()
    conn.close()

def buscar_insumos():
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, quantidade_atual, unidade, estoque_minimo FROM insumos ORDER BY nome ASC")
    itens = cursor.fetchall()
    conn.close()
    return itens

def registrar_entrada_estoque(insumo_id, qtd_adicionar):
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE insumos SET quantidade_atual = quantidade_atual + ? WHERE id = ?", (qtd_adicionar, insumo_id))
    conn.commit()
    conn.close()

garantir_estoque_teste()

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
        if "pagina_gerente" not in st.session_state:
            st.session_state.pagina_gerente = "Dashboard"

        with st.sidebar:
            if st.button("📊 Dashboard", type="primary" if st.session_state.pagina_gerente == "Dashboard" else "secondary", use_container_width=True, key="btn_gerente_dashboard"):
                st.session_state.pagina_gerente = "Dashboard"
                st.rerun()
                
            if st.button("🍔 Gestão de Cardápio", type="primary" if st.session_state.pagina_gerente == "Cardapio" else "secondary", use_container_width=True, key="btn_gerente_cardapio"):
                st.session_state.pagina_gerente = "Cardapio"
                st.rerun()
                
            if st.button("📍 Taxas de Bairros", type="primary" if st.session_state.pagina_gerente == "Bairros" else "secondary", use_container_width=True, key="btn_gerente_bairros"):
                st.session_state.pagina_gerente = "Bairros"
                st.rerun()

            if st.button("👥 Colaboradores", type="primary" if st.session_state.pagina_gerente == "Colaboradores" else "secondary", use_container_width=True, key="btn_gerente_colaboradores"):
                st.session_state.pagina_gerente = "Colaboradores"
                st.rerun()

            st.divider()
            if st.button("Sair da Conta", use_container_width=True, key="btn_gerente_sair"):
                st.session_state.usuario_logado = None
                st.query_params.clear() 
                st.rerun()

        # --- TELA: DASHBOARD GERENCIAL ---
            if st.session_state.pagina_gerente == "Dashboard":
                st.title("Dashboard Gerencial")
                st.caption("Visão geral do movimento e desempenho do Dragon-Hot")

            # Exemplo de KPIs (Cards superiores)
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(label="Faturamento Hoje", value="R$ 1.240,00", delta="+12%")
            with col2:
                st.metric(label="Total de Pedidos", value="38", delta="+5")
            with col3:
                st.metric(label="Ticket Médio", value="R$ 32,60", delta="-R$ 1,20")
            with col4:
                st.metric(label="Pedidos Cancelados", value="2", delta="-1", delta_color="inverse")

            st.divider()

            col_esq, col_dir = st.columns(2)
            
            with col_esq:
                with st.container(border=True):
                    st.subheader("📦 Pedidos por Status")
                    st.write("• **Recebidos:** 3")
                    st.write("• **Em Preparo:** 1")
                    st.write("• **Prontos/Entregues:** 34")
                    st.write("• **Cancelados:** 2")

            with col_dir:
                with st.container(border=True):
                    st.subheader("🔥 Lanches Mais Vendidos")
                    st.write("1. Dog Duplo Prensado (18 un)")
                    st.write("2. Dog Tradicional (12 un)")
                    st.write("3. Dog Frango Catupiry (8 un)")

        # --- TELA: CARDÁPIO ---
    elif st.session_state.pagina_gerente == "Cardapio":
            st.subheader("Gestão de Cardápio")
            st.info("Tela de cadastro e edição de lanches e bebidas em construção.")

        # --- TELA: BAIRROS ---
    elif st.session_state.pagina_gerente == "Bairros":
            st.subheader("Gestão de Bairros e Taxas de Entrega")
            st.info("Tela de taxas por bairro em construção.")

        # --- TELA: COLABORADORES ---
    elif st.session_state.pagina_gerente == "Colaboradores":
            st.subheader("Gestão de Colaboradores")
            st.info("Tela de cadastro de novos usuários e alteração de senhas em construção.")

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
            with st.container(border=True):
                # Cabeçalho e Filtro por Alerta no canto superior direito
                col_titulo, col_filtro = st.columns([3, 1])
                with col_titulo:
                    st.subheader("Controle e Reposição de Estoque")
                with col_filtro:
                    filtro_alerta = st.selectbox(
                        "Filtrar por alerta",
                        ["Todos", "OK", "ABAIXO DO MÍNIMO", "ESGOTADO"]
                    )

                # Caixa de Pesquisa
                with st.container(border=True):
                    busca = st.text_input("Pesquisar Insumo", placeholder="🔍 Digite o nome do ingrediente...")

                st.write("")

                # Cabeçalho da Tabela
                h1, h2, h3, h4, h5, h6 = st.columns([2.2, 1.3, 0.9, 1.3, 1.6, 2.5])
                h1.markdown("**Ingrediente**")
                h2.markdown("**Quantidade atual**")
                h3.markdown("**Unidade**")
                h4.markdown("**Estoque mínimo**")
                h5.markdown("**Alerta**")
                h6.markdown("**Reposição de Estoque**")
                st.divider()

                insumos = buscar_insumos()
                encontrou_algum = False

                for item in insumos:
                    i_id, nome_ing, qtd_atual, unidade, est_min = item

                    # Calcula status do alerta automaticamente
                    if qtd_atual <= 0:
                        status_alerta = "ESGOTADO"
                        cor_badge = "#FF4B4B"  # Vermelho
                    elif qtd_atual < est_min:
                        status_alerta = "ABAIXO DO MÍNIMO"
                        cor_badge = "#6C757D"  # Cinza escuro
                    else:
                        status_alerta = "OK"
                        cor_badge = "#A0A0A0"  # Cinza claro

                    # Aplica filtros de pesquisa e alerta
                    if busca and busca.lower() not in nome_ing.lower():
                        continue
                    if filtro_alerta != "Todos" and status_alerta != filtro_alerta:
                        continue

                    encontrou_algum = True

                    # Formata números inteiros sem ".0" quando aplicável
                    qtd_fmt = int(qtd_atual) if qtd_atual.is_integer() else qtd_atual
                    min_fmt = int(est_min) if est_min.is_integer() else est_min

                    # Linha do ingrediente
                    c1, c2, c3, c4, c5, c6 = st.columns([2.2, 1.3, 0.9, 1.3, 1.6, 2.5], vertical_alignment="center")
                    c1.write(f"**{nome_ing}**")
                    c2.write(f"{qtd_fmt}")
                    c3.write(unidade)
                    c4.write(f"{min_fmt}")

                    # Badge visual de Alerta
                    c5.markdown(
                        f"<div style='background-color: {cor_badge}; color: white; padding: 6px 10px; "
                        f"border-radius: 12px; text-align: center; font-size: 12px; font-weight: bold;'>"
                        f"{status_alerta}</div>",
                        unsafe_allow_html=True
                    )

                    # Campo numérico + Botão REGISTRAR ENTRADA
                    with c6:
                        col_input, col_btn = st.columns([1, 1.4], vertical_alignment="center")
                        qtd_entrada = col_input.number_input(
                            "Qtd",
                            min_value=0.0,
                            step=1.0,
                            key=f"input_est_{i_id}",
                            label_visibility="collapsed"
                        )
                        if col_btn.button("REGISTRAR ENTRADA", key=f"btn_est_{i_id}", use_container_width=True):
                            if qtd_entrada > 0:
                                registrar_entrada_estoque(i_id, qtd_entrada)
                                st.success(f"+{qtd_entrada:g} {unidade} em {nome_ing}")
                                st.rerun()
                            else:
                                st.warning("Informe > 0")

                    st.divider()

                if not encontrou_algum:
                    st.info("Nenhum insumo encontrado para os filtros selecionados.")

    elif st.session_state.pagina_chapa == "Cadastrar insumo":
            st.subheader("Cadastrar Insumo")
            st.info("Tela em construção.")