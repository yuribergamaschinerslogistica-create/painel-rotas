import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from datetime import datetime

st.set_page_config(
    page_title="Painel de Acompanhamento - Transportadoras",
    page_icon="🚚",
    layout="wide"
)

HISTORY_DIR = "historico_diario"
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

FILES = {
    "iMile": {"data": "dados_imile.xlsx", "prefix": "imile"},
    "Anjun": {"data": "dados_anjun.xlsx", "prefix": "anjun"}
}

def tratar_dataframe_imile(df_raw):
    df = df_raw.copy()
    df.columns = df.columns.str.strip()
    df['Número AWB'] = df['Número da Etiqueta'].astype(str) if 'Número da Etiqueta' in df.columns else (df['Waybill No'].astype(str) if 'Waybill No' in df.columns else 'Nao informado')
    df['Nome do Motorista'] = df['Motorista'].fillna('Sem Motorista Atribuido') if 'Motorista' in df.columns else (df['Driver Name'].fillna('Sem Motorista Atribuido') if 'Driver Name' in df.columns else 'Sem Motorista Atribuido')
    df['Último Status'] = df['Último status'].fillna('Nao informado') if 'Último status' in df.columns else (df['Last scan type'].fillna('Nao informado') if 'Last scan type' in df.columns else 'Nao informado')
    df['Cidade Destino'] = df['Cidade destinatária'].fillna('Nao informada') if 'Cidade destinatária' in df.columns else (df['Destination City'].fillna('Nao informada') if 'Destination City' in df.columns else 'Nao informada')
    df['Data/Hora Última Leitura'] = pd.to_datetime(df['Horário da última leitura'], errors='coerce') if 'Horário da última leitura' in df.columns else (pd.to_datetime(df['Last scan time'], errors='coerce') if 'Last scan time' in df.columns else pd.NaT)
    df['Hora de Criação'] = pd.to_datetime(df['Hora de Criação'], errors='coerce') if 'Hora de Criação' in df.columns else pd.NaT
    return df

def tratar_dataframe_anjun(df_raw):
    df = df_raw.copy()
    df.columns = df.columns.str.strip()
    df['Número AWB'] = df['Número do Waybill'].astype(str) if 'Número do Waybill' in df.columns else (df['AWB'].astype(str) if 'AWB' in df.columns else 'Nao informado')
    df['Nome do Motorista'] = df['Entregador'].fillna('Sem Motorista Atribuido') if 'Entregador' in df.columns else (df['Motorista'].fillna('Sem Motorista Atribuido') if 'Motorista' in df.columns else 'Sem Motorista Atribuido')
    df['Último Status'] = df['Status do Pacote'].fillna('Nao informado') if 'Status do Pacote' in df.columns else (df['Status'].fillna('Nao informado') if 'Status' in df.columns else 'Nao informado')
    df['Cidade Destino'] = df['Cidade do destinatário'].fillna('Nao informada') if 'Cidade do destinatário' in df.columns else (df['Cidade'].fillna('Nao informada') if 'Cidade' in df.columns else 'Nao informada')
    df['Data/Hora Última Leitura'] = pd.to_datetime(df['Último data de rastreio'], errors='coerce') if 'Último data de rastreio' in df.columns else (pd.to_datetime(df['Data Última Leitura'], errors='coerce') if 'Data Última Leitura' in df.columns else pd.NaT)
    df['Hora de Criação'] = pd.to_datetime(df['Tempo de Criação'], errors='coerce') if 'Tempo de Criação' in df.columns else (pd.to_datetime(df['Data Criação'], errors='coerce') if 'Data Criação' in df.columns else pd.NaT)
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
if "transportadora_ativa" not in st.session_state:
    st.session_state["transportadora_ativa"] = "iMile"
if "view_mode" not in st.session_state:
    st.session_state["view_mode"] = "Painel Principal"

