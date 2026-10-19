import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
import io
from github import Github

# Configuração inicial da página
st.set_page_config(
    page_title="Painel de Acompanhamento Diário",
    page_icon="🚚",
    layout="wide"
)

# --- CONFIGURAÇÃO DO GITHUB PARA SINCRONIZAÇÃO EM TEMPO REAL ---
REPO_NAME = "yuribergamaschinerslogistica-create/painel-rotas"
DATA_FILE_PATH = "dados_rotas.xlsx"

def get_github_repo():
    try:
        if "GITHUB_TOKEN" in st.secrets:
            g = Github(st.secrets["GITHUB_TOKEN"])
            return g.get_repo(REPO_NAME)
    except Exception as e:
        st.warning(f"Aviso de ligação ao GitHub: {e}")
    return None

def carregar_dados_nuvem():
    repo = get_github_repo()
    if repo:
        try:
            file_content = repo.get_contents(DATA_FILE_PATH)
            decoded_content = file_content.decoded_content
            return io.BytesIO(decoded_content)
        except Exception:
            # Ficheiro ainda não existe no repositório
            pass
    return None

def salvar_dados_nuvem(uploaded_file):
    repo = get_github_repo()
    if repo:
        try:
            file_bytes = uploaded_file.getvalue()
            try:
                contents = repo.get_contents(DATA_FILE_PATH)
                repo.update_file(
                    path=DATA_FILE_PATH,
                    message="Atualização automática de dados pelo supervisor",
                    content=file_bytes,
                    sha=contents.sha
                )
            except Exception:
                repo.create_file(
                    path=DATA_FILE_PATH,
                    message="Primeiro envio de dados pelo supervisor",
                    content=file_bytes
                )
            return True
        except Exception as e:
            st.error(f"Erro ao sincronizar com o GitHub: {e}")
    return False

# --- SISTEMA DE GESTÃO DE UTILIZADORES (LOGIN / SENHAS) ---
USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        default_users = {
            "admin": {"name": "Supervisor Geral", "password": "admin", "role": "Supervisor"},
            "operador": {"name": "Operador Padrão", "password": "123", "role": "Operador"}
        }
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_users, f, indent=4, ensure_ascii=False)
        return default_users
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

users_db = load_users()

# Inicialização do Estado de Sessão
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None

# --- TELA DE LOGIN ---
if not st.session_state["logged_in"]:
    st.title("🔐 Login - Painel de Rotas")
    st.markdown("---")
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        with st.form("login_form"):
            username_input = st.text_input("Utilizador / Login")
            password_input = st.text_input("Senha", type="password")
            submit_button = st.form_submit_button("Entrar")
            
            if submit_button:
                if username_input in users_db and users_db[username_input]["password"] == password_input:
                    st.session_state["logged_in"] = True
                    st.session_state["user_info"] = users_db[username_input]
                    st.session_state["username"] = username_input
                    st.success(f"Bem-vindo(a), {users_db[username_input]['name']}!")
                    st.rerun()
                else:
                    st.error("Utilizador ou senha incorretos.")
    st.stop()

# --- ÁREA LOGADA (PAINEL PRINCIPAL) ---

st.sidebar.title(f"👤 {st.session_state['user_info']['name']}")
st.sidebar.caption(f"Perfil: {st.session_state['user_info']['role']}")

if st.sidebar.button("🚪 Sair / Logout"):
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None
    st.rerun()

st.sidebar.markdown("---")

# PAINEL DO SUPERVISOR: Cadastro de Novos Utilizadores
if st.session_state["user_info"]["role"] == "Supervisor":
    with st.sidebar.expander("➕ Cadastrar Novo Utilizador"):
        with st.form("new_user_form"):
            new_username = st.text_input("Novo Login")
            new_name = st.text_input("Nome Completo")
            new_password = st.text_input("Nova Senha", type="password")
            new_role = st.selectbox("Perfil de Acesso", ["Operador", "Supervisor"])
            create_btn = st.form_submit_button("Guardar Utilizador")
            
            if create_btn:
                if new_username and new_password and new_name:
                    users_db[new_username] = {
                        "name": new_name,
                        "password": new_password,
                        "role": new_role
                    }
                    save_users(users_db)
                    st.success(f"Utilizador '{new_username}' cadastrado com sucesso!")
                else:
                    st.warning("Preencha todos os campos do formulário.")

st.title("🚚 Painel de Acompanhamento Diário - Rotas & AWBs")
st.markdown("---")

# Gestão de Ficheiro (Upload pelo Supervisor ou Leitura Automática da Nuvem)
uploaded_file = None

if st.session_state["user_info"]["role"] == "Supervisor":
    uploaded_file = st.file_uploader("Faça o upload do ficheiro (.xlsx) extraído de manhã", type=["xlsx", "xls"])
    if uploaded_file is not None:
        if salvar_dados_nuvem(uploaded_file):
            st.success("Ficheiro enviado e sincronizado com sucesso para todos os dispositivos!")

# Se não foi feito upload agora, tenta carregar o último ficheiro sincronizado do GitHub
if uploaded_file is None:
    uploaded_file = carregar_dados_nuvem()
    if uploaded_file is not None:
        st.info("📊 A exibir os dados sincronizados mais recentes da operação.")

