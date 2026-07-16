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
    /* Global table tightening */
    [data-testid="stDataFrame"] { border: 1px solid #1E293B; }
    </style>
""", unsafe_allow_html=True)

# --- 2. AUTHENTICATION ---
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

# --- 3. CONFIG ---
API_KEY = st.secrets["api_key"]
YEAR, TOURN_ID = "2026", "100"

# --- 4. DATA FETCHING ---
@st.cache_data(ttl=900)
def get_live_scores():
    try:
        url = "https://live-golf-data.p.rapidapi.com/leaderboard"
        headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
        params = {"orgId": "1", "tournId": TOURN_ID, "year": YEAR}
        res = requests.get(url, headers=headers, params=params)
        return res.json().get('leaderboardRows', [])
    except Exception as e:
        return []

# --- 5. APP TABS ---
st.title("🏆 154th Open Championship Tracker")

tab_lead, tab_field, tab_intel, tab_data = st.tabs([
    "📊 Live Standings", 
    "⛳ Official Master Board",
    "🧠 Field Intelligence", 
    "📁 Registry Data"
])

# TAB 1: LIVE STANDINGS
with tab_lead:
    st.header("Tournament Standings")
    try:
        live_rows = get_live_scores()
        score_map = {f"{r.get('firstName', '')} {r.get('lastName', '')}".strip().lower(): r.get('total', 'E') for r in live_rows}
        
        raw_entries = get_sheet().get_all_records()
        if raw_entries:
            final_data = []
            sample = raw_entries[0]
            k_user = next((k for k in sample.keys() if 'user' in str(k).lower()), "User")
            k_p1 = next((k for k in sample.keys() if 'p1' in str(k).lower()), "P1")
            k_p2 = next((k for k in sample.keys() if 'p2' in str(k).lower()), "P2")
            k_p3 = next((k for k in sample.keys() if 'p3' in str(k).lower()), "P3")

            for entry in raw_entries:
                p1_name, p2_name, p3_name = str(entry.get(k_p1, "")), str(entry.get(k_p2, "")), str(entry.get(k_p3, ""))
                if not p1_name: continue

                scores = []
                for name in [p1_name, p2_name, p3_name]:
                    s = score_map.get(name.lower(), 'E')
                    try: 
                        val = int(str(s).replace('+', '')) if s not in ['E', 'Even', '-', ''] else 0
                    except: 
                        val = 0
                    scores.append(val)

                final_data.append({
                    "User": entry.get(k_user, "Unknown"),
                    "P1": f"{p1_name} ({'E' if scores[0]==0 else (f'+{scores[0]}' if scores[0]>0 else scores[0])})",
                    "P2": f"{p2_name} ({'E' if scores[1]==0 else (f'+{scores[1]}' if scores[1]>0 else scores[1])})",
                    "P3": f"{p3_name} ({'E' if scores[2]==0 else (f'+{scores[2]}' if scores[2]>0 else scores[2])})",
                    "TotalInt": sum(scores)
                })
            
            df_standings = pd.DataFrame(final_data)
            df_standings = df_standings.sort_values("TotalInt")
            df_standings.insert(0, 'Rank', range(1, 1 + len(df_standings)))
            df_standings['Total'] = df_standings['TotalInt'].apply(lambda x: "E" if x == 0 else (f"+{x}" if x > 0 else x))
            
            st.dataframe(
                df_standings[['Rank', 'User', 'P1', 'P2', 'P3', 'Total']], 
                hide_index=True, 
                use_container_width=True,
                column_config={
                    "Rank": st.column_config.NumberColumn("Rank", width=30, help="Position"),
                    "User": st.column_config.TextColumn("User"), # Absorbs space
                    "P1": st.column_config.TextColumn("P1"), # Absorbs space
                    "P2": st.column_config.TextColumn("P2"), # Absorbs space
                    "P3": st.column_config.TextColumn("P3"), # Absorbs space
                    "Total": st.column_config.TextColumn("Total", width=40)
                }
            )
    except Exception as e:
        st.error(f"Error: {e}")

# TAB 2: OFFICIAL MASTER BOARD
with tab_field:
    st.header("Official 154th Open Leaderboard")
    live_rows = get_live_scores()
    if live_rows:
        master_data = [{"Pos": r.get('position'), "Golfer": f"{r.get('firstName')} {r.get('lastName')}", "Thru": r.get('thru'), "Score": r.get('total', 'E')} for r in live_rows]
        st.dataframe(
            pd.DataFrame(master_data), 
            hide_index=True, 
            use_container_width=True,
            column_config={
                "Pos": st.column_config.TextColumn("Pos", width=30),
                "Golfer": st.column_config.TextColumn("Golfer"), # Greedy column
                "Thru": st.column_config.TextColumn("Thru", width=50),
                "Score": st.column_config.TextColumn("Score", width=50)
            }
        )

# TAB 3: FIELD INTELLIGENCE
with tab_intel:
    st.header("Trends & Analysis")
    try:
        raw_entries = get_sheet().get_all_records()
        if raw_entries:
            sample = raw_entries[0]
            k_p1 = next((k for k in sample.keys() if 'p1' in str(k).lower()), "P1")
            k_p2 = next((k for k in sample.keys() if 'p2' in str(k).lower()), "P2")
            k_p3 = next((k for k in sample.keys() if 'p3' in str(k).lower()), "P3")

            all_picks, triplets, duos = [], [], []
            for row in raw_entries:
                p1, p2, p3 = row.get(k_p1, ""), row.get(k_p2, ""), row.get(k_p3, "")
                if not p1: continue
                
                team = sorted([str(p1), str(p2), str(p3)])
                all_picks.extend(team)
                triplets.append(tuple(team))
                duos.extend(list(combinations(team, 2)))
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("Most Selected Players")
                df_picks = pd.DataFrame(Counter(all_picks).most_common(10), columns=['Golfer', 'Selections'])
                df_picks.insert(0, '#', range(1, 1 + len(df_picks)))
                st.dataframe(df_picks, hide_index=True, use_container_width=True, column_config={"#": st.column_config.NumberColumn(width=30)})
                
            with col_b:
                st.subheader("Most Popular Pairs")
                df_duos = pd.DataFrame([{"Pair": f"{d[0]} & {d[1]}", "Count": c} for d, c in Counter(duos).most_common(5)])
                df_duos.insert(0, '#', range(1, 1 + len(df_duos)))
                st.dataframe(df_duos, hide_index=True, use_container_width=True, column_config={"#": st.column_config.NumberColumn(width=30)})

            st.subheader("Identical Teams")
            df_trips = pd.DataFrame([{"Full Roster": f"{t[0]}, {t[1]}, {t[2]}", "Count": c} for t, c in Counter(triplets).most_common(5)])
            df_trips.insert(0, '#', range(1, 1 + len(df_trips)))
            st.dataframe(df_trips, hide_index=True, use_container_width=True, column_config={"#": st.column_config.NumberColumn(width=30)})
    except:
        st.info("Gathering more data for analysis...")

# TAB 4: REGISTRY DATA
with tab_data:
    st.header("Search Registry")
    try:
        entries = get_sheet().get_all_records()
        if entries:
            df_raw = pd.DataFrame(entries)
            # Reindex starting at 1
            df_raw.insert(0, '#', range(1, 1 + len(df_raw)))
            
            search_query = st.text_input("🔍 Search by User or Player Name", "").lower()
            
            if search_query:
                mask = df_raw.astype(str).apply(lambda x: x.str.lower().str.contains(search_query)).any(axis=1)
                df_filtered = df_raw[mask]
            else:
                df_filtered = df_raw

            st.dataframe(
                df_filtered, 
                hide_index=True, 
                use_container_width=True,
                column_config={"#": st.column_config.NumberColumn(width=30)}
            )
    except:
        st.error("Could not fetch registry data.")
