

import streamlit as st
import requests
import pandas as pd
import re

# ==========================================
# 1. SETUP & THEME
# ==========================================
st.set_page_config(page_title="US Open: The Syndicate Derby", layout="wide")

API_KEY = st.secrets["api_key"]
URL = "https://live-golf-data.p.rapidapi.com/leaderboard"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
PARAMS = {"orgId": "1", "tournId": "026", "year": "2024"} 

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&family=JetBrains+Mono:wght@500&display=swap');
    :root { --fairway: #064E3B; --gold: #EAB308; --bunker: #F5F5F4; }
    .stApp { background-color: var(--bunker); background-image: radial-gradient(#000 1px, transparent 0); background-size: 30px 30px; }
    h1, h2, h3 { font-family: 'Inter', sans-serif !important; font-weight: 900 !important; text-transform: uppercase; color: #000; }
    .podium-card { background: white; border: 4px solid #000; padding: 25px; box-shadow: 10px 10px 0px #000; margin-bottom: 30px; min-height: 200px; }
    .player-row { background: white; border: 2px solid #000; padding: 10px 20px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
    .marquee { background: var(--fairway); color: var(--gold); padding: 10px 0; font-family: 'Inter', sans-serif; font-weight: 900; border-bottom: 4px solid #000; margin-bottom: 40px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA INPUT (SMART PARSING)
# ==========================================
# I have cleaned this up to match your screenshot. 
# The code below will now handle spaces OR tabs automatically.
RAW_EXCEL_DATA = """
Martin	Patrick Cantlay	Rory Mcilroy	Sergio Garcia
Frederik 2	Thomas Detry	Sam Burns	Corey Conners
Jason 2	Bryson Dechambeau	Thomas Detry	Sergio Garcia
Wynand 2	Patrick Cantlay	Tony Finau	Akshay Bhatia
Martin 2	Tony Finau	Tommy Fleetwood	Russel Henley
Rupert	Patrick Cantlay	Tony Finau	Tommy Fleetwood
Rupert 3	Akshay Bhatia	Sergio Garcia	Bryson Dechambeau
"""

# ==========================================
# 3. THE ENGINE
# ==========================================

@st.cache_data(ttl=600)
def get_engine_data():
    try:
        response = requests.get(URL, headers=HEADERS, params=PARAMS)
        data = response.json()
        rows = data.get('leaderboardRows', data.get('leaderboard', []))
        
        score_map = {}
        for r in rows:
            # Create full name
            fname = str(r.get('firstName', '')).strip()
            lname = str(r.get('lastName', '')).strip()
            full_name = f"{fname} {lname}".lower()
            
            # GET SCORE (Mapping to 'total' as seen in your screenshot)
            raw_score = r.get('total', r.get('toParValue', 0))
            
            # Handle "E" for Even
            if str(raw_score).strip().upper() == "E":
                final_score = 0
            else:
                try:
                    # Remove any "+" signs if they exist
                    final_score = int(str(raw_score).replace('+', ''))
                except:
                    final_score = 0
            
            score_map[full_name] = final_score
                
        return score_map, rows
    except Exception as e:
        st.error(f"Engine Failure: {e}")
        return {}, []

def smart_parse_teams(raw_text):
    teams = []
    for line in raw_text.strip().split('\n'):
        # This regex splits by TAB or by 2+ SPACES (common when copying from Excel)
        parts = re.split(r'\t|\s{2,}', line.strip())
        if len(parts) >= 4:
            teams.append({
                "owner": parts[0],
                "players": [p.strip().strip('"').lower() for p in parts[1:4]]
            })
    return teams

# ==========================================
# 4. RENDER
# ==========================================

st.markdown('<div class="marquee"><marquee scrollamount="12">THE SHINNECOCK SYNDICATE // 2026 US OPEN // LIVE SCORING ACTIVE</marquee></div>', unsafe_allow_html=True)
st.title("🏆 THE US OPEN PREDICTION TRACKER")

score_map, pro_rows = get_engine_data()
teams = smart_parse_teams(RAW_EXCEL_DATA)

# Calculate Leaderboard
results = []
for t in teams:
    team_total = 0
    display_names = []
    for p in t['players']:
        # Direct match
        score = score_map.get(p, 0)
        # Fallback fuzzy match (check if your input is part of the API name)
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

# UI: PODIUM
st.subheader("CHAMPIONSHIP FLIGHT")
cols = st.columns(3)
podium_list = df.head(3).to_dict('records')

for i, (col, color) in enumerate(zip(cols, ["#EAB308", "#94A3B8", "#B45309"])):
    if i < len(podium_list):
        with col:
            st.markdown(f"""
                <div class="podium-card" style="border-color: {color}">
                    <h2 style="color: {color}; margin:0;">#{i+1} {podium_list[i]['Owner']}</h2>
                    <div style="font-family:'JetBrains Mono'; font-size:4rem; font-weight:bold;">{podium_list[i]['Score']}</div>
                    <div style="font-size:0.8rem; color:#666; line-height:1.2;">{podium_list[i]['Roster']}</div>
                </div>
            """, unsafe_allow_html=True)

# UI: THE PACK
st.subheader("THE FULL FIELD")
for _, row in df.iloc[3:].iterrows():
    st.markdown(f"""
        <div class="player-row">
            <div><b>{row['Owner']}</b> <span style="margin-left:15px; color:#666; font-size:0.85rem;">{row['Roster']}</span></div>
            <div style="font-family:'JetBrains Mono'; font-weight:bold; font-size:1.2rem;">{row['Score']}</div>
        </div>
    """, unsafe_allow_html=True)

# UI: TABLES
with st.expander("📊 OFFICIAL TOURNAMENT LEADERBOARD"):
    if pro_rows:
        st.dataframe(pd.DataFrame(pro_rows), use_container_width=True)

with st.expander("🛠️ THE ENGINE ROOM"):
    st.write("API Names found:")
    st.write(list(score_map.keys()))
    st.write("Parsed Teams found:")
    st.write(teams)
