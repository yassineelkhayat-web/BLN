import streamlit as st
import pandas as pd
from upstash_redis import Redis

# Connexion aux identifiants Upstash
URL = st.secrets["UPSTASH_URL"]
TOKEN = st.secrets["UPSTASH_TOKEN"]
redis = Redis(url=URL, token=TOKEN)

st.title("📖 Bilan Coran Sync")

# Charger les données depuis Upstash
def load_data():
    data = redis.get("bilan_data")
    if data:
        return pd.read_json(data)
    # Liste par défaut si la base est vide
    return pd.DataFrame([{"Nom": "ABLA", "Page": 1}, {"Nom": "YAEL", "Page": 1}])

# Sauvegarder sur Upstash
def save_data(df):
    redis.set("bilan_data", df.to_json())

df = load_data()

# Formulaire pour l'iPad et le PC
with st.expander("Modifier une page"):
    nom = st.selectbox("Nom", df["Nom"].tolist())
    page = st.number_input("Nouvelle Page", 1, 604)
    if st.button("Enregistrer"):
        df.loc[df["Nom"] == nom, "Page"] = page
        save_data(df)
        st.success("Synchronisé !")
        st.rerun()

st.table(df)
