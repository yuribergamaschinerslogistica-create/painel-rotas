import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

st.set_page_config(
    page_title="Painel de Acompanhamento Diario",
    page_icon="🚚",
    layout="wide"
)

DATA_FILE = "dados_atuais.xlsx"

def tratar_dataframe(df_raw):
    df = df_raw.copy()
    df.columns = df.columns.str.strip()
    
    if 'Número da Etiqueta' in df.columns:
        df['Número AWB'] = df['Número da Etiqueta'].astype(str)
    elif 'Waybill No' in df.columns:
        df['Número AWB'] = df['Waybill No'].astype(str)
    else:
        df['Número AWB'] = 'Nao informado'

    if 'Motorista' in df.columns:
        df['Nome do Motorista'] = df['Motorista']
    elif 'Driver Name' in df.columns:
        df['Nome do Motorista'] = df['Driver Name']
    else:
        df['Nome do Motorista'] = 'Sem Motorista Atribuido'
    df['Nome do Motorista'] = df['Nome do Motorista'].fillna('Sem Motorista Atribuido')

    if 'Último status' in df.columns:
        df['Último Status'] = df['Último status']
    elif 'Last scan type' in df.columns:
        df['Último Status'] = df['Last scan type']
    else:
        df['Último Status'] = 'Nao informado'
    df['Último Status'] = df['Último Status'].fillna('Nao informado')

    if 'Cidade destinatária' in df.columns:
        df['Cidade Destino'] = df['Cidade destinatária']
    elif 'Destination City' in df.columns:
        df['Cidade Destino'] = df['Destination City']
    else:
        df['Cidade Destino'] = 'Nao informada'
    df['Cidade Destino'] = df['Cidade Destino'].fillna('Nao informada')

    if 'Horário da última leitura' in df.columns:
        df['Data/Hora Última Leitura'] = pd.to_datetime(df['Horário da última leitura'], errors='coerce')
    elif 'Last scan time' in df.columns:
        df['Data/Hora Última Leitura'] = pd.to_datetime(df['Last scan time'], errors='coerce')
    else:
        df['Data/Hora Última Leitura'] = pd.NaT

    return df

USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        default_users = {
            "admin": {
                "name": "Supervisor Geral", 
                "password": "admin", 
                "role": "Supervisor",
                "email": "admin@logistica.com",
                "phone": "000000000"
            },
            "operador": {
                "name": "Operador Padrao", 
                "password": "123", 
                "role": "Operador",
                "email": "operador@logistica.com",
                "phone": "111111111"
            }
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

if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "login"

# --- TELA DE LOGIN / RECUPERACAO ---
if not st.session_state["logged_in"]:
    st.title("Acesso - Painel de Rotas")
    st.markdown("---")
    col_a, col_b, col_c = st.columns([1, 2, 1])
    
    with col_b:
        if st.session_state["auth_mode"] == "login":
            with st.form("login_form"):
                st.subheader("Iniciar Sessao")
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
            
            if st.button("Esqueci a minha senha / Recuperar Acesso"):
                st.session_state["auth_mode"] = "recuperar"
                st.rerun()

        elif st.session_state["auth_mode"] == "recuperar":
            with st.form("recovery_form"):
                st.subheader("Recuperacao de Senha")
                rec_username = st.text_input("Digite o seu Utilizador / Login")
                rec_email = st.text_input("Digite o seu Email cadastrado")
                rec_nova_senha = st.text_input("Defina uma Nova Senha", type="password")
                submit_rec = st.form_submit_button("Redefinir Senha")
                
                if submit_rec:
                    if rec_username in users_db:
                        if users_db[rec_username].get("email") == rec_email:
                            users_db[rec_username]["password"] = rec_nova_senha
                            save_users(users_db)
                            st.success("Senha redefinida com sucesso! Faca login com a nova senha.")
                            st.session_state["auth_mode"] = "login"
                            st.rerun()
                        else:
                            st.error("O email informado nao confere com o registo deste utilizador.")
                    else:
                        st.error("Utilizador nao encontrado.")
            
            if st.button("Voltar ao Login"):
                st.session_state["auth_mode"] = "login"
                st.rerun()
                
    st.stop()

# --- SIDEBAR ---
st.sidebar.title(f"Utilizador: {st.session_state['user_info']['name']}")
st.sidebar.caption(f"Perfil: {st.session_state['user_info']['role']}")

if st.sidebar.button("Sair / Logout"):
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None
    st.session_state["view_mode"] = "Painel Principal"
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("Navegacao")
if st.sidebar.button("Ver Painel Principal"):
    st.session_state["view_mode"] = "Painel Principal"
    st.rerun()

if st.sidebar.button("Ver Painel Individual por Motorista"):
    st.session_state["view_mode"] = "Painel Motoristas"
    st.rerun()

if st.sidebar.button("Ver AWBs Criticas em Destaque"):
    st.session_state["view_mode"] = "AWBs Criticas"
    st.rerun()

st.sidebar.markdown("---")

if st.session_state["user_info"]["role"] == "Supervisor":
    with st.sidebar.expander("Cadastrar Novo Utilizador"):
        with st.form("new_user_form"):
            new_username = st.text_input("Login (Utilizador)")
            new_name = st.text_input("Nome Completo")
            new_email = st.text_input("Email")
            new_phone = st.text_input("Telefone")
            new_password = st.text_input("Senha Inicial", type="password")
            new_role = st.selectbox("Perfil de Acesso", ["Operador", "Supervisor"])
            create_btn = st.form_submit_button("Guardar Utilizador")
            
            if create_btn:
                if new_username and new_password and new_name and new_email:
                    users_db[new_username] = {
                        "name": new_name, 
                        "password": new_password, 
                        "role": new_role,
                        "email": new_email,
                        "phone": new_phone
                    }
                    save_users(users_db)
                    st.success(f"Utilizador '{new_username}' cadastrado com sucesso!")
                else:
                    st.warning("Preencha os campos obrigatorios (Login, Nome, Email e Senha).")

st.title("Painel de Acompanhamento Diario - Rotas e AWBs")
st.markdown("---")

if st.session_state["user_info"]["role"] == "Supervisor":
    col_up1, col_up2 = st.columns([3, 1])
    with col_up1:
        uploaded_file = st.file_uploader("Faca o upload da nova planilha (.xlsx) para partilhar com a equipa", type=["xlsx", "xls"])
        if uploaded_file is not None:
            try:
                df_raw = pd.read_excel(uploaded_file, sheet_name=0)
                df_tratado = tratar_dataframe(df_raw)
                df_tratado.to_excel(DATA_FILE, index=False)
                st.success("Planilha carregada e partilhada com todos os utilizadores online!")
                st
