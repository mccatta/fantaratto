import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# === CONFIGURAZIONE SUPABASE ===
SUPABASE_URL = "https://kcakeewkrmxyldvcpdbe.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtjYWtlZXdrcm14eWxkdmNwZGJlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE4MjM0MjUsImV4cCI6MjA3NzM5OTQyNX0.-3vvufy6budEU-HwTU-4I0sNfRn7QWN0kad1bJN4BD8"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

GIOCATORI = ["Ali", "Ale", "Ani", "Catta", "Corra", "Dada", "Gabbo",
             "Giugi", "Pippo", "Ricky", "Sert", "Simo", "Sofi"]

st.set_page_config(page_title="Fantaratto", layout="centered")

# === FUNZIONI SUPABASE ===
def supabase_get(table):
    try:
        res = supabase.table(table).select("*").execute()
        return res.data or []
    except Exception as e:
        st.error(f"Errore caricamento {table}: {e}")
        return []

def supabase_insert(table, data):
    try:
        res = supabase.table(table).insert(data).execute()
        return res.data
    except Exception as e:
        st.error(f"Errore inserimento in {table}: {e}")
        return None

def supabase_patch(table, key, value, data):
    try:
        res = supabase.table(table).update(data).eq(key, value).execute()
        return res.data
    except Exception as e:
        st.error(f"Errore aggiornamento {table}: {e}")
        return None


# === INTERFACCIA ===
st.title("🐀 Fantaratto")
menu = st.sidebar.selectbox("Menu", ["Nuova proposta", "Vota", "Classifica", "Storico"])

# === NUOVA PROPOSTA ===
if menu == "Nuova proposta":
    st.header("➕ Crea una nuova proposta")

    proponente = st.selectbox("Chi propone?", GIOCATORI)
    bersaglio = st.selectbox("Chi è il bersaglio?", [g for g in GIOCATORI if g != proponente])
    punti = st.number_input("Quanti punti (+ o -)?", step=1, format="%d")
    motivazione = st.text_area("Motivazione")

    if st.button("Invia proposta"):
        if not motivazione.strip():
            st.warning("Scrivi una motivazione!")
        else:
            data = {
                "proponente": proponente,
                "bersaglio": bersaglio,
                "punti": int(punti),
                "motivazione": motivazione.strip(),
                "approvata": False,
                "data": datetime.now().isoformat()
            }
            supabase_insert("proposte", data)
            st.success("✅ Proposta inviata!")

# === VOTA ===
elif menu == "Vota":
    st.header("🗳️ Vota le proposte")

    votante = st.selectbox("Chi sei?", GIOCATORI)
    proposte = supabase_get("proposte")
    voti = supabase_get("voti")

    for p in proposte:
        proposta_id = p.get("id")
        if proposta_id is None:
            continue

        # Mostra solo le proposte non ancora approvate
        if not p.get("approvata", False):
            st.subheader(f"{p['proponente']} → {p['bersaglio']} ({p['punti']} punti)")
            st.caption(p["motivazione"])

            # Verifica se ha già votato
            ha_votato = any(v.get("votante") == votante and v.get("proposta_id") == proposta_id for v in voti)
            if ha_votato:
                st.info("Hai già votato questa proposta.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("👍 Approva", key=f"ok_{proposta_id}_{votante}"):
                        supabase_insert("voti", {"proposta_id": proposta_id, "votante": votante, "voto": True})
                        st.success("Voto registrato!")
                with col2:
                    if st.button("👎 Boccia", key=f"no_{proposta_id}_{votante}"):
                        supabase_insert("voti", {"proposta_id": proposta_id, "votante": votante, "voto": False})
                        st.success("Voto registrato!")

    # Verifica se una proposta ha ricevuto tutti i voti
    voti = supabase_get("voti")
    for p in proposte:
        proposta_id = p.get("id")
        if proposta_id is None:
            continue

        voti_assoc = [v for v in voti if v.get("proposta_id") == proposta_id]
        votanti_unici = {v.get("votante") for v in voti_assoc if v.get("votante") is not None}

        if len(votanti_unici) == len(GIOCATORI):
            yes_votes = sum(1 for v in voti_assoc if v.get("voto"))
            approvata = yes_votes > len(GIOCATORI) / 2
            supabase_patch("proposte", "id", proposta_id, {"approvata": approvata})

# === CLASSIFICA ===
elif menu == "Classifica":
    st.header("🏆 Classifica Attuale")

    proposte = supabase_get("proposte")
    df = pd.DataFrame(proposte)
    if not df.empty:
        df_approvate = df[df["approvata"] == True]
        classifica = df_approvate.groupby("bersaglio")["punti"].sum().reindex(GIOCATORI, fill_value=0)
        st.bar_chart(classifica)
    else:
        st.info("Nessuna proposta ancora approvata.")

# === STORICO ===
elif menu == "Storico":
    st.header("📜 Storico Proposte")
    proposte = supabase_get("proposte")
    df = pd.DataFrame(proposte)

    if not df.empty:
        st.dataframe(
            df[["proponente", "bersaglio", "punti", "motivazione", "approvata", "data"]],
            use_container_width=True
        )
    else:
        st.info("Nessuna proposta registrata ancora.")
