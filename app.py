import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from datetime import datetime

st.set_page_config(page_title="RS Logistica", page_icon="🚚", layout="wide")

DIR_H = "historico_diario"
if not os.path.exists(DIR_H):
    os.makedirs(DIR_H)

FILES = {
    "iMile": {"data": "dados_imile.xlsx", "prefix": "imile", "logo": "logo_imile.png"},
    "Anjun": {"data": "dados_anjun.xlsx", "prefix": "anjun", "logo": "logo_anjun.png"}
}

def tratar_imile(df_r):
    df = df_r.copy()
    df.columns = df.columns.str.strip()
    
    # AWB dinâmico
    awb_col = 'Nao'
    for col in df.columns:
        c = col.lower()
        if 'etiqueta' in c or 'waybill' in c or 'awb' in c:
            awb_col = col
            break
    df['Numero AWB'] = df[awb_col].astype(str) if awb_col != 'Nao' else 'Nao'
        
    # Motorista: prioriza exatamente a coluna "MOTORISTA" (case insensitive) ou colunas equivalentes
    mot_col = 'Sem Motorista'
    for col in df.columns:
        if col.upper() == 'MOTORISTA':
            mot_col = col
            break
    if mot_col == 'Sem Motorista':
        for col in df.columns:
            c = col.lower()
            if 'motorista' in c or 'driver' in c or 'entregador' in c:
                mot_col = col
                break
    df['Nome do Motorista'] = df[mot_col].fillna('Sem Motorista') if mot_col != 'Sem Motorista' else 'Sem Motorista'
        
    # Status dinâmico
    stat_col = 'Nao'
    for col in df.columns:
        c = col.lower()
        if 'status' in c or 'scan type' in c or 'estado' in c:
            stat_col = col
            break
    df['Ultimo Status'] = df[stat_col].fillna('Nao') if stat_col != 'Nao' else 'Nao'
        
    # Cidade dinâmica
    cid_col = 'Nao'
    for col in df.columns:
        c = col.lower()
        if 'cidade' in c or 'destination' in c:
            cid_col = col
            break
    df['Cidade Destino'] = df[cid_col].fillna('Nao') if cid_col != 'Nao' else 'Nao'
        
    # Data/Hora Última Leitura dinâmica
    h_leitura = None
    for col in df.columns:
        c = col.lower()
        if 'horário' in c or 'horario' in c or 'time' in c or 'leitura' in c or 'rastreio' in c:
            h_leitura = col
            break
    df['Data/Hora Ultima Leitura'] = pd.to_datetime(df[h_leitura], errors='coerce') if h_leitura else pd.NaT
        
    # Hora de Criação dinâmica
    h_criacao = None
    for col in df.columns:
        c = col.lower()
        if 'criação' in c or 'criacao' in c or 'creation' in c or 'tempo' in c:
            h_criacao = col
            break
    df['Hora de Criacao'] = pd.to_datetime(df[h_criacao], errors='coerce') if h_criacao else pd.NaT
        
    return df

def tratar_anjun(df_r):
    return tratar_imile(df_r)

USERS_F = "users.json"
def load_users():
    def_u = {"13894491655": {"name": "Yuri Bergamaschine", "password": "172550", "role": "Supervisor", "email": "yuri@logistica.com", "phone": "0"}}
    if not os.path.exists(USERS_F):
        with open(USERS_F, "w", encoding="utf-8") as f:
            json.dump(def_u, f, indent=4, ensure_ascii=False)
        return def_u
    try:
        with open(USERS_F, "r", encoding="utf-8") as f:
            d = json.load(f)
            for k, v in def_u.items():
                if k not in d:
                    d[k] = v
            return d
    except:
        return def_u

def save_users(u):
    with open(USERS_F, "w", encoding="utf-8") as f:
        json.dump(u, f, indent=4, ensure_ascii=False)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None
if "transportadora_ativa" not in st.session_state:
    st.session_state["transportadora_ativa"] = "iMile"
if "view_mode" not in st.session_state:
    st.session_state["view_mode"] = "Principal"

