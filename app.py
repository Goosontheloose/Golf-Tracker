import streamlit as st
import pandas as pd
import requests
from streamlit_gsheets import GSheetsConnection
from collections import Counter
from itertools import combinations

# --- 1. SETTINGS & TOP 30 DEFINITION ---
st.set_page_config(page_title="154th Claret Jug Syndicate", layout="wide")

# Updated Top 30 based on 2025 OWGR
TOP_30 = [
    "Scottie Scheffler", "Rory McIlroy", "Tommy Fleetwood", "Xander Schauffele", 
    "Russell Henley", "J.J. Spaun", "Robert MacIntyre", "Ben Griffin", 
    "Justin Thomas", "Justin Rose", "Alex Noren", "Sepp Straka", 
    "Harris English", "Viktor Hovland", "Keegan Bradley", "Collin Morikawa", 
    "Hideki Matsuyama", "Ludvig Aberg", "Jon Rahm", "Tony Finau", 
    "Min Woo Lee", "Cameron Young", "Adam Hadwin", "Kurt Kitayama", 
    "Sam Burns", "Wyndham Clark", "Christiaan Bezuidenhout", "Shane Lowry", 
    "Matthieu Pavon", "Corey Conners"
]

# Coastal Brutalism CSS (Same as before)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=Roboto+Mono:wght@400;700&display=swap');
    .main { background-color: #020617; color: #f8fafc; }
    h1, h2, h3 { font-family: 'Archivo Black', sans-serif; text-transform: uppercase; letter-spacing: -1px; }
    .stMetric { background-color: #1e293b; border: 1px solid #334155; padding: 15px; box-shadow: 4px 4px 0px #D4AF37; }
    .stButton>button { width: 100%; border-radius: 0px; font-family: 'Archivo Black'; background-color: #D4AF37; color: #020617; border: none; }
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA CONNECTIONS ---
SHEET_URL = "YOUR_GOOGLE_SHEET_URL_HERE"
API_KEY = st.secrets["api_key"]

@st.cache_data(ttl=600)
def get_live_data():
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"
    params = {"orgId": "1", "tournId": "026", "year": "2024"} 
    headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json().get('leaderboardRows', [])
    except: return []

conn = st.connection("gsheets", type=GSheetsConnection)

def load_teams():
    try: return conn.read(spreadsheet=SHEET_URL).to_dict('records')
    except: return []

# --- 3. UI LAYOUT ---
st.title("🏆 154th Claret Jug Syndicate")

# Sidebar: Tiered Team Entry
with st.sidebar:
    st.header("THE TERMINAL")
    st.info("Limit: Pick 2 from the Top 30. Your 3rd player is a Wildcard.")
    
    with st.form("entry_form"):
        u_name = st.text_input("Entry Name")
        
        st.write("---")
        st.subheader("Elite Picks (Top 30)")
        p1 = st.selectbox("Elite Player 1", TOP_30)
        p2 = st.selectbox("Elite Player 2", [p for p in TOP_30 if p != p1])
        
        st.write("---")
        st.subheader("The Wildcard")
        p3 = st.text_input("Wildcard Player (Any other pro)")
        
        submit = st.form_submit_button("LOCK IN SYNDICATE")
        
        if submit and u_name and p3:
            current_df = conn.read(spreadsheet=SHEET_URL)
            new_row = pd.DataFrame([{"User": u_name, "P1": p1, "P2": p2, "P3": p3}])
            updated_df = pd.concat([current_df, new_row], ignore_index=True)
            conn.update(spreadsheet=SHEET_URL, data=updated_df)
            st.success("Team Locked!")
            st.cache_data.clear()

# --- 4. CALCULATION & DISPLAY ---
rows = get_live_data()
teams = load_teams()

if rows:
    # Build fast lookup
    player_map = {}
    for r in rows:
        name = f"{r.get('firstName','')} {r.get('lastName','')}".strip().lower()
        player_map[name] = {"score": r.get('totalToPar', 0), "label": f"{name.title()} ({r.get('totalToPar', 'E')})"}

    leaderboard = []
    for team in teams:
        user = team['User']
        roster = [str(team['P1']), str(team['P2']), str(team['P3'])]
        
        total_score = 0
        display_roster = []
        
        for p in roster:
            p_clean = p.strip().lower()
            # Try to match name
            match = next((v for k, v in player_map.items() if p_clean in k or k in p_clean), None)
            if match:
                total_score += match['score'] if isinstance(match['score'], int) else 0
                display_roster.append(match['label'])
            else:
                display_roster.append(f"{p} (???)")
        
        leaderboard.append({"User": user, "Total": total_score, "Roster": " | ".join(display_roster)})

    # Display Standings
    sorted_lb = sorted(leaderboard, key=lambda x: x['Total'])
    st.header("THE BOARD: SYNDICATE STANDINGS")
    st.table(pd.DataFrame(sorted_lb))
