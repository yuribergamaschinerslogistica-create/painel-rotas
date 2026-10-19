import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

st.set_page_config(
    page_title="Painel de Acompanhamento Diário",
    page_icon="🚚",
    layout="wide"
)

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

def tratar_dataframe(df_raw):
    df = df_raw.copy()
    df.columns = df.columns.str.strip()
    
    if 'Waybill No' not in df.columns:
        for col in df.columns:
            if 'waybill' in col.lower() or 'awb' in col.lower():
                df = df.rename(columns={col: 'Waybill No'})
                break

    df['Driver Name'] = df['Driver Name'] if 'Driver Name' in df.columns else 'Sem Motorista Atribuído'
    df['Driver Name'] = df['Driver Name'].fillna('Sem Motorista Atribuído')

    df['Backlog time(Station)'] = df['Backlog time(Station)'] if 'Backlog time(Station)' in df.columns else 0
    df['Backlog time(Station)'] = df['Backlog time(Station)'].fillna(0).astype(int)

    df['Last scan type'] = df['Last scan type'] if 'Last scan type' in df.columns else 'Não informado'
    df['Last scan type'] = df['Last scan type'].fillna('Não informado')

    df['Type'] = df['Type'] if 'Type' in df.columns else 'Outro'
    df['Type'] = df['Type'].fillna('Outro')

    df['Destination City'] = df['Destination City'] if 'Destination City' in df.columns else 'Não informada'
    df['Destination City'] = df['Destination City'].fillna('Não informada')
    
    if 'Last scan time' in df.columns:
        df['Last scan time'] = pd.to_datetime(df['Last scan time'], errors='coerce')

    df['Faixa Aging'] = df['Backlog time(Station)'].apply(categorizar_dias)
    return df

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

# --- LOGIN ---
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

# --- SIDEBAR ---
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

df = None

if st.session_state["user_info"]["role"] == "Supervisor":
    uploaded_file = st.file_uploader("Faça o upload do ficheiro Excel (.xlsx) para iniciar", type=["xlsx", "xls"])
    if uploaded_file is not None:
        df_raw = pd.read_excel(uploaded_file)
        df = tratar_dataframe(df_raw)
        st.session_state["df_temp"] = df
    elif "df_temp" in st.session_state:
        df = st.session_state["df_temp"]
else:
    if "df_temp" in st.session_state:
        df = st.session_state["df_temp"]

if df is not None:
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
    
    cols_existentes = [c for c in cols_map.keys() if c in df.columns]
    df_display = df[cols_existentes].rename(columns=cols_map)

    # --- FILTROS NA SIDEBAR ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Filtros Globais")

    # 1. Filtro por Cidade Destino
    if 'Cidade Destino' in df_display.columns:
        cidades_disponiveis = sorted(df_display['Cidade Destino'].astype(str).unique().tolist())
        cidades_selecionadas = st.sidebar.multiselect(
            "📍 Filtrar por Cidade Destino:",
            options=cidades_disponiveis,
            default=cidades_disponiveis
        )
        if cidades_selecionadas:
            df_display = df_display[df_display['Cidade Destino'].isin(cidades_selecionadas)]

    # 2. Filtro por Intervalo de Datas
    if 'Data/Hora Último Scan' in df_display.columns and df_display['Data/Hora Último Scan'].notna().any():
        min_date = df_display['Data/Hora Último Scan'].min().date()
        max_date = df_display['Data/Hora Último Scan'].max().date()
        
        filtro_datas = st.sidebar.date_input(
            "📅 Selecione o intervalo de datas:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        if isinstance(filtro_datas, tuple) and len(filtro_datas) == 2:
            start_d, end_d = filtro_datas
            df_display = df_display[
                (df_display['Data/Hora Último Scan'].dt.date >= start_d) & 
                (df_display['Data/Hora Último Scan'].dt.date <= end_d)
            ]

    df_criticas = df_display[df_display['Dias em Rota'] > 3]

    if st.session_state["view_mode"] == "AWBs Criticas":
        st.subheader("🚨
