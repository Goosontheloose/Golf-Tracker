import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- APP CONFIG & SECRETS ---
st.set_page_config(page_title="The Syndicate Derby 2026", layout="wide")

# Securely pull API Key from Streamlit Secrets
try:
    RAPID_API_KEY = st.secrets["RAPID_API_KEY"]
except KeyError:
    st.error("API Key 'RAPID_API_KEY' not found in Secrets. Please add it to your Streamlit Cloud settings.")
    st.stop()

# --- CSS: CHAMPIONSHIP BRUTALISM (PC & MOBILE OPTIMIZED) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@700;900&display=swap');

    /* Global Overrides */
    .stApp { background-color: #F5F5F4; }
    
    /* Podium Cards */
    .podium-card {
        padding: 1.5rem;
        border: 4px solid #064E3B;
        background-color: white;
        box-shadow: 6px 6px 0px #064E3B;
        margin-bottom: 20px;
        display: flex;
        flex-direction: column;
        transition: transform 0.2s;
    }

    .podium-rank {
        font-family: 'Inter', sans-serif;
        font-weight: 900;
        text-transform: uppercase;
        color: #064E3B;
        font-size: 1.2rem;
        border-bottom: 2px solid #EAB308;
        padding-bottom: 5px;
        margin-bottom: 10px;
    }

    .podium-score {
        font-family: 'Inter', sans-serif;
        font-weight: 900;
        color: #064E3B;
        line-height: 1;
        margin: 10px 0;
    }

    .player-list {
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        color: #444;
        line-height: 1.4;
    }

    /* Mobile vs Desktop Logic */
    @media (min-width: 768px) {
        .podium-score { font-size: 5rem; }
        .podium-card { min-height: 280px; }
    }
    @media (max-width: 767px) {
        .podium-score { font-size: 3rem; }
        .podium-card { padding: 1rem; }
        .stColumn { margin-bottom: 0.5rem; }
    }

    /* Dark Mode Protection (Force high-contrast colors) */
    @media (prefers-color-scheme: dark) {
        .podium-card, .podium-card *, .full-field-row * {
            color: #064E3B !important;
        }
    }

    /* Full Field Styling */
    .full-field-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px;
        border: 2px solid #064E3B;
        background: white;
        margin-bottom: 6px;
        box-shadow: 3px 3px 0px #064E3B;
    }
</style>
""", unsafe_allow_html=True)

# --- DATA RAW INPUT ---
RAW_EXCEL_DATA = """
Martin	Bryson DeChambeau	Scottie Scheffler	Rory McIlroy
Wynand	Patrick Cantlay	Xander Schauffele	Ludvig Aberg
Rupert	Collin Morikawa	Hideki Matsuyama	Brooks Koepka
Frederik	Jordan Spieth	Viktor Hovland	Tommy Fleetwood
"""

# --- DATA ENGINE ---
@st.cache_data(ttl=600)
def get_leaderboard_data():
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"
    # Using 2024 for testing as 2026 hasn't happened yet
    querystring = {"orgId":"1","tournId":"026","year":"2024"}
    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers, params=querystring)
        return response.json()
    except:
        return None

def parse_data():
    data = get_leaderboard_data()
    if not data or 'leaderboardRows' not in data:
        return None
    
    # Create lookup for pro scores
    pro_scores = {}
    all_picks = []
    for row in data['leaderboardRows']:
        full_name = f"{row.get('firstName', '')} {row.get('lastName', '')}".strip()
        score = row.get('toParValue', 0)
        thru = row.get('thru', '-')
        pro_scores[full_name.lower()] = {"score": score, "thru": thru}
    
    # Parse Syndicate Teams
    syndicate_results = []
    for line in RAW_EXCEL_DATA.strip().split('\n'):
        parts = line.split('\t')
        user_name = parts[0]
        picks = parts[1:]
        all_picks.extend(picks)
        
        total_score = 0
        details = []
        for pick in picks:
            match = pro_scores.get(pick.lower(), {"score": 0, "thru": "-"})
            total_score += match['score']
            details.append(f"{pick} ({'+' if match['score'] > 0 else ''}{match['score']}) [{match['thru']}]")
        
        syndicate_results.append({
            "User": user_name,
            "Total": total_score,
            "Picks": details,
            "RawPicks": picks
        })
    
    df = pd.DataFrame(syndicate_results).sort_values("Total")
    return df, all_picks

# --- MAIN UI ---
st.title("🏆 THE SYNDICATE DERBY")
st.subheader("SHINNECOCK HILLS · US OPEN 2026")

results_df, picks_list = parse_data()

if results_df is not None:
    # 1. CHAMPIONSHIP FLIGHT (PODIUM)
    st.markdown("### 🥇 CHAMPIONSHIP FLIGHT")
    cols = st.columns(3)
    
    top_3 = results_df.head(3)
    for i, (idx, row) in enumerate(top_3.iterrows()):
        with cols[i]:
            score_display = "E" if row['Total'] == 0 else f"{'+' if row['Total'] > 0 else ''}{row['Total']}"
            st.markdown(f"""
                <div class="podium-card">
                    <div class="podium-rank">#{i+1} {row['User']}</div>
                    <div class="podium-score">{score_display}</div>
                    <div class="player-list">{"<br>".join(row['Picks'])}</div>
                </div>
            """, unsafe_allow_html=True)

    # 2. FULL FIELD & OWNERSHIP TABS
    tab1, tab2 = st.tabs(["📊 FULL STANDINGS", "🎯 MARKET SENTIMENT"])
    
    with tab1:
        for idx, row in results_df.iterrows():
            score_display = "E" if row['Total'] == 0 else f"{'+' if row['Total'] > 0 else ''}{row['Total']}"
            st.markdown(f"""
                <div class="full-field-row">
                    <span style="font-weight:900;">{row['User']}</span>
                    <span style="color:#064E3B; font-weight:900;">{score_display}</span>
                </div>
            """, unsafe_allow_html=True)

    with tab2:
        st.markdown("### MOST SELECTED PLAYERS")
        counts = pd.Series(picks_list).value_counts()
        st.bar_chart(counts)
        st.dataframe(counts, column_config={"count": "Selections", "value": "Pro Player"})

else:
    st.error("Waiting for live data... Please check your API key and Tournament ID.")

# --- FOOTER ---
st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')} · Data cached for 10 mins")
