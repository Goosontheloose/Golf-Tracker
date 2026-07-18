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

# --- 2. AUTHENTICATION ---
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

# --- 3. CONFIG & API ---
API_KEY = st.secrets.get("api_key", "")
YEAR, TOURN_ID = "2026", "100"

@st.cache_data(ttl=600)
def get_live_scores_debug():
    """Returns (data, status_code, error_msg)"""
    try:
        url = "https://live-golf-data.p.rapidapi.com/leaderboard"
        headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
        params = {"orgId": "1", "tournId": TOURN_ID, "year": YEAR}
        res = requests.get(url, headers=headers, params=params)
        
        if res.status_code == 200:
            return res.json().get('leaderboardRows', []), 200, ""
        else:
            return [], res.status_code, res.text
    except Exception as e:
        return [], 500, str(e)

def parse_score_to_int(s):
    if isinstance(s, dict): s = s.get('$numberInt', 0)
    if s is None or s in ['E', 'Even', '-', '', 'null']: return 0
    try: return int(str(s).replace('+', ''))
    except: return 0

def format_score_val(val):
    if val == 0: return "E"
    return f"+{val}" if val > 0 else str(val)

def get_round_averages(live_rows):
    avgs = {1: 0, 2: 0, 3: 0, 4: 0}
    for r_num in range(1, 5):
        scores = []
        for r in live_rows:
            for rd_data in r.get('rounds', []):
                rd_id = rd_data.get('roundId', {})
                rd_val = int(rd_id.get('$numberInt', 0)) if isinstance(rd_id, dict) else int(rd_id)
                if rd_val == r_num:
                    s_raw = rd_data.get('scoreToPar')
                    if s_raw is not None and s_raw != "":
                        scores.append(parse_score_to_int(s_raw))
        if scores:
            avgs[r_num] = round(sum(scores) / len(scores))
    return avgs

# --- 4. DATA LOAD ---
live_rows, api_status, api_error = get_live_scores_debug()
round_avgs = get_round_averages(live_rows)

