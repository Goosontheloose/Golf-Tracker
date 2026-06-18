import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="The Syndicate Derby", layout="wide")

# Mobile-Optimized Championship Brutalism
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap');
    .stApp { background-color: #F5F5F4; }
    
    .podium-card {
        padding: 1.2rem;
        border: 4px solid #064E3B;
        background-color: white;
        box-shadow: 8px 8px 0px #064E3B;
        margin-bottom: 20px;
    }

    .podium-score {
        font-family: 'Inter', sans-serif;
        font-weight: 900;
        color: #064E3B;
        font-size: clamp(2.5rem, 8vw, 4.5rem);
        line-height: 1;
        margin: 5px 0;
    }

    .user-name {
        font-family: 'Inter', sans-serif;
        text-transform: uppercase;
        font-weight: 900;
        color: #064E3B;
        font-size: 1.1rem;
    }

    .player-row {
        font-size: 0.85rem;
        display: flex;
        justify-content: space-between;
        border-bottom: 1px solid #eee;
        padding: 4px 0;
    }

    /* Fix for mobile stacking */
    @media (max-width: 767px) {
        .podium-card { padding: 1rem; box-shadow: 4px 4px 0px #064E3B; }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA INPUT ---
RAW_EXCEL_DATA = """
Martin	Bryson DeChambeau	Scottie Scheffler	Rory McIlroy
Wynand	Patrick Cantlay	Xander Schauffele	Ludvig Aberg
Rupert	Collin Morikawa	Hideki Matsuyama	Brooks Koepka
Frederik	Jordan Spieth	Viktor Hovland	Tommy Fleetwood
"""

# --- 3. THE GOLF ENGINE (RESTORED TO YESTERDAY'S WORKING LOGIC) ---
@st.cache_data(ttl=600)
def get_leaderboard():
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"
    params = {"orgId":"1", "tournId":"026", "year":"2024"}
    headers = {
        "X-RapidAPI-Key": st.secrets["api_key"],
        "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json().get('leaderboardRows', [])
    except:
        return []

def run_app():
    data = get_leaderboard()
    
    # Simple mapping exactly like yesterday
    scores = {}
    for row in data:
        name = f"{row.get('firstName')} {row.get('lastName')}".strip().lower()
        # Use toParValue for the math
        val = row.get('toParValue')
        scores[name] = {
            "score": int(val) if val is not None else 0,
            "thru": row.get('thru', '-')
        }

    # Process Syndicate Standings
    results = []
    for line in RAW_EXCEL_DATA.strip().split('\n'):
        parts = line.split('\t')
        user = parts[0]
        picks = parts[1:]
        
        total = 0
        details = []
        for p in picks:
            p_data = scores.get(p.lower(), {"score": 0, "thru": "-"})
            s = p_data['score']
            total += s
            s_str = "E" if s == 0 else f"{'+' if s > 0 else ''}{s}"
            details.append(f'<div class="player-row"><span>{p}</span><span><b>{s_str}</b> [{p_data["thru"]}]</span></div>')
            
        results.append({"User": user, "Total": total, "HTML": "".join(details)})

    df = pd.DataFrame(results).sort_values("Total")

    # --- 4. DISPLAY ---
    st.markdown("<h1 style='color:#064E3B; font-family:Inter; font-weight:900;'>🏆 THE SYNDICATE DERBY</h1>", unsafe_allow_html=True)

    # Top 3 Podium
    cols = st.columns(3)
    for i, (_, row) in enumerate(df.head(3).iterrows()):
        with cols[i]:
            disp = "E" if row['Total'] == 0 else f"{'+' if row['Total'] > 0 else ''}{row['Total']}"
            st.markdown(f"""
                <div class="podium-card">
                    <div class="user-name">#{i+1} {row['User']}</div>
                    <div class="podium-score">{disp}</div>
                    {row['HTML']}
                </div>
            """, unsafe_allow_html=True)

    # Full Field Table
    st.markdown("### FULL STANDINGS")
    display_df = df[["User", "Total"]].copy()
    display_df["Total"] = display_df["Total"].apply(lambda x: f"+{x}" if x > 0 else ("E" if x == 0 else x))
    st.table(display_df.set_index("User"))

run_app()
st.caption(f"Last Sync: {datetime.now().strftime('%H:%M:%S')}")
