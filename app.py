import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from itertools import combinations
from collections import Counter

# --- 1. SETTINGS ---
YEAR = "2026"
TOURN_ID = "100"  # The Open / British Open
RAPID_API_KEY = "213c2f2306mshe3d8b437cc34999p108477jsn6f448fb2b30c"

st.set_page_config(page_title="154th Open Championship Tracker", layout="wide")

# --- 2. HELPER FUNCTIONS ---
def parse_score(val):
    """Converts API values (None, 'E', '+1') into integers for math."""
    if val is None or val == "" or val == "E": return 0
    try: return int(str(val).replace('+', ''))
    except: return 0

def format_score_val(val):
    """Converts integers back to display strings (0 becomes 'E')."""
    if val == 0: return "E"
    return f"+{val}" if val > 0 else str(val)

@st.cache_data(ttl=600)
def get_live_scores(y, t_id):
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"
    headers = {"X-RapidAPI-Key": RAPID_API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
    params = {"orgId": "1", "tournId": t_id, "year": y}
    try:
        resp = requests.get(url, headers=headers, params=params).json()
        return resp.get('leaderboardRows') or resp.get('leaderboard') or resp.get('players') or []
    except:
        return []

# --- 3. TEAM DATA (PASTE FULL EXCEL LIST HERE) ---
RAW_DATA = """
User	P1	P2	P3
Frederik	Rory McIlroy	Scottie Scheffler	Bryson DeChambeau
Martin	Jon Rahm	Brooks Koepka	Viktor Hovland
"""

def get_teams(raw_str):
    teams = {}
    lines = raw_str.strip().split('\n')[1:]
    for line in lines:
        parts = line.split('\t')
        if len(parts) >= 4:
            teams[parts[0]] = [parts[1].strip(), parts[2].strip(), parts[3].strip()]
    return teams

TEAMS = get_teams(RAW_DATA)

# --- 4. CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&family=JetBrains+Mono&display=swap');
    .main { background-color: #020617; color: #f8fafc; }
    h1, h2, h3 { font-family: 'Inter', sans-serif; text-transform: uppercase; letter-spacing: -1px; }
    .stTabs [data-baseweb="tab-list"] { background-color: #020617; border-bottom: 2px solid #EAB308; }
    .stTabs [data-baseweb="tab"] { color: #94a3b8; font-family: 'JetBrains Mono'; font-size: 14px; }
    .stTabs [aria-selected="true"] { color: #EAB308 !important; border-bottom: 2px solid #EAB308 !important; }
    
    .podium-card {
        background: #0f172a; border: 2px solid #EAB308; padding: 20px;
        text-align: center; border-radius: 0px; box-shadow: 6px 6px 0px #EAB308;
    }
    .score-under { color: #22C55E; font-weight: bold; }
    .score-over { color: #EF4444; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 5. DATA PROCESSING ---
rows = get_live_scores(YEAR, TOURN_ID)

# Master Map for scores and round data
player_map = {}
for r in rows:
    p_name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip().lower()
    round_scores = {f"R{rd.get('roundId')}": parse_score(rd.get('scoreToPar')) for rd in r.get('rounds', [])}
    player_map[p_name] = {
        "total": parse_score(r.get('totalToPar') or r.get('toPar') or 0),
        "rounds": round_scores,
        "thru": r.get('thru', 'F')
    }

# --- 6. APP CONTENT ---
tab1, tab2, tab3, tab4 = st.tabs(["LEADERBOARD", "ROUND ANALYSIS", "FIELD INTEL", "OFFICIAL MASTER BOARD"])

with tab1:
    st.title("🏆 154TH OPEN CHAMPIONSHIP")
    st.divider()
    
    standings = []
    for user, roster in TEAMS.items():
        u_total = 0
        u_details = []
        for p in roster:
            p_data = player_map.get(p.lower(), {"total": 0, "thru": "-"})
            u_total += p_data['total']
            u_details.append(f"{p} ({format_score_val(p_data['total'])})")
        
        standings.append({
            "User": user,
            "Total": u_total,
            "Roster": " • ".join(u_details)
        })
    
    df_standings = pd.DataFrame(standings).sort_values("Total")
    df_standings.insert(0, "Rank", range(1, len(df_standings) + 1))
    
    # Podium Display
    if len(df_standings) >= 3:
        p_cols = st.columns(3)
        for i, pos in enumerate(["1st", "2nd", "3rd"]):
            row = df_standings.iloc[i]
            with p_cols[i]:
                st.markdown(f"""
                <div class="podium-card">
                    <h3>{pos}</h3>
                    <h2>{row['User']}</h2>
                    <h1 style="color:#EAB308">{format_score_val(row['Total'])}</h1>
                </div>
                """, unsafe_allow_html=True)
    
    st.write("---")
    st.table(df_standings)

with tab2:
    st.header("ROUND ANALYSIS")
    sel_rd = st.radio("Select Round", ["R1", "R2", "R3", "R4"], horizontal=True)
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader(f"Dream Team ({sel_rd})")
        # Get top 3 pro scores for this round
        rd_pros = []
        for r in rows:
            name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip()
            score = player_map.get(name.lower(), {}).get('rounds', {}).get(sel_rd, 99)
            if score != 99: rd_pros.append((name, score))
        
        top_pros = sorted(rd_pros, key=lambda x: x[1])[:5]
        for p, s in top_pros:
            st.write(f"⛳ {p}: **{format_score_val(s)}**")

    with col_b:
        st.subheader(f"Daily Burners ({sel_rd})")
        burner_list = []
        for user, roster in TEAMS.items():
            rd_sum = sum([player_map.get(p.lower(), {}).get('rounds', {}).get(sel_rd, 0) for p in roster])
            burner_list.append({"User": user, "Score": rd_sum})
        
        df_burners = pd.DataFrame(burner_list).sort_values("Score").head(5)
        st.table(df_burners)

with tab3:
    st.header("FIELD INTELLIGENCE")
    all_picks = [p for roster in TEAMS.values() for p in roster]
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Most Selected Players")
        counts = Counter(all_picks).most_common(10)
        st.table(pd.DataFrame(counts, columns=["Player", "Count"]))
        
    with c2:
        st.subheader("The Hive Mind (Pairs)")
        pair_list = []
        for roster in TEAMS.values():
            for pair in combinations(sorted(roster), 2):
                pair_list.append(" & ".join(pair))
        
        common_pairs = Counter(pair_list).most_common(5)
        st.table(pd.DataFrame(common_pairs, columns=["Pairing", "Frequency"]))

with tab4:
    st.header("OFFICIAL MASTER BOARD")
    master_field = []
    for r in rows:
        p_name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip()
        p_data = player_map.get(p_name.lower())
        master_field.append({
            "Pos": r.get('position', '-'),
            "Player": p_name,
            "Thru": p_data['thru'],
            "Score": format_score_val(p_data['total'])
        })
    st.dataframe(pd.DataFrame(master_field), use_container_width=True, hide_index=True)

st.sidebar.write(f"Tournament Year: {YEAR}")
st.sidebar.write(f"Last API Sync: {datetime.now().strftime('%H:%M:%S')}")
