import streamlit as st
import pandas as pd
from upstash_redis import Redis

# --- 1. CONNEXION AUX SECRETS ---
# Ces noms doivent être IDENTIQUES à ceux dans tes "Secrets" Streamlit
try:
    URL = st.secrets["UPSTASH_URL"]
    TOKEN = st.secrets["UPSTASH_TOKEN"]
    redis = Redis(url=URL, token=TOKEN)
except Exception as e:
    st.error("Erreur de configuration : Vérifie tes Secrets (URL ou TOKEN manquants).")
    st.stop()

st.set_page_config(page_title="Bilan Coran Sync", layout="wide")
st.title("📖 Suivi Coran - Synchronisation iPad/PC")

# --- 2. FONCTIONS DE CHARGEMENT ET SAUVEGARDE ---
def load_data():
    try:
        # On essaie de récupérer les données sur Upstash
        data = redis.get("bilan_data")
        if data:
            # Si les données existent, on les transforme en tableau
            return pd.read_json(str(data))
    except Exception:
        # Si la base est vide ou erreur, on ne bloque pas le programme
        pass
    
    # Données de départ par défaut
    return pd.DataFrame([
        {"Nom": "ABLA", "Page": 1, "Rythme": 10},
        {"Nom": "YAEL", "Page": 1, "Rythme": 10},
        {"Nom": "ISRE", "Page": 1, "Rythme": 10},
        {"Nom": "ELEL", "Page": 1, "Rythme": 10}
    ])

def save_data(df_to_save):
    # On transforme le tableau en texte JSON pour l'envoyer sur Upstash
    redis.set("bilan_data", df_to_save.to_json())

# Charger les données au démarrage
df = load_data()

# --- 3. INTERFACE DE MISE À JOUR ---
with st.expander("📝 Enregistrer une progression"):
    nom_choisi = st.selectbox("Choisir l'élève", df["Nom"].tolist())
    
    # On récupère les valeurs actuelles pour les afficher par défaut
    current_page = int(df.loc[df["Nom"] == nom_choisi, "Page"].values[0])
    current_rythme = int(df.loc[df["Nom"] == nom_choisi, "Rythme"].values[0])
    
    nouvelle_page = st.number_input("Page actuelle", 1, 604, value=current_page)
    nouveau_rythme = st.number_input("Pages par jour", 1, 100, value=current_rythme)
    
    if st.button("💾 Synchroniser avec l'iPad"):
        # Mise à jour du tableau
        df.loc[df["Nom"] == nom_choisi, ["Page", "Rythme"]] = [nouvelle_page, nouveau_rythme]
        # Envoi vers Upstash
        save_data(df)
        st.success(f"Bravo ! Les données de {nom_choisi} sont à jour.")
        st.rerun()

# --- 4. AFFICHAGE DES RÉSULTATS ---
st.subheader("📊 État de la classe")
st.dataframe(df, use_container_width=True)

# Petit calcul rapide pour le plaisir
st.info("💡 Dès que tu modifies une page ici, l'iPad se met à jour instantanément.")
