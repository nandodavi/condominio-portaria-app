import psycopg2
from pathlib import Path
from io import BytesIO

import pandas as pd
import streamlit as st

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(
    page_title="Portaria Condomínio",
    page_icon="🏢",
    layout="wide",
)

# =========================================================
# PATHS / ASSETS
# =========================================================
logo_path = Path("assets/logo_condominio.png")

# =========================================================
# CONFIGURAÇÕES DO CONDOMÍNIO
# =========================================================
QUADRAS = ["A", "B", "C", "D", "E", "F", "G", "H"]
CASAS = [str(i) for i in range(1, 50)]

# =========================================================
# ESTILO VISUAL - TEMA PRETO E VERDE
# =========================================================
st.markdown(
    """
    <style>
        .stApp {
            background: linear-gradient(180deg, #020817 0%, #04112a 100%);
            color: #f8fafc;
        }

        .main-title {
            font-size: 2rem;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 0.3rem;
        }

        .subtitle {
            color: #d1d5db;
            margin-bottom: 1rem;
        }

        .section-card {
            background: linear-gradient(135deg, rgba(6,18,43,0.98), rgba(4,14,34,0.98));
            border: 1px solid rgba(34,197,94,0.14);
            border-radius: 18px;
            padding: 18px;
            margin-bottom: 16px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.16);
        }

        .metric-card {
            background: linear-gradient(135deg, rgba(6,18,43,0.98), rgba(4,14,34,0.98));
            border: 1px solid rgba(34,197,94,0.14);
            border-radius: 18px;
            padding: 18px;
            min-height: 120px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.16);
        }

        .hero-card {
            background: linear-gradient(135deg, rgba(7,20,48,0.98), rgba(5,15,37,0.98));
            border: 1px solid rgba(34,197,94,0.14);
            border-radius: 22px;
            padding: 24px;
            margin-bottom: 18px;
            box-shadow: 0 10px 28px rgba(0,0,0,0.18);
        }

        .badge-green {
            display: inline-block;
            padding: 8px 14px;
            border-radius: 999px;
            font-size: 0.9rem;
            font-weight: 700;
            color: #bbf7d0;
            background: rgba(16, 185, 129, 0.14);
            border: 1px solid rgba(34,197,94,0.24);
        }

        div[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #07140f 0%, #0a1b13 100%);
            border-right: 1px solid rgba(34,197,94,0.10);
        }

        div[data-testid="stSidebar"] button {
            border-radius: 14px !important;
            border: 1px solid rgba(255,255,255,0.14) !important;
            background: rgba(255,255,255,0.02) !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            margin-bottom: 10px !important;
            padding: 0.8rem 0.9rem !important;
            box-shadow: none !important;
        }

        div[data-testid="stSidebar"] button:hover {
            border: 1px solid rgba(57,255,136,0.35) !important;
            background: linear-gradient(90deg, rgba(8,51,28,0.88), rgba(7,70,37,0.45)) !important;
            color: #ffffff !important;
        }

        .status-ok {
            color: #39ff88;
            font-weight: 700;
        }

        .status-out {
            color: #ff6961;
            font-weight: 700;
        }

        .small-muted {
            color: #aab7c4;
            font-size: 0.92rem;
        }

        .metric-label {
            color: #cbd5e1;
            font-size: 0.95rem;
            margin-bottom: 0.4rem;
        }

        .metric-value {
            color: #ffffff;
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.1;
        }

        .metric-accent {
            height: 6px;
            width: 56px;
            border-radius: 999px;
            background: linear-gradient(90deg, #39ff88, #10b981);
            margin-bottom: 12px;
        }

        hr {
            border-color: rgba(255,255,255,0.08);
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# BANCO DE DADOS - POSTGRESQL
# =========================================================
def get_connection():
    return psycopg2.connect(
        host=st.secrets["db_host"],
        database=st.secrets["db_name"],
        user=st.secrets["db_user"],
        password=st.secrets["db_password"],
        port=int(st.secrets["db_port"]),
    )


def criar_tabelas():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS visitantes (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                documento TEXT,
                telefone TEXT,
                casa_destino TEXT NOT NULL,
                quadra TEXT,
                possui_veiculo TEXT NOT NULL,
                placa TEXT,
                modelo TEXT,
                cor TEXT,
                observacao TEXT,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prestadores (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                empresa TEXT,
                servico TEXT NOT NULL,
                documento TEXT,
                telefone TEXT,
                casa_destino TEXT NOT NULL,
                quadra TEXT,
                possui_veiculo TEXT NOT NULL,
                placa TEXT,
                modelo TEXT,
                cor TEXT,
                observacao TEXT,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movimentacoes (
                id SERIAL PRIMARY KEY,
                tipo_cadastro TEXT NOT NULL,
                cadastro_id INTEGER,
                nome TEXT NOT NULL,
                documento TEXT,
                placa TEXT,
                casa_destino TEXT NOT NULL,
                quadra TEXT,
                acao TEXT NOT NULL,
                observacao TEXT,
                data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        st.error(f"Erro ao conectar no PostgreSQL: {e}")
        st.stop()

# =========================================================
# FUNÇÕES UTILITÁRIAS
# =========================================================
def normalizar_placa(placa: str) -> str:
    if not placa:
        return ""
    return placa.strip().upper().replace("-", "").replace(" ", "")


def render_metric_card(label: str, value):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-accent"></div>
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# FUNÇÕES DE DADOS
# =========================================================
def salvar_visitante(nome, documento, telefone, casa_destino, quadra, possui_veiculo, placa, modelo, cor, observacao):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO visitantes (
            nome, documento, telefone, casa_destino, quadra,
            possui_veiculo, placa, modelo, cor, observacao
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            nome,
            documento,
            telefone,
            casa_destino,
            quadra,
            possui_veiculo,
            placa,
            modelo,
            cor,
            observacao,
        ),
    )

    conn.commit()
    cursor.close()
    conn.close()



def salvar_prestador(nome, empresa, servico, documento, telefone, casa_destino, quadra, possui_veiculo, placa, modelo, cor, observacao):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO prestadores (
            nome, empresa, servico, documento, telefone,
            casa_destino, quadra, possui_veiculo, placa, modelo, cor, observacao
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            nome,
            empresa,
            servico,
            documento,
            telefone,
            casa_destino,
            quadra,
            possui_veiculo,
            placa,
            modelo,
            cor,
            observacao,
        ),
    )

    conn.commit()
    cursor.close()
    conn.close()



def listar_visitantes():
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT
            id,
            nome,
            documento,
            telefone,
            casa_destino,
            quadra,
            possui_veiculo,
            placa,
            modelo,
            cor,
            observacao,
            data_cadastro
        FROM visitantes
        ORDER BY id DESC
        """,
        conn,
    )
    conn.close()
    return df



