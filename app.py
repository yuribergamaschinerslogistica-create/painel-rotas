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

# --- TELA DE LOGIN ---
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
                        st.session_state["username_key"] = username_input
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
                            st.error("O email informado nao confere com o registo.")
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

if st.sidebar.button("Ver Painel por Motorista"):
    st.session_state["view_mode"] = "Painel Motoristas"
    st.rerun()

if st.sidebar.button("Ver Histórico de Dias Anteriores"):
    st.session_state["view_mode"] = "Historico"
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
            new_role = st.selectbox("Perfil", ["Operador", "Supervisor"])
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
                    st.warning("Preencha os campos obrigatorios.")

st.title("Painel de Acompanhamento Diario - Rotas e AWBs")
st.markdown("---")

# --- TELA: HISTÓRICO DE DIAS ANTERIORES ---
if st.session_state["view_mode"] == "Historico":
    st.subheader("📚 Histórico de Fechamentos Diários")
    st.markdown("Consulte os dados salvos de dias anteriores:")
    st.markdown("---")
    
    arquivos_historico = sorted([f for f in os.listdir(HISTORY_DIR) if f.endswith('.xlsx')], reverse=True)
    
    if arquivos_historico:
        arq_selecionado = st.selectbox("Selecione a data/ficheiro anterior:", options=arquivos_historico)
        if arq_selecionado:
            df_hist = pd.read_excel(os.path.join(HISTORY_DIR, arq_selecionado))
            st.success(f"Visualizando dados do ficheiro: {arq_selecionado} (Total de registos: {len(df_hist)})")
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum histórico diário arquivado até o momento.")
        
    st.markdown("---")
    if st.button("⬅️ Voltar ao Painel Principal"):
        st.session_state["view_mode"] = "Painel Principal"
        st.rerun()

