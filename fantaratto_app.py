import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client
import uuid

# --- CONFIG ---
st.set_page_config(page_title="Fantaratto Cloud", page_icon="🐀", layout="centered")

GIOCATORI = ["Ali","Ale","Ani","Catta","Corra","Dada","Gabbo","Giugi","Pippo","Ricky","Sert","Simo","Sofi"]

SUPABASE_URL = "https://kcakeewkrmxyldvcpdbe.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtjYWtlZXdrcm14eWxkdmNwZGJlIiwicm9sZSIsImFub24iLCJpYXQiOjE3NjE4MjM0MjUsImV4cCI6MjA3NzM5OTQyNX0.-3vvufy6budEU-HwTU-4I0sNfRn7QWN0kad1bJN4BD8"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- FUNZIONI ---
def carica_proposte():
    res = supabase.table("proposte").select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["id","proponente","bersaglio","punti","motivazione","data","approvata"])

def carica_voti():
    res = supabase.table("voti").select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["id","proposta_id","votante","voto"])

def invia_proposta(proponente, bersaglio, punti, motivazione):
    supabase.table("proposte").insert({
        "id": str(uuid.uuid4()),
        "proponente": proponente,
        "bersaglio": bersaglio,
        "punti": punti,
        "motivazione": motivazione,
        "data": datetime.now().isoformat(),
        "approvata": False
    }).execute()

def invia_voto(proposta_id, votante, voto):
    supabase.table("voti").insert({
        "id": str(uuid.uuid4()),
        "proposta_id": proposta_id,
        "votante": votante,
        "voto": voto
    }).execute()
    # Controlla approvazione automatica
    voti = carica_voti()
    voti_proposta = voti[voti["proposta_id"]==proposta_id]
    if len(voti_proposta["votante"].unique()) == len(GIOCATORI):
        if all(voti_proposta["voto"]):
            supabase.table("proposte").update({"approvata": True}).eq("id", proposta_id).execute()

# --- INTERFACCIA ---
st.title("🐀 Fantaratto Cloud")
tabs = st.tabs(["Proponi","Vota","Classifica","Costituzione"])
tab_prop, tab_vota, tab_class, tab_pdf = tabs

# --- PROPONI ---
with tab_prop:
    st.header("💡 Proponi punti ratto")
    proponente = st.selectbox("Chi sei?", GIOCATORI)
    target = st.selectbox("A chi?", [g for g in GIOCATORI if g != proponente])
    punti = st.number_input("Punti (+ cattiveria, - gesto buono)", step=1, value=1)
    motivo = st.text_area("Motivazione")
    if st.button("Invia proposta"):
        if motivo.strip() != "":
            invia_proposta(proponente, target, punti, motivo)
            st.success("✅ Proposta inviata!")

# --- VOTA ---
with tab_vota:
    st.header("🗳️ Vota le proposte")
    votante = st.selectbox("Chi sta votando?", GIOCATORI, key="votante_cloud")
    proposte = carica_proposte()
    voti = carica_voti()
    in_attesa = proposte[proposte["approvata"]==False]

    if in_attesa.empty:
        st.info("Nessuna proposta in attesa di voto.")
    else:
        for _, p in in_attesa.iterrows():
            st.divider()
            st.subheader(f"{p['proponente']} → {p['bersaglio']} ({p['punti']} punti)")
            st.write(f"📝 *Motivo:* {p['motivazione']}")
            if votante in voti[voti["proposta_id"]==p["id"]]["votante"].values:
                st.info("Hai già votato questa proposta.")
            else:
                voto = st.radio("Il tuo voto:", ["Sì","No"], key=p["id"])
                if st.button("Invia voto", key=f"btn_{p['id']}"):
                    invia_voto(p["id"], votante, voto=="Sì")
                    st.success("✅ Voto registrato!")

# --- CLASSIFICA ---
with tab_class:
    st.header("🏆 Classifica")
    proposte_approvate = carica_proposte()
    proposte_approvate = proposte_approvate[proposte_approvate["approvata"]==True]
    if proposte_approvate.empty:
        st.info("Nessuna proposta approvata.")
    else:
        df = proposte_approvate.groupby("bersaglio")["punti"].sum().reset_index()
        df.columns = ["Giocatore","Punti"]
        df = df.sort_values("Punti",ascending=False)
        st.dataframe(df, use_container_width=True)

# --- COSTITUZIONE ---
with tab_pdf:
    st.header("📜 Costituzione del Fantaratto")
    try:
        with open("costituzione.pdf","rb") as f:
            st.download_button("📥 Scarica Costituzione", f, file_name="Costituzione_Fantaratto.pdf")
    except FileNotFoundError:
        st.warning("Carica 'costituzione.pdf' nella cartella dell'app.")