def listar_prestadores():
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT
            id,
            nome,
            empresa,
            servico,
            documento,
            telefone,
            casa_destino,
            quadra,
            possui_veiculo,
            placa,
            modelo,
            cor,
            observacao,
            data_cadastro
        FROM prestadores
        ORDER BY id DESC
        """,
        conn,
    )
    conn.close()
    return df



def listar_movimentacoes():
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT
            id,
            tipo_cadastro,
            cadastro_id,
            nome,
            documento,
            placa,
            casa_destino,
            quadra,
            acao,
            observacao,
            data_hora
        FROM movimentacoes
        ORDER BY id DESC
        """,
        conn,
    )
    conn.close()
    return df



def buscar_cadastro_por_placa(placa):
    placa_normalizada = normalizar_placa(placa)
    if not placa_normalizada:
        return None

    conn = get_connection()

    visitantes = pd.read_sql_query(
        """
        SELECT
            id, nome, documento, telefone, casa_destino, quadra,
            possui_veiculo, placa, modelo, cor, observacao,
            'Visitante' AS tipo_cadastro
        FROM visitantes
        WHERE REPLACE(REPLACE(UPPER(COALESCE(placa, '')), '-', ''), ' ', '') = %s
        LIMIT 1
        """,
        conn,
        params=(placa_normalizada,),
    )

    if not visitantes.empty:
        conn.close()
        return visitantes.iloc[0].to_dict()

    prestadores = pd.read_sql_query(
        """
        SELECT
            id, nome, documento, telefone, casa_destino, quadra,
            possui_veiculo, placa, modelo, cor, observacao, empresa, servico,
            'Prestador' AS tipo_cadastro
        FROM prestadores
        WHERE REPLACE(REPLACE(UPPER(COALESCE(placa, '')), '-', ''), ' ', '') = %s
        LIMIT 1
        """,
        conn,
        params=(placa_normalizada,),
    )

    conn.close()
    if not prestadores.empty:
        return prestadores.iloc[0].to_dict()

    return None



