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
    df['Driver Name'] = df['Driver Name'].fillna('Sem Motorista Atribuído')
    df['Backlog time(Station)'] = df['Backlog time(Station)'].fillna(0).astype(int)
    df['Last scan type'] = df['Last scan type'].fillna('Não informado')
    df['Type'] = df['Type'].fillna('Outro')
    
    if 'Last scan time' in df.columns:
        df['Last scan time'] = pd.to_datetime(df['Last scan time'], errors='coerce')

    df['Faixa Aging'] = df['Backlog time(Station)'].apply(categorizar_dias)
    return df

# Carregamento rápido com cache local em sessão
def carregar_historico():
    if "df_cached" in st.session_state and st.session_state["df_cached"] is not None:
        return st.session_state["df_cached"]

    repo = get_github_repo()
    if repo:
        try:
            file_content = repo.get_contents(HISTORY_FILE_PATH)
            decoded_content = file_content.decoded_content
            df = pd.read_excel(io.BytesIO(decoded_content))
            df_tratado = tratar_dataframe(df)
            st.session_state["df_cached"] = df_tratado
            return df_tratado
        except Exception:
            pass
    return None

def sincronizar_github(df_combinado):
    repo = get_github_repo()
    if repo:
        try:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_combinado.to_excel(writer, index=False)
            file_bytes = output.getvalue()

            timestamp_str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

            try:
                contents = repo.get_contents(HISTORY_FILE_PATH)
                repo.update_file(
                    path=HISTORY_FILE_PATH,
                    message=f"Sync rápido: {timestamp_str}",
                    content=file_bytes,
                    sha=contents.sha
                )
            except Exception:
                repo.create_file(
                    path=HISTORY_FILE_PATH,
                    message=f"Criação histórico: {timestamp_str}",
                    content=file_bytes
                )
        except Exception as e:
            st.error(f"Erro ao salvar no GitHub: {e}")

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
        if st.button("🔄 Recarregar Nuvem"):
            st.session_state["df_cached"] = None
            st.rerun()

    if uploaded_file is not None:
        df_novo = pd.read_excel(uploaded_file)
        df_novo_tratado = tratar_dataframe(df_novo)
        
        df_atual = carregar_historico()
        if df_atual is not None:
            df_combinado = pd.concat([df_atual, df_novo_tratado]).drop_duplicates(subset=['Waybill No'], keep='last')
        else:
            df_combinado = df_novo_tratado

        st.session_state["df_cached"] = df_combinado
        sincronizar_github(df_combinado)
        st.success("⚡ Dados atualizados em tempo recorde!")

