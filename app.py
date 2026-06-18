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

def parse_score(val):
    """Robustly converts API score values to integers."""
    if val is None:
        return 0
    s_val = str(val).strip().upper()
    if s_val in ["E", "EVEN", ""]:
        return 0
    try:
        # Handles "+2", "-6", etc.
        return int(s_val.replace("+", ""))
    except ValueError:
        return 0

# --- 3. LOGIC ---
def run():
    rows = get_data()
    
    # Map API data to names
    api_map = {}
    for r in rows:
        # Create full name key
        fname = r.get('firstName', '')
        
        # Check multiple potential keys for the score relative to par
        raw_score = r.get('toParValue') 
        if raw_score is None:
            raw_score = r.get('toPar') # Often a string like "-6"
            
        api_map[name] = {
            "score": parse_score(raw_score),
            "thru": r.get('thru', 'F')
        }

    # Match Excel picks to API map
    results = []
    for line in RAW_EXCEL_DATA.strip().split('\n'):
        parts = line.split('\t')
        if not parts: continue
        user, picks = parts[0], parts[1:]
        user_total = 0
        html = ""
        
        for p in picks:
            p_clean = p.strip().lower()
            # Find the match in the api_map
            match = None
            for api_name, data in api_map.items():
                if p_clean in api_name or api_name in p_clean:
                    match = data
                    break
            
            if match:
                s = match['score']
                thru = match['thru']
            else:
                s = 0
                thru = "N/A"
            
            user_total += s
            s_str = "E" if s == 0 else-row"><span>{p}</span><span><b>{s_str}</b> [{thru}]</span></div>'
            
        results.append({"User": user, "Score": user_total, "HTML": html})

    df = pd.DataFrame(results).sort_values("Score")

    # --- 4. UI ---
    st.markdown("<h1 style='color:#064E3B; font-family:Inter; font-weight:900;'>🏆 THE SYNDICATE DERBY</h1>", unsafe_allow_html=True)
    
    # Podium (Top 3)
    cols = st.columns(3)
    for i, (_, row) in enumerate(df.head(3).iterrows()):
        with cols[i]:
            disp = "E" if row['Score'] == 0 else f"{'+' if row['Score'] > 0 else '' class="podium-score">{disp}</div>
                    {row['HTML']}
                </div>
            """, unsafe_allow_html=True)

    # Standings Table
    st.markdown("### FULL STANDINGS")
    display_df = df[["User", "Score"]].copy()
    display_df["Score"] = display_df["Score"].apply(lambda x: f"+{x}" if x > 0 else ("E" if x == 0 else x))
    st.table(display_df.set_index("User"))

run()
st.caption(f"Last Sync: {datetime.now().strftime('%H:%M:%S')}")
