import streamlit as st
import pandas as pd
import requests
from streamlit_gsheets import GSheetsConnection
from collections import Counter
from itertools import combinations
import re

# --- 1. SETTINGS & BRANDING ---
st.set_page_config(page_title="154th Claret Jug Syndicate", layout="wide")

# Coastal Brutalism CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=Roboto+Mono:wght@400;700&display=swap');
    
    .main { background-color: #020617; color: #f8fafc; }
    h1, h2, h3 { font-family: 'Archivo Black', sans-serif; text-transform: uppercase; letter-spacing: -1px; }
    .stMetric { background-color: #1e293b; border: 1px solid #334155; padding: 15px; border-radius: 0px; box-shadow: 4px 4px 0px #D4AF37; }
    .stButton>button { width: 100%; border-radius: 0px; font-family: 'Archivo Black'; background-color: #D4AF37; color: #020617; border: none; transition: 0.2s; }
    .stButton>button:hover { background-color: #2DD4BF; transform: translate(-2px, -2px); box-shadow: 4px 4px 0px #020617; }
    
    /* Score Colors */
    .score-under { color: #2DD4BF; font-weight: bold; }
    .score-over { color: #EF4444; font-weight: bold; }
    .score-even { color: #94a3b8; }
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA CONNECTIONS ---
# Replace with your actual Sheet URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1X5X.../edit?usp=sharing"
API_KEY = st.secrets["api_key"] # Ensure this is in your secrets

@st.cache_data(ttl=600)
def get_live_data():
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"
    # Testing with 2024 (ID: 026) until 2025 starts
    params = {"orgId": "1", "tournId": "026", "year": "2024"} 
    headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        return data.get('leaderboardRows', [])
    except Exception as e:
        st.error(f"API Connection Error: {e}")
        return []

# --- 3. TEAM MANAGEMENT (GOOGLE SHEETS) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_teams():
    try:
        df = conn.read(spreadsheet=SHEET_URL)
        # Convert to dictionary format our app expects
        teams = {}
        for _, row in df.iterrows():
            teams[row['User']] = [str(row['P1']), str(row['P2']), str(row['P3'])]
        return teams
    except Exception:
        return {}

def save_team(user, p1, p2, p3):
    current_df = conn.read(spreadsheet=SHEET_URL)
    new_data = pd.DataFrame([{"User": user, "P1": p1, "P2": p2, "P3": p3}])
    updated_df = pd.concat([current_df, new_data], ignore_index=True)
    conn.update(spreadsheet=SHEET_URL, data=updated_df)
    st.cache_data.clear() # Force reload

# --- 4. LOGIC ENGINE ---
def fuzzy_match(input_name, pro_rows):
    """Matches a user-typed name against official API names."""
    input_clean = str(input_name).lower().strip()
    for row in pro_rows:
        full_name = f"{row.get('firstName', '')} {row.get('lastName', '')}".lower()
        if input_clean in full_name or full_name in input_clean:
            return row
    return None

# --- 5. UI LAYOUT ---
st.title("🏆 154th Claret Jug Syndicate")
st.markdown("---")

# Sidebar: Team Entry
with st.sidebar:
    st.header("THE TERMINAL")
    with st.form("entry_form"):
        u_name = st.text_input("Entry Name")
        p1_input = st.text_input("Golfer 1")
        p2_input = st.text_input("Golfer 2")
        p3_input = st.text_input("Golfer 3")
        submit = st.form_submit_button("LOCK IN SYNDICATE")
        
        if submit and u_name and p1_input:
            save_team(u_name, p1_input, p2_input, p3_input)
            st.success("Team Broadcasted to the Cloud!")

# Main Dashboard
rows = get_live_data()
teams_data = load_teams()

if not rows:
    st.warning("Waiting for tournament pulse... (API Offline or No Data)")
else:
    # Build a lookup map for speed
    player_map = {}
    for r in rows:
        name = f"{r.get('firstName','')} {r.get('lastName','')}".strip()
        player_map[name.lower()] = {
            "score": r.get('totalToPar', 0),
            "display": f"{name} ({r.get('totalToPar', 'E')})",
            "thru": r.get('thru', '-'),
            "rounds": {rd.get('roundId'): rd.get('scoreToPar', 0) for rd in r.get('rounds', [])}
        }

    # Calculate Leaderboard
    leaderboard = []
    all_picks = []
    
    for user, roster in teams_data.items():
        total_score = 0
        details = []
        for p in roster:
            match = fuzzy_match(p, rows)
            if match:
                m_name = f"{match.get('firstName','')} {match.get('lastName','')}".lower()
                p_data = player_map.get(m_name)
                s = p_data['score'] if isinstance(p_data['score'], int) else 0
                total_score += s
                details.append(p_data['display'])
                all_picks.append(f"{match.get('firstName','')} {match.get('lastName','')}")
            else:
                details.append(f"{p} (???)")
        
        leaderboard.append({
            "User": user,
            "Total": total_score,
            "Roster": " / ".join(details)
        })

    # Display Top 3 Podium
    sorted_lb = sorted(leaderboard, key=lambda x: x['Total'])
    cols = st.columns(3)
    for i, user_data in enumerate(sorted_lb[:3]):
        with cols[i]:
            st.metric(f"#{i+1} {user_data['User']}", f"{user_data['Total']} to Par")

    # Full Standings Table
    st.header("THE BOARD: SYNDICATE STANDINGS")
    df_lb = pd.DataFrame(sorted_lb)
    if not df_lb.empty:
        st.table(df_lb[["User", "Total", "Roster"]])

    # Hive Mind Section
    st.markdown("---")
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.header("THE HIVE MIND")
        if all_picks:
            counts = Counter(all_picks).most_common(5)
            for p, count in counts:
                st.write(f"**{p}**: {count} Picks")

    with col_right:
        st.header("SYNDICATE INSIGHTS")
        # Most common 2-player pairings
        if len(teams_data) > 0:
            all_pairs = []
            for roster in teams_data.values():
                # Sort to ensure (A,B) matches (B,A)
                all_pairs.extend(combinations(sorted(roster), 2))
            
            top_pair = Counter(all_pairs).most_common(1)
            if top_pair:
                p1, p2 = top_pair[0][0]
                st.write(f"🔥 **Hottest Duo:** {p1} + {p2}")

# Footer
st.markdown("<br><br><p style='text-align:center; color:#475569;'>STORM-DRIVEN DATA | SHINNECOCK 2026 PREP</p>", unsafe_allow_html=True)
