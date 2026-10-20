import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from datetime import datetime

st.set_page_config(page_title="RS Logística - Painel Transportadoras", page_icon="🚚", layout="wide")

DIR_H = "historico_diario"
if not os.path.exists(DIR_H): os.makedirs(DIR_H)

FILES = {
    "iMile": {"data": "dados_imile.xlsx", "prefix": "imile", "logo": "logo_imile.png"},
    "Anjun": {"data": "dados_anjun.xlsx", "prefix": "anjun", "logo": "logo_anjun.png"}
}

def tratar_imile(df_r):
    df = df_r.copy()
    df.columns = df.columns.str.strip()
    df['Número AWB'] = df['Número da Etiqueta'].astype(str) if 'Número da Etiqueta' in df.columns else df.get('Waybill No', 'Nao informado').astype(str)
    df['Nome do Motorista'] = df.get('Motorista', df.get('Driver Name', 'Sem Motorista')).fillna('Sem Motorista')
    df['Último Status'] = df.get('Último status', df.get('Last scan type', 'Nao informado')).fillna('Nao informado')
    df['Cidade Destino'] = df.get('Cidade destinatária', df.get('Destination City', 'Nao informada')).fillna('Nao informada')
    df['Data/Hora Última Leitura'] = pd.to_datetime(df.get('Horário da última leitura', df.get('Last scan time')), errors='coerce')
    df['Hora de Criação'] = pd.to_datetime(df.get('Hora de Criação'), errors='coerce')
    return df

def tratar_anjun(df_r):
    df = df_r.copy()
    df.columns = df.columns.str.strip()
    df['Número AWB'] = df.get('Número do Waybill', df.get('AWB', df.get('Waybill No', 'Nao informado'))).astype(str)
    df['Nome do Motorista'] = df.get('Entregador', df.get('Motorista', df.get('Driver Name', 'Sem Motorista'))).fillna('Sem Motorista')
    df['Último Status'] = df.get('Status do Pacote', df.get('Status', df.get('Último status', 'Nao informado'))).fillna('Nao informado')
    df['Cidade Destino'] = df.get('Cidade do destinatário', df.get('Cidade', df.get('Cidade destinatária', 'Nao informada'))).fillna('Nao informada')
    df['Data/Hora Última Leitura'] = pd.to_datetime(df.get('Último data de rastreio', df.get('Data Última Leitura', df.get('Horário da última leitura'))), errors='coerce')
    df['Hora de Criação'] = pd.to_datetime(df.get('Tempo de Criação', df.get('Data Criação', df.get('Hora de Criação'))), errors='coerce')
    return df

USERS_F = "users.json"
def load_users():
    if not os.path.exists(USERS_F):
        d = {"admin": {"name": "Supervisor Geral", "password": "admin", "role": "Supervisor", "email": "admin@logistica.com", "phone": "0"}}
        with open(USERS_F, "w", encoding="utf-8") as f: json.dump(d, f, indent=4, ensure_ascii=False)
        return d
    with open(USERS_F, "r", encoding="utf-8") as f: return json.load(f)

users_db = load_users()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None
if "transportadora_ativa" not in st.session_state:
    st.session_state["transportadora_ativa"] = "iMile"
if "view_mode" not in st.session_state:
    st.session_state["view_mode"] = "Painel Principal"

if not st.session_state["logged_in"]:
    if os.path.exists("logo_base.png"):
        st.image("logo_base.png", width=220)
    st.title("RS Logística - Portal de Operações")
    st.markdown("---")
    _, c_mid, _ = st.columns([1, 2, 1])
    with c_mid:
        with st.form("login"):
            u = st.text_input("Utilizador")
            p = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                if u in users_db and users_db[u]["password"] == p:
                    st.session_state["logged_in"] = True
                    st.session_state["username_key"] = u
                    st.session_state["user_info"] = users_db[u]
                    st.rerun()
                else:
                    st.error("Dados incorretos.")
    st.stop()

if os.path.exists("logo_base.png"):
    st.sidebar.image("logo_base.png", use_container_width=True)

st.sidebar.title(f"Utilizador: {st.session_state['user_info']['name']}")
st.sidebar.caption(f"Perfil: {st.session_state['user_info']['role']}")

if st.sidebar.button("Sair / Logout"):
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🚚 Transportadoras")
col_l1, col_l2 = st.sidebar.columns(2)
with col_l1:
    if os.path.exists("logo_imile.png"): st.image("logo_imile.png", width=50)
    if st.button("iMile", use_container_width=True):
        st.session_state["transportadora_ativa"] = "iMile"
        st.session_state["view_mode"] = "Painel Principal"
        st.rerun()
with col_l2:
    if os.path.exists("logo_anjun.png"): st.image("logo_anjun.png", width=50)
    if st.button("Anjun", use_container_width=True):
        st.session_state["transportadora_ativa"] = "Anjun"
        st.session_state["view_mode"] = "Painel Principal"
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("Navegacao")
if st.sidebar.button("Painel Principal"): st.session_state["view_mode"] = "Painel Principal"; st.rerun()
if st.sidebar.button("Painel por Motorista"): st.session_state["view_mode"] = "Painel Motoristas"; st.rerun()
if st.sidebar.button("Histórico de Dias"): st.session_state["view_mode"] = "Historico"; st.rerun()

