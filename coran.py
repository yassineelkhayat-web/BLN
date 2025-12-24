import streamlit as st
import pandas as pd
from datetime import date, timedelta
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
CODE_SECRET = "Yassine05"
URL_SHEET = "https://docs.google.com/spreadsheets/d/1nee3KSXpedA2JQpyPfTfreLeKNHxrXxjnNP7TrLawaA/edit?gid=0#gid=0"

st.set_page_config(page_title="Bilan Coran", layout="wide")

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

# --- CONNEXION GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # On lit les données depuis Google Sheets
    return conn.read(spreadsheet=URL_SHEET, ttl=0)

try:
    df = load_data()
    # On s'assure que les colonnes sont bien nommées
    df.columns = ["Nom", "Page Actuelle", "Rythme", "Cycles Finis"]
    df.set_index("Nom", inplace=True)
except Exception as e:
    st.error("Erreur de connexion au tableau Google. Vérifiez le partage avec l'e-mail du compte de service.")
    st.stop()

# --- INTERFACE PRINCIPALE ---
st.title("📖 Bilan de Lecture (Sync iPad/PC)")

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("Paramètres")
    nom_saisie = st.text_input("Ajouter un prénom :")
    if st.button("➕ Ajouter"):
        if nom_saisie and nom_saisie not in df.index:
            new_row = pd.DataFrame([{"Nom": nom_saisie, "Page Actuelle": 1, "Rythme": 10, "Cycles Finis": 0}])
            updated_df = pd.concat([df.reset_index(), new_row], ignore_index=True)
            conn.update(spreadsheet=URL_SHEET, data=updated_df)
            st.cache_data.clear()
            st.rerun()
    
    if not df.empty:
        st.divider()
        cible = st.selectbox("Supprimer un profil :", df.index)
        if st.button("🗑️ Supprimer"):
            updated_df = df.drop(cible).reset_index()
            conn.update(spreadsheet=URL_SHEET, data=updated_df)
            st.cache_data.clear()
            st.rerun()
    
    st.divider()
    if st.button("🔒 Déconnexion"):
        st.session_state["auth"] = False
        st.rerun()

# --- CONTENU ---
if not df.empty:
    st.subheader("📊 État des lieux actuel")
    recap_df = df.copy()
    # Calcul de progression basé sur 604 pages
    recap_df["Progression"] = (pd.to_numeric(recap_df["Page Actuelle"]) / 604 * 100).round(1).astype(str) + "%"
    st.table(recap_df[["Rythme", "Cycles Finis", "Page Actuelle", "Progression"]])

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        with st.expander("💬 Générer message"):
            date_cible = st.date_input("Échéance :", date.today() + timedelta(days=3))
            jours = (date_cible - date.today()).days
            msg = f"Objectifs pour {date_cible.strftime('%d/%m')} :\n\n"
            for n, row in df.iterrows():
                p_obj = int(row["Page Actuelle"]) + (int(row["Rythme"]) * jours)
                while p_obj > 604: p_obj -= 604
                msg += f"{n} : p.{p_obj}\n"
            st.text_area("Copier le message :", value=msg, height=200)

    with col_b:
        with st.expander("📝 Mise à jour Rapide"):
            user = st.selectbox("Personne :", df.index, key="up")
            p_act = st.number_input("Page actuelle :", 1, 604, int(df.loc[user, "Page Actuelle"]))
            r_act = st.number_input("Rythme quotidien :", 1, 100, int(df.loc[user, "Rythme"]))
            if st.button("💾 Enregistrer"):
                df.at[user, "Page Actuelle"] = p_act
                df.at[user, "Rythme"] = r_act
                conn.update(spreadsheet=URL_SHEET, data=df.reset_index())
                st.cache_data.clear()
                st.rerun()

    with col_c:
        with st.expander("⚙️ Bouton de Précision"):
            user_adj = st.selectbox("Personne :", df.index, key="adj")
            d_adj = st.date_input("Date du constat :", date.today() - timedelta(days=1))
            p_adj = st.number_input("Page lue ce jour-là :", 1, 604)
            if st.button("⚙️ Recalculer"):
                delta = (date.today() - d_adj).days
                nouvelle_p = p_adj + (int(df.loc[user_adj, "Rythme"]) * delta)
                while nouvelle_p > 604: nouvelle_p -= 604
                df.at[user_adj, "Page Actuelle"] = nouvelle_p
                conn.update(spreadsheet=URL_SHEET, data=df.reset_index())
                st.cache_data.clear()
                st.rerun()

    st.divider()
    st.subheader("📅 Planning Prévisionnel (30 jours)")
    dates_list = [(date.today() + timedelta(days=i)) for i in range(30)]
    planning = pd.DataFrame(index=[d.strftime("%d/%m") for d in dates_list])
    
    for nom_l, row in df.iterrows():
        pages = []
        curr = int(row["Page Actuelle"])
        rythme = int(row["Rythme"])
        for i in range(30):
            if i > 0:
                curr += rythme
                while curr > 604: curr -= 604
            pages.append(curr)
        planning[nom_l] = pages
    st.dataframe(planning, use_container_width=True)
else:
    st.info("Le tableau est vide. Ajoutez des participants dans la barre latérale.")
