import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
import io
import time
from github import Github
from datetime import datetime

st.set_page_config(
    page_title="Painel de Acompanhamento Diário",
    page_icon="🚚",
    layout="wide"
)

REPO_NAME = "yuribergamaschinerslogistica-create/painel-rotas"
HISTORY_FILE_PATH = "historico_mes.xlsx"

def get_github_repo():
    try:
        if "GITHUB_TOKEN" in st.secrets:
            g = Github(st.secrets["GITHUB_TOKEN"])
            return g.get_repo(REPO_NAME)
    except Exception as e:
        pass
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

if "df_ativo" not in st.session_state:
    st.session_state["df_ativo"] = None

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
    st.session_state["df_ativo"] = None
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
        if st.button("🔄 Forçar Limpeza / Reset"):
            # Limpa de forma absoluta a sessão
            st.session_state["df_ativo"] = "RESETADO"
            
            # Remove o ficheiro do GitHub para evitar recarga fantasma
            repo = get_github_repo()
            if repo:
                try:
                    contents = repo.get_contents(HISTORY_FILE_PATH)
                    repo.delete_file(HISTORY_FILE_PATH, "Reset completo", contents.sha)
                except Exception:
                    pass
            
            st.success("Painel limpo com sucesso!")
            time.sleep(0.5)
            st.rerun()

    if uploaded_file is not None:
        df_novo = pd.read_excel(uploaded_file)
        df_tratado = tratar_dataframe(df_novo)
        st.session_state["df_ativo"] = df_tratado
        
        # Sincroniza o novo ficheiro no GitHub
        repo = get_github_repo()
        if repo:
            try:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_tratado.to_excel(writer, index=False)
                file_bytes = output.getvalue()
                timestamp_str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                
                try:
                    contents = repo.get_contents(HISTORY_FILE_PATH)
                    repo.update_file(HISTORY_FILE_PATH, f"Upload: {timestamp_str}", file_bytes, contents.sha)
                except Exception:
                    repo.create_file(HISTORY_FILE_PATH, f"Criar histórico: {timestamp_str}", file_bytes)
            except Exception:
                pass
                
        st.success("⚡ Planilha carregada e aplicada instantaneamente no painel!")
        time.sleep(0.5)
        st.rerun()

df = None

if st.session_state["df_ativo"] == "RESETADO":
    df = None
elif st.session_state["df_ativo"] is not None:
    df = st.session_state["df_ativo"]
else:
    repo = get_github_repo()
    if repo:
        try:
            file_content = repo.get_contents(HISTORY_FILE_PATH)
            df = tratar_dataframe(pd.read_excel(io.BytesIO(file_content.decoded_content)))
            st.session_state["df_ativo"] = df
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
            df_filtrada_criticas[['Número AWB', 'Nome do Motorista', 'Faixa D0-D3', 'Dias em Rota', 'Cidade Destino', 'Última Movimentação', 'Data/Hora Último Scan']],
            use_container_width=True,
            hide_index=True
        )
        
        if st.button("⬅️ Voltar ao Painel Principal"):
            st.session_state["view_mode"] = "Painel Principal"
            st.rerun()
            
    else:
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

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de AWBs (Histórico)", len(df_display))
        col2.metric("Motoristas Ativos", df_display[df_display['Nome do Motorista'] != 'Sem Motorista Atribuído']['Nome do Motorista'].nunique())
        col3.metric("Média de Dias em Rota", f"{df_display['Dias em Rota'].mean():.1f} dias")
        col4.metric("AWBs Críticas (>3 dias)", len(df_criticas))
        
        st.markdown("---")

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
                    df_driver_pendente[['Número AWB', 'Faixa D0-D3', 'Dias em Rota', 'Última Movimentação', 'Data/Hora Último Scan', 'Cidade Destino']],
                    use_container_width=True,
                    hide_index=True
                )

        with tab2:
            awb_per_driver = df_motoristas['Nome do Motorista'].value_counts().reset_index()
            awb_per_driver.columns = ['Nome do Motorista', 'Quantidade de AWBs']
            fig1 = px.bar(
                awb_per_driver, 
                x='Nome do Motorista', 
                y='Quantidade de AWBs',
                text='Quantidade de AWBs',
                title="Total Geral de AWBs por Motorista (Acumulado)",
                color='Quantidade de AWBs',
                color_continuous_scale='Blues'
            )
            fig1.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig1, use_container_width=True)
            
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

        with tab4:
            df_aging_driver = df_motoristas.groupby(['Nome do Motorista', 'Faixa D0-D3']).size().reset_index(name='Quantidade')
            fig3 = px.bar(
                df_aging_driver,
                x='Nome do Motorista',
                y='Quantidade',
                color='Faixa D0-D3',
                title="Distribuição de Aging (D0, D1, D2, D3, >D3) por Motorista",
                category_orders={'Faixa D0-D3': ['D0', 'D1', 'D2', 'D3', '> D3']}
            )
            fig3.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
else:
    st.info("Aguardando o supervisor carregar o ficheiro Excel (.xlsx) atualizado para iniciar o painel.")
