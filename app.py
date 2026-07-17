import streamlit as st
import pandas as pd
import requests
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURATION ---
TOURN_ID = "100"
YEAR = "2026"
# API_KEY fetched from st.secrets['api_key']

def parse_score_to_int(val):
    if val is None or str(val).lower() in ['none', 'e', '']: return 0
    try: return int(val)
    except: return 0

def format_score_val(val):
    if val == 0: return "E"
    return f"+{val}" if val > 0 else str(val)

@st.cache_data(ttl=900)
def get_live_scores():
    url = f"https://live-golf-data.p.rapidapi.com/leaderboard?orgId=1&tournId={TOURN_ID}&year={YEAR}"
    headers = {"X-RapidAPI-Key": st.secrets["api_key"], "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
    response = requests.get(url, headers=headers).json()
    # Check for various possible keys in the API response
    return response.get('leaderboardRows') or response.get('leaderboard') or response.get('players') or []

def get_round_averages(rows):
    """Calculates the average score for each round based only on active players."""
    averages = {1: 0, 2: 0, 3: 0, 4: 0}
    for rd in range(1, 5):
        scores = []
        for r in rows:
            # The API stores rounds in a list. We find the one where roundId or roundNumber matches.
            rd_data = next((item for item in r.get('rounds', []) if item.get('roundNumber', -1) == rd or item.get('roundId', -1) == rd-1), None)
            if rd_data:
                s = rd_data.get('scoreToPar')
                if s is not None and str(s).lower() != 'none':
                    scores.append(parse_score_to_int(s))
        if scores:
            averages[rd] = round(sum(scores) / len(scores))
    return averages

# --- MAIN APP ---
st.set_page_config(page_title="154th Open Tracker", layout="wide")
st.title("🏆 154th Open Championship Tracker")

try:
    rows = get_live_scores()
    averages = get_round_averages(rows)
    
    # Build the player score map with Missed Cut logic
    player_map = {}
    for r in rows:
        name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip().lower()
        
        # Determine actual rounds played
        rd_scores = {}
        for rd_obj in r.get('rounds', []):
            num = rd_obj.get('roundNumber') or (rd_obj.get('roundId', -1) + 1)
            rd_scores[num] = parse_score_to_int(rd_obj.get('scoreToPar'))
        
        # Calculate Total: Actual scores + Averages for missed rounds
        total = 0
        for rd in range(1, 5):
            if rd in rd_scores:
                total += rd_scores[rd]
            elif averages[rd] != 0 and rd > 2: # Only apply penalty for R3/R4
                total += averages[rd]
        
        player_map[name] = total

    # --- TABS ---
    tab1, tab2, tab3, tab4 = st.tabs(["Standings", "Master Board", "Round Winners", "Registry"])

    with tab1:
        st.subheader("Leaderboard (Missed Cut Penalty Applied)")
        # Load Registry from Google Sheets
        # (Assuming gspread authentication is already configured in your script)
        # ... [Your existing gspread connection code here] ...
        
        # Example processing loop for the Standings Table
        # entries = sheet.get_all_records()
        # ...
        # score = player_map.get(p1.lower(), 0) + player_map.get(p2.lower(), 0) + player_map.get(p3.lower(), 0)

    with tab3:
        st.subheader("Daily Performance Analysis")
        selected_rd = st.radio("Select Round", [1, 2, 3, 4], horizontal=True)
        
        st.write(f"**Field Average for Round {selected_rd}:** {format_score_val(averages[selected_rd])}")
        
        # Daily Burners Logic
        # For the selected round, if a player in a user's roster didn't play,
        # they receive the 'averages[selected_rd]' as their score for that tab.

except Exception as e:
    st.error(f"Critical System Error: {e}")
