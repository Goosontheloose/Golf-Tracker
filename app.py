import streamlit as st
import pandas as pd
import requests
from streamlit_gsheets import GSheetsConnection
from collections import Counter
from itertools import combinations

# --- 1. SETTINGS & BRANDING ---
st.set_page_config(page_title="British Open 2026", layout="wide")

# Coastal Brutalism CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=Roboto+Mono:wght@400;700&display=swap');
    .main { background-color: #020617; color: #f8fafc; }
    h1, h2, h3 { font-family: 'Archivo Black', sans-serif; text-transform: uppercase; letter-spacing: -1px; }
    .stMetric { background-color: #1e293b; border: 1px solid #334155; padding: 15px; box-shadow: 4px 4px 0px #D4AF37; }
    .stButton>button { width: 100%; border-radius: 0px; font-family: 'Archivo Black'; background-color: #D4AF37; color: #020617; border: none; }
    .stButton>button:hover { background-color: #2DD4BF; color: #020617; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONFIGURATION & DATA ---
# Replace with your actual Sheet URL from Google
SHEET_URL = "https://docs.google.com/spreadsheets/d/1X5X.../edit?usp=sharing"
API_KEY = st.secrets["api_key"]

# Current Tournament Settings (Update for the 2025/2026 Open)
ORG_ID = "1"
TOURN_ID = "100"  # Using 026 (US Open 2024) for testing data
YEAR = "2026"

# Official Top 30 Elite List
# Updated Top 30 for the 154th Open (July 2026)
TOP_30 = [
    "Scottie Scheffler", "Rory McIlroy", "Cameron Young", "Matt Fitzpatrick", 
    "Russell Henley", "Collin Morikawa", "Chris Gotterup", "Wyndham Clark", 
    "Tommy Fleetwood", "Justin Rose", "Jon Rahm", "J.J. Spaun", 
    "Viktor Hovland", "Xander Schauffele", "Ben Griffin", "Aaron Rai", 
    "Sam Burns", "Justin Thomas", "Ludvig Aberg", "Robert MacIntyre", 
    "Tyrrell Hatton", "Si Woo Kim", "Min Woo Lee", "Alex Noren", 
    "Patrick Reed", "Rickie Fowler", "Ryan Gerard", "Akshay Bhatia", 
    "Jacob Bridgeman", "Tom Kim"
]

@st.cache_data(ttl=3600)
def get_full_field():
    """Fetches every player in the field to prevent spelling errors."""
    url = "https://live-golf-data.p.rapidapi.com/tournament"
    params = {"orgId": ORG_ID, "tournId": TOURN_ID, "year": YEAR}
    headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        players = [f"{p['firstName']} {p['lastName']}".strip() for p in data.get('players', [])]
        return sorted(list(set(players)))
    except:
        return ["Tiger Woods", "Dustin Johnson", "Phil Mickelson"] # Small fallback

@st.cache_data(ttl=600)
def get_live_data():
    """Fetches the live leaderboard scores."""
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"
    params = {"orgId": ORG_ID, "tournId": TOURN_ID, "year": YEAR}
    headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json().get('leaderboardRows', [])
    except:
        return []

# --- 3. TEAM STORAGE (GOOGLE SHEETS) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_teams():
    try:
        df = conn.read(spreadsheet=SHEET_URL)
        return df.to_dict('records')
    except:
        return []

# --- 4. SIDEBAR: THE TERMINAL ---
full_field = get_full_field()
# Exclude Top 30 from wildcard so the lists don't overlap
wildcard_options = [p for p in full_field if p not in TOP_30]

with st.sidebar:
    st.header("THE TERMINAL")
    st.info("Pick 2 from the Elite Top 30. Pick 1 Wildcard from the field.")
    
    with st.form("entry_form"):
        u_name = st.text_input("Entry Name (e.g. Team Smith)")
        st.write("---")
        p1 = st.selectbox("Elite Player 1", TOP_30)
        p2 = st.selectbox("Elite Player 2", [p for p in TOP_30 if p != p1])
        st.write("---")
        p3 = st.selectbox("Wildcard Selection", wildcard_options if wildcard_options else full_field)
        
        submit = st.form_submit_button("LOCK IN SYNDICATE")
        
        if submit and u_name:
            try:
                current_df = conn.read(spreadsheet=SHEET_URL)
                new_row = pd.DataFrame([{"User": u_name, "P1": p1, "P2": p2, "P3": p3}])
                updated_df = pd.concat([current_df, new_row], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, data=updated_df)
                st.success(f"Confirmed! {u_name} is locked in.")
                st.cache_data.clear() # Force app to refresh data
            except Exception as e:
                st.error(f"Save Failed: {e}")

# --- 5. MAIN DASHBOARD ---
st.title("🏆 154th Claret Jug Syndicate")
st.markdown("---")

rows = get_live_data()
teams = load_teams()

if not rows:
    st.warning("📡 Waiting for tournament broadcast... (API fetching historical or live data)")
else:
    # 5a. Build Player Lookup
    player_map = {}
    all_pros_seen = []
    for r in rows:
        fn, ln = r.get('firstName', ''), r.get('lastName', '')
        full_name = f"{fn} {ln}".strip().lower()
        score = r.get('totalToPar', 0)
        # Handle 'E' for Even
        score_val = 0 if score in ['E', 'Even', 0] else int(score)
        
        player_map[full_name] = {
            "score": score_val,
            "display": f"{fn} {ln} ({score})"
        }

    # 5b. Calculate Leaderboard
    leaderboard = []
    all_picks = []
    
    for team in teams:
        user = team.get('User', 'Unknown')
        roster = [str(team.get('P1','')), str(team.get('P2','')), str(team.get('P3',''))]
        
        total_team_score = 0
        roster_status = []
        
        for p in roster:
            p_clean = p.strip().lower()
            # Simple substring match (Fuzzy)
            match = next((v for k, v in player_map.items() if p_clean in k or k in p_clean), None)
            
            if match:
                total_team_score += match['score']
                roster_status.append(match['display'])
                all_picks.append(p.strip())
            else:
                roster_status.append(f"{p} (Cut/NS)")
        
        leaderboard.append({
            "User": user,
            "Total": total_team_score,
            "Roster": " | ".join(roster_status)
        })

    # 5c. Display Rankings
    if leaderboard:
        df_final = pd.DataFrame(leaderboard).sort_values("Total")
        
        # Top 3 Podium
        cols = st.columns(3)
        for i, row_data in enumerate(df_final.head(3).to_dict('records')):
            with cols[i]:
                st.metric(f"#{i+1} {row_data['User']}", f"{row_data['Total']} to Par")

        st.header("THE BOARD: SYNDICATE STANDINGS")
        st.table(df_final[["User", "Total", "Roster"]])

    # 5d. Hive Mind Statistics
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.header("THE HIVE MIND")
        if all_picks:
            top_picked = Counter(all_picks).most_common(5)
            for p, count in top_picked:
                st.write(f"**{p}**: {count} Syndicate Members")
    
    with c2:
        st.header("SYNDICATE INSIGHTS")
        if len(teams) > 0:
            all_pairs = []
            for t in teams:
                roster = sorted([str(t.get('P1','')), str(t.get('P2','')), str(t.get('P3',''))])
                all_pairs.extend(combinations(roster, 2))
            
            top_pair = Counter(all_pairs).most_common(1)
            if top_pair:
                p1, p2 = top_pair[0][0]
                st.write(f"🔥 **Power Duo:** {p1} & {p2}")

st.markdown("<p style='text-align:center; opacity:0.5; margin-top:50px;'>BROADCAST DATA VIA RAPIDAPI | COASTAL BRUTALISM v2.0</p>", unsafe_allow_html=True)
