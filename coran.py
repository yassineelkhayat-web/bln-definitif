import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os

# --- CONFIGURATION SÉCURITÉ ---
CODE_SECRET = "Yassine05"

# --- CONFIGURATION DU FICHIER ---
dossier_actuel = os.path.dirname(__file__)
DATA_FILE = os.path.join(dossier_actuel, "sauvegarde_lecture.csv")

# Données issues de ton image (Nom: [Page_Départ, Rythme/Obj_Lect, Cycles])
donnees_initiales = {
    "ABLA": [1, 15, 0],
    "ELEL": [1, 15, 0],
    "ISRE": [1, 13, 0],
    "MKAI": [1, 10, 0],
    "SOCH": [1, 13, 0],
    "SOMO": [1, 10, 0],
    "TADA": [1, 10, 0],
    "YAEL": [1, 20, 0],
    "ZAHO": [1, 10, 0]
}

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE, index_col=0)
else:
    df = pd.DataFrame.from_dict(donnees_initiales, orient='index', columns=["Page Actuelle", "Rythme", "Cycles Finis"])
    df.index.name = "Nom"
    df.to_csv(DATA_FILE)

st.set_page_config(page_title="Bilan", layout="wide")

# --- SYSTÈME DE VERRU ---
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.title("🔐 Accès Sécurisé")
    saisie = st.text_input("Veuillez entrer le code d'accès :", type="password")
    if st.button("Déverrouiller"):
        if saisie == CODE_SECRET:
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("Code incorrect.")
    st.stop()

# --- INTERFACE PRINCIPALE ---
st.title("📖 Bilan")

# --- BARRE LATÉRALE (AJOUT / SUPPRESSION / DÉCONNEXION) ---
with st.sidebar:
    st.header("Paramètres")
    nom_saisie = st.text_input("Ajouter un prénom :")
    if st.button("➕ Ajouter"):
        if nom_saisie and nom_saisie not in df.index:
            df.loc[nom_saisie] = [1, 2, 0]
            df.to_csv(DATA_FILE)
            st.rerun()
    
    if not df.empty:
        st.divider()
        cible = st.selectbox("Supprimer un profil :", df.index)
        if st.button("🗑️ Supprimer"):
            df = df.drop(cible)
            df.to_csv(DATA_FILE)
            st.rerun()
    
    st.divider()
    if st.button("🔒 Déconnexion"):
        st.session_state["auth"] = False
        st.rerun()

# --- CONTENU ---
if not df.empty:
    st.subheader("récapitulatif")
    recap_df = df.copy()
    recap_df["Progression"] = (recap_df["Page Actuelle"] / 604 * 100).round(1).astype(str) + "%"
    st.table(recap_df[["Rythme", "Cycles Finis", "Page Actuelle", "Progression"]])

    # --- MENUS DÉPLOYABLES (MESSAGE / MAJ / PRÉCISION) ---
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        with st.expander("💬 Générer message"):
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
        with st.expander("📝 Mise à jour (Aujourd'hui)"):
            user = st.selectbox("Personne :", df.index, key="up")
            p_act = st.number_input("Page actuelle :", 1, 604, int(df.loc[user, "Page Actuelle"]))
            r_act = st.number_input("Rythme :", 1, 100, int(df.loc[user, "Rythme"]))
            if st.button("💾 Enregistrer"):
                df.loc[user, ["Page Actuelle", "Rythme"]] = [p_act, r_act]
                df.to_csv(DATA_FILE)
                st.rerun()

    with col_c:
        with st.expander("🔄 date précise"):
            user_adj = st.selectbox("Personne :", df.index, key="adj")
            d_adj = st.date_input("Date précise :", date.today())
            p_adj = st.number_input("Page à cette date :", 1, 604)
            if st.button("⚙️ Recalculer"):
                delta = (date.today() - d_adj).days
                nouvelle_p = p_adj + (int(df.loc[user_adj, "Rythme"]) * delta)
                while nouvelle_p > 604: nouvelle_p -= 604
                while nouvelle_p < 1: nouvelle_p += 604
                df.loc[user_adj, "Page Actuelle"] = nouvelle_p
                df.to_csv(DATA_FILE)
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
else:
    st.info("Ajoutez des prénoms dans la barre latérale.")