df = carregar_historico()

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

    # --- FILTRO DE DATA NA BARRA LATERAL ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 Filtro por Período")
    
    if 'Data/Hora Último Scan' in df_display.columns and df_display['Data/Hora Último Scan'].notna().any():
        min_date = df_display['Data/Hora Último Scan'].min().date()
        max_date = df_display['Data/Hora Último Scan'].max().date()
        
        filtro_datas = st.sidebar.date_input(
            "Selecione o intervalo de datas:",
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

    # --- VERIFICAÇÃO DO MODO DE EXIBIÇÃO NO CENTRO DA TELA ---
    if st.session_state["view_mode"] == "AWBs Criticas":
        st.subheader("🚨 Listagem Completa de AWBs Críticas (>3 Dias em Rota)")
        st.markdown("Aqui estão centralizadas todas as encomendas críticas que ultrapassaram 3 dias em rota:")
        
        pesquisa_central = st.text_input("🔍 Pesquisar por número da AWB ou Motorista na lista crítica:")
        df_filtrada_criticas = df_criticas
        if pesquisa_central:
            df_filtrada_criticas = df_criticas[
                df_criticas['Número AWB'].astype(str).str.contains(pesquisa_central, case=False, na=False) |
                df_criticas['Nome do Motorista'].str.contains(pesquisa_central, case=False, na=False)
            ]
        
        st.dataframe(
            df_filtrada_criticas[['Número AWB', 'Nome do Motorista', 'Faixa D0-D3', 'Dias em Rota', 'Cidade Destino', 'Última Movimentação', 'Data/Hora Último Scan']],
            use_container_width=True,
            hide_index=True
        )
        
        if st.button("⬅️ Voltar ao Painel Principal"):
            st.session_state["view_mode"] = "Painel Principal"
            st.rerun()
            
    else:
        # --- CAMPO DE BUSCA GLOBAL DE AWB NO TOPO ---
        st.markdown("### 🔍 Pesquisa Rápida de AWB")
        busca_global = st.text_input("Digite o número da AWB para localizar instantaneamente:", placeholder="Ex: 3320108174832")
        
        if busca_global:
            df_resultado_busca = df_display[df_display['Número AWB'].astype(str).str.contains(busca_global, case=False, na=False)]
            if len(df_resultado_busca) > 0:
                st.success(f"Encontrado(s) {len(df_resultado_busca)} registo(s) para a AWB pesquisada:")
                st.dataframe(
                    df_resultado_busca[['Número AWB', 'Nome do Motorista', 'Status do Registro', 'Faixa D0-D3', 'Dias em Rota', 'Cidade Destino', 'Última Movimentação', 'Data/Hora Último Scan']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("Nenhuma AWB encontrada com este número no histórico.")
            st.markdown("---")

        # Indicadores principais (KPIs)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de AWBs (Histórico)", len(df_display))
        col2.metric("Motoristas Ativos", df_display[df_display['Nome do Motorista'] != 'Sem Motorista Atribuído']['Nome do Motorista'].nunique())
        col3.metric("Média de Dias em Rota", f"{df_display['Dias em Rota'].mean():.1f} dias")
        col4.metric("AWBs Críticas (>3 dias)", len(df_criticas))
        
        st.markdown("---")

        # --- PAINEL DE AGING / DISTRIBUIÇÃO D0, D1, D2, D3, > D3 ---
        st.subheader("⏱️ Distribuição de Entregas por Antiguidade (Aging D0 a >D3)")
        
        c_d0, c_d1, c_d2, c_d3, c_d_critico = st.columns(5)
        c_d0.metric("D0 (0 Dias)", len(df_display[df_display['Faixa D0-D3'] == 'D0']))
        c_d1.metric("D1 (1 Dia)", len(df_display[df_display['Faixa D0-D3'] == 'D1']))
        c_d2.metric("D2 (2 Dias)", len(df_display[df_display['Faixa D0-D3'] == 'D2']))
        c_d3.metric("D3 (3 Dias)", len(df_display[df_display['Faixa D0-D3'] == 'D3']))
        c_d_critico.metric("> D3 (Críticas)", len(df_display[df_display['Faixa D0-D3'] == '> D3']))

        with st.expander("📋 Filtrar Tabela por Faixa de Aging (D0, D1, D2, D3, >D3)"):
            faixas_selecionadas = st.multiselect(
                "Selecione a(s) faixa(s) que pretende visualizar:",
                options=['D0', 'D1', 'D2', 'D3', '> D3'],
                default=['D0', 'D1', 'D2', 'D3', '> D3']
            )
            if faixas_selecionadas:
                df_aging_filtrado = df_display[df_display['Faixa D0-D3'].isin(faixas_selecionadas)]
                st.dataframe(
                    df_aging_filtrado[['Número AWB', 'Nome do Motorista', 'Faixa D0-D3', 'Dias em Rota', 'Status do Registro', 'Cidade Destino', 'Última Movimentação', 'Data/Hora Último Scan']],
                    use_container_width=True,
                    hide_index=True
                )

        st.markdown("---")

        # --- SEÇÃO DE GRÁFICOS E DETALHAMENTO ---
        st.subheader("📊 Análise Visual & Detalhamento por Motorista")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "AWBs em Aberto por Motorista", 
            "Volume Total de AWBs por Motorista", 
            "Média de Dias em Rota por Motorista",
            "Aging por Motorista (D0 a >D3)"
        ])
        
        df_motoristas = df_display[df_display['Nome do Motorista'] != 'Sem Motorista Atribuído']
        
        with tab1:
            df_aberto = df_motoristas[df_motoristas['Status do Registro'].str.lower() == 'em aberto']
            awb_aberto_per_driver = df_aberto['Nome do Motorista'].value_counts().reset_index()
            awb_aberto_
