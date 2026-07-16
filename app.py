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
        st.sidebar.error(f"API Sync Error: {e}")
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
        
        # Build Score Map from API
        score_map = {}
        for r in live_rows:
            full_name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip().lower()
            raw_score = r.get('total', 'E')
            
            if raw_score in ['E', 'Even', '-', '', '0']:
                val = 0
            else:
                try:
                    val = int(str(raw_score).replace('+', ''))
                except:
                    val = 0
            score_map[full_name] = val
        
        # Fetch Sheet and Normalize Headers to prevent "P1" errors
        raw_entries = get_sheet().get_all_records()
        if raw_entries:
            # Re-mapping keys to lowercase to be safe
            entries = []
            for row in raw_entries:
                normalized_row = {str(k).strip().lower(): v for k, v in row.items()}
                entries.append(normalized_row)

            final_data = []
            for entry in entries:
                # Using .get with lowercase keys
                user = entry.get('user', 'Unknown')
                p1_name = str(entry.get('p1', '')).strip()
                p2_name = str(entry.get('p2', '')).strip()
                p3_name = str(entry.get('p3', '')).strip()

                s1 = score_map.get(p1_name.lower(), 0)
                s2 = score_map.get(p2_name.lower(), 0)
                s3 = score_map.get(p3_name.lower(), 0)
                
                d1 = "E" if s1 == 0 else (f"+{s1}" if s1 > 0 else s1)
                d2 = "E" if s2 == 0 else (f"+{s2}" if s2 > 0 else s2)
                d3 = "E" if s3 == 0 else (f"+{s3}" if s3 > 0 else s3)
                
                final_data.append({
                    "User": user,
                    "P1": f"{p1_name} ({d1})",
                    "P2": f"{p2_name} ({d2})",
                    "P3": f"{p3_name} ({d3})",
                    "Total Score": s1 + s2 + s3
                })
            
            df_standings = pd.DataFrame(final_data).sort_values("Total Score")
            # Number from 1
            df_standings.insert(0, 'Rank', range(1, 1 + len(df_standings)))
            
            st.subheader("Live Leaderboard")
            df_display = df_standings.copy()
            df_display['Total Score'] = df_display['Total Score'].apply(lambda x: "E" if x == 0 else (f"+{x}" if x > 0 else x))
            st.dataframe(df_display, hide_index=True, use_container_width=True)
            
            st.subheader("Participation Summary")
            entry_counts = df_standings['User'].value_counts().reset_index()
            entry_counts.columns = ['Participant', 'Total Entries']
            # Number from 1
            entry_counts.index = entry_counts.index + 1
            st.table(entry_counts)
        else:
            st.info("No entries found in the Google Sheet.")
    except Exception as e:
        st.error(f"Failed to load leaderboard: {e}")

# TAB 2: OFFICIAL MASTER BOARD
with tab_field:
    st.header("Official 154th Open Leaderboard")
    live_rows = get_live_scores()
    if live_rows:
        master_data = []
        for r in live_rows:
            s = r.get('total', 'E')
            master_data.append({
                "Pos": r.get('position'), 
                "Golfer": f"{r.get('firstName')} {r.get('lastName')}", 
                "Thru": r.get('thru'), 
                "Score": s
            })
        df_master = pd.DataFrame(master_data)
        # Number from 1
        df_master.index = df_master.index + 1
        st.dataframe(df_master, use_container_width=True)
    else:
        st.info("Official scores will appear here when play begins.")

# TAB 3: FIELD INTELLIGENCE
with tab_intel:
    st.header("Trends & Analysis")
    try:
        raw_entries = get_sheet().get_all_records()
        if raw_entries:
            all_picks, triplets, duos = [], [], []
            for row in raw_entries:
                normalized_row = {str(k).strip().lower(): v for k, v in row.items()}
                p1 = normalized_row.get('p1', '')
                p2 = normalized_row.get('p2', '')
                p3 = normalized_row.get('p3', '')
                
                team = sorted([str(p1), str(p2), str(p3)])
                all_picks.extend(team)
                triplets.append(tuple(team))
                duos.extend(list(combinations(team, 2)))
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("Most Selected Players")
                df_picks = pd.DataFrame(Counter(all_picks).most_common(10), columns=['Golfer', 'Selections'])
                df_picks.insert(0, '#', range(1, 1 + len(df_picks)))
                st.dataframe(df_picks, hide_index=True)
                
            with col_b:
                st.subheader("Most Popular Pairs")
                df_duos = pd.DataFrame([{"Pair": f"{d[0]} & {d[1]}", "Count": c} for d, c in Counter(duos).most_common(5)])
                df_duos.insert(0, '#', range(1, 1 + len(df_duos)))
                st.dataframe(df_duos, hide_index=True)

            st.subheader("Identical Teams")
            df_trips = pd.DataFrame([{"Full Roster": f"{t[0]}, {t[1]}, {t[2]}", "Count": c} for t, c in Counter(triplets).most_common(5)])
            df_trips.insert(0, '#', range(1, 1 + len(df_trips)))
            st.dataframe(df_trips, hide_index=True, use_container_width=True)
    except Exception as e:
        st.error(f"Intelligence Error: {e}")

# TAB 4: REGISTRY DATA
with tab_data:
    st.header("Google Sheets Raw Data")
    try:
        entries = get_sheet().get_all_records()
        if entries:
            df_raw = pd.DataFrame(entries)
            # Number from 1
            df_raw.index = df_raw.index + 1
            st.dataframe(df_raw, use_container_width=True)
        else:
            st.info("No records to display.")
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
