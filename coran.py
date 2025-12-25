import streamlit as st
import pandas as pd
from datetime import date, timedelta
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION ET CAMOUFLAGE ---
st.set_page_config(page_title="Bilan Coran PRO", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stHeader"] {display: none !important;}
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .stAppDeployButton {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    .block-container {padding-top: 2rem !important;}
    stTable {width: 100%;}
    </style>
""", unsafe_allow_html=True)

# --- 2. CONNEXION GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet=0, ttl=0)
    df.columns = df.columns.str.strip()
    df = df.dropna(how='all')
    if "Nom" in df.columns:
        df.set_index("Nom", inplace=True)
    else:
        st.error("Colonne 'Nom' manquante dans le Google Sheet.")
        st.stop()
except Exception as e:
    st.error(f"Erreur de synchronisation : {e}")
    st.stop()

# --- 3. SÉCURITÉ ---
CODE_SECRET = "Y"
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.markdown("<h2 style='text-align: center;'>🔐 Accès Sécurisé</h2>", unsafe_allow_html=True)
    cols = st.columns([1, 2, 1])
    with cols[1]:
        saisie = st.text_input("Entrez le code :", type="password")
        if st.button("Valider", use_container_width=True):
            if saisie == CODE_SECRET:
                st.session_state["auth"] = True
                st.rerun()
            else:
                st.error("Code incorrect.")
    st.stop()

# --- 4. TITRE ---
st.markdown("<h1 style='text-align: center; color: #15803d;'>📖 Suivi de Lecture Coran</h1>", unsafe_allow_html=True)

# --- 5. BARRE LATÉRALE (GESTION DES PROFILS) ---
with st.sidebar:
    st.header("👤 Profils")
    nouveau_nom = st.text_input("Nouveau prénom :")
    if st.button("➕ Ajouter"):
        if nouveau_nom and nouveau_nom not in df.index:
            new_data = pd.DataFrame({"Page Actuelle": [1], "Rythme": [10], "Cycles Finis": [0]}, index=[nouveau_nom])
            df = pd.concat([df, new_data])
            conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], data=df.reset_index())
            st.success(f"{nouveau_nom} ajouté !")
            st.rerun()
    
    st.divider()
    if not df.empty:
        nom_suppr = st.selectbox("Supprimer un compte :", df.index)
        if st.button("🗑️ Supprimer définitivement"):
            df = df.drop(nom_suppr)
            conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], data=df.reset_index())
            st.rerun()
    
    st.divider()
    if st.button("🔒 Déconnexion"):
        st.session_state["auth"] = False
        st.rerun()

# --- 6. AFFICHAGE ET FONCTIONNALITÉS ---
if not df.empty:
    # --- TABLEAU DE BORD ---
    st.subheader("📊 État de la progression")
    recap = df.copy()
    recap["Page Actuelle"] = pd.to_numeric(recap["Page Actuelle"])
    recap["Progression"] = (recap["Page Actuelle"] / 604 * 100).round(1).astype(str) + "%"
    
    # Affichage propre
    st.table(recap[["Page Actuelle", "Rythme", "Cycles Finis", "Progression"]])

    st.divider()

    # --- ACTIONS ---
    col1, col2, col3 = st.columns(3)

    with col1:
        with st.expander("📝 Mise à jour Quotidienne"):
            p_nom = st.selectbox("Qui ?", df.index, key="daily")
            p_val = st.number_input("Nouvelle Page :", 1, 604, int(df.loc[p_nom, "Page Actuelle"]))
            r_val = st.number_input("Nouveau Rythme :", 1, 100, int(df.loc[p_nom, "Rythme"]))
            
            if st.button("💾 Enregistrer"):
                # Si la nouvelle page est inférieure à l'ancienne, on considère qu'un cycle est fini
                if p_val < int(df.loc[p_nom, "Page Actuelle"]):
                    df.loc[p_nom, "Cycles Finis"] = int(df.loc[p_nom, "Cycles Finis"]) + 1
                
                df.loc[p_nom, "Page Actuelle"] = p_val
                df.loc[p_nom, "Rythme"] = r_val
                conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], data

