import streamlit as st
import requests
import pandas as pd
import re
from collections import Counter

# ==========================================
# 1. SETUP & THEME
# ==========================================
st.set_page_config(page_title="US Open: The Syndicate Derby", layout="wide")

# API Config
API_KEY = "213c2f2306mshe3d8b437cc34999p108477jsn6f448fb2b30c"
URL = "https://live-golf-data.p.rapidapi.com/leaderboard"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
PARAMS = {"orgId": "1", "tournId": "026", "year": "2024"} 

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&family=JetBrains+Mono:wght@500&display=swap');
    :root { --fairway: #064E3B; --gold: #EAB308; --bunker: #F5F5F4; --live: #22C55E; }
    .stApp { background-color: var(--bunker); background-image: radial-gradient(#000 1px, transparent 0); background-size: 30px 30px; }
    h1, h2, h3 { font-family: 'Inter', sans-serif !important; font-weight: 900 !important; text-transform: uppercase; color: #000; letter-spacing: -1px; }
    .podium-card { background: white; border: 4px solid #000; padding: 25px; box-shadow: 10px 10px 0px #000; margin-bottom: 30px; min-height: 250px; }
    .player-row { background: white; border: 2px solid #000; padding: 12px 20px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
    .marquee { background: var(--fairway); color: var(--gold); padding: 10px 0; font-family: 'Inter', sans-serif; font-weight: 900; border-bottom: 4px solid #000; margin-bottom: 40px; }
    .status-tag { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; background: #000; color: #fff; padding: 2px 6px; margin-left: 5px; }
    .live-dot { height: 8px; width: 8px; background-color: var(--live); border-radius: 50%; display: inline-block; margin-right: 5px; animation: blink 1.5s infinite; }
    .ownership-bar { background: var(--fairway); height: 20px; border: 2px solid #000; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA INPUT
# ==========================================
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
        player_stats = {}
        for r in rows:
            fname, lname = str(r.get('firstName', '')).strip(), str(r.get('lastName', '')).strip()
            display_name = f"{fname} {lname}"
            raw_score = r.get('total', r.get('toParValue', 0))
            if str(raw_score).strip().upper() == "E": final_score = 0
            else:
                try: final_score = int(str(raw_score).replace('+', ''))
                except: final_score = 0
            thru = str(r.get('thru', r.get('status', '-'))).strip()
            player_stats[display_name.lower()] = {"score": final_score, "thru": thru, "display_name": display_name}
        return player_stats, rows
    except Exception as e:
        st.error(f"Engine Failure: {e}")
        return {}, []

def smart_parse_teams(raw_text):
    teams = []
    all_picks = [] # To track ownership
    for line in raw_text.strip().split('\n'):
        parts = re.split(r'\t|\s{2,}', line.strip())
        if len(parts) >= 4:
            roster = [p.strip().strip('"').lower() for p in parts[1:4]]
            teams.append({"owner": parts[0], "players": roster})
            all_picks.extend(roster)
    return teams, all_picks

# ==========================================
# 4. RENDER
# ==========================================

st.markdown('<div class="marquee"><marquee scrollamount="12">THE SHINNECOCK SYNDICATE // OWNERSHIP ANALYTICS LIVE // US OPEN 2026</marquee></div>', unsafe_allow_html=True)
st.title("🏆 THE SYNDICATE DERBY")

player_stats, pro_rows = get_engine_data()
teams, all_picks = smart_parse_teams(RAW_EXCEL_DATA)

# Calculate Standings
results = []
for t in teams:
    team_total = 0
    bracket_roster = []
    for p in t['players']:
        score, thru, found_name = 0, "-", p.title()
        if p in player_stats:
            score, thru, found_name = player_stats[p]['score'], player_stats[p]['thru'], player_stats[p]['display_name']
        else:
            for api_name, stats in player_stats.items():
                if p in api_name or api_name in p:
                    score, thru, found_name = stats['score'], stats['thru'], stats['display_name']
                    break
        team_total += score
        status_html = f'<span class="status-tag">THR {thru}</span>' if thru.upper() == "F" else f'<span class="status-tag"><span class="live-dot"></span>H{thru}</span>'
        bracket_roster.append(f"{found_name} [{score if score <= 0 else '+' + str(score)}] {status_html}")
    results.append({"Owner": t['owner'], "Total": team_total, "Roster": " <br> ".join(bracket_roster)})

df = pd.DataFrame(results).sort_values("Total")

# UI: PODIUM & THE PACK
st.subheader("CHAMPIONSHIP FLIGHT")
cols = st.columns(3)
podium_list = df.head(3).to_dict('records')
for i, (col, color) in enumerate(zip(cols, ["#EAB308", "#94A3B8", "#B45309"])):
    if i < len(podium_list):
        with col:
            st.markdown(f'<div class="podium-card" style="border-color: {color}"><h2 style="color: {color}; margin:0;">#{i+1} {podium_list[i]["Owner"]}</h2><div style="font-family:\'JetBrains Mono\'; font-size:3.5rem; font-weight:bold; margin-bottom:10px;">{podium_list[i]["Total"]}</div><div style="font-size:0.85rem; color:#444; line-height:1.8;">{podium_list[i]["Roster"]}</div></div>', unsafe_allow_html=True)

st.subheader("THE FULL FIELD")
for _, row in df.iloc[3:].iterrows():
    st.markdown(f'<div class="player-row"><div style="flex: 2;"><b>{row["Owner"]}</b></div><div style="flex: 6; color:#666; font-size:0.8rem;">{row["Roster"].replace(" <br> ", " • ")}</div><div style="flex: 1; text-align:right; font-family:\'JetBrains Mono\'; font-weight:bold; font-size:1.4rem;">{row["Total"]}</div></div>', unsafe_allow_html=True)

# ==========================================
# 5. THE ANALYTICS TABS (NEW)
# ==========================================
st.write("---")
tab1, tab2 = st.tabs(["📊 OWNERSHIP REPORT", "📈 PRO LEADERBOARD"])

with tab1:
    st.subheader("THE MARKET SENTIMENT")
    st.write("Who did the Syndicate bet on?")
    
    # Process pick counts
    pick_counts = Counter(all_picks)
    # Map back to display names for beauty
    display_counts = {}
    for p_lower, count in pick_counts.items():
        # Try to get the real name from API, fallback to Title Case
        name = player_stats.get(p_lower, {}).get('display_name', p_lower.title())
        display_counts[name] = count
    
    owner_df = pd.DataFrame(list(display_counts.items()), columns=['Golfer', 'Selections']).sort_values('Selections', ascending=False)
    
    # Render Ownership Bars
    for _, row in owner_df.iterrows():
        pct = (row['Selections'] / len(teams)) * 100
        st.markdown(f"""
            <div style="margin-bottom:15px;">
                <div style="display:flex; justify-content:space-between; font-family:'JetBrains Mono'; font-weight:bold;">
                    <span>{row['Golfer']}</span>
                    <span>{row['Selections']} PICKS ({pct:.1f}%)</span>
                </div>
                <div class="ownership-bar" style="width: {pct}%"></div>
            </div>
        """, unsafe_allow_html=True)

with tab2:
    if pro_rows:
        st.dataframe(pd.DataFrame(pro_rows)[['position', 'firstName', 'lastName', 'thru', 'total']], use_container_width=True)
