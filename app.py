import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
import io
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

def carregar_historico_nuvem():
    repo = get_github_repo()
    if repo:
        try:
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
            df_atual = carregar_historico_nuvem()
            if df_atual is not None:
                df_combinado = pd.concat([df_atual, df_novo]).drop_duplicates(subset=['Waybill No'], keep='last')
            else:
                df_combinado = df_novo

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_combinado.to_excel(writer, index=False)
            file_bytes = output.getvalue()

            try:
                contents = repo.get_contents(HISTORY_FILE_PATH)
                repo.update_file(
                    path=HISTORY_FILE_PATH,
                    message="Atualização e acumulação de histórico pelo supervisor",
                    content=file_bytes,
                    sha=contents.sha
                )
            except Exception:
                repo.create_file(
                    path=HISTORY_FILE_PATH,
                    message="Criação inicial do histórico mensal",
                    content=file_bytes
                )
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
    st.rerun()

st.sidebar.markdown("---")

if st.session_state["user_info"]["role"] == "Supervisor":
    with st.sidebar.expander("➕ Cadastrar Novo Utilizador"):
        with st.form("new_user_form"):
            new_username = st.text_input("Novo Login")
            new_name = st.text_input("Nome Completo")
            new_password = st.text_input("Nova Senha", type="password")
            new_role = st.selectbox("Perfil de A
