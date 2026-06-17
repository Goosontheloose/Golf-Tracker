
import streamlit as st
import requests
import pandas as pd

# ==========================================
# 1. CONFIGURATION & SCALING
# ==========================================
st.set_page_config(page_title="US Open: The Syndicate Derby", layout="wide")

# API Setup
API_KEY = st.secrets["api_key"]
URL = "https://live-golf-data.p.rapidapi.com/leaderboard"

# Tournament Parameters (Set to 2024 for testing, update to 2026 when live)
PARAMS = {"orgId": "1", "tournId": "026", "year": "2024"} 
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}

# ==========================================
# 2. THE SYNDICATE DATA (Paste your 100 people here)
# ==========================================
RAW_EXCEL_DATA = """
Frederik	Bryson DeChambeau	Russel Henley	Colin Morikawa
Wynand	Rory Mcllroy	Sam Burns	Tommy Fleetwood
Jason	Tony Finau	Corey Connors	Akshay Bhatia
Martin	Patrick Cantlay	Thomas Detry	Sergio Garcia
Frederik  2	Thomas Detry	Sam Burns	Corey Connors
Jason 2	Bryson DeChambeau	Thomas Detry	Sergio Garcia
Wynand 2	Patrick Cantlay	Tony Finau	Akshay Bhatia
Martin 2	Tony Finau	Tommy Fleetwood	Russel Henley
Rupert	Patrick Cantlay	Tony Finau	Tommy Fleetwood
Rupert 3	Akshay Bhatia	Sergio Garcia	Bryson DeChambeau

""" # Add all 100 names here following this tab-separated format

# ==========================================
# 3. CHAMPIONSHIP BRUTALISM STYLING
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&family=JetBrains+Mono:wght@500&display=swap');
    
    :root {
        --fairway: #064E3B;
        --gold: #EAB308;
        --bunker: #F5F5F4;
    }

    .stApp { background-color: var(--bunker); background-image: radial-gradient(#000 1px, transparent 0); background-size: 30px 30px; }
    
    h1, h2, h3 { font-family: 'Inter', sans-serif !important; font-weight: 900 !important; text-transform: uppercase; color: #000; }
    
    .podium-card {
        background: white;
        border: 4px solid #000;
        padding: 25px;
        box-shadow: 10px 10px 0px #000;
        margin-bottom: 30px;
    }

    .metric-value { font-family: 'JetBrains Mono', monospace; font-size: 3rem; font-weight: bold; }
    
    .marquee {
        background: var(--fairway);
        color: var(--gold);
        padding: 10px 0;
        font-family: 'Inter', sans-serif;
        font-weight: 900;
        border-bottom: 4px solid #000;
        margin-bottom: 40px;
    }
    
    .player-row {
        background: white;
        border: 2px solid #000;
        padding: 10px 20px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. CORE ENGINE (API & LOGIC)
# ==========================================

@st.cache_data(ttl=600) # Refreshes every 10 minutes to save API credits
def get_live_scores():
    try:
        response = requests.get(URL, headers=HEADERS, params=PARAMS)
        data = response.json()
        rows = data.get('leaderboardRows', [])
        
        score_map = {}
        for r in rows:
            name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip().lower()
            score = r.get('toParValue', 0)
            if score == "E": score = 0
            score_map[name] = int(score)
        return score_map, rows
    except Exception as e:
        st.error(f"Engine Failure: {e}")
        return {}, []

def parse_syndicate_teams(raw_data):
    teams = []
    lines = raw_data.strip().split('\n')
    for line in lines:
        parts = line.split('\t')
        if len(parts) >= 4:
            teams.append({
                "owner": parts[0],
                "players": [p.strip().lower() for p in parts[1:4]]
            })
    return teams

# ==========================================
# 5. UI GENERATION
# ==========================================

# 1. Header Marquee
st.markdown('<div class="marquee"><marquee scrollamount="12">THE SHINNECOCK SYNDICATE // 2026 US OPEN // 100 PLAYERS // LIVE FROM NEW YORK</marquee></div>', unsafe_allow_html=True)
st.title("🏆 The Syndicate Derby")

# Get Data
score_map, pro_rows = get_live_scores()
syndicate_teams = parse_syndicate_teams(RAW_EXCEL_DATA)

# Calculate Leaderboard
leaderboard = []
for team in syndicate_teams:
    total = sum(score_map.get(p, 0) for p in team['players'])
    leaderboard.append({
        "Owner": team['owner'],
        "Score": total,
        "Team": ", ".join([p.title() for p in team['players']])
    })

df_leaderboard = pd.DataFrame(leaderboard).sort_values("Score")

# 2. The Podium (Top 3)
st.subheader("The Championship Flight")
col1, col2, col3 = st.columns(3)
top_3 = df_leaderboard.head(3).to_dict('records')

for i, (col, color) in enumerate(zip([col1, col2, col3], ["#EAB308", "#94A3B8", "#B45309"])):
    if i < len(top_3):
        with col:
            st.markdown(f"""
                <div class="podium-card" style="border-color: {color}">
                    <h3 style="color: {color}">#{i+1} {top_3[i]['Owner']}</h3>
                    <div class="metric-value">{top_3[i]['Score']}</div>
                    <p style="font-size: 0.8rem; color: #666;">{top_3[i]['Team']}</p>
                </div>
            """, unsafe_allow_html=True)

# 3. The Pack (All 100 Players)
st.subheader("The Full Derby Field")
for _, row in df_leaderboard.iloc[3:].iterrows():
    st.markdown(f"""
        <div class="player-row">
            <div><strong>{row['Owner']}</strong> <span style="margin-left: 20px; color: #666; font-size: 0.8rem;">{row['Team']}</span></div>
            <div style="font-family: 'JetBrains Mono'; font-weight: bold;">{row['Score']}</div>
        </div>
    """, unsafe_allow_html=True)

# 4. Pro Master Board
with st.expander("📊 VIEW OFFICIAL TOURNAMENT MASTER BOARD"):
    st.write("Live Professional Field at Shinnecock Hills")
    pro_df = pd.DataFrame(pro_rows)[['position', 'firstName', 'lastName', 'thru', 'toParValue']]
    st.table(pro_df)

# 5. The Engine Room (Debug Info)
with st.expander("🛠️ THE ENGINE ROOM (DEBUG)"):
    st.write("If someone has a score of 0 and shouldn't, check their name spelling against this list:")
    st.write(list(score_map.keys()))
