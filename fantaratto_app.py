import streamlit as st
import requests
import json
import pandas as pd

SUPABASE_URL = "https://kcakeewkrmxyldvcpdbe.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtjYWtlZXdrcm14eWxkdmNwZGJlIiwicm9sZSIsImFub24iLCJpYXQiOjE3NjE4MjM0MjUsImV4cCI6MjA3NzM5OTQyNX0.-3vvufy6budEU-HwTU-4I0sNfRn7QWN0kad1bJN4BD8"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# ---- FUNZIONI ----

def carica_proposte():
    url = f"{SUPABASE_URL}/rest/v1/proposte?select=*"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()
    else:
        st.error(f"Errore caricamento proposte: {res.text}")
        return []

def salva_proposta(proponente, bersaglio, punti, motivazione):
    url = f"{SUPABASE_URL}/rest/v1/proposte"
    data = [{
        "proponente": proponente,
        "bersaglio": bersaglio,
        "punti": punti,
        "motivazione": motivazione,
        "approvata": False
    }]
    res = requests.post(url, headers=headers, data=json.dumps(data))
    if res.status_code in [200, 201]:
        st.success("✅ Proposta aggiunta con successo!")
    else:
        st.error(f"Errore salvataggio: {res.text}")

def aggiorna_proposta(proposta_id, approvata=True):
    url = f"{SUPABASE_URL}/rest/v1/proposte?id=eq.{proposta_id}"
    data = {"approvata": approvata}
    res = requests.patch(url, headers=headers, data=json.dumps(data))
    if res.status_code in [200, 204]:
        st.success("✅ Proposta aggiornata!")
    else:
        st.error(f"Errore aggiornamento: {res.text}")
