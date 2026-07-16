import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from itertools import combinations
from collections import Counter

# --- 1. SETTINGS ---
YEAR = "2026"
TOURN_ID = "100"  # The Open / British Open
RAPID_API_KEY = "213c2f2306mshe3d8b437cc34999p108477jsn6f448fb2b30c"

st.set_page_config(page_title="154th Open Championship Tracker", layout="wide")

# --- 2. HELPER FUNCTIONS ---
def bold_text(text):
    return f"**{text}**"

def parse_score(val):
    """Converts API values (None, 'E', '+1') into integers for math."""
    if val is None or val == "" or val == "E": return 0
    try: return int(str(val).replace('+', ''))
    except: return 0

def format_score_val(val):
    """Converts integers back to display strings (0 becomes 'E')."""
    if val == 0: return "E"
    return f"+{val}" if val > 0 else str(val)

@st.cache_data(ttl=600)
def get_live_scores():
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"
    headers = {"X-RapidAPI-Key": RAPID_API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
    params = {"orgId": "1", "tournId": TOURN_ID, "year": YEAR}
    try:
        resp = requests.get(url, headers=headers, params=params).json()
        return resp.get('leaderboardRows') or resp.get('leaderboard') or resp.get('players') or []
    except:
        return []

# --- 3. THE TEAM DATA (RAW EXCEL) ---
RAW_DATA = """
User	P1	P2	P3
Frederik	Rory McIlroy	Scottie Scheffler	Bryson DeChambeau
Martin	Jon Rahm	Brooks Koepka	Viktor Hovland
"""

def get_teams(raw_str):
    teams = {}
    lines = raw_str.strip().split('\n')[1:]
    for line in lines:
        parts = line.split('\t')
        if len(parts) >= 4:
            teams[parts[0]] = [parts[1], parts[2], parts[3]]
    return teams

TEAMS = get_teams(RAW_DATA)

# --- 4. CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&family=JetBrains+Mono&display=swap');
    .main { background-color: #020617; color: #f8fafc; }
    h1, h2, h3 { font-family: 'Inter', sans-serif; text-transform: uppercase; letter-spacing: -1px; }
    .stTabs [data-baseweb="tab-list"] { background-color: #020617; border-bottom: 2px solid #EAB308; }
    .stTabs [data-baseweb="tab"] { color: #94a3b8; font-family: 'JetBrains Mono'; }
    .stTabs [aria-selected="true"] { color: #EAB308 !important; border-bottom: 2px solid #EAB308 !important; }
</style>
""", unsafe_content_as_html=True)

# --- 5. DATA PROCESSING ---
live_rows = get_live_scores()

# Map scores with the new fallback logic
score_map = {
    f"{r.get('firstName', '')} {r.get('lastName', '')}".strip().lower(): parse_score(r.get('totalToPar') or r.get('toPar') or 0) 
    for r in live_rows
}

# --- 6. APP TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["SYNDICATE HUB", "LEADERBOARD", "FIELD INTEL", "OFFICIAL MASTER BOARD"])

with tab1:
    st.title("🏆 154TH OPEN CHAMPIONSHIP")
    st.subheader("Royal Birkdale • 2026")
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("Tournament Status: Live Data Stream Active")
    with col2:
        st.success(f"Last Sync: {datetime.now().strftime('%H:%M:%S')}")

with tab2:
    st.header("SYNDICATE STANDINGS")
    
    standings = []
    for user, roster in TEAMS.items():
        total = 0
        details = []
        for p_name in roster:
            s = score_map.get(p_name.lower(), 0)
            total += s
            details.append(f"{p_name} ({format_score_val(s)})")
        
        standings.append({
            "User": user,
            "Total": total,
            "Roster": " • ".join(details)
        })
    
    df_standings = pd.DataFrame(standings).sort_values("Total")
    df_standings.insert(0, "Rank", range(1, len(df_standings) + 1))
    st.table(df_standings)

with tab3:
    st.header("FIELD INTELLIGENCE")
    all_picks = [p for roster in TEAMS.values() for p in roster]
    counts = Counter(all_picks).most_common(10)
    
    st.subheader("Most Selected Players")
    intel_df = pd.DataFrame(counts, columns=["Player", "Picks"])
    intel_df.insert(0, "Rank", range(1, len(intel_df) + 1))
    st.table(intel_df)

with tab4:
    st.header("OFFICIAL MASTER BOARD")
    if not live_rows:
        st.warning("Waiting for tournament data...")
    else:
        master_list = []
        for r in live_rows:
            master_list.append({
                "Pos": r.get('position', '-'),
                "Player": f"{r.get('firstName', '')} {r.get('lastName', '')}".strip(),
                "Thru": r.get('thru', 'F'),
                "Score": format_score_val(parse_score(r.get('totalToPar') or r.get('toPar') or 0))
            })
        
        st.dataframe(pd.DataFrame(master_list), use_container_width=True, hide_index=True)

st.sidebar.markdown("---")
st.sidebar.write("Sync Frequency: 10 mins")