else:
    df = None
    if st.session_state["user_info"]["role"] == "Supervisor":
        col_up1, col_up2 = st.columns([3, 1])
        with col_up1:
            uploaded_file = st.file_uploader("Faca o upload da nova planilha (.xlsx)", type=["xlsx", "xls"])
            if uploaded_file is not None:
                try:
                    df_raw = pd.read_excel(uploaded_file, sheet_name=0)
                    df = tratar_dataframe(df_raw)
                    df.to_excel(DATA_FILE, index=False)
                    st.success("Planilha carregada e processada com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao processar o ficheiro: {e}")
        
        with col_up2:
            st.write("")
            st.write("")
            with st.expander("🔒 Encerrar o Dia / Arquivar"):
                with st.form("form_arquivar_dia"):
                    st.warning("Esta acao vai arquivar o dia atual e limpar a tela para o dia seguinte.")
                    senha_confirmacao = st.text_input("Digite a sua senha para confirmar:", type="password")
                    btn_confirma_arq = st.form_submit_button("Confirmar Fechamento")
                    
                    if btn_confirma_arq:
                        user_key = st.session_state.get("username_key", "")
                        if user_key in users_db and users_db[user_key]["password"] == senha_confirmacao:
                            if os.path.exists(DATA_FILE):
                                data_hoje = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                                destino_hist = os.path.join(HISTORY_DIR, f"fechamento_{data_hoje}.xlsx")
                                os.rename(DATA_FILE, destino_hist)
                                st.success("Dia encerrado! Dados arquivados com sucesso e sistema zerado.")
                                st.rerun()
                            else:
                                st.warning("Não há dados ativos para arquivar.")
                        else:
                            st.error("Senha incorreta. Fechamento cancelado.")

    if df is None and os.path.exists(DATA_FILE):
        try:
            df = pd.read_excel(DATA_FILE)
            if 'Data/Hora Última Leitura' in df.columns:
                df['Data/Hora Última Leitura'] = pd.to_datetime(df['Data/Hora Última Leitura'], errors='coerce')
            if 'Hora de Criação' in df.columns:
                df['Hora de Criação'] = pd.to_datetime(df['Hora de Criação'], errors='coerce')
        except Exception:
            df = None

    if df is not None and not df.empty:
        cols_desejadas = ['Número AWB', 'Nome do Motorista', 'Último Status', 'Cidade Destino', 'Data/Hora Última Leitura', 'Hora de Criação']
        cols_existentes = [c for c in cols_desejadas if c in df.columns]
        df_display = df[cols_existentes]

        total_geral = len(df_display)
        total_entregue = len(df_display[df_display['Último Status'].str.lower() == 'entregue']) if 'Último Status' in df_display.columns else 0
        total_em_rota = len(df_display[df_display['Último Status'].str.lower() == 'em rota de entrega']) if 'Último Status' in df_display.columns else 0
        total_insucesso = total_geral - (total_entregue + total_em_rota)
        
        pct_entregue = (total_entregue / total_geral * 100) if total_geral > 0 else 0.0
        pct_em_rota = (total_em_rota / total_geral * 100) if total_geral > 0 else 0.0
        pct_insucesso = (total_insucesso / total_geral * 100) if total_geral > 0 else 0.0

        sla_geral = pct_entregue
        otif = pct_entregue

        oct_medio = 0.0
        if 'Hora de Criação' in df.columns and 'Data/Hora Última Leitura' in df.columns:
            df_entregues_oct = df[(df['Último Status'].str.lower() == 'entregue') & df['Hora de Criação'].notna() & df['Data/Hora Última Leitura'].notna()]
            if not df_entregues_oct.empty:
                diferencas = (df_entregues_oct['Data/Hora Última Leitura'] - df_entregues_oct['Hora de Criação']).dt.total_seconds() / 86400.0
                oct_medio = diferencas.mean()

        # --- TELA: PAINEL POR MOTORISTA ---
        if st.session_state["view_mode"] == "Painel Motoristas":
            st.subheader("Painel Individual por Motorista")
            st.markdown("Pesquise pelo nome do motorista ou clique nos status para detalhar as AWBs:")
            
            busca_motorista = st.text_input("🔍 Digite o nome do motorista para localizar:", placeholder="Ex: Rodrigo")
            st.markdown("---")

            df_motoristas = df_display[df_display['Nome do Motorista'] != 'Sem Motorista Atribuido']
            
            if busca_motorista:
                df_motoristas = df_motoristas[df_motoristas['Nome do Motorista'].astype(str).str.contains(busca_motorista, case=False, na=False)]

            lista_motoristas = sorted(df_motoristas['Nome do Motorista'].unique().tolist())

            if lista_motoristas:
                cols_per_row = 3
                for i in range(0, len(lista_motoristas), cols_per_row):
                    row_cols = st.columns(cols_per_row)
                    for j in range(cols_per_row):
                        if i + j < len(lista_motoristas):
                            motorista = lista_motoristas[i + j]
                            df_mot = df_motoristas[df_motoristas['Nome do Motorista'] == motorista]
                            
                            m_entregue = len(df_mot[df_mot['Último Status'].str.lower() == 'entregue'])
                            m_em_rota = len(df_mot[df_mot['Último Status'].str.lower() == 'em rota de entrega'])
                            m_anormal = len(df_mot) - (m_entregue + m_em_rota)
                            
                            with row_cols[j]:
                                with st.container(border=True):
                                    st.markdown(f"**{motorista}**")
                                    
                                    df_pie = pd.DataFrame({
                                        'Status': ['Entregue', 'Em rota', 'Outros/Anormal'],
                                        'Quantidade': [m_entregue, m_em_rota, m_anormal]
                                    })
                                    fig_donut = px.pie(
                                        df_pie, 
                                        names='Status', 
                                        values='Quantidade', 
                                        hole=0.6,
                                        color='Status',
                                        color_discrete_map={
                                            'Entregue': '#28a745', 
                                            'Em rota': '#ffc107', 
                                            'Outros/Anormal': '#dc3545'
                                        }
                                    )
                                    fig_donut.update_traces(textinfo='value', textfont_size=12, showlegend=False)
