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

    # Selezione del votante
    votante = st.selectbox("Chi sta votando?", ["-- Seleziona il tuo nome --"] + GIOCATORI)
    if votante == "-- Seleziona il tuo nome --":
        st.info("👆 Seleziona il tuo nome per visualizzare le proposte da votare.")
        st.stop()

    # Recupera proposte e voti dal database
    proposte = supabase_get("proposte")
    voti = supabase_get("voti")

    if not proposte:
        st.info("Nessuna proposta presente.")
    else:
        # Ordina per data (più recente prima, se presente)
        proposte = sorted(proposte, key=lambda x: x.get("data", ""), reverse=True)

        # Divide le proposte in categorie
        proposte_non_votate = [
            p for p in proposte
            if not p.get("approvata")
            and not any(v for v in voti if v.get("proposta_id") == p.get("id") and v.get("votante") == votante)
        ]

        proposte_votate_attesa = [
            p for p in proposte
            if not p.get("approvata")
            and any(v for v in voti if v.get("proposta_id") == p.get("id") and v.get("votante") == votante)
        ]

        proposte_concluse = [p for p in proposte if p.get("approvata") is not None]

        # =======================
        # PROPOSTE DA VOTARE
        # =======================
        st.subheader("🟢 Proposte attive da votare")

        if not proposte_non_votate:
            st.info("Hai già votato tutte le proposte attive 👏")
        else:
            for p in proposte_non_votate:
                st.divider()
                st.subheader(f"{p['proponente']} → {p['bersaglio']} ({p['punti']} punti)")
                st.write(p["motivazione"])

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("👍 Approva", key=f"yes_{p['id']}_{votante}"):
                        voto = {
                            "id": str(uuid.uuid4()),
                            "proposta_id": p["id"],
                            "votante": votante,
                            "voto": True
                        }
                        supabase_insert("voti", voto)
                        st.success("Hai approvato la proposta ✅")
                        st.session_state["refresh"] = True

                with col2:
                    if st.button("👎 Rifiuta", key=f"no_{p['id']}_{votante}"):
                        voto = {
                            "id": str(uuid.uuid4()),
                            "proposta_id": p["id"],
                            "votante": votante,
                            "voto": False
                        }
                        supabase_insert("voti", voto)
                        st.error("Hai rifiutato la proposta ❌")
                        st.session_state["refresh"] = True

            # 🔁 Ricarica dopo voto
            if st.session_state.get("refresh", False):
                st.session_state["refresh"] = False
                st.rerun()

        # =======================
        # PROPOSTE VOTATE (IN ATTESA)
        # =======================
        st.markdown("---")
        st.subheader("🕓 Proposte votate (in attesa di esito)")

        if not proposte_votate_attesa:
            st.info("Non ci sono proposte in attesa di esito.")
        else:
            for p in proposte_votate_attesa:
                st.divider()
                st.markdown(f"**{p['proponente']} → {p['bersaglio']}**  ({p['punti']} punti)")
                st.caption(f"Motivazione: {p['motivazione']}")

        # =======================
        # CONTROLLO MAGGIORANZA
        # =======================
        voti = supabase_get("voti")  # aggiorna lista voti
        for p in proposte:
            if p.get("approvata"):
                continue
            proposta_id = p.get("id")
            if not proposta_id:
                continue

            voti_assoc = [v for v in voti if v.get("proposta_id") == proposta_id]
            votanti_unici = {v.get("votante") for v in voti_assoc if v.get("votante")}

            if len(votanti_unici) == len(GIOCATORI):
                yes_votes = sum(1 for v in voti_assoc if v.get("voto"))
                approvata = yes_votes > len(GIOCATORI) / 2
                supabase_patch("proposte", "id", proposta_id, {"approvata": approvata})

                if approvata:
                    st.success(f"🎉 La proposta '{p['motivazione']}' è stata approvata!")
                else:
                    st.info(f"❌ La proposta '{p['motivazione']}' è stata bocciata.")

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
elif menu == "Storico proposte":
    st.header("📜 Storico proposte")

    proposte = supabase_get("proposte")

    if not proposte:
        st.info("Nessuna proposta ancora registrata.")
    else:
        # Ordina per data (più recente prima)
        proposte = sorted(proposte, key=lambda x: x.get("data", ""), reverse=True)

        for p in proposte:
            stato = p.get("approvata")

            if stato is True:
                icona = "✅"
                colore = "green"
                testo = "Approvata"
            elif stato is False:
                icona = "❌"
                colore = "red"
                testo = "Rifiutata"
            else:
                icona = "🕓"
                colore = "gray"
                testo = "In attesa"

            st.markdown(
                f"""
                <div style='border:1px solid #ddd; border-radius:10px; padding:10px; margin-bottom:10px;'>
                    <h4 style='margin:0;'>{icona} <span style='color:{colore};'>{testo}</span></h4>
                    <b>{p['proponente']}</b> → <b>{p['bersaglio']}</b> ({p['punti']} punti)<br>
                    <i>{p['motivazione']}</i><br>
                    <small>Data: {p.get('data','')}</small>
                </div>
                """,
                unsafe_allow_html=True
            )


# =======================
# SEZIONE COSTITUZIONE
# =======================
elif menu == "Costituzione":
    st.header("📜 Costituzione del Fantaratto")
    pdf = st.file_uploader("Carica la Costituzione (PDF)", type=["pdf"])
    if pdf:
        st.download_button("📥 Scarica Costituzione", pdf, file_name="costituzione_fantaratto.pdf")