# SIDEBAR DIAGNOSTICS
with st.sidebar:
    st.header("🛠 API Diagnostic Panel")
    if api_status == 200:
        st.success(f"API Connected (Code 200)")
        st.write(f"Total Golfers Found: {len(live_rows)}")
        if len(live_rows) == 0:
            st.warning("No tournament data for ID 100 in 2026 yet.")
    elif api_status == 403:
        st.error("Error 403: Forbidden")
        st.write("You are not subscribed to the 'Slash Golf' API on RapidAPI. Go to their page and click 'Subscribe' on the Free plan.")
    else:
        st.error(f"API Error {api_status}")
        st.write(api_error)
    
    if st.button("Force Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# --- 5. MAIN APP TABS ---
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
    sheet = get_sheet()
    if sheet:
        try:
            raw_entries = sheet.get_all_records()
            if raw_entries:
                final_data = []
                for entry in raw_entries:
                    p_names = [str(entry.get("P1", "")), str(entry.get("P2", "")), str(entry.get("P3", ""))]
                    user_name = str(entry.get("User", "Unknown"))
                    if not p_names[0]: continue

                    s_ints, s_disp = [], []
                    for p_name in p_names:
                        p_api = next((r for r in live_rows if f"{r.get('firstName')} {r.get('lastName')}".lower() == p_name.lower()), None)
                        
                        if p_api:
                            pos = str(p_api.get('position', ''))
                            actual_score = sum(parse_score_to_int(rd.get('scoreToPar')) for rd in p_api.get('rounds', []))
                            
                            if pos in ["CUT", "WD", "DQ"]:
                                completed_rounds = []
                                for rd in p_api.get('rounds', []):
                                    r_id = rd.get('roundId', {})
                                    completed_rounds.append(int(r_id.get('$numberInt', 0)) if isinstance(r_id, dict) else int(r_id))
                                
                                penalty = sum(round_avgs[r] for r in range(1, 5) if r not in completed_rounds)
                                num = actual_score + penalty
                                status = " (MC)"
                            else:
                                num, status = actual_score, ""
                        else:
                            num, status = 0, " (?)"

                        s_ints.append(num)
                        s_disp.append(f"{p_name} ({format_score_val(num)}){status}")

                    final_data.append({"User": user_name, "P1": s_disp[0], "P2": s_disp[1](https://slashgolf.dev/quickstart.html "inline-citation"), "P3": s_disp[2](https://slashgolf.dev/docs.html "inline-citation"), "TotalInt": sum(s_ints)})

                if final_data:
                    df_s = pd.DataFrame(final_data).sort_values("TotalInt")
                    df_s.insert(0, 'Rank', range(1, 1 + len(df_s)))
                    df_s['Total'] = df_s['TotalInt'].apply(format_score_val)
                    st.dataframe(df_s[['Rank', 'User', 'P1', 'P2', 'P3', 'Total']], hide_index=True, use_container_width=True)
                    st.caption(f"MC Penalties Applied: R3: {format_score_val(round_avgs[3](https://en.wikipedia.org/wiki/2026_Open_Championship "inline-citation"))}, R4: {format_score_val(round_avgs[4])}")
                else:
                    st.info("No entries found in the Google Sheet.")
        except Exception as e:
            st.error(f"Standings Logic Error: {e}")

# TAB 2: OFFICIAL MASTER BOARD
with tab_field:
    st.header("Official 154th Open Leaderboard")
    if live_rows:
        master_display_list = []
        for r in live_rows:
            name = f"{r.get('firstName')} {r.get('lastName')}".strip()
            actual_total = sum(parse_score_to_int(rd.get('scoreToPar')) for rd in r.get('rounds', []))
            pos = str(r.get('position', ''))
            master_display_list.append({
                "Pos": pos if pos else "CUT",
                "Golfer": name,
                "Thru": r.get('thru'),
                "Score": format_score_val(actual_total),
                "SortVal": actual_total
            })

        st.subheader("🥇 Championship Leaders")
        top_5 = sorted(master_display_list, key=lambda x: x['SortVal'])[:5]
        cols = st.columns(5)
        for i, p in enumerate(top_5):
            cols[i].metric(label=f"{p['Pos']} | Thru: {p['Thru']}", value=p['Golfer'], delta=f"Score: {p['Score']}", delta_color="inverse")

        st.divider()
        df_master = pd.DataFrame(master_display_list)[["Pos", "Golfer", "Thru", "Score"]]
        st.dataframe(df_master, hide_index=True, use_container_width=True)
    else:
        st.warning("No leaderboard data found. Check the Diagnostic Panel in the sidebar.")

# TAB 3: ROUND WINNERS
with tab_round:
    st.header("Daily Performance Analysis")
    selected_round = st.radio("Select Round", ["Round 1", "Round 2", "Round 3", "Round 4"], horizontal=True)
    target_num = int(selected_round[-1])

    if live_rows:
        pro_round_scores = []
        for r in live_rows:
            name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip()
            for rd in r.get('rounds', []):
                rd_id_obj = rd.get('roundId', {})
                this_rd_id = int(rd_id_obj.get('$numberInt', 0)) if isinstance(rd_id_obj, dict) else int(rd_id_obj)
                if this_rd_id == target_num:
                    pro_round_scores.append({"name": name, "score": parse_score_to_int(rd.get('scoreToPar'))})
                    break

        if pro_round_scores:
            st.subheader(f"🏆 Top Professionals: {selected_round}")
            top_3_rd = sorted(pro_round_scores, key=lambda x: x['score'])[:3]
            cols = st.columns(3)
            for i, p in enumerate(top_3_rd):
                cols[i].metric(label=f"Rank {i+1}", value=p['name'], delta=f"Rd Score: {format_score_val(p['score'])}", delta_color="inverse")
            
            st.divider()
            st.subheader(f"🔥 Daily Burners: {selected_round} Standings")
            rd_lookup = {p['name'].lower(): p['score'] for p in pro_round_scores}
            raw_entries = get_sheet().get_all_records() if sheet else []
            team_perf = []
            for entry in raw_entries:
                user = str(entry.get("User", "Unknown"))
                p_names = [str(entry.get("P1", "")), str(entry.get("P2", "")), str(entry.get("P3", ""))]
                if not p_names[0]: continue
                
                rd_total, p_details = 0, []
                for p_n in p_names:
                    p_s = rd_lookup.get(p_n.lower())
                    if p_s is None:
                        p_status = next((str(r.get('position', '')) for r in live_rows if f"{r.get('firstName')} {r.get('lastName')}".lower() == p_n.lower()), "")
                        p_s = round_avgs.get(target_num, 0) if p_status in ["CUT", "WD", "DQ"] else 0
                    rd_total += p_s
                    p_details.append(f"{p_n} ({format_score_val(p_s)})")
                team_perf.append({"User": user, "P1": p_details[0], "P2": p_details[1](https://slashgolf.dev/quickstart.html "inline-citation"), "P3": p_details[2](https://slashgolf.dev/docs.html "inline-citation"), "Rd Total": rd_total})

            if team_perf:
                df_burners = pd.DataFrame(team_perf).sort_values("Rd Total")
                df_burners.insert(0, 'Rank', range(1, 1 + len(df_burners)))
                df_burners['Rd Total'] = df_burners['Rd Total'].apply(format_score_val)
                st.dataframe(df_burners, hide_index=True, use_container_width=True)

# TAB 4: FIELD INTELLIGENCE
with tab_intel:
    st.header("Trends & Analysis")
    sheet = get_sheet()
    if sheet:
        try:
            raw_entries = sheet.get_all_records()
            if raw_entries:
                all_picks, duos = [], []
                for row in raw_entries:
                    picks = [str(row.get("P1", "")), str(row.get("P2", "")), str(row.get("P3", ""))]
                    if picks[0]:
                        all_picks.extend(picks)
                        duos.extend(list(combinations(sorted(picks), 2)))
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("Most Selected Players")
                    st.dataframe(pd.DataFrame(Counter(all_picks).most_common(10), columns=['Golfer', 'Selections']), hide_index=True)
                with c2:
                    st.subheader("Most Popular Pairs")
                    st.dataframe(pd.DataFrame([{"Pair": f"{d[0]} & {d[1](https://slashgolf.dev/quickstart.html "inline-citation")}", "Count": c} for d, c in Counter(duos).most_common(5)]), hide_index=True)
        except: pass

# TAB 5: REGISTRY DATA
with tab_data:
    st.header("Search Registry")
    sheet = get_sheet()
    if sheet:
        try:
            df_reg = pd.DataFrame(sheet.get_all_records())
            df_reg.insert(0, '#', range(1, 1 + len(df_reg)))
            st.dataframe(df_reg, hide_index=True, use_container_width=True)
        except: st.info("Registry empty.")
