import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- 1. SETTINGS & STYLE ---
st.set_page_config(page_title="The Syndicate Derby", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap');
    .stApp { background-color: #F5F5F4; }
    .podium-card { padding: 1.2rem; border: 4px solid #064E3B; background-color: white; box-shadow: 8px 8px 0px #064E3B; margin-bottom: 20px; }
    .podium-score { font-family: 'Inter', sans-serif; font-weight: 900; color: #064E3B; font-size: clamp(2.5rem, 8vw, 4rem); line-height: 1; margin: 5px 0; }
    .user-name { font-family: 'Inter', sans-serif; text-transform: uppercase; font-weight: 900; color: #064E3B; font-size: 1.1rem; }
    .player-row { font-size: 0.85rem; display: flex; justify-content: space-between; border-bottom: 1px solid #eee; padding: 4px 0; min-height: 25px; align-items: center; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA ---
RAW_EXCEL_DATA = """
Martin	Bryson DeChambeau	Scottie Scheffler	Rory McIlroy
Wynand	Patrick Cantlay	Xander Schauffele	Ludvig Aberg
Rupert	Collin Morikawa	Hideki Matsuyama	Brooks Koepka
Frederik	Jordan Spieth	Viktor Hovland	Tommy Fleetwood
"""

@st.cache_data(ttl=600)
def get_data():
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"
    params = {"orgId":"1", "tournId":"026", "year":"2024"}
    headers = {
        "X-RapidAPI-Key": st.secrets["api_key"],
        "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"
    }
    try:
        r = requests.get(url, headers=headers, params=params)
        return r.json().get('leaderboardRows', [])
    except:
        return []

# --- 3. LOGIC ---
def run():
    rows = get_data()
    
    # Map API data to names
    api_map = {}
    for r in rows:
        name = f"{r.get('firstName','')} {r.get('lastName','')}".strip().lower()
        # FIX: The API uses 'totalToPar' for the relative score (e.g., -6)
        score_val = r.get('totalToPar') 
        
        # If 'totalToPar' is missing, fallback to 'toParValue'
        if score_val is None:
            score_val = r.get('toParValue', 0)
            
        api_map[name] = {
            "score": int(score_val),
            "thru": r.get('thru', 'F')
        }

    # Match Excel picks to API map
    results = []
    for line in RAW_EXCEL_DATA.strip().split('\n'):
        parts = line.split('\t')
        user, picks = parts[0], parts[1:]
        user_total = 0
        html = ""
        
        for p in picks:
            p_clean = p.strip().lower()
            # Fuzzy match
            match = next((v for k, v in api_map.items() if p_clean in k or k in p_clean), {"score": 0, "thru": "N/A"})
            
            s = match['score']
            user_total += s
            s_str = "E" if s == 0 else f"{'+' if s > 0 else ''}{s}"
            html += f'<div class="player-row"><span>{p}</span><span><b>{s_str}</b> [{match["thru"]}]</span></div>'
            
        results.append({"User": user, "Score": user_total, "HTML": html})

    df = pd.DataFrame(results).sort_values("Score")

    # --- 4. UI ---
    st.markdown("<h1 style='color:#064E3B; font-family:Inter; font-weight:900;'>🏆 THE SYNDICATE DERBY</h1>", unsafe_allow_html=True)
    
    cols = st.columns(3)
    for i, (_, row) in enumerate(df.head(3).iterrows()):
        with cols[i]:
            disp = "E" if row['Score'] == 0 else f"{'+' if row['Score'] > 0 else ''}{row['Score']}"
            st.markdown(f'<div class="podium-card"><div class="user-name">#{i+1} {row["User"]}</div><div class="podium-score">{disp}</div>{row["HTML"]}</div>', unsafe_allow_html=True)

    st.markdown("### FULL STANDINGS")
    st.table(df[["User", "Score"]].set_index("User"))

run()
