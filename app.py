import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from datetime import datetime

st.set_page_config(
    page_title="Painel de Acompanhamento Diario",
    page_icon="🚚",
    layout="wide"
)

DATA_FILE = "dados_atuais.xlsx"
HISTORY_DIR = "historico_diario"

if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

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

    if 'Hora de Criação' in df.columns:
        df['Hora de Criação'] = pd.to_datetime(df['Hora de Criação'], errors='coerce')

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

# --- LOGIN ---
if not st.session_state["logged_in"]:
    st.title("Acesso - Painel de Rotas")
    st.markdown("---")
    col_a, col_b, col_c = st.columns([1, 2, 1])
    
    with col_b:
        if st.session_state["auth_mode"] == "login":
            with st.form("login_form"):
                st.subheader("Iniciar Sessao")
                username_input = st.text_input("Utilizador")
                password_input = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar"):
                    if username_input in users_db and users_db[username_input]["password"] == password_input:
                        st.session_state["logged_in"] = True
                        st.session_state["username_key"] = username_input
                        st.session_state["user_info"] = users_db[username_input]
                        st.rerun()
                    else:
                        st.error("Utilizador ou senha incorretos.")
            
            if st.button("Esqueci a senha"):
                st.session_state["auth_mode"] = "recuperar"
                st.rerun()

        elif st.session_state["auth_mode"] == "recuperar":
            with st.form("recovery_form"):
                st.subheader("Recuperacao")
                rec_user = st.text_input("Utilizador")
                rec_email = st.text_input("Email")
                rec_nova = st.text_input("Nova Senha", type="password")
                if st.form_submit_button("Redefinir"):
                    if rec_user in users_db and users_db[rec_user].get("email") == rec_email:
                        users_db[rec_user]["password"] = rec_nova
                        save_users(users_db)
                        st.success("Senha redefinida com sucesso!")
                        st.session_state["auth_mode"] = "login"
                        st.rerun()
                    else:
                        st.error("Dados incorretos.")
            if st.button("Voltar"):
                st.session_state["auth_mode"] = "login"
                st.rerun()
    st.stop()

# --- SIDEBAR ---
st.sidebar.title(f"Utilizador: {st.session_state['user_info']['name']}")
st.sidebar.caption(f"Perfil: {st.session_state['user_info']['role']}")

if st.sidebar.button("Sair / Logout"):
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("Navegacao")
if st.sidebar.button("Painel Principal"):
    st.session_state["view_mode"] = "Painel Principal"
    st.rerun()

if st.sidebar.button("Painel por Motorista"):
    st.session_state["view_mode"] = "Painel Motoristas"
    st.rerun()

if st.sidebar.button("Histórico de Dias"):
    st.session_state["view_mode"] = "Historico"
    st.rerun()

st.title("Painel de Acompanhamento Diario - Rotas e AWBs")
st.markdown("---")

# --- HISTÓRICO ---
if st.session_state["view_mode"] == "Historico":
    st.subheader("📚 Histórico de Fechamentos Diários")
    arquivos = sorted([f for f in os.listdir(HISTORY_DIR) if f.endswith('.xlsx')], reverse=True)
    if arquivos:
        sel = st.selectbox("Selecione o ficheiro:", options=arquivos)
        if sel:
            df_h = pd.read_excel(os.path.join(HISTORY_DIR, sel))
            st.success(f"Registos: {len(df_h)}")
            st.dataframe(df_h, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum histórico encontrado.")
    if st.button("⬅️ Voltar"):
        st.session_state["view_mode"] = "Painel Principal"
        st.rerun()

else:
    if st.session_state["user_info"]["role"] == "Supervisor":
        c1, c2 = st.columns([3, 1])
        with c1:
            up_file = st.file_uploader("Carregar Planilha (.xlsx)", type=["xlsx", "xls"])
            if up_file is not None:
                try:
                    df_r = pd.read_excel(up_file, sheet_name=0)
                    df_t = tratar_dataframe(df_r)
                    df_t.to_excel(DATA_FILE, index=False)
                    st.success("Planilha carregada!")
                except Exception as e:
                    st.error(f"Erro: {e}")
        with c2:
            st.write("")
            st.write("")
            with st.expander("🔒 Encerrar o Dia"):
                with st.form("form_arq"):
                    senha_c = st.text_input("Senha:", type="password")
                    if st.form_submit_button("Confirmar"):
                        u_key = st.session_state.get("username_key", "")
                        if u_key in users_db and users_db[u_key]["password"] == senha_c:
                            if os.path.exists(DATA_FILE):
                                dh = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                                os.rename(DATA_FILE, os.path.join(HISTORY_DIR, f"fechamento_{dh}.xlsx"))
                                st.success("Dia encerrado e sistema zerado!")
                                st.rerun()
                            else:
                                st.warning("Sem dados.")
                        else:
                            st.error("Senha incorreta.")

    df = None
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_excel(DATA_FILE)
            if 'Data/Hora Última Leitura' in df.columns:
                df['Data/Hora Última Leitura'] = pd.to_datetime(df['Data/Hora Última Leitura'], errors='coerce')
            if 'Hora de Criação' in df.columns:
                df['Hora de Criação'] = pd.to_datetime(df['Hora de Criação'], errors='coerce')
        except:
            df = None

    if df is not None and not df.empty:
        cols = ['Número AWB', 'Nome do Motorista', 'Último Status', 'Cidade Destino', 'Data/Hora Última Leitura', 'Hora de Criação']
        df_display = df[[c for c in cols if c in df.columns]]

        # --- FILTROS GLOBAIS ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("Filtros Globais")

        if 'Cidade Destino' in df_display.columns:
            cidades_disp = sorted(df_display['Cidade Destino'].astype(str).unique().tolist())
            cidades_sel = st.sidebar.multiselect("Cidade Destino:", options=cidades_disp, default=cidades_disp)
            if cidades_sel:
                df_display = df_display[df_display['Cidade Destino'].isin(cidades_sel)]

        if 'Último Status' in df_display.columns:
            status_disp = sorted(df_display['Último Status'].astype(str).unique().tolist())
            status_sel = st.sidebar.multiselect("Último Status:", options=status_disp, default=status_disp)
            if status_sel:
                df_display = df_display[df_display['Último Status'].isin(status_sel)]

        total_geral = len(df_display)
        total_entregue = len(df_display[df_display['Último Status'].str.lower() == 'entregue']) if 'Último Status' in df_display.columns else 0
        total
