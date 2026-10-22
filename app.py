import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from datetime import datetime

st.set_page_config(page_title="RS Logística", page_icon="🚚", layout="wide")

DIR_H = "historico_diario"
if not os.path.exists(DIR_H): os.makedirs(DIR_H)

FILES = {
    "iMile": {"data": "dados_imile.xlsx", "prefix": "imile", "logo": "logo_imile.png"},
    "Anjun": {"data": "dados_anjun.xlsx", "prefix": "anjun", "logo": "logo_anjun.png"}
}

def tratar_imile(df_r):
    df = df_r.copy()
    df.columns = df.columns.str.strip()
    df['Número AWB'] = df['Número da Etiqueta'].astype(str) if 'Número da Etiqueta' in df.columns else df.get('Waybill No', 'Nao').astype(str)
    df['Nome do Motorista'] = df.get('Motorista', df.get('Driver Name', 'Sem Motorista')).fillna('Sem Motorista')
    df['Último Status'] = df.get('Último status', df.get('Last scan type', 'Nao')).fillna('Nao')
    df['Cidade Destino'] = df.get('Cidade destinatária', df.get('Destination City', 'Nao')).fillna('Nao')
    df['Data/Hora Última Leitura'] = pd.to_datetime(df.get('Horário da última leitura', df.get('Last scan time')), errors='coerce')
    df['Hora de Criação'] = pd.to_datetime(df.get('Hora de Criação'), errors='coerce')
    return df

def tratar_anjun(df_r):
    df = df_r.copy()
    df.columns = df.columns.str.strip()
    df['Número AWB'] = df.get('Número do Waybill', df.get('AWB', df.get('Waybill No', 'Nao'))).astype(str)
    df['Nome do Motorista'] = df.get('Entregador', df.get('Motorista', df.get('Driver Name', 'Sem Motorista'))).fillna('Sem Motorista')
    df['Último Status'] = df.get('Status do Pacote', df.get('Status', df.get('Último status', 'Nao'))).fillna('Nao')
    df['Cidade Destino'] = df.get('Cidade do destinatário', df.get('Cidade', df.get('Cidade destinatária', 'Nao'))).fillna('Nao')
    df['Data/Hora Última Leitura'] = pd.to_datetime(df.get('Último data de rastreio', df.get('Data Última Leitura', df.get('Horário da última leitura'))), errors='coerce')
    df['Hora de Criação'] = pd.to_datetime(df.get('Tempo de Criação', df.get('Data Criação', df.get('Hora de Criação'))), errors='coerce')
    return df

USERS_F = "users.json"
def load_users():
    def_u = {"13894491655": {"name": "Yuri Bergamaschine", "password": "172550", "role": "Supervisor", "email": "yuri@logistica.com", "phone": "0"}}
    if not os.path.exists(USERS_F):
        with open(USERS_F, "w", encoding="utf-8") as f: json.dump(def_u, f, indent=4, ensure_ascii=False)
        return def_u
    try:
        with open(USERS_F, "r", encoding="utf-8") as f:
            d = json.load(f)
            for k, v in def_u.items():
                if k not in d: d[k] = v
            return d
    except:
        return def_u

def save_users(u):
    with open(USERS_F, "w", encoding="utf-8") as f: json.dump(u, f, indent=4, ensure_ascii=False)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None
if "transportadora_ativa" not in st.session_state:
    st.session_state["transportadora_ativa"] = "iMile"
if "view_mode" not in st.session_state:
    st.session_state["view_mode"] = "Principal"

if not st.session_state["logged_in"]:
    st.title("RS Logística - Portal de Operações")
    st.markdown("---")
    u = st.text_input("CPF")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        db = load_users()
        if u in db and db[u]["password"] == p:
            st.session_state["logged_in"] = True
            st.session_state["username_key"] = u
            st.session_state["user_info"] = db[u]
            st.rerun()
        else:
            st.error("Dados incorretos.")
    st.stop()

st.sidebar.title(f"Utilizador: {st.session_state['user_info']['name']}")
st.sidebar.caption(f"Perfil: {st.session_state['user_info']['role']}")

if st.sidebar.button("Sair"):
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("Transportadoras")
if st.sidebar.button("iMile", use_container_width=True):
    st.session_state["transportadora_ativa"] = "iMile"
    st.session_state["view_mode"] = "Principal"
    st.rerun()
if st.sidebar.button("Anjun", use_container_width=True):
    st.session_state["transportadora_ativa"] = "Anjun"
    st.session_state["view_mode"] = "Principal"
    st.rerun()

t_atual = st.session_state["transportadora_ativa"]
cfg = FILES[t_atual]
data_file = cfg["data"]

