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

if st.sidebar.button("Ver AWBs Criticas"):
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

if st.session_state["user_info"]["role"] == "Supervisor":
    col_up1, col_up2 = st.columns([3, 1])
    with col_up1:
        uploaded_file = st.file_uploader("Faca o upload da nova planilha (.xlsx) para partilhar", type=["xlsx", "xls"])
        if uploaded_file is not None:
            try:
                df_raw = pd.read_excel(uploaded_file, sheet_name=0)
                df_tratado = tratar_dataframe(df_raw)
                df_tratado.to_excel(DATA_FILE, index=False)
                st.success("Planilha carregada e partilhada com todos os utilizadores online!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao processar o ficheiro: {e}")
    with col_up2:
        st.write("")
        st.write("")
        if st.button("Limpar Dados"):
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            st.success("Dados limpos!")
            st.rerun()

df = None
if os.path.exists(DATA_FILE):
    try:
        df = pd.read_excel(DATA_FILE)
        if 'Data/Hora Última Leitura' in df.columns:
            df['Data/Hora Última Leitura'] = pd.to_datetime(df['Data/Hora Última Leitura'], errors='coerce')
    except Exception:
        df = None

if df is not None and not df.empty:
    cols_desejadas = ['Número AWB', 'Nome do Motorista', 'Último Status', 'Cidade Destino', 'Data/Hora Última Leitura']
    cols_existentes = [c for c in cols_desejadas if c in df.columns]
    df_display = df[cols_existentes]

    total_geral = len(df_display)
    total_entregue = len(df_display[df_display['Último Status'].str.lower() == 'entregue']) if 'Último Status' in df_display.columns else 0
    total_em_rota = len(df_display[df_display['Último Status'].str.lower() == 'em rota de entrega']) if 'Último Status' in df_display.columns else 0
    total_insucesso = total_geral - (total_entregue + total_em_rota)
    
    # Cálculo do SLA Geral (Percentagem de Entregues sobre o Total)
    sla_geral = (total_entregue / total_geral * 100) if total_geral > 0 else 0.0

    # --- TELA: PAINEL POR MOTORISTA COM BUSCA E FILTRO DE STATUS ---
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
                                fig_donut.update_layout(
                                    margin=dict(t=5, b=5, l=5, r=5),
                                    height=180,
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    plot_bgcolor='rgba(0,0,0,0)'
                                )
                                st.plotly_chart(fig_donut, use_container_width=True, key=f"donut_{i+j}")
                                
                                status_clique = st.selectbox(
                                    f"Ver AWBs de {motorista}:",
                                    options=["Selecionar...", "Entregue", "Em rota de entrega", "Outros/Anormal"],
                                    key=f"sel_{i+j}"
                                )
                                
                                if status_clique == "Entregue":
                                    df_detalhe = df_mot[df_mot['Último Status'].str.lower() == 'entregue']
                                    st.dataframe(df_detalhe[['Número AWB', 'Último Status', 'Cidade Destino']], use_container_width=True, hide_index=True)
                                elif status_clique == "Em rota de entrega":
                                    df_detalhe = df_mot[df_mot['Último Status'].str.lower() == 'em rota de entrega']
                                    st.dataframe(df_detalhe[['Número AWB', 'Último Status', 'Cidade Destino']], use_container_width=True, hide_index=True)
                                elif status_clique == "Outros/Anormal":
                                    df_detalhe = df_mot[~df_mot['Último Status'].str.lower().isin(['entregue', 'em rota de entrega'])]
                                    st.dataframe(df_detalhe[['Número AWB', 'Último Status', 'Cidade Destino']], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum motorista encontrado com este nome.")

        st.markdown("---")
        if st.button("Voltar ao Painel Principal"):
            st.session_state["view_mode"] = "Painel Principal"
            st.rerun()

    else:
        # --- FILTROS NA SIDEBAR ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("Filtros Globais")

        if 'Cidade Destino' in df_display.columns:
            cidades_disponiveis = sorted(df_display['Cidade Destino'].astype(str).unique().tolist())
            cidades_selecionadas = st.sidebar.multiselect(
                "Cidade Destino:",
                options=cidades_disponiveis,
                default=cidades_disponiveis
            )
            if cidades_selecionadas:
                df_display = df_display[df_display['Cidade Destino'].isin(cidades_selecionadas)]

        if 'Último Status' in df_display.columns:
            status_disponiveis = sorted(df_display['Último Status'].astype(str).unique().tolist())
            status_selecionados = st.sidebar.multiselect(
                "Último Status:",
                options=status_disponiveis,
                default=status_disponiveis
            )
            if status_selecionados:
                df_display = df_display[df_display['Último Status'].isin(status_selecionados)]

        if total_geral > 0:
            pct_entregue = (total_entregue / total_geral) * 100
            pct_em_rota = (total_em_rota / total_geral) * 100
