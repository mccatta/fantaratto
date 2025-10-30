import streamlit as st
import requests
import pandas as pd
import uuid
from datetime import datetime

# =======================
# CONFIGURAZIONE SUPABASE
# =======================
SUPABASE_URL = "https://kcakeewkrmxyldvcpdbe.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiIsImtjYWtlZXdrcm14eWxkdmNwZGJlIiwicm9sZSIsImFub24iLCJpYXQiOjE3NjE4MjM0MjUsImV4cCI6MjA3NzM5OTQyNX0.-3vvufy6budEU-HwTU-4I0sNfRn7QWN0kad1bJN4BD8"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

GIOCATORI = ["Ali", "Ale", "Ani", "Catta", "Corra", "Dada", "Gabbo", "Giugi", "Pippo", "Ricky", "Sert", "Simo", "Sofi"]

# =======================
# FUNZIONI DI SUPPORTO
# =======================
def supabase_get(table):
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=*"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        return r.json()
    else:
        st.error(f"Errore nel caricamento di {table}: {r.text}")
        return []

def supabase_insert(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    r = requests.post(url, headers=HEADERS, json=data)
    if r.status_code not in [200, 201]:
        st.error(f"Errore inserimento in {table}: {r.text}")
    return r

def supabase_patch(table, match_field, match_value, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{match_field}=eq.{match_value}"
    r = requests.patch(url, headers=HEADERS, json=data)
    return r.status_code in [200, 204]

# =======================
# UI PRINCIPALE
# =======================
st.set_page_config(page_title="🐀 Fantaratto", page_icon="🐀", layout="centered")
st.title("🐀 Fantaratto")

menu = st.sidebar.radio("Naviga", ["Proposte", "Votazioni", "Classifica", "Costituzione"])

# =======================
# SEZIONE PROPOSTE
# =======================
if menu == "Proposte":
    st.header("📣 Invia una nuova proposta")

    proponente = st.selectbox("Chi propone", GIOCATORI)
    bersaglio = st.selectbox("Chi riceve i punti", [g for g in GIOCATORI if g != proponente])
    punti = st.number_input("Punti ratto (negativi = gesto buono)", min_value=-50.0, max_value=50.0, step=1.0)
    punti = int(punti)
    motivazione = st.text_area("Motivazione")

    if st.button("Invia proposta"):
        if not motivazione.strip():
            st.warning("⚠️ Inserisci una motivazione.")
        else:
            proposta = {
                "id": str(uuid.uuid4()),
                "proponente": proponente,
                "bersaglio": bersaglio,
                "punti": punti,
                "motivazione": motivazione,
                "data": datetime.utcnow().isoformat(),
                "approvata": False
            }
            res = supabase_insert("proposte", proposta)
            if res.status_code in [200, 201]:
                st.success("✅ Proposta inviata con successo!")
            else:
                st.error("❌ Errore nel salvataggio della proposta.")

    st.markdown("---")
    st.subheader("📋 Tutte le proposte")
    proposte = supabase_get("proposte")

    if proposte:
        df = pd.DataFrame(proposte)
        st.dataframe(df[["proponente", "bersaglio", "punti", "motivazione", "approvata", "data"]], use_container_width=True)
    else:
        st.info("Nessuna proposta presente.")

# =======================
# SEZIONE VOTAZIONI
# =======================
elif menu == "Votazioni":
    st.header("🗳️ Vota le proposte")

    votante = st.selectbox("Chi sta votando?", GIOCATORI)
    proposte = supabase_get("proposte")
    voti = supabase_get("voti")

    if not proposte:
        st.info("Nessuna proposta da votare.")
    else:
        for p in proposte:
            if p.get("approvata"):
                continue

            st.divider()
            st.subheader(f"{p['proponente']} → {p['bersaglio']} ({p['punti']} punti)")
            st.write(p["motivazione"])

            ha_votato = any(v for v in voti if v["proposta_id"] == p["id"] and v["votante"] == votante)
            if ha_votato:
                st.caption("Hai già votato questa proposta ✅")
                continue

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"👍 Approva {p['id']}", key=f"yes_{p['id']}_{votante}"):
                    voto = {
                        "id": str(uuid.uuid4()),
                        "proposta_id": p["id"],
                        "votante": votante,
                        "voto": True
                    }
                    supabase_insert("voti", voto)
                    st.success("Hai approvato la proposta ✅")

            with col2:
                if st.button(f"👎 Rifiuta {p['id']}", key=f"no_{p['id']}_{votante}"):
                    voto = {
                        "id": str(uuid.uuid4()),
                        "proposta_id": p["id"],
                        "votante": votante,
                        "voto": False
                    }
                    supabase_insert("voti", voto)
                    st.error("Hai rifiutato la proposta ❌")

            # Ricontrolla voti dopo ogni azione
            voti = supabase_get("voti")
            voti_assoc = [v for v in voti if v["proposta_id"] == p["id"]]
            votanti_unici = {v["votante"] for v in voti_assoc}

            if len(votanti_unici) == len(GIOCATORI):
                tutti_si = all(v["voto"] for v in voti_assoc)
                supabase_patch("proposte", "id", p["id"], {"approvata": tutti_si})
                if tutti_si:
                    st.success("🎉 Proposta approvata all'unanimità!")
                else:
                    st.info("❌ Proposta rifiutata (non unanime).")

# =======================
# SEZIONE CLASSIFICA
# =======================
elif menu == "Classifica":
    st.header("🏆 Classifica Ratto")

    proposte = supabase_get("proposte")
    punteggi = {g: 0 for g in GIOCATORI}

    for p in proposte:
        if p.get("approvata"):
            punteggi[p["bersaglio"]] += int(p["punti"])

    df = pd.DataFrame(list(punteggi.items()), columns=["Giocatore", "Punti Ratto"]).sort_values("Punti Ratto", ascending=False)
    st.dataframe(df, use_container_width=True)

# =======================
# SEZIONE COSTITUZIONE
# =======================
elif menu == "Costituzione":
    st.header("📜 Costituzione del Fantaratto")
    pdf = st.file_uploader("Carica la Costituzione (PDF)", type=["pdf"])
    if pdf:
        st.download_button("📥 Scarica Costituzione", pdf, file_name="costituzione_fantaratto.pdf")