if not st.session_state["logged_in"]:
    st.title("RS Logistica - Portal de Operacoes")
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
                if ur in db:
                    st.success(f"Senha: {db[ur]['password']}")
                else:
                    st.warning("Nao encontrado.")
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

if st.session_state["user_info"]["role"] == "Supervisor":
    st.sidebar.markdown("---")
    st.sidebar.subheader(f"📁 Carregar Dados ({t_atual})")
    up = st.sidebar.file_uploader("Ficheiro .xlsx", type=["xlsx", "xls"], key=f"up_{t_atual}")
    if up is not None:
        try:
            df_r = pd.read_excel(up, sheet_name=0)
            df_p = tratar_imile(df_r)
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
                        st.sidebar.success("Dia encerrado e arquivado com sucesso!")
                        st.rerun()
                    else:
                        st.sidebar.warning("Sem dados ativos para encerrar.")
                else:
                    st.sidebar.error("Senha incorreta.")

st.sidebar.markdown("---")
st.sidebar.subheader("Transportadoras")
cl1, cl2 = st.sidebar.columns(2)
with cl1:
    if st.button("iMile", use_container_width=True):
        st.session_state["transportadora_ativa"] = "iMile"
        st.session_state["view_mode"] = "Principal"
        st.rerun()
with cl2:
    if st.button("Anjun", use_container_width=True):
        st.session_state["transportadora_ativa"] = "Anjun"
        st.session_state["view_mode"] = "Principal"
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("Navegacao")
if st.sidebar.button("Principal"): st.session_state["view_mode"] = "Principal"; st.rerun()
if st.sidebar.button("Motoristas"): st.session_state["view_mode"] = "Motoristas"; st.rerun()
if st.sidebar.button("Historico"): st.session_state["view_mode"] = "Historico"; st.rerun()
if st.sidebar.button("Colaboradores"): st.session_state["view_mode"] = "Colaboradores"; st.rerun()

modo = st.session_state["view_mode"]
st.title(f"RS Logistica - {t_atual}")
st.markdown("---")

if modo == "Colaboradores":
    st.subheader("Colaboradores Cadastrados")
    db = load_users()
    lst = [{"Login": k, "Nome": v.get("name",""), "Perfil": v.get("role",""), "Email": v.get("email",""), "Telefone": v.get("phone","")} for k, v in db.items()]
    st.dataframe(pd.DataFrame(lst), use_container_width=True, hide_index=True)

elif modo == "Historico":
    st.subheader(f"Historico - {t_atual}")
    pfx = cfg["prefix"]
    arq = sorted([f for f in os.listdir(DIR_H) if pfx in f and f.endswith('.xlsx')], reverse=True)
    if arq:
        sel = st.selectbox("Ficheiro:", options=arq)
        if sel:
            df_h = pd.read_excel(os.path.join(DIR_H, sel))
            st.success(f"Registos: {len(df_h)}")
            st.dataframe(df_h, use_container_width=True, hide_index=True)
    else:
        st.info("Sem historico.")

