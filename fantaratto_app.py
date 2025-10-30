import streamlit as st
import pandas as pd
import os
from datetime import datetime

# === CONFIGURAZIONE BASE ===
st.set_page_config(page_title="Fantaratto Easy", page_icon="🐀", layout="centered")

GIOCATORI = ["Ali", "Ale", "Ani", "Catta", "Corra", "Dada", "Gabbo", "Giugi", "Pippo", "Ricky", "Sert", "Simo", "Sofi"]
FILE_PROPOSTE = "proposte.csv"
FILE_VOTI = "voti.csv"

# === FUNZIONI DI SUPPORTO ===
def carica_csv(nome_file, colonne):
    if not os.path.exists(nome_file):
        return pd.DataFrame(columns=colonne)
    return pd.read_csv(nome_file)

def salva_csv(df, nome_file):
    df.to_csv(nome_file, index=False)

# === CARICAMENTO DATI ===
proposte = carica_csv(FILE_PROPOSTE, ["id", "proponente", "bersaglio", "punti", "motivazione", "data", "approvata"])
voti = carica_csv(FILE_VOTI, ["proposta_id", "votante", "voto"])

# === MENU PRINCIPALE ===
st.title("🐀 Fantaratto Easy")
pagina = st.sidebar.selectbox("Naviga:", ["Proponi Punti", "Vota Proposte", "Classifica", "Costituzione"])

# === PAGINA: PROPONI ===
if pagina == "Proponi Punti":
    st.header("📩 Proponi una nuova penalità o bonus")
    proponente = st.selectbox("Chi propone?", GIOCATORI)
    bersaglio = st.selectbox("A chi?", [g for g in GIOCATORI if g != proponente])
    punti = st.number_input("Punti ratto (+ se cattiveria, - se gesto buono)", step=1, value=1)
    motivazione = st.text_area("Motivazione")
    
    if st.button("Invia proposta"):
        nuova_id = datetime.now().strftime("%Y%m%d%H%M%S")
        nuova = {
            "id": nuova_id,
            "proponente": proponente,
            "bersaglio": bersaglio,
            "punti": punti,
            "motivazione": motivazione,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "approvata": False
        }
        proposte = pd.concat([proposte, pd.DataFrame([nuova])], ignore_index=True)
        salva_csv(proposte, FILE_PROPOSTE)
        st.success("✅ Proposta inviata e in attesa di votazione!")

# === PAGINA: VOTA ===
elif pagina == "Vota Proposte":
    st.header("🗳️ Vota le proposte in sospeso")
    votante = st.selectbox("Chi sta votando?", GIOCATORI)
    in_sospeso = proposte[proposte["approvata"] == False]

    if in_sospeso.empty:
        st.info("Nessuna proposta in attesa di votazione.")
    else:
        for _, r in in_sospeso.iterrows():
            st.subheader(f"{r['proponente']} → {r['bersaglio']} ({r['punti']} punti)")
            st.write(f"📝 {r['motivazione']}")
            voti_esistenti = voti[(voti["proposta_id"] == r["id"]) & (voti["votante"] == votante)]

            if not voti_esistenti.empty:
                st.caption("Hai già votato questa proposta.")
            else:
                voto = st.radio(f"Voto per proposta {r['id']}", ["Sì", "No"], key=r['id'])
                if st.button(f"Invia voto per {r['id']}", key=f"btn_{r['id']}"):
                    nuovi_voti = pd.DataFrame([{
                        "proposta_id": r["id"],
                        "votante": votante,
                        "voto": voto
                    }])
                    voti = pd.concat([voti, nuovi_voti], ignore_index=True)
                    salva_csv(voti, FILE_VOTI)
                    st.success("✅ Voto registrato!")

        # Verifica se ci sono proposte da approvare
        for pid in in_sospeso["id"]:
            voti_proposta = voti[voti["proposta_id"] == pid]
            if len(voti_proposta["votante"].unique()) == len(GIOCATORI):
                # Tutti hanno votato
                if all(voti_proposta["voto"] == "Sì"):
                    proposte.loc[proposte["id"] == pid, "approvata"] = True
                    salva_csv(proposte, FILE_PROPOSTE)
                    st.success(f"🎉 Proposta {pid} approvata all'unanimità!")

# === PAGINA: CLASSIFICA ===
elif pagina == "Classifica":
    st.header("🏆 Classifica Ratto")
    approvate = proposte[proposte["approvata"] == True]
    if approvate.empty:
        st.info("Ancora nessuna proposta approvata.")
    else:
        punteggi = approvate.groupby("bersaglio")["punti"].sum().reset_index()
        punteggi.columns = ["Giocatore", "Totale punti ratto"]
        punteggi = punteggi.sort_values("Totale punti ratto", ascending=False)
        st.table(punteggi)

# === PAGINA: COSTITUZIONE ===
elif pagina == "Costituzione":
    st.header("📜 Costituzione del Fantaratto")
    if os.path.exists("costituzione.pdf"):
        with open("costituzione.pdf", "rb") as f:
            st.download_button("Scarica la Costituzione", f, file_name="costituzione.pdf")
    else:
        st.warning("Nessun file costituzione.pdf trovato nella cartella.")
