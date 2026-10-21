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
    if os.path.exists("logo_base.png"): st.image("logo_base.png", width=220)
    st.title("RS Logística - Portal de Operações")
    st.markdown("---")
    _, c_mid, _ = st.columns([1, 2, 1])
    with c_mid:
        t_l, t_e = st.tabs(["Entrar", "Esqueci a Senha"])
        with t_l:
            with st.form("f_log"):
                u = st.text_input("CPF")
                p = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar"):
                    db = load_users()
                    if u in db and db[u]["password"] == p:
                        st.session_state["logged_in"] = True
                        st.session_state["username_key"] = u
                        st.session_state["user_info"] = db[u]
                        st.rerun()
                    else:
                        st.error("Dados incorretos.")
        with t_e:
            st.info("Insira o seu CPF para consultar a senha.")
            ur = st.text_input("CPF:")
            if st.button("Consultar"):
                db = load_users()
                if ur in db: st.success(f"Senha: {db[ur]['password']}")
                else: st.warning("Não encontrado.")
    st.stop()

if os.path.exists("logo_base.png"): st.sidebar.image("logo_base.png", width=200)
st.sidebar.title(f"Utilizador: {st.session_state['user_info']['name']}")
st.sidebar.caption(f"Perfil: {st.session_state['user_info']['role']}")

if st.sidebar.button("Sair"):
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("Transportadoras")
cl1, cl2 = st.sidebar.columns(2)
with cl1:
    if os.path.exists("logo_imile.png"): st.image("logo_imile.png", width=50)
    if st.button("iMile", use_container_width=True):
        st.session_state["transportadora_ativa"] = "iMile"
        st.session_state["view_mode"] = "Principal"
        st.rerun()
with cl2:
    if os.path.exists("logo_anjun.png"): st.image("logo_anjun.png", width=50)
    if st.button("Anjun", use_container_width=True):
        st.session_state["transportadora_ativa"] = "Anjun"
        st.session_state["view_mode"] = "Principal"
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("Navegação")
if st.sidebar.button("Principal"): st.session_state["view_mode"] = "Principal"; st.rerun()
if st.sidebar.button("Motoristas"): st.session_state["view_mode"] = "Motoristas"; st.rerun()
if st.sidebar.button("Histórico"): st.session_state["view_mode"] = "Historico"; st.rerun()
if st.sidebar.button("Colaboradores"): st.session_state["view_mode"] = "Colaboradores"; st.rerun()

if st.session_state["user_info"]["role"] == "Supervisor":
    st.sidebar.markdown("---")
    with st.sidebar.expander("Novo Colaborador"):
        with st.form("f_new"):
            nu = st.text_input("Login")
            nn = st.text_input("Nome")
            ne = st.text_input("Email")
            np = st.text_input("Telefone")
            ns = st.text_input("Senha", type="password")
            nr = st.selectbox("Perfil", ["Operador", "Supervisor"])
            if st.form_submit_button("Guardar"):
                if nu and ns and nn:
                    db = load_users()
                    db[nu] = {"name": nn, "password": ns, "role": nr, "email": ne, "phone": np}
                    save_users(db)
                    st.sidebar.success("Guardado!")
                else:
                    st.sidebar.warning("Preencha os obrigatórios.")
    with st.sidebar.expander("Redefinir Senha"):
        with st.form("f_reset"):
            db = load_users()
            su = st.selectbox("Utilizador:", options=list(db.keys()))
            npw = st.text_input("Nova Senha:", type="password")
            if st.form_submit_button("Atualizar"):
                if npw:
                    db[su]["password"] = npw
                    save_users(db)
                    st.sidebar.success("Atualizado!")
                else:
                    st.sidebar.warning("Insira a senha.")

t_atual = st.session_state["transportadora_ativa"]
cfg = FILES[t_atual]
data_file = cfg["data"]

c1, c2 = st.columns([1, 8])
with c1:
    if os.path.exists(cfg["logo"]): st.image(cfg["logo"], width=80)
with c2:
    st.title(f"RS Logística - {t_atual}")
st.markdown("---")

modo = st.session_state["view_mode"]

if modo == "Colaboradores":
    st.subheader("Colaboradores Cadastrados")
    db = load_users()
    lst = [{"Login": k, "Nome": v.get("name",""), "Perfil": v.get("role",""), "Email": v.get("email",""), "Telefone": v.get("phone","")} for k, v in db.items()]
    st.dataframe(pd.DataFrame(lst), use_container_width=True, hide_index=True)
    if st.button("Voltar"): st.session_state["view_mode"] = "Principal"; st.rerun()

