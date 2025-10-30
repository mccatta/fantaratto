# Fantaratto v1.0 - Streamlit app
# Features:
# - Players list (add/remove)
# - Propose points (proposer visible)
# - Anonymous voting (each voter identifies self to cast vote, but votes shown anonymized)
# - Proposals require unanimous approval of all players present in players.csv
# - Classifica (leaderboard)
# - Cronologia approvata
# - Upload / download of the "Costituzione" PDF

import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime

DATA_DIR = "data"
PLAYERS_FILE = os.path.join(DATA_DIR, "players.csv")
PROPOSALS_FILE = os.path.join(DATA_DIR, "proposals.csv")
VOTES_FILE = os.path.join(DATA_DIR, "votes.csv")
CONSTITUTION_PATH = os.path.join(DATA_DIR, "constitution.pdf")

os.makedirs(DATA_DIR, exist_ok=True)

# Utilities to load/save tables
def load_players():
    if os.path.exists(PLAYERS_FILE):
        return pd.read_csv(PLAYERS_FILE)
    else:
        df = pd.DataFrame(columns=["name","points"])  # points as int
        df.to_csv(PLAYERS_FILE, index=False)
        return df

def save_players(df):
    df.to_csv(PLAYERS_FILE, index=False)

def load_proposals():
    if os.path.exists(PROPOSALS_FILE):
        return pd.read_csv(PROPOSALS_FILE)
    else:
        df = pd.DataFrame(columns=["id","proposer","target","points","reason","status","created_at","approved_at"]) 
        df.to_csv(PROPOSALS_FILE, index=False)
        return df

def save_proposals(df):
    df.to_csv(PROPOSALS_FILE, index=False)

def load_votes():
    if os.path.exists(VOTES_FILE):
        return pd.read_csv(VOTES_FILE)
    else:
        df = pd.DataFrame(columns=["proposal_id","voter","vote","voted_at"]) 
        df.to_csv(VOTES_FILE, index=False)
        return df

def save_votes(df):
    df.to_csv(VOTES_FILE, index=False)

# Initialize dataframes
players = load_players()
proposals = load_proposals()
votes = load_votes()

st.set_page_config(page_title="Fantaratto", layout="wide")

st.title("🏴‍☠️ Fantaratto — la democrazia dei ratti")

# Sidebar navigation
page = st.sidebar.selectbox("Sezione", ["Home","Gestione Giocatori","Proponi punti","Vota proposte","Classifica","Cronologia","Costituzione"])

# Helper: number of players currently registered
def num_players():
    df = load_players()
    return len(df)

# Helper: finalize a proposal if all players have voted
def try_finalize_proposal(proposal_id):
    proposals = load_proposals()
    votes = load_votes()
    p = proposals[proposals.id == proposal_id]
    if p.empty:
        return
    # count votes for that proposal
    v = votes[votes.proposal_id == proposal_id]
    required = num_players()
    if len(v) < required:
        return
    # unanimous requirement: all votes must be 'yes'
    # votes stored as 'yes' or 'no'
    if (v.vote == 'yes').all():
        # approve
        proposals.loc[proposals.id==proposal_id, 'status'] = 'approved'
        proposals.loc[proposals.id==proposal_id, 'approved_at'] = datetime.utcnow().isoformat()
        save_proposals(proposals)
        # apply points
        prow = proposals[proposals.id==proposal_id].iloc[0]
        players = load_players()
        if prow.target in players.name.values:
            idx = players.index[players.name==prow.target][0]
            players.at[idx, 'points'] = int(players.at[idx, 'points']) + int(prow.points)
            save_players(players)
    else:
        proposals.loc[proposals.id==proposal_id, 'status'] = 'rejected'
        proposals.loc[proposals.id==proposal_id, 'approved_at'] = datetime.utcnow().isoformat()
        save_proposals(proposals)

