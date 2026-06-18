import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- APP CONFIG ---
st.set_page_config(page_title="The Syndicate Derby", layout="wide")

# Secure API Key
API_KEY = st.secrets["api_key"]

# --- RESTORED CHAMPIONSHIP BRUTALISM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap');
    .stApp { background-color: #F5F5F4; }
    
    .podium-card {
        padding: 1.5rem;
        border: 4px solid #064E3B;
        background-color: white;
        box-shadow: 8px 8px 0px #064E3B;
        margin-bottom: 25px;
    }

    .podium-score {
        font-family: 'Inter', sans-serif;
        font-weight: 900;
        color: #064E3B;
        font-size: clamp(3rem, 10vw, 5rem);
        line-height: 1;
        margin: 10px 0;
    }

    .user-name {
        font-family: 'Inter', sans-serif;
        text-transform: uppercase;
        font-size: 1.2rem;
        letter-spacing: -1px;
        color: #064E3B;
    }

    .player-row {
        font-size: 0.9rem;
        color: #444;
        border-bottom: 1px solid #eee;
        padding: 4px 0;
    }

    /* Mobile scaling */
    @media (max-width: 767px) {
        .podium-card { padding: 1rem; box-shadow: 4px 4px 0px #064E3B; }
        .podium-score { font-size: 3.5rem; }
    }
</style>
""", unsafe_allow_html=True)

# --- USER DATA ---
RAW_EXCEL_DATA = """
Martin	Bryson DeChambeau	Scottie Scheffler	Rory McIlroy
Wynand	Patrick Cantlay	Xander Schauffele	Ludvig Aberg
Rupert	Collin Morikawa	Hideki Matsuyama	Brooks Koepka
Frederik	Jordan Spieth	Viktor Hovland	Tommy Fleetwood
"""

# --- DATA ENGINE ---
@st.cache_data(ttl=600)
def get_live_data():
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"
    params = {"orgId":"1", "tournId":"026", "year":"2024"}
    headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
    try:
        r = requests.get(url, headers=headers, params=params)
        return r.json().get('leaderboardRows', [])
    except:
        return []

def run_dashboard():
    rows = get_live_data()
    
    # 1. Map scores precisely (Fixing the "Even" bug)
    score_map = {}
    for r in rows:
        fname = r.get('firstName', '')
        lname = r.get('lastName', '')
        full_name = f"{fname} {lname}".strip().lower()
        
        # Capture numeric score
        raw_val = r.get('toParValue')
        try:
            score_val = int(raw_val) if raw_val is not None else 0
        except:
            score_val = 0
            
        score_map[full_name] = {
            "val": score_val,
            "thru": r.get('thru', 'F')
        }

    # 2. Build Team Standings
    results = []
    all_picks = []
    for line in RAW_EXCEL_DATA.strip().split('\n'):
        parts = line.split('\t')
        user = parts[0]
        picks = parts[1:]
        all_picks.extend(picks)
        
        u_total = 0
        u_details = []
        for pick in picks:
            data = score_map.get(pick.lower(), {"val": 0, "thru": "-"})
            s = data['val']
            u_total += s
            txt_score = "E" if s == 0 else f"{'+' if s > 0 else ''}{s}"
            u_details.append(f"<b>{pick}</b> <span style='float:right;'>{txt_score} [{data['thru']}]</span>")
        
        results.append({"User": user, "Total": u_total, "Details": u_details})

    df = pd.DataFrame(results).sort_values("Total")

    # --- RENDER UI ---
    st.markdown("<h1 style='color:#064E3B; font-family:Inter; font-weight:900; letter-spacing:-2px;'>🏆 THE SYNDICATE DERBY</h1>", unsafe_allow_html=True)
    
    # Top 3 Bold Cards
    cols = st.columns(3)
    for i, (_, row) in enumerate(df.head(3).iterrows()):
        with cols[i]:
            disp = "E" if row['Total'] == 0 else f"{'+' if row['Total'] > 0 else ''}{row['Total']}"
            st.markdown(f"""
                <div class="podium-card">
                    <div class="user-name">#{i+1} {row['User']}</div>
                    <div class="podium-score">{disp}</div>
                    <div>{"".join([f'<div class="player-row">{p}</div>' for p in row['Details']])}</div>
                </div>
            """, unsafe_allow_html=True)

    # Tabs for the rest
    tab1, tab2 = st.tabs(["📊 STANDINGS", "🎯 MARKET SENTIMENT"])
    
    with tab1:
        # High-contrast table
        st.table(df[["User", "Total"]].set_index("User"))

    with tab2:
        sentiment = pd.Series(all_picks).value_counts().reset_index()
        sentiment.columns = ['Player', 'Picks']
        st.bar_chart(data=sentiment, x='Player', y='Picks', color="#064E3B")

run_dashboard()
st.caption(f"Refreshed: {datetime.now().strftime('%H:%M:%S')}")
