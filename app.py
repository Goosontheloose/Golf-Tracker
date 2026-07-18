import streamlit as st
import pandas as pd
import requests
import gspread
from google.oauth2.service_account import Credentials
from collections import Counter
from itertools import combinations

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="154th Open Championship Tracker", layout="wide")

st.markdown("""
   <style>
   .main { background-color: #0B1221; color: #F1E9DB; }
   [data-testid="stHeader"] { background: rgba(0,0,0,0); }
   .stTabs [data-baseweb="tab-list"] { gap: 10px; }
   .stTabs [data-baseweb="tab"] {
       background-color: #1E293B;
       border: 1px solid #D4AF37;
       padding: 10px 20px;
       color: #D4AF37;
       font-weight: bold;
       border-radius: 4px 4px 0 0;
   }
   .stTabs [aria-selected="true"] { background-color: #D4AF37 !important; color: #0B1221 !important; }
   </style>
""", unsafe_allow_html=True)

# --- 2. HELPER FUNCTIONS ---
def parse_score_to_int(val):
    if isinstance(val, dict): val = val.get('$numberInt', 0)
    if val is None or val in ['E', 'Even', '-', '', 'null']: return 0
    try: return int(str(val).replace('+', ''))
    except: return 0

def format_score_val(val):
    if val == 0: return "E"
    return f"+{val}" if val > 0 else str(val)

def calculate_universal_score(r):
    """
    The Universal Fix:
    Sums all scores in the 'rounds' list + adds 'currentRoundScore' 
    ONLY if that round isn't already inside the 'rounds' list.
    """
    # 1. Sum of all rounds already finished and in the rounds array
    completed_total = sum(parse_score_to_int(rd.get('scoreToPar')) for rd in r.get('rounds', []))
    
    # 2. Check if the current round is already 'finalized' into the array
    curr_rd_num = parse_score_to_int(r.get('currentRound', 0))
    rds_in_list = len(r.get('rounds', []))
    
    # 3. If we are playing Round 3, but the array only has 2 rounds, add the live R3 score
    if curr_rd_num > rds_in_list:
        return completed_total + parse_score_to_int(r.get('currentRoundScore', 0))
    
    return completed_total