def registrar_movimentacao(tipo_cadastro, cadastro_id, nome, documento, placa, casa_destino, quadra, acao, observacao):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO movimentacoes (
            tipo_cadastro, cadastro_id, nome, documento, placa,
            casa_destino, quadra, acao, observacao
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            tipo_cadastro,
            cadastro_id,
            nome,
            documento,
            placa,
            casa_destino,
            quadra,
            acao,
            observacao,
        ),
    )

    conn.commit()
    cursor.close()
    conn.close()



def atualizar_visitante(id_visitante, nome, documento, telefone, casa_destino, quadra, possui_veiculo, placa, modelo, cor, observacao):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE visitantes
        SET nome = %s,
            documento = %s,
            telefone = %s,
            casa_destino = %s,
            quadra = %s,
            possui_veiculo = %s,
            placa = %s,
            modelo = %s,
            cor = %s,
            observacao = %s
        WHERE id = %s
        """,
        (
            nome,
            documento,
            telefone,
            casa_destino,
            quadra,
            possui_veiculo,
            placa,
            modelo,
            cor,
            observacao,
            id_visitante,
        ),
    )

    conn.commit()
    cursor.close()
    conn.close()



def atualizar_prestador(id_prestador, nome, empresa, servico, documento, telefone, casa_destino, quadra, possui_veiculo, placa, modelo, cor, observacao):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE prestadores
        SET nome = %s,
            empresa = %s,
            servico = %s,
            documento = %s,
            telefone = %s,
            casa_destino = %s,
            quadra = %s,
            possui_veiculo = %s,
            placa = %s,
            modelo = %s,
            cor = %s,
            observacao = %s
        WHERE id = %s
        """,
        (
            nome,
            empresa,
            servico,
            documento,
            telefone,
            casa_destino,
            quadra,
            possui_veiculo,
            placa,
            modelo,
            cor,
            observacao,
            id_prestador,
        ),
    )

    conn.commit()
    cursor.close()
    conn.close()



def excluir_visitante(id_visitante):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM visitantes WHERE id = %s", (id_visitante,))
    conn.commit()
    cursor.close()
    conn.close()



def excluir_prestador(id_prestador):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM prestadores WHERE id = %s", (id_prestador,))
    conn.commit()
    cursor.close()
    conn.close()



def exportar_excel():
    visitantes_df = listar_visitantes()
    prestadores_df = listar_prestadores()
    movimentacoes_df = listar_movimentacoes()

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        visitantes_df.to_excel(writer, sheet_name="Visitantes", index=False)
        prestadores_df.to_excel(writer, sheet_name="Prestadores", index=False)
        movimentacoes_df.to_excel(writer, sheet_name="Historico", index=False)

    output.seek(0)
    return output.getvalue()


# =========================================================
# SIDEBAR / NAVEGAÇÃO
# =========================================================
PAGINAS = [
    "🏠 Dashboard",
    "👤 Cadastro de Visitante",
    "🛠️ Cadastro de Prestador de Serviço",
    "👥 Cadastros",
    "🚪 Registrar Entrada / Saída",
    "📋 Histórico de Entradas",
]

if "pagina" not in st.session_state:
    st.session_state.pagina = "🏠 Dashboard"

with st.sidebar:
    st.markdown("## 🏢 Portaria")
    st.caption("Sistema de controle do condomínio")
    st.markdown("---")

    for pagina in PAGINAS:
        if st.button(pagina, use_container_width=True):
            st.session_state.pagina = pagina

    st.markdown("---")
    st.download_button(
        label="📥 Exportar dados para Excel",
        data=exportar_excel(),
        file_name="portaria_condominio.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    st.markdown("---")
    st.caption("Visual V2 • Preto & Verde")

pagina = st.session_state.pagina

# =========================================================
# CABEÇALHO
# =========================================================
col_logo, col_titulo = st.columns([1.1, 4])

with col_logo:
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)
    else:
        st.markdown(
            '<div class="section-card"><div class="small-muted">Logo não encontrada em assets/logo_condominio.png</div></div>',
            unsafe_allow_html=True,
        )