if st.session_state["user_info"]["role"] == "Supervisor":
    st.sidebar.markdown("---")
    st.sidebar.subheader(f"📁 Carregar Dados ({t_atual})")
    up = st.sidebar.file_uploader("Ficheiro .xlsx", type=["xlsx", "xls"], key=f"up_{t_atual}")
    if up is not None:
        try:
            df_r = pd.read_excel(up, sheet_name=0)
            df_p = tratar_imile(df_r) if t_atual == "iMile" else tratar_anjun(df_r)
            df_p.to_excel(data_file, index=False)
            st.sidebar.success("Carregado com sucesso!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Erro: {e}")

    st.sidebar.markdown("---")
    with st.sidebar.expander("🔒 Encerrar Dia"):
        with st.form("f_enc"):
            pc = st.text_input("Senha do Supervisor:", type="password")
            if st.form_submit_button("Confirmar Fecho"):
                k = st.session_state.get("username_key", "")
                db = load_users()
                if k in db and db[k]["password"] == pc:
                    if os.path.exists(data_file):
                        dh = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        os.rename(data_file, os.path.join(DIR_H, f"{cfg['prefix']}_fechamento_{dh}.xlsx"))
                        st.sidebar.success("Dia encerrado e arquivado!")
                        st.rerun()
                    else:
                        st.sidebar.warning("Sem dados para encerrar.")
                else:
                    st.sidebar.error("Senha incorreta.")

st.sidebar.markdown("---")
st.sidebar.subheader("Navegação")
if st.sidebar.button("Principal"): st.session_state["view_mode"] = "Principal"; st.rerun()
if st.sidebar.button("Motoristas"): st.session_state["view_mode"] = "Motoristas"; st.rerun()
if st.sidebar.button("Histórico"): st.session_state["view_mode"] = "Historico"; st.rerun()

modo = st.session_state["view_mode"]
st.title(f"RS Logística - {t_atual}")
st.markdown("---")

if modo == "Historico":
    st.subheader(f"Histórico - {t_atual}")
    pfx = cfg["prefix"]
    arq = sorted([f for f in os.listdir(DIR_H) if pfx in f and f.endswith('.xlsx')], reverse=True)
    if arq:
        sel = st.selectbox("Ficheiro:", options=arq)
        if sel:
            df_h = pd.read_excel(os.path.join(DIR_H, sel))
            st.success(f"Registos: {len(df_h)}")
            st.dataframe(df_h, use_container_width=True, hide_index=True)
    else:
        st.info("Sem histórico.")

elif modo == "Motoristas":
    st.subheader(f"Motoristas - {t_atual}")
    df = pd.read_excel(data_file) if os.path.exists(data_file) else None
    if df is not None and not df.empty:
        bm = st.text_input("Procurar Motorista:")
        st.markdown("---")
        df_m = df[df['Nome do Motorista'] != 'Sem Motorista']
        if bm: df_m = df_m[df_m['Nome do Motorista'].astype(str).str.contains(bm, case=False, na=False)]
        mots = sorted(df_m['Nome do Motorista'].unique().tolist())
        if mots:
            for m in mots:
                with st.expander(f"Motorista: {m}"):
                    df_mot = df_m[df_m['Nome do Motorista'] == m]
                    st.write(f"Total pacotes: {len(df_mot)}")
                    st.dataframe(df_mot, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum motorista encontrado.")
    else:
        st.info("Sem dados ativos.")

else:
    df = pd.read_excel(data_file) if os.path.exists(data_file) else None
    if df is not None and not df.empty:
        if 'Data/Hora Última Leitura' in df.columns: df['Data/Hora Última Leitura'] = pd.to_datetime(df['Data/Hora Última Leitura'], errors='coerce')
        if 'Hora de Criação' in df.columns: df['Hora de Criação'] = pd.to_datetime(df['Hora de Criação'], errors='coerce')

        cols = ['Número AWB', 'Nome do Motorista', 'Último Status', 'Cidade Destino', 'Data/Hora Última Leitura', 'Hora de Criação']
        df_disp = df[[c for c in cols if c in df.columns]]

        tot = len(df_disp)
        st_s = df_disp['Último Status'].astype(str).str.lower() if 'Último Status' in df_disp.columns else pd.Series([""] * tot)
        t_ent = int(st_s.str.contains('entregue', na=False).sum())
        t_rot = int(st_s.str.contains('rota', na=False).sum())
        t_out = tot - t_ent - t_rot
        p_ent = (t_ent / tot * 100) if tot > 0 else 0.0

        if tot > 0:
            st.subheader("Progresso Geral")
            st.progress(float(p_ent / 100.0))
            st.write(f"Entregue: {p_ent:.1f}% | Total: {tot} | Entregues: {t_ent} | Em Rota: {t_rot}")
            st.markdown("---")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", tot)
        c2.metric("Entregues", t_ent)
        c3.metric("Em Rota", t_rot)
        c4.metric("SLA", f"{p_ent:.1f}%")

        st.markdown("---")
        st.subheader("Pesquisa AWB")
        bg = st.text
