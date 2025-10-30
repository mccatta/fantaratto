import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

# =============== CONFIGURAZIONE ===============
SUPABASE_URL = "https://kcakeewkrmxyldvcpdbe.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtjYWtlZXdrcm14eWxkdmNwZGJlIiwicm9sZSIsImFub24iLCJpYXQiOjE3NjE4MjM0MjUsImV4cCI6MjA3NzM5OTQyNX0.-3vvufy6budEU-HwTU-4I0sNfRn7QWN0kad1bJN4BD8"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

GIOCATORI = ["Ali", "Ale", "Ani", "Catta", "Corra", "Dada", "Gabbo", "Giugi", "Pippo", "Ricky", "Sert", "Simo", "Sofi"]

# =============== FUNZIONI DB ===============
def carica_proposte():
    url = f"{SUPABASE_URL}/rest/v1/proposte?select=*"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()
    return []

def salva_proposta(proponente, bersaglio, punti, motivazione):
    url = f"{SUPABASE_URL}/rest/v1/proposte"
    data = [{
        "proponente": proponente,
        "bersaglio": bersaglio,
        "punti": punti,
        "motivazione": motivazione,
        "approvata": False,
        "data": datetime.now().isoformat()
    }]
    res = requests.post(url, headers=headers, data=json.dumps(data))
    return res.status_code in [200, 201]

def carica_voti():
    url = f"{SUPABASE_URL}/rest/v1/voti?select=*"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()
    return []

def salva_voto(proposta_id, votante, voto):
    url = f"{SUPABASE_URL}/rest/v1/voti"
    data = [{
        "proposta_id": proposta_id,
        "votante": votante,
        "voto": voto
    }]
    res = requests.post(url, headers=headers, data=json.dumps(data))
    return res.status_code in [200, 201]

def aggiorna_proposta(proposta_id, approvata=True):
    url = f"{SUPABASE_URL}/rest/v1/proposte?id=eq.{proposta_id}"
    data = {"approvata": approvata}
    requests.patch(url, headers=headers, data=json.dumps(data))

# =============== INTERFACCIA STREAMLIT ===============
st.set_page_config(page_title="Fantaratto", page_icon="🐀", layout="centered")

menu = st.sidebar.selectbox("Naviga", ["📜 Proposte", "🗳️ Votazioni", "🏆 Classifica", "📘 Costituzione"])

# ---- SEZIONE PROPOSTE ----
if menu == "📜 Proposte":
    st.title("📜 Proposte Fantaratto")

    st.subheader("Nuova proposta")
    col1, col2 = st.columns(2)
    with col1:
        proponente = st.selectbox("Chi propone", GIOCATORI)
        bersaglio = st.selectbox("A chi vanno i punti ratto", [g for g in GIOCATORI if g != proponente])
    with col2:
punti = st.number_input("Punti ratto (negativi = gesto buono)", min_value=-10, max_value=10, step=1)
        motivazione = st.text_area("Motivazione")

    if st.button("💾 Invia proposta"):
        if salva_proposta(proponente, bersaglio, punti, motivazione):
            st.success("✅ Proposta salvata!")
        else:
            st.error("❌ Errore nel salvataggio della proposta.")

    st.divider()
    st.subheader("Proposte esistenti")
    proposte = carica_proposte()
    if proposte:
        df = pd.DataFrame(proposte)
        st.dataframe(df[["id", "proponente", "bersaglio", "punti", "motivazione", "approvata", "data"]])
    else:
        st.info("Nessuna proposta presente.")

# ---- SEZIONE VOTAZIONI ----
elif menu == "🗳️ Votazioni":
    st.title("🗳️ Vota le proposte")

    votante = st.selectbox("Chi sta votando?", GIOCATORI)
    proposte = carica_proposte()
    voti = carica_voti()

    if not proposte:
        st.info("Nessuna proposta da votare.")
    else:
        for p in proposte:
            st.write(f"**{p['proponente']} → {p['bersaglio']} ({p['punti']} punti)**")
            st.caption(p["motivazione"])

            ha_votato = any(v["votante"] == votante and v["proposta_id"] == p["id"] for v in voti)
            if not ha_votato:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"👍 Approva {p['id']}"):
                        salva_voto(p["id"], votante, True)
                        st.success("Hai votato ✅")
                with col2:
                    if st.button(f"👎 Rifiuta {p['id']}"):
                        salva_voto(p["id"], votante, False)
                        st.error("Hai votato ❌")
            else:
                st.caption("Hai già votato questa proposta.")

# ---- SEZIONE CLASSIFICA ----
elif menu == "🏆 Classifica":
    st.title("🏆 Classifica Ratti")
    proposte = carica_proposte()
    voti = carica_voti()

    punteggi = {g: 0 for g in GIOCATORI}

    for p in proposte:
        # una proposta è approvata se tutti hanno votato o la maggioranza ha approvato
        voti_assoc = [v for v in voti if v["proposta_id"] == p["id"]]
        if voti_assoc:
            approvati = sum(v["voto"] for v in voti_assoc)
            if approvati > len(GIOCATORI)//2:
                punteggi[p["bersaglio"]] += p["punti"]

    df = pd.DataFrame(list(punteggi.items()), columns=["Giocatore", "Punti Ratto"])
    st.dataframe(df.sort_values("Punti Ratto", ascending=False))

# ---- SEZIONE COSTITUZIONE ----
elif menu == "📘 Costituzione":
    st.title("📘 Costituzione del Fantaratto")
    pdf = st.file_uploader("Carica il PDF della Costituzione", type=["pdf"])
    if pdf:
        st.download_button("📄 Scarica la Costituzione", data=pdf, file_name="costituzione_fantaratto.pdf")