if uploaded_file is not None:
    # Leitura dos dados
    df = pd.read_excel(uploaded_file)
    
    # Tratamento dos dados
    df['Driver Name'] = df['Driver Name'].fillna('Sem Motorista Atribuído')
    df['Backlog time(Station)'] = df['Backlog time(Station)'].fillna(0).astype(int)
    df['Last scan type'] = df['Last scan type'].fillna('Não informado')
    df['Type'] = df['Type'].fillna('Outro')
    
    cols_map = {
        'Waybill No': 'Número AWB',
        'Driver Name': 'Nome do Motorista',
        'Backlog time(Station)': 'Dias em Rota',
        'Last scan type': 'Última Movimentação',
        'Last scan time': 'Data/Hora Último Scan',
        'Destination City': 'Cidade Destino',
        'Type': 'Status do Registro'
    }
    
    df_display = df[list(cols_map.keys())].rename(columns=cols_map)
    
    # Indicadores principais (KPIs)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de AWBs", len(df_display))
    col2.metric("Motoristas Ativos", df_display[df_display['Nome do Motorista'] != 'Sem Motorista Atribuído']['Nome do Motorista'].nunique())
    col3.metric("Média de Dias em Rota", f"{df_display['Dias em Rota'].mean():.1f} dias")
    col4.metric("AWBs Críticas (>3 dias)", len(df_display[df_display['Dias em Rota'] > 3]))
    
    st.markdown("---")

    # --- SEÇÃO DE GRÁFICOS VISUAIS E DETALHAMENTO ---
    st.subheader("📊 Análise Visual & Detalhamento por Motorista")
    
    tab1, tab2, tab3 = st.tabs([
        "AWBs em Aberto por Motorista", 
        "Volume Total de AWBs por Motorista", 
        "Média de Dias em Rota por Motorista"
    ])
    
    df_motoristas = df_display[df_display['Nome do Motorista'] != 'Sem Motorista Atribuído']
    
    # ABA 1: AWBs em Aberto com Detalhamento por Motorista
    with tab1:
        df_aberto = df_motoristas[df_motoristas['Status do Registro'].str.lower() == 'em aberto']
        awb_aberto_per_driver = df_aberto['Nome do Motorista'].value_counts().reset_index()
        awb_aberto_per_driver.columns = ['Nome do Motorista', 'AWBs em Aberto']
        
        fig0 = px.bar(
            awb_aberto_per_driver, 
            x='Nome do Motorista', 
            y='AWBs em Aberto',
            text='AWBs em Aberto',
            title="Quantidade de AWBs 'Em Aberto' por Motorista",
            color='AWBs em Aberto',
            color_continuous_scale='Reds'
        )
        fig0.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig0, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 🔍 Detalhar Entregas em Aberto")
        
        lista_motoristas_pendentes = sorted(df_aberto['Nome do Motorista'].unique().tolist())
        
        selected_driver = st.selectbox(
            "Selecione o motorista para visualizar todas as suas entregas em aberto:",
            options=lista_motoristas_pendentes,
            index=0 if len(lista_motoristas_pendentes) > 0 else None
        )
        
        if selected_driver:
            df_driver_pendente = df_aberto[df_aberto['Nome do Motorista'] == selected_driver]
            
            col_d1, col_d2 = st.columns(2)
            col_d1.subheader(f"🚚 Motorista: {selected_driver}")
            col_d2.metric("Total de Entregas em Aberto", len(df_driver_pendente))
            
            st.dataframe(
                df_driver_pendente[['Número AWB', 'Dias em Rota', 'Última Movimentação', 'Data/Hora Último Scan', 'Cidade Destino']],
                use_container_width=True,
                hide_index=True
            )

    # ABA 2: Volume Total
    with tab2:
        awb_per_driver = df_motoristas['Nome do Motorista'].value_counts().reset_index()
        awb_per_driver.columns = ['Nome do Motorista', 'Quantidade de AWBs']
        
        fig1 = px.bar(
            awb_per_driver, 
            x='Nome do Motorista', 
            y='Quantidade de AWBs',
            text='Quantidade de AWBs',
            title="Total Geral de AWBs por Motorista",
            color='Quantidade de AWBs',
            color_continuous_scale='Blues'
        )
        fig1.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig1, use_container_width=True)
        
    # ABA 3: Média de Dias em Rota
    with tab3:
        days_per_driver = df_motoristas.groupby('Nome do Motorista')['Dias em Rota'].mean().reset_index()
        days_per_driver.columns = ['Nome do Motorista', 'Média Dias em Rota']
        days_per_driver = days_per_driver.sort_values(by='Média Dias em Rota', ascending=False)
        
        fig2 = px.bar(
            days_per_driver, 
            x='Nome do Motorista', 
            y='Média Dias em Rota',
            text_auto='.1f',
            title="Média de Dias em Rota por Motorista",
            color='Média Dias em Rota',
            color_continuous_scale='Oranges'
        )
        fig2.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
else:
    st.info("Aguardando o supervisor carregar o ficheiro Excel da operação para sincronizar os dados.")