# --- 3. AUTHENTICATION ---
@st.cache_resource
def get_sheet():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_dict = {
            "type": st.secrets["connections"]["gsheets"]["type"],
            "project_id": st.secrets["connections"]["gsheets"]["project_id"],
            "private_key_id": st.secrets["connections"]["gsheets"]["private_key_id"],
            "private_key": st.secrets["connections"]["gsheets"]["private_key"],
            "client_email": st.secrets["connections"]["gsheets"]["client_email"],
            "client_id": st.secrets["connections"]["gsheets"]["client_id"],
            "auth_uri": st.secrets["connections"]["gsheets"]["auth_uri"],
            "token_uri": st.secrets["connections"]["gsheets"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["connections"]["gsheets"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["connections"]["gsheets"]["client_x509_cert_url"],
        }
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        return client.open("British Open Sheet").sheet1
    except Exception as e:
        st.sidebar.error(f"Google Sheet Auth Failed: {e}")
        return None

@st.cache_data(ttl=600)
def get_registry_data():
    sheet = get_sheet()
    return sheet.get_all_records() if sheet else []

# --- 4. CONFIG & API ---
API_KEY = st.secrets.get("api_key", "")
YEAR, TOURN_ID = "2026", "100"

@st.cache_data(ttl=300)
def get_live_scores():
    try:
        url = "https://live-golf-data.p.rapidapi.com/leaderboard"
        headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
        params = {"orgId": "1", "tournId": TOURN_ID, "year": YEAR}
        res = requests.get(url, headers=headers, params=params)
        return res.json().get('leaderboardRows', []), res.status_code
    except:
        return [], 500

# --- 5. DATA LOAD ---
live_rows, status_code = get_live_scores()
registry_data = get_registry_data()

# Calculate Field Averages for MC Penalty
def get_round_averages(rows):
    avgs = {1: 0, 2: 0, 3: 0, 4: 0}
    for r_num in range(1, 5):
        scores = []
        for r in rows:
            for rd in r.get('rounds', []):
                rid = parse_score_to_int(rd.get('roundId'))
                if rid == r_num:
                    scores.append(parse_score_to_int(rd.get('scoreToPar')))
        if scores: avgs[r_num] = round(sum(scores) / len(scores))
    return avgs

round_avgs = get_round_averages(live_rows)

# --- 6. MAIN APP ---
st.title("🏆 154th Open Championship Tracker")

# Fix: Changed tab_field to tab_master to match the code below
tab_lead, tab_master, tab_round, tab_intel, tab_data = st.tabs([
    "📊 Live Standings", 
    "⛳ Official Master Board", 
    "🥇 Round Winners", 
    "🧠 Field Intelligence", 
    "📂 Registry Data"
])

# TAB 1: LIVE STANDINGS
with tab_lead:
    st.header("Tournament Standings")
    if registry_data:
        user_results = []
        for entry in registry_data:
            user = str(entry.get("User", "Unknown"))
            picks = [str(entry.get("P1", "")), str(entry.get("P2", "")), str(entry.get("P3", ""))]
            if not picks[0]: continue

            u_score_int, u_disp = 0, []
            for p_name in picks:
                p_api = next((r for r in live_rows if f"{r.get('firstName')} {r.get('lastName')}".lower() == p_name.lower()), None)
                
                if p_api:
                    p_score = calculate_universal_score(p_api)
                    pos = str(p_api.get('position', ''))
                    
                    if pos in ["CUT", "WD", "DQ"]:
                        done = [parse_score_to_int(rd.get('roundId')) for rd in p_api.get('rounds', [])]
                        penalty = sum(round_avgs[r] for r in range(1, 5) if r not in done)
                        final_p_score = p_score + penalty
                        status = " (MC)"
                    else:
                        final_p_score, status = p_score, ""
                else:
                    final_p_score, status = 0, " (?)"

                u_score_int += final_p_score
                u_disp.append(f"{p_name} ({format_score_val(final_p_score)}){status}")

            user_results.append({"User": user, "P1": u_disp[0], "P2": u_disp[1], "P3": u_disp[2], "TotalInt": u_score_int})

        df_s = pd.DataFrame(user_results).sort_values("TotalInt")
        df_s.insert(0, 'Rank', range(1, 1 + len(df_s)))
        df_s['Total'] = df_s['TotalInt'].apply(format_score_val)
        st.dataframe(df_s[['Rank', 'User', 'P1', 'P2', 'P3', 'Total']], hide_index=True, use_container_width=True)

# TAB 2: OFFICIAL MASTER BOARD
with tab_master:
    st.header("Official 154th Open Leaderboard")
    if live_rows:
        master_data = []
        for r in live_rows:
            name = f"{r.get('firstName')} {r.get('lastName')}".strip()
            score = calculate_universal_score(r)
            pos = str(r.get('position', ''))
            master_data.append({
                "Pos": pos if pos else "CUT", 
                "Golfer": name, 
                "Thru": r.get('thru'), 
                "Score": format_score_val(score), 
                "Sort": score
            })

        # Correct Sorting by Integer
        master_df = pd.DataFrame(master_data).sort_values("Sort")
        
        st.subheader("⛳ Championship Leaders")
        top_5 = master_df.head(5).to_dict('records')
        cols = st.columns(5)
        for i, p in enumerate(top_5):
            cols[i].metric(label=f"{p['Pos']} | Thru: {p['Thru']}", value=p['Golfer'], delta=f"Score: {p['Score']}", delta_color="inverse")

        st.divider()
        st.dataframe(master_df[["Pos", "Golfer", "Thru", "Score"]], hide_index=True, use_container_width=True)

# TAB 3: ROUND WINNERS
with tab_round:
    st.header("Daily Performance Analysis")
    sel_rd = st.radio("Select Round", ["Round 1", "Round 2", "Round 3", "Round 4"], horizontal=True)
    target = int(sel_rd[-1])

    if live_rows:
        rd_scores = []
        for r in live_rows:
            name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip()
            for rd in r.get('rounds', []):
                if parse_score_to_int(rd.get('roundId')) == target:
                    rd_scores.append({"Golfer": name, "Daily": parse_score_to_int(rd.get('scoreToPar'))})
        
        if rd_scores:
            df_daily = pd.DataFrame(rd_scores).sort_values("Daily")
            df_daily["Daily"] = df_daily["Daily"].apply(format_score_val)
            st.dataframe(df_daily, hide_index=True, use_container_width=True)

# TAB 4: FIELD INTELLIGENCE
with tab_intel:
    st.header("Trends & Analysis")
    if registry_data:
        all_p, pairs = [], []
        for row in registry_data:
            picks = [str(row.get("P1", "")), str(row.get("P2", "")), str(row.get("P3", ""))]
            if picks[0]:
                all_p.extend(picks)
                pairs.extend(list(combinations(sorted(picks), 2)))
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Most Selected Players")
            st.dataframe(pd.DataFrame(Counter(all_p).most_common(10), columns=['Golfer', 'Selections']), hide_index=True)
        with c2:
            st.subheader("Most Popular Pairs")
            st.dataframe(pd.DataFrame([{"Pair": f"{d[0]} & {d[1]}", "Count": c} for d, c in Counter(pairs).most_common(5)]), hide_index=True)

# TAB 5: REGISTRY DATA
with tab_data:
    st.header("Search Registry")
    if registry_data:
        df_reg = pd.DataFrame(registry_data)
        df_reg.insert(0, '#', range(1, 1 + len(df_reg)))
        st.dataframe(df_reg, hide_index=True, use_container_width=True)
