import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Fantaratto Easy", page_icon="🐀", layout="centered")

GIOCATORI = ["Ali", "Ale", "Ani", "Catta", "Corra", "Dada", "Gabbo", "Giugi", "Pippo", "Ricky", "Sert", "Simo", "Sofi"]

# Inizializza session state
if "proposte" not in st.session_state:
    st.session_state.proposte = []  # lista di dizionari: id, proponente, target, punti, motivo, voti, stato, data
if "punteggi" not in st.session_state:
    st.session_state.punteggi = {nome: 0 for nome in GIOCATORI}

# Funzioni
def aggiungi_proposta(proponente, target, punti, motivo):
    nuova = {
        "id": len(st.session_state.proposte) + 1,
        "proponente": proponente,
        "target": target,
        "punti": punti,
        "motivo": motivo,
        "voti": {},
        "stato": "In attesa",
        "data": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    st.session_state.proposte.append(nuova)

def vota(proposta_id, votante, voto):
    for p in st.session_state.proposte:
        if p["id"] == proposta_id:
            p["voti"][votante] = voto
            if len(p["voti"]) == len(GIOCATORI):
                if all(v == "Sì" for v in p["voti"].values()):
                    p["stato"] = "Approvata"
                    st.session_state.punteggi[p["target"]] += p["punti"]
                else:
                    p["stato"] = "Rifiutata"

# Interfaccia
st.title("🐀 Fantaratto Easy")
tabs = st.tabs(["Proponi", "Vota", "Classifica", "Storico", "Costituzione"])
tab_proponi, tab_vota, tab_class, tab_storico, tab_pdf = tabs

# TAB 1: Proponi
with tab_proponi:
    st.header("💡 Proponi punti ratto")
    proponente = st.selectbox("Chi sei?", GIOCATORI)
    target = st.selectbox("A chi assegni i punti?", [g for g in GIOCATORI if g != proponente])
    punti = st.number_input("Punti (+ torto, - gesto buono)", step=1, value=1)
    motivo = st.text_area("Motivazione")
    if st.button("Invia proposta"):
        if motivo.strip() == "":
            st.warning("Scrivi una motivazione!")
        else:
            aggiungi_proposta(proponente, target, punti, motivo)
            st.success("Proposta inviata! Tutti devono ora votare.")

# TAB 2: Vota
with tab_vota:
    st.header("🗳️ Vota proposte")
    votante = st.selectbox("Chi sta votando?", GIOCATORI, key="votante")
    in_attesa = [p for p in st.session_state.proposte if p["stato"] == "In attesa"]

    if not in_attesa:
        st.info("Nessuna proposta in attesa di voto.")
    else:
        for p in in_attesa:
            st.divider()
            st.subheader(f"Proposta #{p['id']} — {p['proponente']} → {p['target']} ({p['punti']} punti)")
            st.write(f"📝 *Motivo:* {p['motivo']}")
            if votante in p["voti"]:
                st.info("Hai già votato questa proposta.")
            else:
                scelta = st.radio("Il tuo voto:", ["Sì", "No"], key=f"voto_{p['id']}_{votante}")
                if st.button("Invia voto", key=f"btn_{p['id']}_{votante}"):
                    vota(p["id"], votante, scelta)
                    st.success("Voto registrato (anonimo per gli altri).")

# TAB 3: Classifica
with tab_class:
    st.header("🏆 Classifica Ratto")
    df = pd.DataFrame({
        "Giocatore": list(st.session_state.punteggi.keys()),
        "Punti": list(st.session_state.punteggi.values())
    }).sort_values("Punti", ascending=False)
    st.dataframe(df, use_container_width=True)

# TAB 4: Storico
with tab_storico:
    st.header("📚 Storico Proposte")
    if not st.session_state.proposte:
        st.info("Nessuna proposta finora.")
    else:
        df = pd.DataFrame(st.session_state.proposte)
        st.dataframe(df[["id", "proponente", "target", "punti", "motivo", "stato", "data"]], use_container_width=True)

# TAB 5: Costituzione
with tab_pdf:
    st.header("📜 Costituzione del Fantaratto")
    try:
        with open("costituzione.pdf", "rb") as f:
            st.download_button("📥 Scarica la Costituzione", f, file_name="Costituzione_Fantaratto.pdf")
    except FileNotFoundError:
        st.warning("Carica il file 'costituzione.pdf' nella stessa cartella del programma.")

st.markdown("---")
st.caption("Fantaratto Easy 2.1 — sistema equo e trasparente per punire e premiare le ratterie.")
