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

def cadastrar_novo_insumo(nome, unidade, qtd_inicial, estoque_minimo):
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM insumos WHERE LOWER(nome) = LOWER(?)", (nome.strip(),))
    if cursor.fetchone():
        conn.close()
        return False
    cursor.execute("""
        INSERT INTO insumos (nome, quantidade_atual, unidade, estoque_minimo)
        VALUES (?, ?, ?, ?)
    """, (nome.strip(), qtd_inicial, unidade, estoque_minimo))
    conn.commit()
    conn.close()
    return True

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

    # Exibe a logo específica de cada perfil na sidebar
    if perfil == "Gerente":
        imagem_sidebar = Image.open("imagens/dragao_gerente.avif")
    else:
        imagem_sidebar = Image.open("imagens/dragao_cozinha.avif")

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

        # Renderização das Telas do Gerente
        if st.session_state.pagina_gerente == "Dashboard":
            st.title("Dashboard Gerencial")
            st.caption("Visão geral do movimento e desempenho do Dragon-Hot")

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

        elif st.session_state.pagina_gerente == "Cardapio":
            st.subheader("Gestão de Cardápio")
            st.info("Tela de cadastro e edição de lanches e bebidas em construção.")

        elif st.session_state.pagina_gerente == "Bairros":
            st.subheader("Gestão de Bairros e Taxas de Entrega")
            st.info("Tela de taxas por bairro em construção.")

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
            if st.button("Fila de Pedidos", type="primary" if st.session_state.pagina_chapa == "Fila de Pedidos" else "secondary", use_container_width=True, key="btn_chapa_fila"):
                st.session_state.pagina_chapa = "Fila de Pedidos"
                st.rerun()
                
            if st.button("Controle de Estoque", type="primary" if st.session_state.pagina_chapa == "Controle de Estoque" else "secondary", use_container_width=True, key="btn_chapa_estoque"):
                st.session_state.pagina_chapa = "Controle de Estoque"
                st.rerun()
                
            if st.button("Cadastrar insumo", type="primary" if st.session_state.pagina_chapa == "Cadastrar insumo" else "secondary", use_container_width=True, key="btn_chapa_cad_insumo"):
                st.session_state.pagina_chapa = "Cadastrar insumo"
                st.rerun()

            st.divider()
            if st.button("Sair da Conta", use_container_width=True, key="btn_chapa_sair"):
                st.session_state.usuario_logado = None
                st.query_params.clear()  
                st.rerun()

        # ------------------------------------------
        # TELA 1: FILA DE PEDIDOS
        # ------------------------------------------
        if st.session_state.pagina_chapa == "Fila de Pedidos":
            with st.container(border=True):
                st.subheader("Fila de Pedidos da Cozinha e Expedição")
                st.caption("Clique nos botões para avançar etapas ou cancelar (estorno)")

            recebidos = buscar_pedidos_por_status("RECEBIDO")
            em_preparo = buscar_pedidos_por_status("EM_PREPARO")
            prontos = buscar_pedidos_por_status("PRONTO")

            if not recebidos and not em_preparo and not prontos:
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
                                col_tag.button(tipo, key=f"tag_rec_{p_id}", disabled=True, use_container_width=True)
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
                                col_tag.button(tipo, key=f"tag_prep_{p_id}", disabled=True, use_container_width=True)
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
                                col_tag.button(tipo, key=f"tag_pronto_{p_id}", disabled=True, use_container_width=True)
                                st.caption(f"{cliente} • {hora}")
                                st.divider()
                                
                                with st.container(border=True):
                                    st.markdown(itens.replace("\n", "  \n"))
                                    if obs:
                                        st.caption(obs)
                                
                                if st.button("CONFIRMAR RETIRADA", key=f"retirar_{p_id}", type="primary", use_container_width=True):
                                    atualizar_status_pedido(p_id, "FINALIZADO")
                                    st.rerun()

        # ------------------------------------------
        # TELA 2: CONTROLE DE ESTOQUE
        # ------------------------------------------
        elif st.session_state.pagina_chapa == "Controle de Estoque":
            with st.container(border=True):
                col_titulo, col_filtro = st.columns([3, 1], vertical_alignment="center")
                with col_titulo:
                    st.subheader("Controle e Reposição de Estoque")
                with col_filtro:
                    filtro_alerta = st.selectbox(
                        "Filtrar por alerta",
                        ["Todos", "OK", "ABAIXO DO MÍNIMO", "ESGOTADO"]
                    )

                with st.container(border=True):
                    busca = st.text_input("Pesquisar Insumo", placeholder="🔍 Digite o nome do ingrediente...")

                st.write("")

                proporcoes = [1.8, 1.2, 0.8, 1.2, 1.6, 2.8]

                st.markdown("""
                    <style>
                        .titulo-coluna {
                            font-size: 16px;
                            font-weight: 800;
                            color: var(--text-color);
                            text-transform: uppercase;
                            letter-spacing: 0.6px;
                            padding-bottom: 8px;
                            border-bottom: 2px solid #FF4B4B;
                        }
                    </style>
                """, unsafe_allow_html=True)

                h1, h2, h3, h4, h5, h6 = st.columns(proporcoes, vertical_alignment="center")
                h1.markdown("<div class='titulo-coluna'>Ingrediente</div>", unsafe_allow_html=True)
                h2.markdown("<div class='titulo-coluna' style='text-align: center;'>Qtd. Atual</div>", unsafe_allow_html=True)
                h3.markdown("<div class='titulo-coluna' style='text-align: center;'>Unidade</div>", unsafe_allow_html=True)
                h4.markdown("<div class='titulo-coluna' style='text-align: center;'>Estoque Mín.</div>", unsafe_allow_html=True)
                h5.markdown("<div class='titulo-coluna' style='text-align: center;'>Alerta</div>", unsafe_allow_html=True)
                h6.markdown("<div class='titulo-coluna' style='text-align: center;'>Reposição</div>", unsafe_allow_html=True)
                st.write("")

                insumos = buscar_insumos()
                encontrou_algum = False

                for item in insumos:
                    i_id, nome_ing, qtd_atual, unidade, est_min = item

                    if qtd_atual <= 0:
                        status_alerta = "ESGOTADO"
                        cor_badge = "#FF4B4B"
                    elif qtd_atual < est_min:
                        status_alerta = "ABAIXO DO MÍNIMO"
                        cor_badge = "#6C757D"
                    else:
                        status_alerta = "OK"
                        cor_badge = "#A0A0A0"

                    if busca and busca.lower() not in nome_ing.lower():
                        continue
                    if filtro_alerta != "Todos" and status_alerta != filtro_alerta:
                        continue

                    encontrou_algum = True

                    qtd_fmt = int(qtd_atual) if qtd_atual.is_integer() else qtd_atual
                    min_fmt = int(est_min) if est_min.is_integer() else est_min

                    c1, c2, c3, c4, c5, c6 = st.columns(proporcoes, vertical_alignment="center")
                    c1.markdown(f"**{nome_ing}**")
                    c2.markdown(f"<div style='text-align: center;'>{qtd_fmt}</div>", unsafe_allow_html=True)
                    c3.markdown(f"<div style='text-align: center;'>{unidade}</div>", unsafe_allow_html=True)
                    c4.markdown(f"<div style='text-align: center;'>{min_fmt}</div>", unsafe_allow_html=True)

                    c5.markdown(
                        f"<div style='background-color: {cor_badge}; color: white; padding: 6px 8px; "
                        f"border-radius: 12px; text-align: center; font-size: 12px; font-weight: bold;'>"
                        f"{status_alerta}</div>",
                        unsafe_allow_html=True
                    )

                    with c6:
                        col_input, col_btn = st.columns([0.9, 1.6], vertical_alignment="center")
                        qtd_entrada = col_input.number_input(
                            "Qtd",
                            min_value=0.0,
                            step=1.0,
                            key=f"input_est_{i_id}",
                            label_visibility="collapsed"
                        )
                        if col_btn.button("REGISTRAR", key=f"btn_est_{i_id}", use_container_width=True):
                            if qtd_entrada > 0:
                                registrar_entrada_estoque(i_id, qtd_entrada)
                                st.success(f"+{qtd_entrada:g} {unidade} em {nome_ing}")
                                st.rerun()
                            else:
                                st.warning("Informe > 0")

                    st.divider()

                if not encontrou_algum:
                    st.info("Nenhum insumo encontrado para os filtros selecionados.")

        # ------------------------------------------
        # TELA 3: CADASTRAR NOVO INSUMO
        # ------------------------------------------
        elif st.session_state.pagina_chapa == "Cadastrar insumo":
            with st.container(border=True):
                st.subheader("Cadastro de Novo Insumo")
                st.divider()

                with st.container(border=True):
                    st.markdown("**Dados do Novo Ingrediente / Insumo**")
                    st.write("")

                    with st.form("form_cadastrar_insumo", clear_on_submit=True):
                        nome_insumo = st.text_input(
                            "Nome do Insumo *",
                            placeholder="Ex: Salsicha Viena, Molho Barbecue, Bacon..."
                        )

                        col_unid, col_qtd = st.columns([1, 1.5])
                        with col_unid:
                            opcao_unidade = st.selectbox(
                                "Unidade de Medida *",
                                ["Unidade (UN)", "Gramas (G)", "Mililitros (ML)"]
                            )
                        with col_qtd:
                            qtd_inicial = st.number_input(
                                "Quantidade Inicial (Saldo Atual) *",
                                min_value=0.0,
                                step=1.0,
                                value=0.0
                            )

                        st.write("")

                        col_min, col_btn = st.columns([1.2, 1.3], vertical_alignment="bottom")
                        with col_min:
                            estoque_minimo = st.number_input(
                                "Estoque Mínimo (Gatilho de Alerta) *",
                                min_value=0.0,
                                step=1.0,
                                value=10.0
                            )
                        with col_btn:
                            botao_salvar = st.form_submit_button(
                                "SALVAR NOVO INSUMO",
                                type="primary",
                                use_container_width=True
                            )

                        if botao_salvar:
                            if not nome_insumo.strip():
                                st.warning("Por favor, preencha o Nome do Insumo.")
                            else:
                                sigla_unidade = opcao_unidade.split("(")[1].replace(")", "")
                                sucesso = cadastrar_novo_insumo(
                                    nome_insumo,
                                    sigla_unidade,
                                    qtd_inicial,
                                    estoque_minimo
                                )
                                if sucesso:
                                    st.success(f"Insumo '{nome_insumo.strip()}' cadastrado com sucesso! Já está disponível no Controle de Estoque.")
                                else:
                                    st.error("Já existe um insumo cadastrado com esse nome.")