# --- LOGIN ---
if not st.session_state["logged_in"]:
    st.title("Acesso - Painel de Transportadoras")
    st.markdown("---")
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        with st.form("login_form"):
            st.subheader("Iniciar Sessao")
            u_in = st.text_input("Utilizador")
            p_in = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                if u_in in users_db and users_db[u_in]["password"] == p_in:
                    st.session_state["logged_in"] = True
                    st.session_state["username_key"] = u_in
                    st.session_state["user_info"] = users_db[u_in]
                    st.rerun()
                else:
                    st.error("Utilizador ou senha incorretos.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.title(f"Utilizador: {st.session_state['user_info']['name']}")
st.sidebar.caption(f"Perfil: {st.session_state['user_info']['role']}")

if st.sidebar.button("Sair / Logout"):
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🚚 Transportadoras")
if st.sidebar.button("📦 iMile", use_container_width=True):
    st.session_state["transportadora_ativa"] = "iMile"
    st.session_state["view_mode"] = "Painel Principal"
    st.rerun()
if st.sidebar.button("📦 Anjun", use_container_width=True):
    st.session_state["transportadora_ativa"] = "Anjun"
    st.session_state["view_mode"] = "Painel Principal"
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

# --- CADASTRO DE NOVOS COLABORADORES (APENAS SUPERVISOR) ---
if st.session_state["user_info"]["role"] == "Supervisor":
    st.sidebar.markdown("---")
    with st.sidebar.expander("Cadastrar Novo Colaborador"):
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
                    st.sidebar.success(f"Utilizador '{new_username}' cadastrado com sucesso!")
                else:
                    st.sidebar.warning("Preencha todos os campos obrigatórios.")

transp_atual = st.session_state["transportadora_ativa"]
config_atual = FILES[transp_atual]
DATA_FILE = config_atual["data"]

st.title(f"Painel de Acompanhamento - {transp_atual}")
st.markdown("---")

if st.session_state["view_mode"] == "Historico":
    st.subheader(f"📚 Histórico - {transp_atual}")
    prefixo = config_atual["prefix"]
    arquivos = sorted([f for f in os.listdir(HISTORY_DIR) if f.startswith(prefix) and f.endswith('.xlsx')], reverse=True)
    if arquivos:
        sel = st.selectbox("Selecione o ficheiro anterior:", options=arquivos)
        if sel:
            df_h = pd.read_excel(os.path.join(HISTORY_DIR, sel))
            st.success(f"Registos: {len(df_h)}")
            st.dataframe(df_h, use_container_width=True, hide_index=True)
    else:
        st.info(f"Nenhum histórico encontrado para {transp_atual}.")
    if st.button("⬅️ Voltar"):
        st.session_state["view_mode"] = "Painel Principal"
        st.rerun()
else:
    df = None
    if st.session_state["user_info"]["role"] == "Supervisor":
        c1, c2 = st.columns([3, 1])
        with c1:
            up_file = st.file_uploader(f"Carregar Planilha da {transp_atual} (.xlsx)", type=["xlsx", "xls"])
            if up_file is not None:
                try:
                    df_r = pd.read_excel(up_file, sheet_name=0)
                    if transp_atual == "iMile":
                        df = tratar_dataframe_imile(df_r)
                    else:
                        df = tratar_dataframe_anjun(df_r)
                    df.to_excel(DATA_FILE, index=False)
                    st.success(f"Planilha da {transp_atual} carregada com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao processar: {e}")
        with c2:
            st.write("")
            st.write("")
            with st.expander(f"🔒 Encerrar Dia ({transp_atual})"):
                with st.form(f"form_arq_{transp_atual}"):
                    senha_c = st.text_input("Senha:", type="password")
                    if st.form_submit_button("Confirmar"):
                        u_key = st.session_state.get("username_key", "")
                        if u_key in users_db and users_db[u_key]["password"] == senha_c:
                            if os.path.exists(DATA_FILE):
                                dh = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                                novo_nome = f"{config_atual['prefix']}_fechamento_{dh}.xlsx"
                                os.rename(DATA_FILE, os.path.join(HISTORY_DIR, novo_nome))
                                st.success("Dia encerrado e sistema zerado!")
                                st.rerun()
                            else:
                                st.warning("Sem dados ativos.")
                        else:
                            st.error("Senha incorreta.")

    # Se não carregou agora, tenta ler o ficheiro específico da transportadora
    if df is None:
        if os.path.exists(DATA_FILE):
            try:
                df = pd.read_excel(DATA_FILE)
            except:
                df = None
        # Fallback de compatibilidade caso exista o ficheiro antigo unificado
        elif os.path.exists("dados_atuais.xlsx"):
            try:
                df = pd.read_excel("dados_atuais.xlsx")
            except:
                df = None

    if df is not None and not df.empty:
        if 'Data/Hora Última Leitura' in df.columns:
            df['Data/Hora Última Leitura'] = pd.to_datetime(df['Data/Hora Última Leitura'], errors='coerce')
        if 'Hora de Criação' in df.columns:
            df['Hora de Criação'] = pd.to_datetime(df['Hora de Criação'], errors='coerce')

        cols = ['Número AWB', 'Nome do Motorista', 'Último Status', 'Cidade Destino', 'Data/Hora Última Leitura', 'Hora de Criação']
        df_display = df[[c for c in cols if c in df.columns]]

        st.sidebar.markdown("---")
        st.sidebar.subheader(f"Filtros ({transp_atual})")

        if 'Cidade Destino' in df_display.columns:
            cidades_disp = sorted(df_display['Cidade Destino'].astype(str).unique().tolist())
            cidades_sel = st.sidebar.multiselect("Cidade Destino:", options=cidades_disp, default=cidades_disp, key=f"cid_{transp_atual}")
            if cidades_sel:
                df_display = df_display[df_display['Cidade Destino'].isin(cidades_sel)]

        if 'Último Status' in df_display.columns:
            status_disp = sorted(df_display['Último Status'].astype(str).unique().tolist())
            status_sel = st.sidebar.multiselect("Último Status:", options=status_disp, default=status_disp, key=f"stat_{transp_atual}")
            if status_sel:
                df_display = df_display[df_display['Último Status'].isin(status_sel)]

        total_geral = len(df_display)
        status_lower = df_display['Último Status'].astype(str).str.lower() if 'Último Status' in df_display.columns else pd.Series([""] * total_geral)
        
        total_entregue = int(status_lower.str.contains('entregue', na=False).sum())
        total_em_rota = int(status_lower.str.contains('rota', na=False).sum())
        total_insucesso = total_geral - total_entregue - total_em_rota
        
        pct_entregue = (total_entregue / total_geral * 100) if total_geral > 0 else 0.0
        pct_em_rota = (total_em_rota / total_geral * 100) if total_geral > 0 else 0.0
        pct_insucesso = (total_insucesso / total_geral * 100) if total_geral > 0 else 0.0

        sla_geral = pct_entregue
        otif = pct_entregue

        oct_medio = 0.0
        if 'Hora de Criação' in df.columns and 'Data/Hora Última Leitura' in df.columns:
            df_oct = df[status_lower.str.contains('entregue', na=False) & df['Hora de Criação'].notna() & df['Data/Hora Última Leitura'].notna()]
            if not df_oct.empty:
                oct_medio = ((df_oct['Data/Hora Última Leitura'] - df_oct['Hora de Criação']).dt.total_seconds() / 86400.0).mean()

        if st.session_state["view_mode"] == "Painel Motoristas":
            st.subheader(f"Painel por Motorista - {transp_atual}")
            busca_m = st.text_input("🔍 Procurar Motorista:", placeholder="Ex: Rodrigo")
            st.markdown("---")

            df_mot_all = df_display[df_display['Nome do Motorista'] != 'Sem Motorista Atribuido']
            if busca_m:
                df_mot_all = df_mot_all[df_mot_all['Nome do Motorista'].astype(str).str.contains(busca_m, case=False, na=False)]

            lista_mot = sorted(df_mot_all['Nome do Motorista'].unique().tolist())
            if lista_mot:
                for i in range(0, len(lista_mot), 3):
                    cols_r = st.columns(3)
                    for j in range(3):
                        if i + j < len(lista_mot):
                            mot = lista_mot[i + j]
                            df_m = df_mot_all[df_mot_all['Nome do Motorista'] == mot]
                            m_st_low = df_m['Último Status'].astype(str).str.lower()
                            m_ent = int(m_st_low.str.contains('entregue', na=False).sum())
                            m_rot = int(m_st_low.str.contains('rota', na=False).sum())
                            m_out = len(df_m) - m_ent - m_rot
                            with cols_r[j]:
                                with st.container(border=True):
                                    st.markdown(f"**{mot}**")
                                    fig = px.pie(
                                        pd.DataFrame({'S': ['Entregue', 'Rota', 'Outros'], 'Q': [m_ent, m_rot, m_out]}),
                                        names='S', values='Q', hole=0.6,
                                        color='S', color_discrete_map={'Entregue': '#28a745', 'Rota': '#ffc107', 'Outros': '#dc3545'}
                                    )
                                    fig.update_traces(textinfo='value', showlegend=False)
                                    fig.update_layout(margin=dict(t=5, b=5, l=5, r=5), height=160, paper_bgcolor='rgba(0,0,0,0)')
                                    st.plotly_chart(fig, use_container_width=True, key=f"d_{transp_atual}_{i+j}")
                                    st.write(f"Entregues: {m_ent} | Rota: {m_rot} | Outros: {m_out}")
            else:
                st.info("Nenhum motorista encontrado.")

            st.markdown("---")
            if st.button("Voltar"):
                st.session_state["view_mode"] = "Painel Principal"
                st.rerun()
        else:
            if total_geral > 0:
                st.subheader(f"Progresso Geral - {transp_atual}")
                st.markdown(
                    f"""
                    <div style="background-color: #ddd; border-radius: 8px; overflow: hidden; display: flex; height: 28px; width: 100%;">
                        <div style="width: {pct_entregue}%; background-color: #28a745; text-align: center; color: white; font-weight: bold; line-height: 28px; font-size: 13px;">Entregue: {pct_entregue:.1f}%</div>
                        <div style="width: {pct_em_rota}%; background-color: #ffc107; text-align: center; color: black; font-weight: bold; line-height: 28px; font-size: 13px;">Em rota: {pct_em_rota:.1f}%</div>
                        <div style="width: {pct_insucesso}%; background-color: #dc3545; text-align: center; color: white; font-weight: bold; line-height: 28px; font-size: 13px;">Outros: {pct_insucesso:.1f}%</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.caption(f"Total: {total_geral} pacotes | Entregues: {total_entregue} | Em Rota: {total_em_rota} | Outros: {total_insucesso}")
                st.markdown("---")

            c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
            c1.metric("Total", total_geral)
            c2.metric("Motoristas", df_display[df_display['Nome do Motorista'] != 'Sem Motorista Atribuido']['Nome do Motorista'].nunique())
            c3.metric("Entregues", total_entregue)
            c4.metric("Em Rota", total_em_rota)
            c5.metric("SLA", f"{sla_geral:.1f}%")
            c6.metric("OTIF", f"{otif:.1f}%")
            c7.metric("OCT", f"{oct_medio:.1f} dias")
            
            st.markdown("---")
            st.subheader("Pesquisa AWB")
            b_global = st.text_input("Número da AWB:", key=f"search_{transp_atual}")
            if b_global:
                df_res = df_display[df_display['Número AWB'].astype(str).str.contains(b_global, case=False, na=False)]
                if not df_res.empty:
                    st.success(f"{len(df_res)} registo(s) encontrado(s):")
                    st.dataframe(df_res, use_container_width=True, hide_index=True)
                else:
                    st.warning("Não encontrado.")
                st.markdown("---")

            st.subheader(f"Tabela de Acompanhamento - {transp_atual}")
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info(f"Aguardando carregamento da planilha da **{transp_atual}** para iniciar o dia.")