elif modo == "Historico":
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
    if st.button("Voltar"): st.session_state["view_mode"] = "Principal"; st.rerun()

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
            for i in range(0, len(mots), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(mots):
                        m = mots[i+j]
                        df_mot = df_m[df_m['Nome do Motorista'] == m]
                        st_m = df_mot['Último Status'].astype(str).str.lower()
                        me = int(st_m.str.contains('entregue', na=False).sum())
                        mr = int(st_m.str.contains('rota', na=False).sum())
                        mo = len(df_mot) - me - mr
                        with cols[j]:
                            with st.container(border=True):
                                st.markdown(f"**{m}**")
                                fig = px.pie(pd.DataFrame({'S': ['Entregue', 'Rota', 'Outros'], 'Q': [me, mr, mo]}), names='S', values='Q', hole=0.6, color='S', color_discrete_map={'Entregue': '#28a745', 'Rota': '#ffc107', 'Outros': '#dc3545'})
                                fig.update_traces(textinfo='value', showlegend=False)
                                fig.update_layout(margin=dict(t=5, b=5, l=5, r=5), height=160, paper_bgcolor='rgba(0,0,0,0)')
                                st.plotly_chart(fig, use_container_width=True, key=f"pie_{t_atual}_{i+j}")
                                st.write(f"Entregues: {me} | Rota: {mr} | Outros: {mo}")
        else:
            st.info("Nenhum motorista.")
    else:
        st.info("Sem dados.")
    if st.button("Voltar"): st.session_state["view_mode"] = "Principal"; st.rerun()

else:
    if st.session_state["user_info"]["role"] == "Supervisor":
        cup, cenc = st.columns([3, 1])
        with cup:
            up = st.file_uploader(f"Carregar Planilha da {t_atual} (.xlsx)", type=["xlsx", "xls"])
            if up is not None:
                try:
                    df_r = pd.read_excel(up, sheet_name=0)
                    df_p = tratar_imile(df_r) if t_atual == "iMile" else tratar_anjun(df_r)
                    df_p.to_excel(data_file, index=False)
                    st.success("Carregado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
        with cenc:
            st.write("")
            with st.expander("Encerrar Dia"):
                with st.form("f_enc"):
                    pc = st.text_input("Digite a Senha do Supervisor:", type="password")
                    if st.form_submit_button("Confirmar Fecho"):
                        k = st.session_state.get("username_key", "")
                        db = load_users()
                        if k in db and db[k]["password"] == pc:
                            if os.path.exists(data_file):
                                dh = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                                os.rename(data_file, os.path.join(DIR_H, f"{cfg['prefix']}_fechamento_{dh}.xlsx"))
                                st.success("Dia encerrado e arquivado com sucesso!")
                                st.rerun()
                            else:
                                st.warning("Sem dados ativos para encerrar.")
                        else:
                            st.error("Senha incorreta.")

    df = pd.read_excel(data_file) if os.path.exists(data_file) else None
    if df is not None and not df.empty:
        if 'Data/Hora Última Leitura' in df.columns: df['Data/Hora Última Leitura'] = pd.to_datetime(df['Data/Hora Última Leitura'], errors='coerce')
        if 'Hora de Criação' in df.columns: df['Hora de Criação'] = pd.to_datetime(df['Hora de Criação'], errors='coerce')

        cols = ['Número AWB', 'Nome do Motorista', 'Último Status', 'Cidade Destino', 'Data/Hora Última Leitura', 'Hora de Criação']
        df_disp = df[[c for c in cols if c in df.columns]]

        st.sidebar.markdown("---")
        st.sidebar.subheader("Filtros")
        if 'Nome do Motorista' in df_disp.columns:
            mots = sorted(df_disp['Nome do Motorista'].astype(str).unique().tolist())
            ms = st.sidebar.multiselect("Motorista:", options=mots, default=mots, key=f"m_{t_atual}")
            if ms: df_disp = df_disp[df_disp['Nome do Motorista'].isin(ms)]
        if 'Cidade Destino' in df_disp.columns:
            cids = sorted(df_disp['Cidade Destino'].astype(str).unique().tolist())
            cs = st.sidebar.multiselect("Cidade:", options=cids, default=cids, key=f"c_{t_atual}")
            if cs: df_disp = df_disp[df_disp['Cidade Destino'].isin(cs)]
        if 'Último Status' in df_disp.columns:
            stats = sorted(df_disp['Último Status'].astype(str).unique().tolist())
            ss = st.sidebar.multiselect("Status:", options=stats, default=stats, key=f"s_{t_atual}")
            if ss: df_disp = df_disp[df_disp['Último Status'].isin(ss)]

        tot = len(df_disp)
        st_s = df_disp['Último Status'].astype(str).str.lower() if 'Último Status' in df_disp.columns else pd.Series([""] * tot)
        t_ent = int(st_s.str.contains('entregue', na=False).sum())
        t_rot = int(st_s.str.contains('rota', na=False).sum())
        t_out = tot - t_ent - t_rot
        p_ent = (t_ent / tot * 100) if tot > 0 else 0.0
        p_rot = (t_rot / tot * 100) if tot > 0 else 0.0
        p_out = (t_out / tot * 100) if tot > 0 else 0.0

        oct_m = 0.0
        if 'Hora de Criação' in df.columns and 'Data/Hora Última Leitura' in df.columns:
            st_orig = df['Último Status'].astype(str).str.lower() if 'Último Status' in df.columns else pd.Series([""] * len(df))
            df_oct = df[st_orig.str.contains('entregue', na=False) & df['Hora de Criação'].notna() & df['Data/Hora Última Leitura'].notna()]
            if not df_oct.empty:
                oct_m = ((df_oct['Data/Hora Última Leitura'] - df_oct['Hora de Criação']).dt.total_seconds() / 86400.0).mean()

        if tot > 0:
            st.subheader(f"Progresso - {t_atual}")
            st.markdown(f'<div style="background-color: #ddd; border-radius: 8px; overflow: hidden; display: flex; height:
