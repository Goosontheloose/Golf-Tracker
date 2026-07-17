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
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1E293B;
        border: 1px solid #D4AF37;
        padding: 10px 20px;
        color: #D4AF37;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] { background-color: #D4AF37 !important; color: #0B1221 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. TOP 30 REFERENCE ---
TOP_30 = [
    "Scottie Scheffler", "Rory McIlroy", "Xander Schauffele", "Ludvig Aberg", "Wyndham Clark",
    "Viktor Hovland", "Collin Morikawa", "Patrick Cantlay", "Bryson DeChambeau", "Jon Rahm",
    "Tommy Fleetwood", "Brooks Koepka", "Matt Fitzpatrick", "Jordan Spieth", "Max Homa",
    "Hideki Matsuyama", "Sahith Theegala", "Tyrrell Hatton", "Cameron Smith", "Keegan Bradley",
    "Jason Day", "Tom Kim", "Tony Finau", "Brian Harman", "Sungjae Im", 
    "Russell Henley", "Justin Thomas", "Shane Lowry", "Min Woo Lee", "Corey Conners"
]

# --- 3. AUTHENTICATION ---
@st.cache_resource
def get_sheet():
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

# --- 4. CONFIG ---
API_KEY = st.secrets["api_key"]
YEAR, TOURN_ID = "2026", "100"

# --- 5. DATA FETCHING ---
@st.cache_data(ttl=300)
def get_live_scores():
    try:
        url = "https://live-golf-data.p.rapidapi.com/leaderboard"
        headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
        params = {"orgId": "1", "tournId": TOURN_ID, "year": YEAR}
        res = requests.get(url, headers=headers, params=params)
        return res.json().get('leaderboardRows', [])
    except Exception as e:
        return []

def parse_score_to_int(s):
    if s is None or s in ['E', 'Even', '-', '', 'null']: return 0
    try: return int(str(s).replace('+', ''))
    except: return 0

# --- 6. APP TABS ---
st.title("🏆 154th Open Championship Tracker")

tab_lead, tab_field, tab_round, tab_intel, tab_data = st.tabs([
    "📊 Live Standings", 
    "⛳ Official Master Board",
    "🏆 Round Winners",
    "🧠 Field Intelligence", 
    "📁 Registry Data"
])

# TAB 1: LIVE STANDINGS
with tab_lead:
    st.header("Tournament Standings")
    try:
        live_rows = get_live_scores()
        score_map = {}
        for r in live_rows:
            name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip().lower()
            # In your image, 'total' is the key for the tournament score
            val = r.get('total', 'E')
            score_map[name] = val
        
        raw_entries = get_sheet().get_all_records()
        if raw_entries:
            final_data = []
            for entry in raw_entries:
                p1, p2, p3 = str(entry.get("P1", "")), str(entry.get("P2", "")), str(entry.get("P3", ""))
                user_name = str(entry.get("User", "Unknown"))
                if not p1: continue
                
                s_ints, s_disp = [], []
                for p_name in [p1, p2, p3]:
                    api_val = score_map.get(p_name.lower(), 'E')
                    num = parse_score_to_int(api_val)
                    s_ints.append(num)
                    fmt = "E" if num == 0 else (f"+{num}" if num > 0 else num)
                    s_disp.append(f"{p_name} ({fmt})")

                final_data.append({"User": user_name, "P1": s_disp[0], "P2": s_disp[1], "P3": s_disp[2], "TotalInt": sum(s_ints)})
            
            df_s = pd.DataFrame(final_data).sort_values("TotalInt")
            df_s.insert(0, 'Rank', range(1, 1 + len(df_s)))
            df_s['Total'] = df_s['TotalInt'].apply(lambda x: "E" if x == 0 else (f"+{x}" if x > 0 else x))
            st.dataframe(df_s[['Rank', 'User', 'P1', 'P2', 'P3', 'Total']], hide_index=True, use_container_width=True)
    except Exception as e:
        st.error(f"Error calculating standings: {e}")

# TAB 2: OFFICIAL MASTER BOARD
with tab_field:
    st.header("Official 154th Open Leaderboard")
    live_rows = get_live_scores()
    if live_rows:
        st.subheader("🥇 Championship Leaders")
        pro_list = []
        for r in live_rows:
            name = f"{r.get('firstName')} {r.get('lastName')}".strip()
            s = r.get('total', 'E')
            pro_list.append({"name": name, "score": parse_score_to_int(s), "thru": r.get('thru'), "pos": r.get('position')})
        
        top_5 = sorted(pro_list, key=lambda x: x['score'])[:5]
        cols = st.columns(5)
        for i, p in enumerate(top_5):
            score_fmt = "E" if p['score'] == 0 else (f"+{p['score']}" if p['score'] > 0 else p['score'])
            cols[i].metric(label=f"{p['pos']} | Thru: {p['thru']}", value=p['name'], delta=f"Score: {score_fmt}", delta_color="inverse")

        st.divider()
        master_df = pd.DataFrame([{"Pos": r.get('position'), "Golfer": f"{r.get('firstName')} {r.get('lastName')}", "Thru": r.get('thru'), "Score": r.get('total', 'E')} for r in live_rows])
        st.dataframe(master_df, hide_index=True, use_container_width=True)