with col_titulo:
    st.markdown(
        """
        <div class="hero-card">
            <div class="main-title">🏢 Sistema de Controle de Portaria</div>
            <div class="subtitle">Controle de visitantes, prestadores, movimentações e consultas em um único painel.</div>
            <div class="badge-green">Ambiente online ativo</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# DASHBOARD
# =========================================================
if pagina == "🏠 Dashboard":
    visitantes_total = len(listar_visitantes())
    prestadores_total = len(listar_prestadores())
    movimentacoes_df = listar_movimentacoes()
    movimentacoes_total = len(movimentacoes_df)
    total_cadastros = visitantes_total + prestadores_total

    st.subheader("Resumo geral")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Visitantes", visitantes_total)
    with col2:
        render_metric_card("Prestadores", prestadores_total)
    with col3:
        render_metric_card("Movimentações", movimentacoes_total)
    with col4:
        render_metric_card("Total cadastros", total_cadastros)

    st.markdown(
        """
        <div class="section-card">
            <h3>Status do sistema</h3>
            <p>Cadastros e movimentações estão sendo salvos em banco PostgreSQL. O histórico pode ser exportado para Excel a qualquer momento.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not movimentacoes_df.empty:
        st.markdown("### Últimas movimentações")
        st.dataframe(movimentacoes_df.head(10), use_container_width=True, hide_index=True)

# =========================================================
# CADASTRO DE VISITANTE
# =========================================================
elif pagina == "👤 Cadastro de Visitante":
    st.subheader("Cadastro de Visitante")

    possui_veiculo_visitante = st.selectbox(
        "Possui veículo?",
        ["Não", "Sim"],
        key="possui_veiculo_visitante"
    )

    with st.form("form_visitante", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome")
        documento = col2.text_input("Documento")
        telefone = col1.text_input("Telefone")
        quadra = col1.selectbox("Quadra", QUADRAS, key="quadra_visitante")
        casa_destino = col2.selectbox("Casa", CASAS, key="casa_visitante")

        placa = ""
        modelo = ""
        cor = ""

        if st.session_state.possui_veiculo_visitante == "Sim":
            placa = col1.text_input("Placa")
            modelo = col2.text_input("Modelo")
            cor = col1.text_input("Cor")

        observacao = st.text_area("Observação")
        salvar = st.form_submit_button("Salvar visitante")

        if salvar:
            if not nome.strip() or not casa_destino.strip():
                st.error("Preencha pelo menos nome e casa do visitante.")
            else:
                salvar_visitante(
                    nome.strip(),
                    documento.strip(),
                    telefone.strip(),
                    casa_destino.strip(),
                    quadra.strip(),
                    st.session_state.possui_veiculo_visitante,
                    placa.strip().upper(),
                    modelo.strip(),
                    cor.strip(),
                    observacao.strip(),
                )
                st.success("Visitante cadastrado com sucesso.")

# =========================================================
# CADASTRO DE PRESTADOR
# =========================================================
elif pagina == "🛠️ Cadastro de Prestador de Serviço":
    st.subheader("Cadastro de Prestador de Serviço")

    possui_veiculo_prestador = st.selectbox(
        "Possui veículo?",
        ["Não", "Sim"],
        key="possui_veiculo_prestador_selector"
    )

    with st.form("form_prestador", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome")
        empresa = col2.text_input("Empresa")
        servico = col1.text_input("Serviço")
        documento = col2.text_input("Documento")
        telefone = col1.text_input("Telefone")
        quadra = col1.selectbox("Quadra", QUADRAS, key="quadra_prestador")
        casa_destino = col2.selectbox("Casa", CASAS, key="casa_prestador")

        placa = ""
        modelo = ""
        cor = ""

        if st.session_state.possui_veiculo_prestador_selector == "Sim":
            placa = col1.text_input("Placa", key="placa_prestador")
            modelo = col2.text_input("Modelo", key="modelo_prestador")
            cor = col1.text_input("Cor", key="cor_prestador")

        observacao = st.text_area("Observação", key="obs_prestador")
        salvar = st.form_submit_button("Salvar prestador")

        if salvar:
            if not nome.strip() or not servico.strip() or not casa_destino.strip():
                st.error("Preencha nome, serviço e casa do prestador.")
            else:
                salvar_prestador(
                    nome.strip(),
                    empresa.strip(),
                    servico.strip(),
                    documento.strip(),
                    telefone.strip(),
                    casa_destino.strip(),
                    quadra.strip(),
                    st.session_state.possui_veiculo_prestador_selector,
                    placa.strip().upper(),
                    modelo.strip(),
                    cor.strip(),
                    observacao.strip(),
                )
                st.success("Prestador cadastrado com sucesso.")
                
# =========================================================
# CADASTROS
# =========================================================
elif pagina == "👥 Cadastros":
    st.subheader("Cadastros")
    tab1, tab2 = st.tabs(["Visitantes", "Prestadores"])

    with tab1:
        visitantes_df = listar_visitantes()
        filtro_visitante = st.text_input("Buscar visitante por nome, documento, casa, quadra ou placa")

        if filtro_visitante:
            termo = filtro_visitante.lower()
            visitantes_df = visitantes_df[
                visitantes_df.astype(str).apply(lambda col: col.str.lower()).apply(
                    lambda row: row.str.contains(termo, na=False)
                ).any(axis=1)
            ]

        st.dataframe(visitantes_df, use_container_width=True, hide_index=True)

        if not visitantes_df.empty:
            visitante_id = st.selectbox(
                "Selecione o ID do visitante para editar/excluir",
                visitantes_df["id"].tolist(),
                key="visitante_id",
            )
            visitante = visitantes_df[visitantes_df["id"] == visitante_id].iloc[0]

            with st.expander("Editar visitante"):
                with st.form("editar_visitante"):
                    nome = st.text_input("Nome", value=visitante["nome"])
                    documento = st.text_input("Documento", value=visitante["documento"] or "")
                    telefone = st.text_input("Telefone", value=visitante["telefone"] or "")
                    quadra_valor = (visitante["quadra"] or "A") if (visitante["quadra"] or "A") in QUADRAS else QUADRAS[0]
                    casa_valor = str(visitante["casa_destino"] or "1")
                    if casa_valor not in CASAS:
                        casa_valor = CASAS[0]
                    quadra = st.selectbox("Quadra", QUADRAS, index=QUADRAS.index(quadra_valor), key="edit_quadra_visitante")
                    casa_destino = st.selectbox("Casa", CASAS, index=CASAS.index(casa_valor), key="edit_casa_visitante")
                    possui_veiculo = st.selectbox(
                        "Possui veículo?",
                        ["Não", "Sim"],
                        index=0 if visitante["possui_veiculo"] == "Não" else 1,
                    )
                    placa = st.text_input("Placa", value=visitante["placa"] or "")
                    modelo = st.text_input("Modelo", value=visitante["modelo"] or "")
                    cor = st.text_input("Cor", value=visitante["cor"] or "")
                    observacao = st.text_area("Observação", value=visitante["observacao"] or "")
                    salvar = st.form_submit_button("Salvar alterações")

                    if salvar:
                        atualizar_visitante(
                            int(visitante_id),
                            nome.strip(),
                            documento.strip(),
                            telefone.strip(),
                            casa_destino.strip(),
                            quadra.strip(),
                            possui_veiculo,
                            placa.strip().upper(),
                            modelo.strip(),
                            cor.strip(),
                            observacao.strip(),
                        )
                        st.success("Visitante atualizado com sucesso.")
                        st.rerun()

            if st.button("Excluir visitante", type="secondary"):
                excluir_visitante(int(visitante_id))
                st.success("Visitante excluído com sucesso.")
                st.rerun()

    with tab2:
        prestadores_df = listar_prestadores()
        filtro_prestador = st.text_input("Buscar prestador por nome, empresa, serviço, documento, casa, quadra ou placa")

        if filtro_prestador:
            termo = filtro_prestador.lower()
            prestadores_df = prestadores_df[
                prestadores_df.astype(str).apply(lambda col: col.str.lower()).apply(
                    lambda row: row.str.contains(termo, na=False)
                ).any(axis=1)
            ]

        st.dataframe(prestadores_df, use_container_width=True, hide_index=True)

        if not prestadores_df.empty:
            prestador_id = st.selectbox(
                "Selecione o ID do prestador para editar/excluir",
                prestadores_df["id"].tolist(),
                key="prestador_id",
            )
            prestador = prestadores_df[prestadores_df["id"] == prestador_id].iloc[0]

            with st.expander("Editar prestador"):
                with st.form("editar_prestador"):
                    nome = st.text_input("Nome", value=prestador["nome"])
                    empresa = st.text_input("Empresa", value=prestador["empresa"] or "")
                    servico = st.text_input("Serviço", value=prestador["servico"] or "")
                    documento = st.text_input("Documento", value=prestador["documento"] or "")
                    telefone = st.text_input("Telefone", value=prestador["telefone"] or "")
                    quadra_valor = (prestador["quadra"] or "A") if (prestador["quadra"] or "A") in QUADRAS else QUADRAS[0]
                    casa_valor = str(prestador["casa_destino"] or "1")
                    if casa_valor not in CASAS:
                        casa_valor = CASAS[0]
                    quadra = st.selectbox("Quadra", QUADRAS, index=QUADRAS.index(quadra_valor), key="edit_quadra_prestador")
                    casa_destino = st.selectbox("Casa", CASAS, index=CASAS.index(casa_valor), key="edit_casa_prestador")
                    possui_veiculo = st.selectbox(
                        "Possui veículo?",
                        ["Não", "Sim"],
                        index=0 if prestador["possui_veiculo"] == "Não" else 1,
                    )
                    placa = st.text_input("Placa", value=prestador["placa"] or "")
                    modelo = st.text_input("Modelo", value=prestador["modelo"] or "")
                    cor = st.text_input("Cor", value=prestador["cor"] or "")
                    observacao = st.text_area("Observação", value=prestador["observacao"] or "")
                    salvar = st.form_submit_button("Salvar alterações")

                    if salvar:
                        atualizar_prestador(
                            int(prestador_id),
                            nome.strip(),
                            empresa.strip(),
                            servico.strip(),
                            documento.strip(),
                            telefone.strip(),
                            casa_destino.strip(),
                            quadra.strip(),
                            possui_veiculo,
                            placa.strip().upper(),
                            modelo.strip(),
                            cor.strip(),
                            observacao.strip(),
                        )
                        st.success("Prestador atualizado com sucesso.")
                        st.rerun()

            if st.button("Excluir prestador", type="secondary"):
                excluir_prestador(int(prestador_id))
                st.success("Prestador excluído com sucesso.")
                st.rerun()

# =========================================================
# REGISTRAR ENTRADA / SAÍDA
# =========================================================
elif pagina == "🚪 Registrar Entrada / Saída":
    st.subheader("Registrar Entrada / Saída")

    col1, col2 = st.columns([1, 2])

    with col1:
        busca_placa = st.text_input("Buscar por placa")
        if st.button("Consultar placa"):
            cadastro = buscar_cadastro_por_placa(busca_placa)
            if cadastro:
                st.session_state.registro_tipo_cadastro = cadastro.get("tipo_cadastro", "Outro")
                st.session_state.registro_cadastro_id = int(cadastro.get("id"))
                st.session_state.registro_nome = cadastro.get("nome", "")
                st.session_state.registro_documento = cadastro.get("documento", "")
                st.session_state.registro_placa = cadastro.get("placa", "")
                st.session_state.registro_casa = cadastro.get("casa_destino", "")
                st.session_state.registro_quadra = cadastro.get("quadra", "")
                st.success(f"Cadastro encontrado: {cadastro.get('tipo_cadastro')} - {cadastro.get('nome')}")
            else:
                st.warning("Nenhum cadastro encontrado para a placa informada.")

    with col2:
        with st.form("form_movimentacao"):
            tipo_cadastro = st.selectbox(
                "Tipo de cadastro",
                ["Visitante", "Prestador", "Outro"],
                index=["Visitante", "Prestador", "Outro"].index(st.session_state.get("registro_tipo_cadastro", "Outro")),
            )
            nome = st.text_input("Nome", value=st.session_state.get("registro_nome", ""))
            documento = st.text_input("Documento", value=st.session_state.get("registro_documento", ""))
            placa = st.text_input("Placa", value=st.session_state.get("registro_placa", ""))
            quadra_padrao = st.session_state.get("registro_quadra", "A") or "A"
            if quadra_padrao not in QUADRAS:
                quadra_padrao = QUADRAS[0]
            casa_padrao = str(st.session_state.get("registro_casa", "1") or "1")
            if casa_padrao not in CASAS:
                casa_padrao = CASAS[0]
            quadra = st.selectbox("Quadra", QUADRAS, index=QUADRAS.index(quadra_padrao), key="registro_quadra_select")
            casa_destino = st.selectbox("Casa", CASAS, index=CASAS.index(casa_padrao), key="registro_casa_select")
            observacao = st.text_area("Observação")

            c1, c2 = st.columns(2)
            registrar_entrada = c1.form_submit_button("Registrar entrada")
            registrar_saida = c2.form_submit_button("Registrar saída")

            if registrar_entrada:
                if not nome.strip() or not casa_destino.strip():
                    st.error("Informe pelo menos nome e casa para registrar a entrada.")
                else:
                    registrar_movimentacao(
                        tipo_cadastro,
                        st.session_state.get("registro_cadastro_id"),
                        nome.strip(),
                        documento.strip(),
                        placa.strip().upper(),
                        casa_destino.strip(),
                        quadra.strip(),
                        "Entrada",
                        observacao.strip(),
                    )
                    st.success("Entrada registrada com sucesso.")
                    for chave in [
                        "registro_tipo_cadastro",
                        "registro_cadastro_id",
                        "registro_nome",
                        "registro_documento",
                        "registro_placa",
                        "registro_casa",
                        "registro_quadra",
                    ]:
                        st.session_state.pop(chave, None)
                    st.rerun()

            if registrar_saida:
                if not nome.strip() or not casa_destino.strip():
                    st.error("Informe pelo menos nome e casa para registrar a saída.")
                else:
                    registrar_movimentacao(
                        tipo_cadastro,
                        st.session_state.get("registro_cadastro_id"),
                        nome.strip(),
                        documento.strip(),
                        placa.strip().upper(),
                        casa_destino.strip(),
                        quadra.strip(),
                        "Saída",
                        observacao.strip(),
                    )
                    st.success("Saída registrada com sucesso.")
                    for chave in [
                        "registro_tipo_cadastro",
                        "registro_cadastro_id",
                        "registro_nome",
                        "registro_documento",
                        "registro_placa",
                        "registro_casa",
                        "registro_quadra",
                    ]:
                        st.session_state.pop(chave, None)
                    st.rerun()

# =========================================================
# HISTÓRICO
# =========================================================
elif pagina == "📋 Histórico de Entradas":
    st.subheader("Histórico de Entradas")

    historico_df = listar_movimentacoes()

    col1, col2, col3, col4 = st.columns(4)
    filtro_nome = col1.text_input("Filtrar por nome")
    filtro_placa = col2.text_input("Filtrar por placa")
    filtro_casa = col3.text_input("Filtrar por casa")
    filtro_acao = col4.selectbox("Filtrar por ação", ["Todos", "Entrada", "Saída"])

    if filtro_nome:
        historico_df = historico_df[historico_df["nome"].astype(str).str.contains(filtro_nome, case=False, na=False)]
    if filtro_placa:
        historico_df = historico_df[historico_df["placa"].astype(str).str.contains(filtro_placa, case=False, na=False)]
    if filtro_casa:
        historico_df = historico_df[historico_df["casa_destino"].astype(str).str.contains(filtro_casa, case=False, na=False)]
    if filtro_acao != "Todos":
        historico_df = historico_df[historico_df["acao"] == filtro_acao]

    st.dataframe(historico_df, use_container_width=True, hide_index=True)
