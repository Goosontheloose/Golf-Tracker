
import streamlit as st
import requests
import pandas as pd

# ==========================================
# 1. SETUP & THEME
# ==========================================
st.set_page_config(page_title="The 126th US OPEN - SHINNECOCK HILLS", layout="wide")

# API Configuration
API_KEY = st.secrets["api_key"]
URL = "https://live-golf-data.p.rapidapi.com/leaderboard"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
PARAMS = {"orgId": "1", "tournId": "026", "year": "2024"} # Keep 2024 for testing data

# Brutalist Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&family=JetBrains+Mono:wght@500&display=swap');
    :root { --fairway: #064E3B; --gold: #EAB308; --bunker: #F5F5F4; }
    .stApp { background-color: var(--bunker); background-image: radial-gradient(#000 1px, transparent 0); background-size: 30px 30px; }
    h1, h2, h3 { font-family: 'Inter', sans-serif !important; font-weight: 900 !important; text-transform: uppercase; color: #000; }
    .podium-card { background: white; border: 4px solid #000; padding: 25px; box-shadow: 10px 10px 0px #000; margin-bottom: 30px; }
    .player-row { background: white; border: 2px solid #000; padding: 10px 20px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
    .marquee { background: var(--fairway); color: var(--gold); padding: 10px 0; font-family: 'Inter', sans-serif; font-weight: 900; border-bottom: 4px solid #000; margin-bottom: 40px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. YOUR POOL DATA (100 PLAYERS)
# ==========================================
# IMPORTANT: Ensure there is a TAB between the name and the players
RAW_EXCEL_DATA = """
Martin	Patrick Cantlay	Thomas Detry	Sergio Garcia
Frederik 2	Thomas Detry	Sam Burns	Corey Conners
Jason 2	Bryson Dechambeau	Thomas Detry	Sergio Garcia
Wynand 2	Patrick Cantlay	Tony Finau	Akshay Bhatia
Martin 2	Tony Finau	Tommy Fleetwood	Russel Henley
Rupert	Patrick Cantlay	Tony Finau	Tommy Fleetwood
Rupert 3	Akshay Bhatia	Sergio Garcia	Bryson Dechambeau
""" 

# ==========================================
# 3. ROBUST DATA ENGINE
# ==========================================

@st.cache_data(ttl=600)
def get_engine_data():
    try:
        response = requests.get(URL, headers=HEADERS, params=PARAMS)
        data = response.json()
        
        # Look for the leaderboard rows in various possible keys
        rows = data.get('leaderboardRows', data.get('leaderboard', data.get('players', [])))
        
        score_map = {}
        for r in rows:
            # Flexible name building
            f_name = r.get('firstName', r.get('first_name', ''))
            l_name = r.get('lastName', r.get('last_name', ''))
            full_name = f"{f_name} {l_name}".strip().lower()
            
            # Flexible score building
            score = r.get('toParValue', r.get('totalToPar', r.get('score', 0)))
            if str(score).upper() == "E": score = 0
            
            try:
                score_map[full_name] = int(score)
            except:
                score_map[full_name] = 0
                
        return score_map, rows
    except Exception as e:
        st.error(f"Engine Warning: {e}")
        return {}, []

def parse_teams(raw_data):
    teams = []
    for line in raw_data.strip().split('\n'):
        parts = line.split('\t')
        if len(parts) >= 4:
            teams.append({
                "owner": parts[0],
                "players": [p.strip().lower() for p in parts[1:4]]
            })
    return teams

# ==========================================
# 4. DASHBOARD RENDER
# ==========================================

st.markdown('<div class="marquee"><marquee scrollamount="12">THE SHINNECOCK SYNDICATE // 2026 US OPEN // 100 PLAYERS // LIVE FEED ONLINE</marquee></div>', unsafe_allow_html=True)
st.title("🏆 THE SYNDICATE DERBY")

# Fetch and Process
score_map, pro_rows = get_engine_data()
teams = parse_teams(RAW_EXCEL_DATA)

# Calculate Leaderboard
results = []
for t in teams:
    # Match names exactly or partially
    team_total = 0
    display_names = []
    for p in t['players']:
        score = score_map.get(p, 0)
        # Fallback for partial name matches (e.g. "Bryson Dechambeau" vs "Bryson DeChambeau")
        if p not in score_map:
            for api_name, api_score in score_map.items():
                if p in api_name or api_name in p:
                    score = api_score
                    break
        team_total += score
        display_names.append(p.title())
        
    results.append({
        "Owner": t['owner'],
        "Score": team_total,
        "Roster": ", ".join(display_names)
    })

df = pd.DataFrame(results).sort_values("Score")

# --- UI: THE PODIUM ---
st.subheader("CHAMPIONSHIP FLIGHT")
cols = st.columns(3)
podium = df.head(3).to_dict('records')

for i, (col, color) in enumerate(zip(cols, ["#EAB308", "#94A3B8", "#B45309"])):
    if i < len(podium):
        with col:
            st.markdown(f"""
                <div class="podium-card" style="border-color: {color}">
                    <h2 style="color: {color}; margin:0;">#{i+1} {podium[i]['Owner']}</h2>
                    <div style="font-family:'JetBrains Mono'; font-size:3.5rem;">{podium[i]['Score']}</div>
                    <div style="font-size:0.8rem; color:#444;">{podium[i]['Roster']}</div>
                </div>
            """, unsafe_allow_html=True)

# --- UI: THE PACK (EVERYONE ELSE) ---
st.subheader("THE FULL FIELD")
for _, row in df.iloc[3:].iterrows():
    st.markdown(f"""
        <div class="player-row">
            <div><b>{row['Owner']}</b> <span style="margin-left:15px; color:#666; font-size:0.85rem;">{row['Roster']}</span></div>
            <div style="font-family:'JetBrains Mono'; font-weight:bold; font-size:1.2rem;">{row['Score']}</div>
        </div>
    """, unsafe_allow_html=True)

# --- UI: PRO MASTER BOARD (CRASH-PROOF) ---
with st.expander("📊 OFFICIAL TOURNAMENT LEADERBOARD"):
    if pro_rows:
        pro_df = pd.DataFrame(pro_rows)
        # Only show columns that exist to prevent KeyErrors
        cols_to_show = ['position', 'firstName', 'lastName', 'thru', 'toParValue', 'total']
        existing_cols = [c for c in cols_to_show if c in pro_df.columns]
        st.dataframe(pro_df[existing_cols], use_container_width=True)
    else:
        st.info("Waiting for pro leaderboard data...")

# --- UI: ENGINE ROOM (DEBUG) ---
with st.expander("🛠️ THE ENGINE ROOM"):
    st.write("API Names currently in system (use these for your Excel list if scores are 0):")
    st.write(list(score_map.keys()))