# Home
if page == "Home":
    st.header("Benvenuto al Fantaratto")
    st.markdown("Questo è il sistema ufficiale per proporre punti, votare (votazione anonima) e consultare la costituzione del Fantaratto.")
    st.markdown(f"Numero di giocatori registrati: **{num_players()}**")
    st.write("Usa la barra a sinistra per navigare tra le sezioni.")
    if os.path.exists(CONSTITUTION_PATH):
        st.markdown("**Costituzione caricata:**")
        with open(CONSTITUTION_PATH, 'rb') as f:
            st.download_button("Scarica la Costituzione (PDF)", f.read(), file_name="fantaratto_costituzione.pdf")
    else:
        st.info("Nessuna Costituzione caricata — vai nella sezione 'Costituzione' per caricarne una.")

# Manage players
if page == "Gestione Giocatori":
    st.header("Gestione Giocatori")
    st.write("Aggiungi o rimuovi giocatori. I punti vengono salvati in data/players.csv.")
    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input("Aggiungi giocatore (nome)")
        if st.button("Aggiungi"):
            if new_name.strip() == "":
                st.error("Inserisci un nome valido")
            else:
                players = load_players()
                if new_name in players.name.values:
                    st.warning("Giocatore già presente")
                else:
                    players = players.append({"name": new_name, "points": 0}, ignore_index=True)
                    save_players(players)
                    st.success(f"Giocatore {new_name} aggiunto")
    with col2:
        players = load_players()
        st.write("Giocatori registrati:")
        st.dataframe(players)
        rem = st.selectbox("Rimuovi giocatore", options=[""] + players.name.tolist())
        if st.button("Rimuovi"):
            if rem == "":
                st.info("Seleziona un giocatore da rimuovere")
            else:
                players = players[players.name != rem]
                save_players(players)
                st.success(f"Giocatore {rem} rimosso")

# Propose points
if page == "Proponi punti":
    st.header("Proponi punti ratto")
    st.write("Il nome del proponente sarà visibile. Le proposte vanno approvate all'unanimità.")
    players = load_players()
    if len(players) == 0:
        st.warning("Non ci sono giocatori registrati — vai su 'Gestione Giocatori' e aggiungi i partecipanti")
    else:
        proposer = st.selectbox("Tu (proponente)", options=players.name.tolist())
        target = st.selectbox("A chi vuoi assegnare/togliere punti?", options=players.name.tolist())
        points = st.number_input("Punti (usa numeri negativi per togliere)", step=1, value=1)
        reason = st.text_area("Motivazione")
        if st.button("Proponi"):
            if target == "":
                st.error("Seleziona un bersaglio")
            else:
                proposals = load_proposals()
                pid = str(uuid.uuid4())
                proposals = proposals.append({
                    'id': pid,
                    'proposer': proposer,
                    'target': target,
                    'points': int(points),
                    'reason': reason,
                    'status': 'pending',
                    'created_at': datetime.utcnow().isoformat(),
                    'approved_at': ''
                }, ignore_index=True)
                save_proposals(proposals)
                st.success("Proposta creata e messa in votazione (in attesa che tutti votino)")

        # show pending proposals
        proposals = load_proposals()
        pending = proposals[proposals.status == 'pending']
        if not pending.empty:
            st.subheader("Proposte in attesa")
            st.write(pending[['id','proposer','target','points','reason','created_at']])