# TAB 3: ROUND WINNERS
with tab_round:
    st.header("Daily Performance Analysis")
    live_rows = get_live_scores()
    selected_round = st.radio("Select Round", ["Round 1", "Round 2", "Round 3", "Round 4"], horizontal=True)
    target_num = int(selected_round[-1])
    
    if live_rows:
        pro_round_scores = []
        for r in live_rows:
            name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip()
            s_val = None
            
            # EXTRACT CURRENT ROUND FROM OBJECT: {"$numberInt": "2"}
            current_rd_obj = r.get('currentRound', {})
            player_current_rd = int(current_rd_obj.get('$numberInt', 0)) if isinstance(current_rd_obj, dict) else 0
            
            # 1. If selected round is the player's active round
            if player_current_rd == target_num:
                s_val = r.get('currentRoundScore')
            
            # 2. If it's a completed round, check the 'rounds' list
            if s_val is None:
                for rd in r.get('rounds', []):
                    # roundId is also an object: {"$numberInt": "1"}
                    rd_id_obj = rd.get('roundId', {})
                    this_rd_id = int(rd_id_obj.get('$numberInt', 0)) if isinstance(rd_id_obj, dict) else 0
                    
                    if this_rd_id == target_num:
                        s_val = rd.get('scoreToPar')
                        break

            if s_val is not None and str(s_val).lower() != 'none':
                pro_round_scores.append({"name": name, "score": parse_score_to_int(s_val)})
        
        if pro_round_scores:
            st.subheader(f"🏆 Top 3 Professionals: {selected_round}")
            top_3_rd = sorted(pro_round_scores, key=lambda x: x['score'])[:3]
            cols = st.columns(3)
            for i, p in enumerate(top_3_rd):
                score_fmt = "E" if p['score'] == 0 else (f"+{p['score']}" if p['score'] > 0 else p['score'])
                cols[i].metric(label=f"Rank {i+1}", value=p['name'], delta=f"Rd Score: {score_fmt}", delta_color="inverse")
            
            st.divider()
            st.subheader(f"🔥 Daily Burners: Top Teams for {selected_round}")
            raw_entries = get_sheet().get_all_records()
            rd_map = {p['name'].lower(): p['score'] for p in pro_round_scores}
            team_perf = []
            for entry in raw_entries:
                p1, p2, p3 = str(entry.get("P1", "")).strip(), str(entry.get("P2", "")).strip(), str(entry.get("P3", "")).strip()
                user = str(entry.get("User", "Unknown"))
                if not p1: continue
                t_score = sum([rd_map.get(p_name.lower(), 0) for p_name in [p1, p2, p3]])
                team_perf.append({"User": user, "Roster": f"{p1}, {p2}, {p3}", "Rd Score": t_score})
            
            df_burners = pd.DataFrame(team_perf).sort_values("Rd Score")
            df_burners.insert(0, '#', range(1, 1 + len(df_burners)))
            df_burners['Rd Score'] = df_burners['Rd Score'].apply(lambda x: "E" if x == 0 else (f"+{x}" if x > 0 else x))
            st.dataframe(df_burners.head(10), hide_index=True, use_container_width=True)
        else:
            st.warning(f"No score data found for {selected_round}.")

# TAB 4: FIELD INTELLIGENCE
with tab_intel:
    st.header("Trends & Analysis")
    live_rows = get_live_scores()
    if live_rows:
        try:
            pro_scores = []
            for r in live_rows:
                name = f"{r.get('firstName')} {r.get('lastName')}".strip()
                s = r.get('total', 'E')
                pro_scores.append({"name": name, "score": parse_score_to_int(s), "is_elite": name in TOP_30})
            df_pro = pd.DataFrame(pro_scores).sort_values("score")
            wildcards = df_pro[df_pro['is_elite'] == False]
            if not wildcards.empty:
                best_wildcard = wildcards.iloc[0]
                others = df_pro[df_pro['name'] != best_wildcard['name']].iloc[:2]
                perfect_team = [best_wildcard] + others.to_dict('records')
                perfect_score = sum([p['score'] for p in perfect_team])
                perfect_score_fmt = "E" if perfect_score == 0 else (f"+{perfect_score}" if perfect_score > 0 else perfect_score)
                st.subheader("💎 The Perfect Roster")
                p_cols = st.columns(3)
                for i, p in enumerate(perfect_team):
                    tag = " (Wildcard)" if not p['is_elite'] else " (Elite)"
                    score_tag = "E" if p['score'] == 0 else (f"+{p['score']}" if p['score'] > 0 else p['score'])
                    p_cols[i].metric(label=f"Player {i+1}{tag}", value=p['name'], delta=f"Score: {score_tag}", delta_color="inverse")
        except: pass

    try:
        raw_entries = get_sheet().get_all_records()
        if raw_entries:
            all_picks, duos = [], []
            for row in raw_entries:
                p1, p2, p3 = row.get("P1", ""), row.get("P2", ""), row.get("P3", "")
                if not p1: continue
                team = sorted([str(p1), str(p2), str(p3)])
                all_picks.extend(team)
                duos.extend(list(combinations(team, 2)))
            st.divider()
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("Most Selected Players")
                st.dataframe(pd.DataFrame(Counter(all_picks).most_common(10), columns=['Golfer', 'Selections']), hide_index=True)
            with col_b:
                st.subheader("Most Popular Pairs")
                st.dataframe(pd.DataFrame([{"Pair": f"{d[0]} & {d[1]}", "Count": c} for d, c in Counter(duos).most_common(5)]), hide_index=True)
    except: pass

# TAB 5: REGISTRY DATA
with tab_data:
    st.header("Search Registry")
    try:
        entries = get_sheet().get_all_records()
        if entries:
            df_raw = pd.DataFrame(entries)
            df_raw.insert(0, '#', range(1, 1 + len(df_raw)))
            search_query = st.text_input("🔍 Search User/Player", "").lower()
            if search_query:
                mask = df_raw.astype(str).apply(lambda x: x.str.lower().str.contains(search_query)).any(axis=1)
                st.dataframe(df_raw[mask], hide_index=True, use_container_width=True)
            else:
                st.dataframe(df_raw, hide_index=True, use_container_width=True)
    except:
        st.error("Registry unavailable.")
