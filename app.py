import streamlit as st
import pandas as pd
import requests
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURATION ---
TOURN_ID = "100"
YEAR = "2026"

# --- HELPER FUNCTIONS ---

def parse_score_to_int(val):
    """Handles strings, None, and MongoDB-style {'$numberInt': '5'} dicts."""
    if val is None: return 0
    if isinstance(val, dict):
        val = val.get('$numberInt', 0)
    val_str = str(val).lower().strip()
    if val_str in ['none', 'e', '', 'null']: return 0
    try:
        return int(float(val_str))
    except:
        return 0

def format_score_val(val):
    if val == 0: return "E"
    return f"+{val}" if val > 0 else str(val)

@st.cache_data(ttl=900)
def get_live_scores():
    try:
        url = f"https://live-golf-data.p.rapidapi.com/leaderboard?orgId=1&tournId={TOURN_ID}&year={YEAR}"
        headers = {
            "X-RapidAPI-Key": st.secrets["api_key"],
            "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers).json()
        return response.get('leaderboardRows') or response.get('leaderboard') or response.get('players') or []
    except:
        return []

def get_round_averages(rows):
    """Calculates the average score for each round based only on active players."""
    averages = {1: 0, 2: 0, 3: 0, 4: 0}
    for rd in range(1, 5):
        scores = []
        for r in rows:
            # Look for round data in the player's history
            rd_data = next((item for item in r.get('rounds', []) 
                           if parse_score_to_int(item.get('roundNumber')) == rd 
                           or parse_score_to_int(item.get('roundId')) == rd-1), None)
            
            if rd_data:
                s = rd_data.get('scoreToPar')
                if s is not None and str(s).lower() != 'none':
                    scores.append(parse_score_to_int(s))
        if scores:
            averages[rd] = round(sum(scores) / len(scores))
    return averages

def get_sheet_data():
    """Connects to Google Sheets using st.secrets."""
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    return client.open("British Open Sheet").sheet1.get_all_records()

# --- APP SETUP ---
st.set_page_config(page_title="154th Open Tracker", layout="wide")
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; color: #D4AF37; }
    .stDataFrame { border: 1px solid #333; }
    </style>
""", unsafe_allow_html=True)

st.title("🏆 154th Open Championship Tracker")

try:
    rows = get_live_scores()
    averages = get_round_averages(rows)
    
    # 1. BUILD PLAYER SCORE MAP (with Missed Cut Logic)
    player_map = {}
    for r in rows:
        name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip().lower()
        
        rd_scores = {}
        for rd_obj in r.get('rounds', []):
            num = parse_score_to_int(rd_obj.get('roundNumber')) or (parse_score_to_int(rd_obj.get('roundId')) + 1)
            rd_scores[num] = parse_score_to_int(rd_obj.get('scoreToPar'))
        
        # Total = Actual played + Field Avg for any missed rounds (R3 & R4 only)
        total = 0
        for rd in range(1, 5):
            if rd in rd_scores:
                total += rd_scores[rd]
            elif averages[rd] != 0 and rd > 2:
                total += averages[rd]
        
        player_map[name] = total

    # --- TABS ---
    tab1, tab2, tab3, tab4 = st.tabs(["Standings", "Official Master Board", "Round Winners", "Registry"])

    with tab1:
        st.subheader("Live Standings (Missed Cut Logic Applied)")
        registry_entries = get_sheet_data()
        
        if registry_entries:
            standings_list = []
            for entry in registry_entries:
                user = entry.get("User", "Unknown")
                p1, p2, p3 = str(entry.get("P1", "")), str(entry.get("P2", "")), str(entry.get("P3", ""))
                
                s1 = player_map.get(p1.lower(), 0)
                s2 = player_map.get(p2.lower(), 0)
                s3 = player_map.get(p3.lower(), 0)
                
                standings_list.append({
                    "User": user,
                    "P1": f"{p1} ({format_score_val(s1)})",
                    "P2": f"{p2} ({format_score_val(s2)})",
                    "P3": f"{p3} ({format_score_val(s3)})",
                    "TotalInt": s1 + s2 + s3
                })
            
            df_s = pd.DataFrame(standings_list).sort_values("TotalInt")
            df_s.insert(0, 'Rank', range(1, 1 + len(df_s)))
            df_s['Total'] = df_s['TotalInt'].apply(format_score_val)
            
            st.dataframe(
                df_s[['Rank', 'User', 'P1', 'P2', 'P3', 'Total']],
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Rank": st.column_config.Column(width=50),
                    "Total": st.column_config.Column(width=80)
                }
            )
            st.info(f"Penalty for Missed Cut: Round 3 (+{averages[3]}) | Round 4 (+{averages[4]})")

    with tab2:
        st.subheader("Official Tournament Leaderboard")
        pro_field = []
        for r in rows:
            pro_field.append({
                "Pos": r.get('position'),
                "Player": f"{r.get('firstName', '')} {r.get('lastName', '')}",
                "Thru": r.get('thru'),
                "Score": format_score_val(parse_score_to_int(r.get('totalToPar') or r.get('total')))
            })
        st.dataframe(pd.DataFrame(pro_field), hide_index=True, use_container_width=True)

    with tab3:
        st.subheader("Daily Performance Analysis")
        sel_rd = st.radio("Select Round", [1, 2, 3, 4], horizontal=True)
        st.metric(f"Field Average (Round {sel_rd})", format_score_val(averages[sel_rd]))
        
        # Here you can add your "Daily Burners" logic using averages[sel_rd]

    with tab4:
        st.subheader("Raw Registry Data")
        st.dataframe(pd.DataFrame(registry_entries), hide_index=True)

except Exception as e:
    st.error(f"System Error: {e}")
