import streamlit as st
import requests
import pandas as pd

# ==========================================
# 1. CONFIGURATION & API SETUP
# ==========================================
API_KEY = st.secrets["api_key"]
API_URL = "https://live-golf-data.p.rapidapi.com/leaderboard"

st.set_page_config(page_title="Friendship Derby", layout="wide")

# ==========================================
# 2. THE TEAM DATA (Paste your Excel data here)
# ==========================================
# Format: Friend Name [TAB] Player 1 [TAB] Player 2 [TAB] Player 3
RAW_EXCEL_DATA = """
Frederik	Rory McIlroy	Jordan Spieth	Bryson DeChambeau
Martin	Scottie Scheffler	Patrick Cantlay	Matt Fitzpatrick
Spanner	Rory McIlroy	Scottie Scheffler	Bryson DeChambeau
"""

def get_teams_from_excel(raw_data):
    teams = {}
    lines = raw_data.strip().split('\n')
    for line in lines:
        parts = line.split('\t')
        if len(parts) >= 2:
            friend_name = parts[0].strip()
            players = [p.strip() for p in parts[1:] if p.strip()]
            teams[friend_name] = players
    return teams

TEAMS = get_teams_from_excel(RAW_EXCEL_DATA)

# ==========================================
# 3. DATA FETCHING & PROCESSING
# ==========================================
def parse_score(val):
    """Converts API strings like '-6' or 'E' into usable numbers."""
    if not val or str(val).upper() in ["E", "EVEN", "-", "CUT"]:
        return 0
    try:
        # Removes "+" and converts string to integer
        return int(str(val).replace("+", ""))
    except ValueError:
        return 0

@st.cache_data(ttl=60)
def get_leaderboard_data(year):
    querystring = {"orgId": "1", "tournId": "026", "year": str(year)}
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"
    }
    try:
        response = requests.get(API_URL, headers=headers, params=querystring)
        data = response.json()
        # The API provides data in 'leaderboardRows'
        return data.get('leaderboardRows', [])
    except Exception as e:
        st.error(f"API Error: {e}")
        return []

# ==========================================
# 4. MAIN APP UI
# ==========================================
st.title("⛳ US Open: Friendship Derby")

with st.sidebar:
    st.header("Settings")
    selected_year = st.selectbox("Select Season", [2024, 2025, 2026], index=0)
    if st.button("🔄 Refresh Scores"):
        st.cache_data.clear()

rows = get_leaderboard_data(selected_year)

if not rows:
    st.warning("No data found. Check your API key or Year selection.")
else:
    # 1. Map API data to a searchable dictionary
    player_scores = {}
    for row in rows:
        # Based on your screenshot: firstName and lastName are top-level
        fname = row.get('firstName', '').strip()
        lname = row.get('lastName', '').strip()
        full_name = f"{fname} {lname}".lower()
        
        # 'total' is the score field (e.g., "-6")
        raw_score = row.get('total', '0')
        player_scores[full_name] = parse_score(raw_score)

    # 2. Calculate Team Totals
    leaderboard_results = []
    for friend, roster in TEAMS.items():
        total_team_score = 0
        roster_details = []
        for p_name in roster:
            # Match the name from your Excel list
            p_score = player_scores.get(p_name.lower().strip(), 0)
            total_team_score += p_score
            roster_details.append({"name": p_name, "score": p_score})
        
        leaderboard_results.append({
            "Friend": friend,
            "Total Score": total_team_score,
            "Roster": roster_details
        })

    # 3. Sort by lowest score (Golf rules)
    leaderboard_results = sorted(leaderboard_results, key=lambda x: x["Total Score"])

    # 4. Display Results
    for idx, entry in enumerate(leaderboard_results):
        rank = idx + 1
        with st.container():
            col1, col2 = st.columns([1, 4])
            with col1:
                st.metric(label=f"Rank #{rank}", value=entry["Total Score"], delta=None)
            with col2:
                st.subheader(entry["Friend"])
                # Show individual player contributions
                player_line = " | ".join([f"{p['name']}: {p['score']}" for p in entry["Roster"]])
                st.caption(player_line)
            st.divider()

    # DEBUG: Help with name spelling
    with st.expander("🛠️ Debug: Check API Player Names"):
        st.write("If a score is 0 but shouldn't be, match the spelling in your RAW_EXCEL_DATA to these names:")
        all_names = sorted(list(player_scores.keys()))
        st.write(", ".join(all_names))
