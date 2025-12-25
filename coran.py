import streamlit as st
import pandas as pd
from datetime import date, timedelta
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION ET CAMOUFLAGE TOTAL (ANTI-LOGOS) ---
st.set_page_config(page_title="Bilan Coran", layout="wide", initial_sidebar_state="collapsed")

# Cache les menus, le footer et le bouton Deploy pour un aspect application pro
st.markdown("""
    <style>
    [data-testid="stHeader"] {display: none !important;}
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .stAppDeployButton {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    .block-container {padding-top: 2rem !important;}
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
        st.error("La colonne 'Nom' est introuvable dans le Google Sheet.")
        st.stop()
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()

# --- 3. SÉCURITÉ ---
CODE_SECRET = "Yassine05"
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.markdown("<h2 style='text-align: center;'>🔐 Accès Sécurisé</h2>", unsafe_allow_html=True)
    cols = st.columns([1, 2, 1])
    with cols[1]:
        saisie = st.text_input("Code d'accès :", type="password")
        if st.button("Déverrouiller", use_container_width=True):
            if saisie == CODE_SECRET:
                st.session_state["auth"] = True
                st.rerun()
            else:
                st.error("Code incorrect.")
    st.stop()

# --- 4. INTERFACE ---
st.markdown("<h1 style='text-align: center; color: #15803d;'>📖 Mon Bilan Coran</h1>", unsafe_allow_html=True)

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("⚙️ Paramètres")
    nom_saisie = st.text_input("Ajouter un prénom :")
    if st.button("➕ Ajouter"):
        if nom_saisie and nom_saisie not in df.index:
            new_row = pd.DataFrame({"Page Actuelle": [1], "Rythme": [10], "Cycles Finis": [0]}, index=[nom_saisie])
            df = pd.concat([df, new_row])
            conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], data=df.reset_index())
            st.rerun()
    
    if not df.empty:
        st.divider()
        cible = st.selectbox("Supprimer un profil :", df.index)
        if st.button("🗑️ Supprimer"):
            df = df.drop(cible)
            conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], data=df.reset_index())
            st.rerun()
    
    st.divider()
    if st.button("🔒 Déconnexion"):
        st.session_state["auth"] = False
        st.rerun()

# --- 5. FONCTIONNALITÉS ---
if not df.empty:
    st.subheader("📊 Récapitulatif")
    recap_df = df.copy()
    recap_df["Page Actuelle"] = pd.to_numeric(recap_df["Page Actuelle"])
    recap_df["Progression"] = (recap_df["Page Actuelle"] / 604 * 100).round(1).astype(str) + "%"
    st.table(recap_df[["Rythme", "Cycles Finis", "Page Actuelle", "Progression"]])

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        with st.expander("💬 Message"):
            date_cible = st.date_input("Échéance :", date.today() + timedelta(days=3))
            jours = (date_cible - date.today()).days
            nom_jour = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"][date_cible.weekday()]
            msg = f"Salam, voici la page à laquelle il faut arriver pour {nom_jour} :\n\n"
            for n, row in df.iterrows():
                p_obj = int(row["Page Actuelle"]) + (int(row["Rythme"]) * jours)
                while p_obj > 604: p_obj -= 604
                msg += f"{n.upper()} : p.{p_obj}\n"
            st.text_area("Copier :", value=msg, height=150)

    with col_b:
        with st.expander("📝 Mise à jour"):
            user = st.selectbox("Personne :", df.index, key="up")
            p_act = st.number_input("Page :", 1, 604, int(df.loc[user, "Page Actuelle"]))
            r_act = st.number_input("Rythme :", 1, 100, int(df.loc[user, "Rythme"]))
            if st.button("💾 Enregistrer"):
                df.loc[user, ["Page Actuelle", "Rythme"]] = [p_act, r_act]
                conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], data=df.reset_index())
                st.success("Synchro OK !")
                st.rerun()

    with col_c:
        with st.expander("🔄 Date précise"):
            user_adj = st.selectbox("Personne :", df.index, key="adj")
            d_adj = st.date_input("Date précise :", date.today())
            p_adj = st.number_input("Page à cette date :", 1, 604)
            if st.button("⚙️ Recalculer"):
                delta = (date.today() - d_adj).days
                nouvelle_p = p_adj + (int(df.loc[user_adj, "Rythme"]) * delta)
                while nouvelle_p > 604: nouvelle_p -= 604
                while nouvelle_p < 1: nouvelle_p += 604
                df.loc[user_adj, "Page Actuelle"] = nouvelle_p
                conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], data=df.reset_index())
                st.rerun()

    st.divider()
    st.subheader("📅 Planning Global (30 jours)")
    dates_list = [(date.today() + timedelta(days=i)) for i in range(30)]
    planning = pd.DataFrame(index=[d.strftime("%d/%m") for d in dates_list])
    for nom_l, row in df.iterrows():
        pages = []
        curr = int(row["Page Actuelle"])
        for i in range(30):
            if i > 0:
                curr += int(row["Rythme"])
                while curr > 604: curr -= 604
            pages.append(curr)
        planning[nom_l] = pages
    st.dataframe(planning, use_container_width=True)
