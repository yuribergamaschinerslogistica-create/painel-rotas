import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
import io
import time
from github import Github
from datetime import datetime

# Configuração inicial da página
st.set_page_config(
    page_title="Painel de Acompanhamento Diário",
    page_icon="🚚",
    layout="wide"
)

# --- CONFIGURAÇÃO DO GITHUB PARA HISTÓRICO E SINCRONIZAÇÃO ---
REPO_NAME = "yuribergamaschinerslogistica-create/painel-rotas"
HISTORY_FILE_PATH = "historico_mes.xlsx"

def get_github_repo():
    try:
        if "GITHUB_TOKEN" in st.secrets:
            g = Github(st.secrets["GITHUB_TOKEN"])
            return g.get_repo(REPO_NAME)
    except Exception as e:
        st.warning(f"Aviso de ligação ao GitHub: {e}")
    return None

# Forçamos o Streamlit a NÃO guardar em cache antiga
@st.cache_data(ttl=0)
def carregar_historico_nuvem():
    repo = get_github_repo()
    if repo:
        try:
            # Força o GitHub a buscar a versão mais recente sem cache
            file_content = repo.get_contents(HISTORY_FILE_PATH)
            decoded_content = file_content.decoded_content
            return pd.read_excel(io.BytesIO(decoded_content))
        except Exception:
            pass
    return None

def salvar_historico_nuvem(df_novo):
    repo = get_github_repo()
    if repo:
        try:
            # Desativa cache antes de carregar o atual
            st.cache_data.clear()
            df_atual = carregar_historico_nuvem()
            
            if df_atual is not None:
                # Junta e mantém a linha mais recente com base no número da AWB
                df_combinado = pd.concat([df_atual, df_novo]).drop_duplicates(subset=['Waybill No'], keep='last')
            else:
                df_combinado = df_novo

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_combinado.to_excel(writer, index=False)
            file_bytes = output.getvalue()

            timestamp_str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

            try:
                contents = repo.get_contents(HISTORY_FILE_PATH)
                repo.update_file(
                    path=HISTORY_FILE_PATH,
                    message=f"Atualização em tempo real: {timestamp_str}",
                    content=file_bytes,
                    sha=contents.sha
                )
            except Exception:
                repo.create_file(
                    path=HISTORY_FILE_PATH,
                    message=f"Criação do histórico: {timestamp_str}",
                    content=file_bytes
                )
            
            # Limpa qualquer cache mantida na sessão do Streamlit
            st.cache_data.clear()
            return True
        except Exception as e:
            st.error(f"Erro ao sincronizar histórico com o GitHub: {e}")
    return False

# --- SISTEMA DE GESTÃO DE UTILIZADORES ---
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

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None

if "view_mode" not in st.session_state:
    st.session_state["view_mode"] = "Painel Principal"

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
                    st.success(f"Bem-vindo(a), {users_db[username_input]['name']}!")
                    st.rerun()
                else:
                    st.error("Utilizador ou senha incorretos.")
    st.stop()

# --- ÁREA LOGADA ---
st.sidebar.title(f"👤 {st.session_state['user_info']['name']}")
st.sidebar.caption(f"Perfil: {st.session_state['user_info']['role']}")

if st.sidebar.button("🚪 Sair / Logout"):
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None
    st.session_state["view_mode"] = "Painel Principal"
    st.rerun()

st.sidebar.markdown("---")

st.sidebar.subheader("📌 Navegação")
if st.sidebar.button("📊 Ver Painel Principal"):
    st.session_state["view_mode"] = "Painel Principal"
    st.rerun()

if st.sidebar.button("🚨 Ver AWBs Críticas em Destaque"):
    st.session_state["view_mode"] = "AWBs Criticas"
    st.rerun()

st.sidebar.markdown("---")

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
                    users_db[new_username] = {"name": new_name, "password": new_password, "role": new_role}
                    save_users(users_db)
                    st.success(f"Utilizador '{new_username}' cadastrado com sucesso!")
                else:
                    st.warning("Preencha todos os campos.")

st.title("🚚 Painel de Acompanhamento Diário - Rotas & AWBs")
st.markdown("---")

if st.session_state["user_info"]["role"] == "Supervisor":
    col_up1, col_up2 = st.columns([3, 1])
    with col_up1:
        uploaded_file = st.file_uploader("Faça o upload do ficheiro Excel (.xlsx) atualizado", type=["xlsx", "xls"])
    with col_up2:
        st.write("")
        st.write("")
        if st.button("🔄 Forçar Atualização"):
            st.cache_data.clear()
            st.rerun()

    if uploaded_file is not None:
        with st.spinner("Sincronizando e atualizando dados no GitHub..."):
            df_novo = pd.read_excel(uploaded_file)
            if salvar_historico_nuvem(df_novo):
                st.success("✅ Painel e histórico atualizados com sucesso!")
                time.sleep(1)
                st.rerun()

df = carregar_historico_nuvem()

if df is not None:
    df['Driver Name'] = df['Driver Name'].fillna('Sem Motorista Atribuído')
    df['Backlog time(Station)'] = df['Backlog time(Station)'].fillna(0).astype(int)
    df['Last scan type'] = df['Last scan type'].fillna('Não informado')
    df['Type'] = df['Type'].fillna('Outro')
    
    if 'Last scan time' in df.columns:
        df['Last scan time'] = pd.to_datetime(df['Last scan time'], errors='coerce')

    def categorizar_dias(dias):
        if dias == 0:
            return 'D0'
        elif dias == 1:
            return 'D1'
        elif dias == 2:
            return 'D2'
        elif dias == 3:
            return 'D3'
        else:
            return '> D3'

    df['Faixa Aging'] = df['Backlog time(Station)'].apply(categorizar_dias)

    cols_map = {
        'Waybill No': 'Número AWB',
        'Driver Name': 'Nome do Motorista',
        'Backlog time(Station)': 'Dias em Rota',
        'Faixa Aging': 'Faixa D0-D3',
        'Last scan type': 'Última Movimentação',
        'Last scan time': 'Data/Hora Último Scan',
        'Destination City': 'Cidade Destino',
        'Type': 'Status do Registro'
    }
    
    df_display = df[list(cols_map.keys())].rename(columns=cols_map)

    # --- FILTRO DE DATA NA BARRA LATERAL ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 Filtro por Período")
    
    if 'Data/Hora Último Scan' in df_display.columns and df_display['Data/Hora Último Scan'].notna().any():
        min_date = df_display['Data/Hora Último Scan'].min().date()
        max_date = df_display['Data/Hora Último Scan'].max().date()
        
        filtro_datas = st.sidebar
