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

t_atual = st.session_state["transportadora_ativa"]
cfg = FILES[t_atual]
data_file = cfg["data"]

st.sidebar.markdown("---")
st.sidebar.subheader("Transportadora")
if st.sidebar.button("iMile"):
    st.session_state["transportadora_ativa"] = "iMile"
    st.rerun()
if st.sidebar.button("Anjun"):
    st.session_state["transportadora_ativa"] = "Anjun"
    st.rerun()

if st.session_state["user_info"]["role"] == "Supervisor":
    st.sidebar.markdown("---")
    st.sidebar.subheader("📁 Carregar Dados")
    up = st.sidebar.file_uploader("Ficheiro .xlsx", type=["xlsx", "xls"])
    if up is not None:
        try:
            df_r = pd.read_excel(up, sheet_name=0)
            df_p = tratar_imile(df_r) if t_atual == "iMile" else tratar_anjun(df_r)
            df_p.to_excel(data_file, index=False)
            st.sidebar.success("Carregado!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Erro: {e}")

st.title(f"RS Logística - {t_atual}")
st.markdown("---")

if os.path.exists(data_file):
    df = pd.read_excel(data_file)
    tot = len(df)
    st.metric("Total de Pacotes", tot)
    st.dataframe(df, use_container_width=True)
else:
    st.info(f"A carregar... Por favor, faça o upload da planilha de **{t_atual}** na barra lateral esquerda.")
