import streamlit as st
import sqlite3
import hashlib
import pillow_avif
from PIL import Image

# 1. Inicializa o estado da sessão
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

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

# 3. Configuração da página
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

def garantir_cardapio_teste():
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cardapio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL,
            preco REAL NOT NULL,
            descricao TEXT,
            ativo INTEGER DEFAULT 1
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM cardapio")
    if cursor.fetchone()[0] == 0:
        itens_exemplo = [
            ("Dog Tradicional", "Lanches", 18.00, "Pão, 1 salsicha, purê, milho, ervilha, batata palha e molhos", 1),
            ("Dog Duplo Prensado", "Lanches", 24.50, "Pão, 2 salsichas, purê, cheddar, bacon, batata palha e molhos", 1),
            ("Dog Frango Catupiry", "Lanches", 26.00, "Pão, salsicha, frango desfiado, catupiry original e batata palha", 1),
            ("Coca-Cola Lata 350ml", "Bebidas", 6.00, "Gelada", 1),
            ("Porção de Batata Frita", "Porções", 15.00, "300g de batata crocante", 1)
        ]
        cursor.executemany("""
            INSERT INTO cardapio (nome, categoria, preco, descricao, ativo)
            VALUES (?, ?, ?, ?, ?)
        """, itens_exemplo)
        conn.commit()
    conn.close()

def buscar_cardapio():
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, categoria, preco, descricao, ativo FROM cardapio ORDER BY categoria, nome ASC")
    itens = cursor.fetchall()
    conn.close()
    return itens

def adicionar_item_cardapio(nome, categoria, preco, descricao):
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO cardapio (nome, categoria, preco, descricao, ativo)
        VALUES (?, ?, ?, ?, 1)
    """, (nome, categoria, preco, descricao))
    conn.commit()
    conn.close()

def atualizar_item_cardapio(item_id, novo_preco, ativo):
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE cardapio SET preco = ?, ativo = ? WHERE id = ?", (novo_preco, ativo, item_id))
    conn.commit()
    conn.close()

def excluir_item_cardapio(item_id):
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cardapio WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

def garantir_bairros_teste():
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bairros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            distancia_km REAL NOT NULL
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM bairros")
    if cursor.fetchone()[0] == 0:
        bairros_exemplo = [
            ("Jandira", 11.2),
            ("Jardim Gabriela", 1.4),
            ("Jardim Renato", 6.0)
        ]
        cursor.executemany("""
            INSERT INTO bairros (nome, distancia_km)
            VALUES (?, ?)
        """, bairros_exemplo)
        conn.commit()
    conn.close()

def buscar_bairros():
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, distancia_km FROM bairros ORDER BY nome ASC")
    lista = cursor.fetchall()
    conn.close()
    return lista

def adicionar_bairro(nome, distancia_km):
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM bairros WHERE LOWER(nome) = LOWER(?)", (nome.strip(),))
    if cursor.fetchone():
        conn.close()
        return False
    cursor.execute("INSERT INTO bairros (nome, distancia_km) VALUES (?, ?)", (nome.strip(), distancia_km))
    conn.commit()
    conn.close()
    return True

def atualizar_bairro(bairro_id, novo_nome, nova_distancia):
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE bairros SET nome = ?, distancia_km = ? WHERE id = ?", (novo_nome.strip(), nova_distancia, bairro_id))
    conn.commit()
    conn.close()

def excluir_bairro(bairro_id):
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bairros WHERE id = ?", (bairro_id,))
    conn.commit()
    conn.close()

def buscar_usuarios():
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, email, perfil, secao, foto FROM usuarios ORDER BY nome ASC")
    lista = cursor.fetchall()
    conn.close()
    return lista

def cadastrar_usuario(nome, email, senha, perfil, secao, foto):
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email.strip(),))
    if cursor.fetchone():
        conn.close()
        return False
    senha_hash = hashlib.sha256(senha.encode('utf-8')).hexdigest()
    cursor.execute("""
        INSERT INTO usuarios (nome, email, senha_hash, perfil, secao, foto)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (nome.strip(), email.strip(), senha_hash, perfil, secao, foto))
    conn.commit()
    conn.close()
    return True

def excluir_usuario(user_id):
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def atualizar_usuario(user_id, novo_nome, novo_email, novo_perfil, nova_secao, nova_foto):
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    # Verifica se o e-mail já pertence a outro usuário
    cursor.execute("SELECT id FROM usuarios WHERE email = ? AND id != ?", (novo_email.strip(), user_id))
    if cursor.fetchone():
        conn.close()
        return False
    cursor.execute("""
        UPDATE usuarios 
        SET nome = ?, email = ?, perfil = ?, secao = ?, foto = ?
        WHERE id = ?
    """, (novo_nome.strip(), novo_email.strip(), novo_perfil, nova_secao, nova_foto, user_id))
    conn.commit()
    conn.close()
    return True

