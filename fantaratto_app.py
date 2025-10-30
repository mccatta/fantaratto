import streamlit as st
import requests
import pandas as pd
import uuid
from datetime import datetime

# =======================
# CONFIGURAZIONE SUPABASE
# =======================
SUPABASE_URL = "https://kcakeewkrmxyldvcpdbe.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtjYWtlZXdrcm14eWxkdmNwZGJlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE4MjM0MjUsImV4cCI6MjA3NzM5OTQyNX0.-3vvufy6budEU-HwTU-4I0sNfRn7QWN0kad1bJN4BD8"

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

menu = st.sidebar.radio("Naviga", ["Proposte", "Votazioni", "Classifica", "Storico Proposte", "Costituzione"])

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
                "approvata": False,
                "data": datetime.utcnow().isoformat()
            }
            res = supabase_insert("proposte", proposta)
            if res is not None and res.status_code in [200, 201]:
                st.success("✅ Proposta inviata con successo!")
            else:
                st.error("❌ Errore nel salvataggio della proposta.")

    st.markdown("---")
    st.subheader("📋 Tutte le proposte")
    proposte = supabase_get("proposte")
    proposte = sorted(proposte, key=lambda x: x.get("data", ""), reverse=True)
    if proposte:
        df = pd.DataFrame(proposte)
        # Normalizza colonne presenti
        cols = []
        for c in ["proponente", "bersaglio", "punti", "motivazione", "approvata", "data"]:
            if c in df.columns:
                cols.append(c)
        st.dataframe(df[cols], use_container_width=True)
    else:
        st.info("Nessuna proposta presente.")

# =======================
# SEZIONE VOTAZIONI
# =======================
elif menu == "Votazioni":
    st.header("🗳️ Vota le proposte")

    votante = st.selectbox("Chi sta votando?", GIOCATORI)

    # Carica proposte e voti da Supabase
    proposte = supabase_get("proposte")
    voti = supabase_get("voti")

    # Ordina le proposte in ordine temporale (più recente prima)
    proposte = sorted(proposte, key=lambda x: x.get("id", ""), reverse=True)

    # Trova i voti dell'utente corrente
    voti_votante = {v["proposta_id"] for v in voti if v.get("votante") == votante}

    # Dividi in attive e concluse
    proposte_attive = [p for p in proposte if not p.get("approvata") and p["id"] not in voti_votante]
    proposte_concluse = [p for p in proposte if p.get("approvata")]

    # ===============================
    # PROPOSTE ATTIVE
    # ===============================
    st.subheader("🔹 Proposte attive (non ancora votate)")

    if not proposte_attive:
        st.info("Hai già votato tutte le proposte attive ✅")
    else:
        for p in proposte_attive:
            st.divider()
            st.write(f"**Proponente:** {p['proponente']}")
            st.write(f"**Bersaglio:** {p['bersaglio']}")
            st.write(f"**Punti:** {p['punti']}")
            st.write(f"**Motivazione:** {p['motivazione']}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"👍 Approva - {p['id']}", key=f"yes_{p['id']}_{votante}"):
                    voto = {
                        "id": str(uuid.uuid4()),
                        "proposta_id": p["id"],
                        "votante": votante,
                        "voto": True
                    }
                    supabase_insert("voti", voto)
                    st.success("Hai approvato la proposta ✅")
                    st.rerun()

            with col2:
                if st.button(f"👎 Rifiuta - {p['id']}", key=f"no_{p['id']}_{votante}"):
                    voto = {
                        "id": str(uuid.uuid4()),
                        "proposta_id": p["id"],
                        "votante": votante,
                        "voto": False
                    }
                    supabase_insert("voti", voto)
                    st.error("Hai rifiutato la proposta ❌")
                    st.rerun()

    # ===============================
    # CONTROLLO MAGGIORANZA AUTOMATICO
    # ===============================
    voti = supabase_get("voti")  # aggiorna lista voti
    for p in proposte:
        if p.get("approvata"):
            continue  # già gestita

        proposta_id = p.get("id")
        voti_assoc = [v for v in voti if v.get("proposta_id") == proposta_id]
        votanti_unici = {v.get("votante") for v in voti_assoc if v.get("votante") is not None}

        # Applica la regola della maggioranza solo se tutti hanno votato
        if len(votanti_unici) == len(GIOCATORI):
            yes_votes = sum(1 for v in voti_assoc if v.get("voto"))
            approvata = yes_votes > len(GIOCATORI) / 2
            supabase_patch("proposte", "id", proposta_id, {"approvata": approvata})

    # ===============================
    # PROPOSTE CONCLUSE
    # ===============================
    st.markdown("---")
    st.subheader("📜 Proposte concluse")

    if not proposte_concluse:
        st.info("Non ci sono ancora proposte concluse.")
    else:
        for p in proposte_concluse:
            stato = "✅ Approvata" if p["approvata"] else "❌ Rifiutata"
            st.write(f"**{p['proponente']} → {p['bersaglio']} ({p['punti']} punti)** — {stato}")
            st.caption(p["motivazione"])

# =======================
# SEZIONE CLASSIFICA (Opzione B: Rank come indice)
# =======================
elif menu == "Classifica":
      st.header("🏆 Classifica Ratto")

      proposte = supabase_get("proposte")
      punteggi = {g: 0 for g in GIOCATORI}
 
      for p in proposte:
         if isinstance(p, dict) and p.get("approvata"):
             try:
                 punti_val = int(p.get("punti", 0))
             except:
                 punti_val = 0
             bers = p.get("bersaglio")
             if bers in punteggi:
                 punteggi[bers] += punti_val

      df = pd.DataFrame(list(punteggi.items()), columns=["Giocatore", "Punti Ratto"])
      df["Rank"] = df["Punti Ratto"].rank(method="dense", ascending=False).astype(int)
      df = df.sort_values(["Rank", "Punti Ratto"], ascending=[True, False]).reset_index(drop=True)

      display_df = df[["Rank", "Giocatore", "Punti Ratto"]].set_index("Rank")
      st.dataframe(display_df, use_container_width=True)

# =======================
# SEZIONE STORICO
# =======================
elif menu == "Storico Proposte":
    st.header("📜 Storico delle proposte")
    proposte = supabase_get("proposte")
    proposte = sorted(proposte, key=lambda x: x.get("data", ""), reverse=True)
    if proposte:
        df = pd.DataFrame(proposte)
        # mostriamo colonne coerenti con il DB
        display_cols = []
        for c in ["proponente", "bersaglio", "punti", "motivazione", "approvata", "data"]:
            if c in df.columns:
                display_cols.append(c)
        st.dataframe(df[display_cols], use_container_width=True)
    else:
        st.info("Nessuna proposta presente.")

# =======================
# SEZIONE COSTITUZIONE
# =======================
elif menu == "Costituzione":
    st.header("📜 Costituzione del Fantaratto")
    pdf = st.file_uploader("Carica la Costituzione (PDF)", type=["pdf"])
    if pdf:
        st.download_button("📥 Scarica Costituzione", pdf, file_name="costituzione_fantaratto.pdf")
