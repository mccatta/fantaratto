import streamlit as st
import pandas as pd
import os

# --- CONFIGURAZIONE ---
GIOCATORI = [
    "Ali", "Ale", "Ani", "Catta", "Corra", "Dada", "Gabbo",
    "Giugi", "Pippo", "Ricky", "Sert", "Simo", "Sofi"
]
CSV_PROPOSTE = "proposte.csv"
CSV_VOTI = "voti.csv"
PDF_COSTITUZIONE = "costituzione.pdf"

# --- INIZIALIZZAZIONE FILE ---
if not os.path.exists(CSV_PROPOSTE):
    pd.DataFrame(columns=["ID","Proponente","Bersaglio","Punti","Motivazione","Stato"]).to_csv(CSV_PROPOSTE,index=False)
if not os.path.exists(CSV_VOTI):
    pd.DataFrame(columns=["ID","Votante","Voto"]).to_csv(CSV_VOTI,index=False)

proposte = pd.read_csv(CSV_PROPOSTE)
voti = pd.read_csv(CSV_VOTI)

# --- HEADER ---
st.title("🏴 Fantaratto")
st.markdown("Benvenuti nel **Fantaratto ufficiale**. Se fai un torto o uno scherzo, guadagni punti ratto 🐀; se fai qualcosa di buono, li perdi 💔.")

# --- SIDEBAR COSTITUZIONE ---
st.sidebar.header("📜 Costituzione")
if os.path.exists(PDF_COSTITUZIONE):
    with open(PDF_COSTITUZIONE, "rb") as f:
        st.sidebar.download_button("Scarica la Costituzione", f, file_name="costituzione.pdf")
else:
    st.sidebar.warning("Carica il file 'costituzione.pdf' nella stessa cartella dell’app per renderlo scaricabile.")

# --- MENU DI NAVIGAZIONE ---
menu = st.sidebar.radio("Vai a:", ["Proponi punti", "Vota proposte", "Classifica"])

# --- PAGINA: PROPOSTA ---
if menu == "Proponi punti":
    st.header("💡 Proponi una variazione di punti ratto")

    proponente = st.selectbox("Chi propone?", GIOCATORI)
    bersaglio = st.selectbox("A chi vuoi assegnare o togliere punti?", [g for g in GIOCATORI if g != proponente])
    punti = st.number_input("Punti (+ torto, - gesto gentile)", value=1, step=1)
    motivazione = st.text_area("Motivazione della proposta")

    if st.button("Invia proposta 🐀"):
        nuova_id = 1 if proposte.empty else proposte["ID"].max() + 1
        nuova = pd.DataFrame([{
            "ID": nuova_id,
            "Proponente": proponente,
            "Bersaglio": bersaglio,
            "Punti": punti,
            "Motivazione": motivazione,
            "Stato": "In attesa"
        }])
        proposte = pd.concat([proposte, nuova], ignore_index=True)
        proposte.to_csv(CSV_PROPOSTE, index=False)
        st.success(f"✅ Proposta inviata da {proponente} contro {bersaglio}!")

# --- PAGINA: VOTAZIONE ---
elif menu == "Vota proposte":
    st.header("🗳️ Vota le proposte attive")

    votante = st.selectbox("Chi sta votando?", GIOCATORI)
    proposte_in_attesa = proposte[proposte["Stato"] == "In attesa"]

    if proposte_in_attesa.empty:
        st.info("Nessuna proposta in attesa di voto.")
    else:
        for _, row in proposte_in_attesa.iterrows():
            st.subheader(f"Proposta #{int(row['ID'])}")
            st.write(f"**Proponente:** {row['Proponente']}")
            st.write(f"**Bersaglio:** {row['Bersaglio']}")
            st.write(f"**Punti:** {row['Punti']}")
            st.write(f"**Motivazione:** {row['Motivazione']}")

            voto = st.radio(
                f"Voto di {votante} per la proposta #{int(row['ID'])}",
                ["Sì", "No"],
                key=f"voto_{row['ID']}_{votante}"
            )

            if st.button(f"Invia voto #{int(row['ID'])}", key=f"btn_{row['ID']}_{votante}"):
                if ((voti["ID"] == row["ID"]) & (voti["Votante"] == votante)).any():
                    st.warning("⚠️ Hai già votato questa proposta.")
                else:
                    nuovo_voto = pd.DataFrame([{"ID": row["ID"], "Votante": votante, "Voto": voto}])
                    voti = pd.concat([voti, nuovo_voto], ignore_index=True)
                    voti.to_csv(CSV_VOTI, index=False)
                    st.success("✅ Voto registrato!")

        # Aggiornamento stato proposte
        for _, row in proposte.iterrows():
            voti_proposta = voti[voti["ID"] == row["ID"]]
            if len(voti_proposta) == len(GIOCATORI):
                if all(voti_proposta["Voto"] == "Sì"):
                    proposte.loc[proposte["ID"] == row["ID"], "Stato"] = "Approvata"
                else:
                    proposte.loc[proposte["ID"] == row["ID"], "Stato"] = "Rifiutata"
        proposte.to_csv(CSV_PROPOSTE, index=False)

# --- PAGINA: CLASSIFICA ---
elif menu == "Classifica":
    st.header("🏆 Classifica dei ratti")

    if proposte.empty:
        st.info("Nessuna proposta ancora approvata.")
    else:
        classifica = pd.DataFrame({"Nome": GIOCATORI})
        classifica["Punti ratto"] = classifica["Nome"].apply(
            lambda g: proposte[(proposte["Bersaglio"] == g) & (proposte["Stato"] == "Approvata")]["Punti"].sum()
        )
        classifica = classifica.sort_values("Punti ratto", ascending=False)
        st.dataframe(classifica, use_container_width=True)
