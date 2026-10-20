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

DATA_FILE = "dados_atuais.xlsx"

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
            "admin": {
                "name": "Supervisor Geral", 
                "password": "admin", 
                "role": "Supervisor",
                "email": "admin@logistica.com",
                "phone": "000000000"
            },
            "operador": {
                "name": "Operador Padrão", 
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

# --- TELA DE LOGIN / RECUPERAÇÃO ---
if not st.session_state["logged_in"]:
    st.title("🔐 Acesso - Painel de Rotas")
    st.markdown("---")
    col_a, col_b, col_c = st.columns([1, 2, 1])
    
    with col_b:
        if st.session_state["auth_mode"] == "login":
            with st.form("login_form"):
                st.subheader("Iniciar Sessão")
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
            
            if st.button("🔄 Esqueci a minha senha / Recuperar Acesso"):
                st.session_state["auth_mode"] = "recuperar"
                st.rerun()

        elif st.session_state["auth_mode"] == "recuperar":
            with st.form("recovery_form"):
                st.subheader("🔑 Recuperação de Senha")
                rec_username = st.text_input("Digite o seu Utilizador / Login")
                rec_email = st.text_input("Digite o seu Email cadastrado")
                rec_nova_senha = st.text_input("Defina uma Nova Senha", type="password")
                submit_rec = st.form_submit_button("Redefinir Senha")
                
                if submit_rec:
                    if rec_username in users_db:
                        if users_db[rec_username].get("email") == rec_email:
                            users_db[rec_username]["password"] = rec_nova_senha
                            save_users(users_db)
                            st.success("Senha redefinida com sucesso! Faça login com a nova senha.")
                            st.session_state["auth_mode"] = "login"
                            st.rerun()
                        else:
                            st.error("O email informado não confere com o registo deste utilizador.")
                    else:
                        st.error("Utilizador não encontrado.")
            
            if st.button("⬅️ Voltar ao Login"):
                st.session_state["auth_mode"] = "login"
                st.rerun()
                
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
                    st.warning("Preencha os campos obrigatórios (Login, Nome, Email e Senha).")

st.title("🚚 Painel de Acompanhamento Diário - Rotas & AWBs")
st.markdown("---")

if st.session_state["user_info"]["role"] == "Supervisor":
    col_up1, col_up2 = st.columns([3, 1])
    with col_up1:
        uploaded_file = st.file_uploader("Faça o upload do ficheiro Excel (.xlsx) para partilhar com a equipa", type=["xlsx", "xls"])
        if uploaded_file is not None:
            df_raw = pd.read_excel(uploaded_file)
            df_tratado = tratar_dataframe(df_raw)
            df_tratado.to_excel(DATA_FILE, index=False)
            st.success("⚡ Planilha carregada e partilhada com todos os utilizadores online!")
    with col_up2:
        st.write("")
        st.write("")
        if st.button("🗑️ Limpar Dados Partilhados"):
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            st.success("Dados limpos para toda a equipa!")
            st.rerun()

# Carrega os dados partilhados do servidor ou do ficheiro gravado
df = None
if os.path.exists(DATA_FILE):
    try:
        df = pd.read_excel(DATA_FILE)
        if 'Last scan time' in df.columns:
            df['Last scan time'] = pd.to_datetime(df['Last scan time'], errors='coerce')
    except Exception:
        df = None

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
        st.subheader("🚨 Listagem Completa de AWBs Críticas (>3 Dias em Rota)")
        st.markdown("Aqui estão centralizadas todas as encomendas críticas que ultrapassaram 3 dias em rota:")
        
        pesquisa_central = st.text_input("🔍 Pesquisar por número da AWB ou Motorista na lista crítica:")
        df_filtrada_criticas = df_criticas
        if pesquisa_central:
            df_filtrada_criticas = df_criticas[
                df_criticas['Número AWB'].astype(str).str.contains(pesquisa_central, case=False, na=False) |
                df_filtrada_criticas['Nome do Motorista'].str.contains(pesquisa_central, case=False, na=False)
            ]
        
        st.dataframe(