# Voting
if page == "Vota proposte":
    st.header("Vota proposte (voto anonimo)")
    st.write("Per votare devi inserire il tuo nome per registrare il voto. Il risultato delle singole votazioni è pubblico ma i singoli voti sono anonimi.")
    players = load_players()
    if len(players) == 0:
        st.warning("Non ci sono giocatori registrati — vai su 'Gestione Giocatori' e aggiungi i partecipanti")
    else:
        voter = st.selectbox("Sei", options=players.name.tolist())
        proposals = load_proposals()
        pending = proposals[proposals.status == 'pending']
        if pending.empty:
            st.info("Nessuna proposta in sospeso")
        else:
            # show proposals not yet voted by this voter
            votes = load_votes()
            voted_ids = votes[votes.voter == voter].proposal_id.tolist()
            todo = pending[~pending.id.isin(voted_ids)]
            if todo.empty:
                st.success("Hai già votato tutte le proposte in sospeso")
            else:
                for _, row in todo.iterrows():
                    st.markdown("---")
                    st.write(f"**Proposta ID:** {row.id}")
                    st.write(f"**Proponente:** {row.proposer}")
                    st.write(f"**Bersaglio:** {row.target}")
                    st.write(f"**Punti proposti:** {row.points}")
                    st.write(f"**Motivazione:** {row.reason}")
                    choice = st.radio(f"Vota per la proposta {row.id}", ("yes","no"), key=row.id + "_vote")
                    if st.button(f"Invia voto per {row.id}", key=row.id + "_btn"):
                        votes = load_votes()
                        votes = votes.append({
                            'proposal_id': row.id,
                            'voter': voter,
                            'vote': choice,
                            'voted_at': datetime.utcnow().isoformat()
                        }, ignore_index=True)
                        save_votes(votes)
                        st.success("Voto registrato (anonimo pubblicamente)")
                        # try finalize
                        try_finalize_proposal(row.id)

# Leaderboard
if page == "Classifica":
    st.header("Classifica")
    players = load_players()
    if players.empty:
        st.info("Nessun giocatore registrato")
    else:
        players = players.sort_values(by='points', ascending=False).reset_index(drop=True)
        st.table(players)

# History
if page == "Cronologia":
    st.header("Cronologia eventi approvati")
    proposals = load_proposals()
    approved = proposals[proposals.status == 'approved']
    if approved.empty:
        st.info("Nessuna proposta approvata ancora")
    else:
        approved = approved.sort_values(by='approved_at', ascending=False)
        st.write(approved[['approved_at','proposer','target','points','reason']])

# Constitution upload / download
if page == "Costituzione":
    st.header("Costituzione del Fantaratto")
    st.write("Carica il PDF ufficiale della costituzione. Gli altri potranno scaricarlo.")
    uploaded = st.file_uploader("Carica PDF (sovrascrive il precedente)", type=['pdf'])
    if uploaded is not None:
        with open(CONSTITUTION_PATH, 'wb') as f:
            f.write(uploaded.getbuffer())
        st.success("Costituzione caricata")
    if os.path.exists(CONSTITUTION_PATH):
        with open(CONSTITUTION_PATH, 'rb') as f:
            st.download_button("Scarica la Costituzione (PDF)", f.read(), file_name="fantaratto_costituzione.pdf")

# Always show counts of pending proposals and votes
st.sidebar.markdown("---")
proposals = load_proposals()
pending_count = len(proposals[proposals.status == 'pending'])
st.sidebar.write(f"Proposte in sospeso: {pending_count}")

# Show quick admin actions (reset data) hidden behind a confirmation
if st.sidebar.checkbox("Mostra strumenti amministratore"):
    st.sidebar.warning("Attenzione: azioni distruttive")
    if st.sidebar.button("Reinicializza tutto (cancella dati)"):
        for f in [PLAYERS_FILE, PROPOSALS_FILE, VOTES_FILE, CONSTITUTION_PATH]:
            if os.path.exists(f):
                os.remove(f)
        st.sidebar.success("Dati eliminati. Ricarica la pagina.")

# Save state on exit
# (data are saved whenever actions are performed)

# Notes for users
st.sidebar.markdown("---")
st.sidebar.write("Note:")
st.sidebar.write("- Le votazioni sono registrate con il nome del votante nel file dati per evitare doppi voti, ma non sono visibili pubblicamente all'interno dell'app (vengono trattate come anonime nelle interfacce).\n- L'unanimità richiesta è calcolata in base al numero di giocatori presenti nel file players.csv. Aggiungi tutti i 13 partecipanti nella sezione 'Gestione Giocatori'.")
