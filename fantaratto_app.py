import streamlit as st
import pandas as pd
import os

# --- CONFIG ---
GIOCATORI = [
    "Giocatore1","Giocatore2","Giocatore3","Giocatore4","Giocatore5",
    "Giocatore6","Giocatore7","Giocatore8","Giocatore9","Giocatore10",
    "Giocatore11","Giocatore12","Giocatore13"
]
CSV_PROPOSTE = "proposte.csv"
CSV_VOTI = "voti.csv"
PDF_COSTITUZIONE = "costituzione.pdf"

# --- INIT FILES ---
if not os.path.exists(CSV_PROPOSTE):
    pd.DataFrame(columns=["ID","Proponente","Bersaglio","Punti","Motivazione","Stato"]).to_csv(CSV_PROPOSTE,index=False)
if not os.path.exists(CSV_VOTI):
    pd.DataFrame(columns=["ID","Votante","Voto"]).to_csv(CSV_VOTI,index=False)

proposte = pd.read_csv(CSV_PROPOSTE)
voti = pd.read_csv(CSV_VOTI)

# --- HEADER ---
st.title("🏴 Fantaratto")
st.write("La tua app di punti ratto tra amici!")

# --- COSTITUZIONE ---
st.sidebar.header("📄 Costituzione")
st.sidebar.download_button("Scarica PDF Costituzione", PDF_COSTITUZIONE)

# --- NUOVA PROPOSTA ---
st.header("💡 Proponi punti")
proponente = st.selectbox("Chi propone?", GIOCATORI)
bersaglio = st.selectbox("A chi vuoi dare/togliere punti?", GIOCATORI)
punti = st.number_input("Punti (+ torto, - gentilezza)", value=1, step=1)
motivazione = st.text_area("Motivazione")

if st.button("Invia proposta"):
    nuova_id = 1 if proposte.empty else proposte["ID"].max()+1
    proposte = pd.concat([proposte, pd.DataFrame([{
        "ID": nuova_id,
        "Proponente": proponente,
        "Bersaglio": bersaglio,
        "Punti": punti,
        "Motivazione": motivazione,
        "Stato": "In attesa"
    }])], ignore_index=True)
    proposte.to_csv(CSV_PROPOSTE,index=False)
    st.success(f"Proposta inviata! ID: {nuova_id}")

# --- VOTAZIONE ---
st.header("🗳️ Vota le proposte")
votante_corrente = st.selectbox("Seleziona il tuo nome per votare", GIOCATORI)

for _, row in proposte[proposte["Stato"]=="In attesa"].iterrows():
    st.write(f"**ID {row['ID']}**: {row['Proponente']} propone {row['Punti']} punti a {row['Bersaglio']}")
    st.write(f"Motivazione: {row['Motivazione']}")
    
    voto = st.radio(f"Vota proposta ID {row['ID']}", ["Sì","No"], key=f"{row['ID']}_{votante_corrente}")
    
    if st.button(f"Invia voto ID {row['ID']}", key=f"btn_{row['ID']}_{votante_corrente}"):
        if ((voti["ID"]==row["ID"]) & (voti["Votante"]==votante_corrente)).any():
            st.warning("Hai già votato questa proposta")
        else:
            voti = pd.concat([voti, pd.DataFrame([{"ID":row["ID"],"Votante":votante_corrente,"Voto":voto}])], ignore_index=True)
            voti.to_csv(CSV_VOTI,index=False)
            st.success("Voto registrato!")

# --- AGGIORNA STATO PROPOSTE ---
for _, row in proposte.iterrows():
    voti_proposta = voti[voti["ID"]==row["ID"]]
    if len(voti_proposta)==len(GIOCATORI) and all(voti_proposta["Voto"]=="Sì"):
        proposte.loc[proposte["ID"]==row["ID"],"Stato"]="Approvata"
proposte.to_csv(CSV_PROPOSTE,index=False)

# --- CLASSIFICA ---
st.header("🏆 Classifica")
classifica = pd.DataFrame({"Nome":GIOCATORI})
classifica["Punti"] = classifica["Nome"].apply(
    lambda x: proposte[proposte["Stato"]=="Approvata"].loc[proposte["Bersaglio"]==x,"Punti"].sum()
)
st.table(classifica.sort_values("Punti",ascending=False))