def garantir_usuarios_teste():
    conn = sqlite3.connect("dragon_hot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            perfil TEXT NOT NULL,
            secao TEXT DEFAULT 'Geral',
            foto TEXT DEFAULT 'dragao_gerente.avif'
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        senha_gerente = hashlib.sha256("admin123".encode('utf-8')).hexdigest()
        senha_chapa = hashlib.sha256("chapa123".encode('utf-8')).hexdigest()
        usuarios_exemplo = [
            ("Carlos Gerente", "gerente@dragonhot.com", senha_gerente, "Gerente", "Administração", "dragao_gerente.avif"),
            ("João Cozinha", "chapa@dragonhot.com", senha_chapa, "Chapa", "Cozinha / Chapa", "dragao_cozinha.avif")
        ]
        cursor.executemany("""
            INSERT INTO usuarios (nome, email, senha_hash, perfil, secao, foto)
            VALUES (?, ?, ?, ?, ?, ?)
        """, usuarios_exemplo)
        conn.commit()
    conn.close()

# Inicializa todas as tabelas de exemplo (Ordem correta)
garantir_usuarios_teste()
garantir_pedidos_teste()
garantir_estoque_teste()
garantir_cardapio_teste()
garantir_bairros_teste()

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

        # ------------------------------------------
        # TELA 1: DASHBOARD
        # ------------------------------------------
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

        # ------------------------------------------
        # TELA 2: GESTÃO DE CARDÁPIO
        # ------------------------------------------
        elif st.session_state.pagina_gerente == "Cardapio":
            st.title("🍔 Gestão de Cardápio")
            st.caption("Cadastre novos produtos, ajuste preços ou pause itens indisponíveis")

            with st.expander("➕ Cadastrar Novo Item no Cardápio", expanded=False):
                with st.form("form_novo_item_cardapio", clear_on_submit=True):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    novo_nome = col1.text_input("Nome do Produto *", placeholder="Ex: Dog Bacon Especial")
                    nova_cat = col2.selectbox("Categoria", ["Lanches", "Bebidas", "Porções", "Adicionais"])
                    novo_preco = col3.number_input("Preço (R$) *", min_value=0.0, step=0.50, format="%.2f")
                    
                    nova_desc = st.text_area("Ingredientes / Descrição", placeholder="Ex: Pão, 2 salsichas, bacon crocante, cheddar...")
                    
                    if st.form_submit_button("Salvar Produto", type="primary", use_container_width=True):
                        if novo_nome.strip() and novo_preco > 0:
                            adicionar_item_cardapio(novo_nome.strip(), nova_cat, novo_preco, nova_desc.strip())
                            st.success(f"'{novo_nome}' adicionado ao cardápio!")
                            st.rerun()
                        else:
                            st.warning("Preencha o nome do produto e um preço maior que zero.")

            st.divider()

            col_busca, col_cat = st.columns([3, 1])
            busca_card = col_busca.text_input("🔍 Buscar item", placeholder="Digite o nome do lanche ou bebida...")
            filtro_cat = col_cat.selectbox("Filtrar Categoria", ["Todas", "Lanches", "Bebidas", "Porções", "Adicionais"])

            st.write("")

            itens_cardapio = buscar_cardapio()
            encontrou = False

            if not itens_cardapio:
                st.info("Nenhum item cadastrado no cardápio ainda.")
            else:
                for item in itens_cardapio:
                    c_id, c_nome, c_cat, c_preco, c_desc, c_ativo = item

                    if busca_card and busca_card.lower() not in c_nome.lower():
                        continue
                    if filtro_cat != "Todas" and c_cat != filtro_cat:
                        continue

                    encontrou = True

                    with st.container(border=True):
                        col_info, col_preco, col_status, col_acoes = st.columns([3, 1.3, 1.2, 1.3], vertical_alignment="center")
                        
                        with col_info:
                            status_txt = "" if c_ativo else " *(Pausado)*"
                            st.markdown(f"**{c_nome}** `{c_cat}`{status_txt}")
                            if c_desc:
                                st.caption(c_desc)

                        with col_preco:
                            preco_editado = st.number_input(
                                "Preço",
                                min_value=0.0,
                                value=float(c_preco),
                                step=0.50,
                                format="%.2f",
                                key=f"preco_card_{c_id}",
                                label_visibility="collapsed"
                            )

                        with col_status:
                            ativo_editado = st.toggle("Disponível", value=bool(c_ativo), key=f"ativo_card_{c_id}")

                        with col_acoes:
                            b_save, b_del = st.columns(2)
                            if b_save.button("💾", key=f"save_card_{c_id}", help="Salvar alterações", use_container_width=True):
                                atualizar_item_cardapio(c_id, preco_editado, int(ativo_editado))
                                st.toast(f"{c_nome} atualizado!", icon="✅")
                                st.rerun()
                            if b_del.button("🗑️", key=f"del_card_{c_id}", help="Excluir item", use_container_width=True):
                                excluir_item_cardapio(c_id)
                                st.toast(f"{c_nome} removido!", icon="🗑️")
                                st.rerun()

                if not encontrou:
                    st.info("Nenhum item encontrado com os filtros atuais.")

        # ------------------------------------------
        # TELA 3: GESTÃO DE BAIRROS
        # ------------------------------------------
        elif st.session_state.pagina_gerente == "Bairros":
            @st.dialog("Cadastrar Bairro")
            def modal_cadastrar_bairro():
                with st.form("form_novo_bairro", clear_on_submit=True):
                    nome_b = st.text_input("Nome do Bairro", placeholder="Nome:")
                    dist_b = st.number_input("Distância (km)", min_value=0.1, step=0.1, value=1.0, format="%.1f")
                    st.write("")
                    if st.form_submit_button("Adicionar", type="primary", use_container_width=True):
                        if not nome_b.strip():
                            st.warning("Informe o nome do bairro.")
                        else:
                            if adicionar_bairro(nome_b, dist_b):
                                st.rerun()
                            else:
                                st.error("Este bairro já está cadastrado.")

            @st.dialog("Editar Bairro")
            def modal_editar_bairro(b_id, nome_atual, dist_atual):
                with st.form(f"form_edit_bairro_{b_id}"):
                    novo_nome = st.text_input("Novo nome", value=nome_atual, placeholder="Nome:")
                    nova_dist = st.number_input("Distância (km)", min_value=0.1, step=0.1, value=float(dist_atual), format="%.1f")
                    st.write("")
                    if st.form_submit_button("Salvar", type="primary", use_container_width=True):
                        if not novo_nome.strip():
                            st.warning("Informe o nome do bairro.")
                        else:
                            atualizar_bairro(b_id, novo_nome, nova_dist)
                            st.rerun()

            col_topo_esq, col_topo_dir = st.columns([3, 1], vertical_alignment="center")
            with col_topo_esq:
                st.markdown(f"### 👤 Olá, {nome}!")
            with col_topo_dir:
                st.markdown("<div style='text-align: right; color: gray;'>Painel administrativo</div>", unsafe_allow_html=True)

            st.caption("Gerencie os Bairros")
            st.write("")

            bairros = buscar_bairros()

            if not bairros:
                st.info("Nenhum bairro cadastrado no momento.")
            else:
                for b_id, b_nome, b_dist in bairros:
                    dist_fmt = f"{b_dist:.1f}".replace(".", ",") + " km"

                    with st.container(border=True):
                        c_info, c_editar, c_excluir = st.columns([4, 1, 1], vertical_alignment="center")
                        with c_info:
                            st.markdown(f"#### {b_nome}")
                            st.caption(dist_fmt)
                        with c_editar:
                            if st.button("Editar", key=f"edit_bairro_{b_id}", use_container_width=True):
                                modal_editar_bairro(b_id, b_nome, b_dist)
                        with c_excluir:
                            if st.button("Excluir", key=f"del_bairro_{b_id}", use_container_width=True):
                                excluir_bairro(b_id)
                                st.rerun()

            st.write("")

            col_vazia1, col_btn_add, col_vazia2 = st.columns([1.5, 1, 1.5])
            with col_btn_add:
                if st.button("➕ Adicionar Bairro", use_container_width=True):
                    modal_cadastrar_bairro()

        # ------------------------------------------
        # TELA 4: COLABORADORES
        # ------------------------------------------
        # ------------------------------------------
        # TELA 4: COLABORADORES
        # ------------------------------------------
        elif st.session_state.pagina_gerente == "Colaboradores":
            @st.dialog("Cadastrar Novo Colaborador")
            def modal_cadastrar_colaborador():
                with st.form("form_novo_colaborador", clear_on_submit=True):
                    nome_c = st.text_input("Nome Completo *", placeholder="Ex: Roberto Lima")
                    email_c = st.text_input("E-mail (Acesso) *", placeholder="roberto@dragonhot.com")
                    senha_c = st.text_input("Senha Temporária *", type="password", placeholder="******")
                    
                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        perfil_c = st.selectbox("Perfil de Acesso *", ["Gerente", "Chapa"])
                    with col_p2:
                        secao_c = st.selectbox("Seção / Setor *", ["Cozinha / Chapa", "Administração", "Atendimento", "Expedição/Delivery"])

                    foto_c = st.selectbox("Avatar / Ícone", ["dragao_gerente.avif", "dragao_cozinha.avif"])
                    
                    st.write("")
                    if st.form_submit_button("Salvar Colaborador", type="primary", use_container_width=True):
                        if not nome_c.strip() or not email_c.strip() or not senha_c.strip():
                            st.warning("Preencha todos os campos obrigatórios.")
                        else:
                            sucesso = cadastrar_usuario(nome_c, email_c, senha_c, perfil_c, secao_c, foto_c)
                            if sucesso:
                                st.success(f"Colaborador '{nome_c}' cadastrado com sucesso!")
                                st.rerun()
                            else:
                                st.error("Já existe um colaborador cadastrado com este e-mail.")

            @st.dialog("Editar Colaborador")
            def modal_editar_colaborador(u_id, nome_atual, email_atual, perfil_atual, secao_atual, foto_atual):
                with st.form(f"form_edit_colaborador_{u_id}"):
                    novo_nome = st.text_input("Nome Completo *", value=nome_atual)
                    novo_email = st.text_input("E-mail (Acesso) *", value=email_atual)
                    
                    opcoes_perfis = ["Gerente", "Chapa"]
                    idx_perfil = opcoes_perfis.index(perfil_atual) if perfil_atual in opcoes_perfis else 0

                    opcoes_secoes = ["Cozinha / Chapa", "Administração", "Atendimento", "Expedição/Delivery"]
                    idx_secao = opcoes_secoes.index(secao_atual) if secao_atual in opcoes_secoes else 0

                    opcoes_fotos = ["dragao_gerente.avif", "dragao_cozinha.avif"]
                    idx_foto = opcoes_fotos.index(foto_atual) if foto_atual in opcoes_fotos else 0

                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        novo_perfil = st.selectbox("Perfil de Acesso *", opcoes_perfis, index=idx_perfil)
                    with col_p2:
                        nova_secao = st.selectbox("Seção / Setor *", opcoes_secoes, index=idx_secao)

                    nova_foto = st.selectbox("Avatar / Ícone", opcoes_fotos, index=idx_foto)
                    
                    st.write("")
                    if st.form_submit_button("Salvar Alterações", type="primary", use_container_width=True):
                        if not novo_nome.strip() or not novo_email.strip():
                            st.warning("Preencha os campos obrigatórios.")
                        else:
                            sucesso = atualizar_usuario(u_id, novo_nome, novo_email, novo_perfil, nova_secao, nova_foto)
                            if sucesso:
                                st.toast("Colaborador atualizado com sucesso!", icon="✅")
                                st.rerun()
                            else:
                                st.error("Este e-mail já está sendo usado por outro colaborador.")

            st.title("👥 Gestão de Colaboradores")
            st.caption("Cadastre funcionários, defina perfis de acesso, setores e avatares")

            col_topo1, col_topo2 = st.columns([3, 1])
            with col_topo2:
                if st.button("➕ Novo Colaborador", type="primary", use_container_width=True):
                    modal_cadastrar_colaborador()

            st.divider()

            usuarios = buscar_usuarios()

            if not usuarios:
                st.info("Nenhum colaborador cadastrado.")
            else:
                for u_id, u_nome, u_email, u_perfil, u_secao, u_foto in usuarios:
                    with st.container(border=True):
                        c_img, c_info, c_editar, c_acoes = st.columns([0.8, 3.2, 1, 1], vertical_alignment="center")
                        
                        with c_img:
                            try:
                                img_avatar = Image.open(f"imagens/{u_foto}")
                                st.image(img_avatar, width=60)
                            except:
                                st.write("👤")

                        with c_info:
                            st.markdown(f"**{u_nome}** (`{u_perfil}`)")
                            st.caption(f"📧 {u_email}  |  🏷️ Seção: **{u_secao}**")

                        with c_editar:
                            if st.button("✏️ Editar", key=f"edit_user_{u_id}", use_container_width=True):
                                modal_editar_colaborador(u_id, u_nome, u_email, u_perfil, u_secao, u_foto)

                        with c_acoes:
                            if u_email != st.session_state.usuario_logado.get("email"):
                                if st.button("🗑️ Excluir", key=f"del_user_{u_id}", use_container_width=True):
                                    excluir_usuario(u_id)
                                    st.toast(f"Colaborador {u_nome} removido!", icon="🗑️")
                                    st.rerun()
                            else:
                                st.caption("*(Conta Atual)*")

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