if st.session_state["user_info"]["role"] == "Supervisor":
    st.sidebar.markdown("---")
    with st.sidebar.expander("Cadastrar Novo Colaborador"):
        with st.form("new_user"):
            nu = st.text_input("Login")
            nn = st.text_input("Nome")
            ne = st.text_input("Email")
            np = st.text_input("Telefone")
            ns = st.text_input("Senha", type="password")
            nr = st.selectbox("Perfil", ["Operador", "Supervisor"])
            if st.form_submit_button("Guardar"):
                if nu and ns and nn:
                    users_db[nu] = {"name": nn, "password": ns, "role": nr, "email": ne, "phone": np}
                    with open(USERS_F, "w", encoding="utf-8") as f: json.dump(users_db, f, indent=4, ensure_ascii=False)
                    st.sidebar.success("Cadastrado com sucesso!")
                else:
                    st.sidebar.warning("Preencha os campos obrigatórios.")

t_atual = st.session_state["transportadora_ativa"]
cfg = FILES[t_atual]
data_file = cfg["data"]

c_h1, c_h2 = st.columns([1, 8])
with c_h1:
    if os.path.exists(cfg["logo"]): st.image(cfg["logo"], width=80)
with c_h2:
    st.title(f"RS Logística - {t_atual}")
st.markdown("---")

if st.session_state["view_mode"] == "Historico":
    st.subheader(f"📚 Histórico - {t_atual}")
    arq = sorted([f for f in os.listdir(DIR_H) if f.startswith(cfg["prefix"]) and f.endswith('.xlsx')], reverse=True)
    if arq:
        sel = st.selectbox("Ficheiro anterior:", options=arq)
        if sel:
            df_h = pd.read_excel(os.path.join(DIR_H, sel))
            st.success(f"Registos: {len(df_h)}")
            st.dataframe(df_h, use_container_width=True, hide_index=True)
    else:
        st.info("Sem histórico encontrado.")
    if st.button("⬅️ Voltar"): st.session_state["view_mode"] = "Painel Principal"; st.rerun()
else:
    if st.session_state["user_info"]["role"] == "Supervisor":
        c_up, c_enc = st.columns([3, 1])
        with c_up:
            up = st.file_uploader(f"Carregar Planilha da {t_atual} (.xlsx)", type=["xlsx", "xls"])
            if up is not None:
                try:
                    df_raw = pd.read_excel(up, sheet_name=0)
                    df_pr = tratar_imile(df_raw) if t_atual == "iMile" else tratar_anjun(df_raw)
                    df_pr.to_excel(data_file, index=False)
                    st.success("Planilha carregada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
        with c_enc:
            st.write("")
            with st.expander(f"🔒 Encerrar Dia"):
                with st.form("form_enc"):
                    pass_c = st.text_input("Senha:", type="password")
                    if st.form_submit_button("Confirmar"):
                        k = st.session_state.get("username_key", "")
                        if k in users_db and users_db[k]["password"] == pass_c:
                            if os.path.exists(data_file):
                                dh = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                                os.rename(data_file, os.path.join(DIR_H, f"{cfg['prefix']}_fechamento_{dh}.xlsx"))
                                st.success("Dia encerrado!")
                                st.rerun()
                            else:
                                st.warning("Sem dados.")
                        else:
                            st.error("Senha incorreta.")

    df = None
    if os.path.exists(data_file):
        try: df = pd.read_excel(data_file)
        except: df = None
    elif os.path.exists("dados_atuais.xlsx"):
        try: df = pd.read_excel("dados_atuais.xlsx")
        except: df = None

    if df is not None and not df.empty:
        if 'Data/Hora Última Leitura' in df.columns:
            df['Data/Hora Última Leitura'] = pd.to_datetime(df['Data/Hora Última Leitura'], errors='coerce')
        if 'Hora de Criação' in df.columns:
            df['Hora de Criação'] = pd.to_datetime(df['Hora de Criação'], errors='coerce')

        cols = ['Número AWB', 'Nome do Motorista', 'Último Status', 'Cidade Destino', 'Data/Hora Última Leitura', 'Hora de Criação']
        df_disp = df[[c for c in cols if c in df.columns]]

        st.sidebar.markdown("---")
        st.sidebar.subheader(f"Filtros ({t_atual})")

        if 'Nome do Motorista' in df_disp.columns:
            mots = sorted(df_disp['Nome do Motorista'].astype(str).unique().tolist())
            m_s = st.sidebar.multiselect("Nome do Motorista:", options=mots, default=mots, key=f"m_filt_{t_atual}")
            if m_s: df_disp = df_disp[df_disp['Nome do Motorista'].isin(m_s)]

        if 'Cidade Destino' in df
