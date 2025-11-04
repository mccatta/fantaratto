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
    st.header("🗳️ Sezione Votazioni")

    # Carica dati da Supabase
    proposte = supabase_get("proposte") or []
    voti = supabase_get("voti") or []

    # Seleziona chi sta votando
    votante = st.selectbox("Seleziona il tuo nome per votare:", [""] + GIOCATORI)
    if not votante:
        st.warning("👆 Seleziona il tuo nome per procedere con le votazioni.")
        st.stop()

    # Nessuna proposta
    if not proposte:
        st.info("Non ci sono proposte al momento.")
        st.stop()

    # === PROPOSTE ATTIVE (non ancora approvate e non ancora votate da questo utente) ===
    st.subheader("🟢 Proposte attive (non hai ancora votato)")
    attive = [p for p in proposte if not p.get("approvata") and not any(v for v in voti if v["proposta_id"] == p["id"] and v["votante"] == votante)]
    attive = sorted(attive, key=lambda x: x.get("data", ""), reverse=True)

    for p in attive:
        st.divider()
        st.subheader(f"{p['proponente']} → {p['bersaglio']} ({p['punti']} punti)")
        st.write(p["motivazione"])

        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 Approva", key=f"yes_{p['id']}_{votante}"):
                voto = {"id": str(uuid.uuid4()), "proposta_id": p["id"], "votante": votante, "voto": True}
                supabase_insert("voti", voto)
                st.success("Hai approvato la proposta ✅")
                st.rerun()

        with col2:
            if st.button("👎 Rifiuta", key=f"no_{p['id']}_{votante}"):
                voto = {"id": str(uuid.uuid4()), "proposta_id": p["id"], "votante": votante, "voto": False}
                supabase_insert("voti", voto)
                st.error("Hai rifiutato la proposta ❌")
                st.rerun()

    # === PROPOSTE IN ATTESA DI ESITO (già votate ma non ancora decise) ===
    st.subheader("🕓 Proposte in attesa di esito (hai già votato)")
    in_attesa = []
    for p in proposte:
        if p.get("approvata") is None or p.get("approvata") is False:
            voti_assoc = [v for v in voti if v.get("proposta_id") == p["id"]]
            ha_votato = any(v for v in voti_assoc if v.get("votante") == votante)
            if ha_votato and not p.get("approvata"):
                in_attesa.append(p)

    for p in sorted(in_attesa, key=lambda x: x.get("data", ""), reverse=True):
        voti_assoc = [v for v in voti if v.get("proposta_id") == p["id"]]
        votanti_unici = {v.get("votante") for v in voti_assoc if v.get("votante")}
        mancanti = [g for g in GIOCATORI if g not in votanti_unici]

        st.divider()
        st.subheader(f"{p['proponente']} → {p['bersaglio']} ({p['punti']} punti)")
        st.write(p["motivazione"])
        st.caption(f"🕓 In attesa — voti mancanti di: {', '.join(mancanti) if mancanti else 'nessuno'}")
        
# === CONTROLLO AUTOMATICO APPROVAZIONE / RIFIUTO ===
for p in proposte:
    if p.get("approvata") in [True, False]:
        continue  # già decisa

    voti_assoc = [v for v in voti if v.get("proposta_id") == p["id"]]
    if not voti_assoc:
        continue

    yes_votes = sum(1 for v in voti_assoc if v.get("voto") is True)
    no_votes = sum(1 for v in voti_assoc if v.get("voto") is False)
    total_votes = yes_votes + no_votes

    # Solo se almeno metà dei giocatori ha votato
    if total_votes >= len(GIOCATORI) / 2:
        if yes_votes > no_votes:
            approvata = True
        elif no_votes > yes_votes:
            approvata = False
        else:
            approvata = None  # parità, resta in attesa

        if approvata is not None:
            supabase_patch("proposte", "id", p["id"], {"approvata": approvata})


    # === PROPOSTE CON ESITO (approvate o rifiutate) ===
    st.subheader("📜 Proposte concluse")
    concluse = [p for p in proposte if p.get("approvata") is not None]
    concluse = sorted(concluse, key=lambda x: x.get("data", ""), reverse=True)

    for p in concluse:
        icon = "✅" if p["approvata"] else "❌"
        colore = "green" if p["approvata"] else "red"
        st.markdown(f"<span style='color:{colore}; font-size: 18px;'>{icon} {p['proponente']} → {p['bersaglio']} ({p['punti']} punti)</span>", unsafe_allow_html=True)
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

    if not proposte:
        st.info("Nessuna proposta presente.")
    else:
        # Converte la data in datetime per ordinare correttamente
        for p in proposte:
            try:
                p["data"] = datetime.fromisoformat(p["data"])
            except Exception:
                p["data"] = datetime.min  # in caso di errore, metti una data base

        # Ordina dalla più recente alla più vecchia
        proposte = sorted(proposte, key=lambda x: x["data"], reverse=True)

        st.subheader("📅 Tutte le proposte")
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

            data_str = p["data"].strftime("%d/%m/%Y %H:%M")

            st.markdown(
                f"""
                <div style='border:1px solid #ddd; border-radius:10px; padding:10px; margin-bottom:10px;'>
                    <h4 style='margin:0 0 5px 0;'>{icona} <span style='color:{colore};'>{testo}</span></h4>
                    <b>Proponente:</b> {p.get('proponente', '—')}<br>
                    <b>Bersaglio:</b> {p.get('bersaglio', '—')}<br>
                    <b>Punti:</b> {p.get('punti', 0)}<br>
                    <b>Motivazione:</b> {p.get('motivazione', '')}<br>
                    <b>📅 Data:</b> {data_str}
                </div>
                """,
                unsafe_allow_html=True
            )



# =======================
# SEZIONE COSTITUZIONE
# =======================
elif menu == "Costituzione":
    st.header("📜 Costituzione del Fantaratto")

    pdf_file = st.file_uploader("Carica la Costituzione (PDF)", type=["pdf"])

    if pdf_file is not None:
        # Salva su Supabase Storage
        upload_url = f"{SUPABASE_URL}/storage/v1/object/costituzione/costituzione_fantaratto.pdf"
        res = requests.post(
            upload_url,
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/pdf"
            },
            data=pdf_file.getvalue()
        )

        if res.status_code in [200, 201]:
            st.success("📄 Costituzione caricata con successo!")
        else:
            st.error(f"Errore nel caricamento: {res.text}")

    # Mostra sempre il PDF se esiste
    pdf_url = f"{SUPABASE_URL}/storage/v1/object/public/costituzione/costituzione_fantaratto.pdf"
    st.markdown("### Visualizza Costituzione:")
    st.markdown(f"[📥 Scarica Costituzione PDF]({pdf_url})")

    # Mostra direttamente il PDF nella pagina
    google_viewer_url = f"https://docs.google.com/gview?url={pdf_url}&embedded=true"
    st.components.v1.iframe(google_viewer_url, height=600)

