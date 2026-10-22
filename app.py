import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="RS Logística", page_icon="🚚", layout="wide")

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

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("RS Logística - Login")
    u = st.text_input("CPF")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        db = load_users()
        if u in db and db[u]["password"] == p:
            st.session_state["logged_in"] = True
            st.session_state["user_info"] = db[u]
            st.rerun()
        else:
            st.error("Dados incorretos.")
    st.stop()

st.sidebar.title(f"Utilizador: {st.session_state['user_info']['name']}")
if st.sidebar.button("Sair"):
    st.session_state["logged_in"] = False
    st.rerun()

st.title("RS Logística - Painel Principal")
st.success("Sessão iniciada com sucesso! O painel está pronto a operar.")
