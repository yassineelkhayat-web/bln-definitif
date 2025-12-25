import streamlit as st
import pandas as pd
from datetime import date, timedelta
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION ET CAMOUFLAGE (PLUS DE LOGOS) ---
st.set_page_config(page_title="Bilan Coran", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stHeader"] {display: none !important;}
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .stAppDeployButton {display: none !important;}
    .block-container {padding-top: 1rem !important;}
    </style>
""", unsafe_allow_html=True)

# --- 2. CONNEXION GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # On lit les données
    df = conn.read(ttl=0)
    # On nettoie les noms de colonnes au cas où il y aurait des espaces
    df.columns = df.columns.str.strip()
    df.set_index("Nom", inplace=True)
except Exception as e:
    st.error("Connexion en cours... Vérifie que tu as bien mis le lien dans les Secrets.")
    st.stop()

# --- CONFIGURATION SÉCURITÉ ---
CODE_SECRET = "Yassine05"

if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.markdown("<h2 style='text-align: center;'>🔐 Accès Sécurisé</h2>", unsafe_allow_html=True)
    cols = st.columns([1, 2, 1])
    with cols[1]:
        saisie = st.text_input("Code :", type="password")
        if st.button("Déverrouiller", use_container_width=True):
            if saisie == CODE_SECRET:
                st.session_state["auth"] = True
                st.rerun()
            else:
                st.error("Code incorrect.")
    st.stop()

# --- TITRE ---
st.markdown("<h1 style='text-align: center; color: #15803d;'>📖 Mon Bilan Coran</h1>", unsafe_allow_html=True)

# --- RECAPITULATIF ---
if not df.empty:
    recap_df = df.copy()
    recap_df["Progression"] = (recap_df["Page Actuelle"] / 604 * 100).round(1).astype(str) + "%"
    st.table(recap_df[["Rythme", "Cycles Finis", "Page Actuelle", "Progression"]])

    # --- ACTIONS ---
    col_a, col_b, col_c = st.columns(3)
    
    with col_b:
        with st.expander("📝 Mise à jour"):
            user = st.selectbox("Personne :", df.index)
            p_act = st.number_input("Page actuelle :", 1, 604, int(df.loc[user, "Page Actuelle"]))
            r_act = st.number_input("Rythme :", 1, 100, int(df.loc[user, "Rythme"]))
            if st.button("💾 Enregistrer"):
                df.loc[user, ["Page Actuelle", "Rythme"]] = [p_act, r_act]
                # Sauvegarde vers Google Sheets
                conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], data=df.reset_index())
                st.success("Synchronisé !")
                st.rerun()
    # ... (le reste du code pour les messages et le planning est identique)