elif modo == "Motoristas":
    st.subheader(f"Motoristas - {t_atual}")
    df = pd.read_excel(data_file) if os.path.exists(data_file) else None
    if df is not None and not df.empty:
        bm = st.text_input("Procurar Motorista:")
        st.markdown("---")
        df_m = df[df['Nome do Motorista'] != 'Sem Motorista']
        if bm:
            df_m = df_m[df_m['Nome do Motorista'].astype(str).str.contains(bm, case=False, na=False)]
        mots = sorted(df_m['Nome do Motorista'].unique().tolist())
        if mots:
            for i in range(0, len(mots), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(mots):
                        m = mots[i+j]
                        df_mot = df_m[df_m['Nome do Motorista'] == m]
                        st_m = df_mot['Ultimo Status'].astype(str).str.lower()
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

else:
    df = pd.read_excel(data_file) if os.path.exists(data_file) else None
    if df is not None and not df.empty:
        cols = ['Numero AWB', 'Nome do Motorista', 'Ultimo Status', 'Cidade Destino', 'Data/Hora Ultima Leitura', 'Hora de Criacao']
        df_disp = df[[c for c in cols if c in df.columns]]

        st.sidebar.markdown("---")
        st.sidebar.subheader("Filtros")
        if 'Nome do Motorista' in df_disp.columns:
            mots = sorted(df_disp['Nome do Motorista'].astype(str).unique().tolist())
            ms = st.sidebar.multiselect("Motorista:", options=mots, default=mots, key=f"m_{t_atual}")
            if ms:
                df_disp = df_disp[df_disp['Nome do Motorista'].isin(ms)]
        if 'Cidade Destino' in df_disp.columns:
            cids = sorted(df_disp['Cidade Destino'].astype(str).unique().tolist())
            cs = st.sidebar.multiselect("Cidade:", options=cids, default=cids, key=f"c_{t_atual}")
            if cs:
                df_disp = df_disp[df_disp['Cidade Destino'].isin(cs)]
        if 'Ultimo Status' in df_disp.columns:
            stats = sorted(df_disp['Ultimo Status'].astype(str).unique().tolist())
            ss = st.sidebar.multiselect("Status:", options=stats, default=stats, key=f"s_{t_atual}")
            if ss:
                df_disp = df_disp[df_disp['Ultimo Status'].isin(ss)]

        tot = len(df_disp)
        st_s = df_disp['Ultimo Status'].astype(str).str.lower() if 'Ultimo Status' in df_disp.columns else pd.Series([""] * tot)
        t_ent = int(st_s.str.contains('entregue', na=False).sum())
        t_rot = int(st_s.str.contains('rota', na=False).sum())
        t_out = tot - t_ent - t_rot
        p_ent = (t_ent / tot * 100) if tot > 0 else 0.0
        p_rot = (t_rot / tot * 100) if tot > 0 else 0.0
        p_out = (t_out / tot * 100) if tot > 0 else 0.0

        oct_m = 0.0
        if 'Hora de Criacao' in df.columns and 'Data/Hora Ultima Leitura' in df.columns:
            st_orig = df['Ultimo Status'].astype(str).str.lower() if 'Ultimo Status' in df.columns else pd.Series([""] * len(df))
            df_oct = df[st_orig.str.contains('entregue', na=False) & df['Hora de Criacao'].notna() & df['Data/Hora Ultima Leitura'].notna()]
            if not df_oct.empty:
                oct_m = ((df_oct['Data/Hora Ultima Leitura'] - df_oct['Hora de Criacao']).dt.total_seconds() / 86400.0).mean()

        if tot > 0:
            st.subheader("Progresso Geral")
            st.progress(float(p_ent / 100.0))
            st.write(f"Entregue: {p_ent:.1f}% | Em rota: {p_rot:.1f}% | Outros: {p_out:.1f}%")
            st.caption(f"Total: {tot} | Entregues: {t_ent} | Em Rota: {t_rot} | Outros: {t_out}")
            st.markdown("---")

        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        c1.metric("Total", tot)
        c2.metric("Motoristas", df_disp[df_disp['Nome do Motorista'] != 'Sem Motorista']['Nome do Motorista'].nunique())
        c3.metric("Entregues", t_ent)
        c4.metric("Em Rota", t_rot)
        c5.metric("SLA", f"{p_ent:.1f}%")
        c6.metric("OTIF", f"{p_ent:.1f}%")
        c7.metric("OCT", f"{oct_m:.1f} dias")

        st.markdown("---")
        st.subheader("Pesquisa AWB")
        bg = st.text_input("AWB:", key=f"srch_{t_atual}")
        if bg:
            df_res = df_disp[df_disp['Numero AWB'].astype(str).str.contains(bg, case=False, na=False)]
            if not df_res.empty:
                st.success(f"{len(df_res)} encontrado(s):")
                st.dataframe(df_res, use_container_width=True, hide_index=True)     
            else:
                st.warning("Nao encontrado.")
            st.markdown("---")

        st.subheader("Tabela de Dados")
        st.dataframe(df_disp, use_container_width=True, hide_index=True)
    else:
        st.info(f"Aguardando carregamento da planilha da **{t_atual}** na barra lateral.")
