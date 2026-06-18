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

# --- 2. DATA INPUT ---
TEAMS = {
    "Martin": ["Bryson DeChambeau", "Scottie Scheffler", "Rory McIlroy"],
    "Wynand": ["Patrick Cantlay", "Xander Schauffele", "Ludvig Aberg"],
    "Rupert": ["Collin Morikawa", "Hideki Matsuyama", "Brooks Koepka"],
    "Frederik": ["Jordan Spieth", "Viktor Hovland", "Tommy Fleetwood"]
}

# --- 3. HELPER LOGIC ---
def parse_score(val):
    if not val or str(val).upper() in ["E", "EVEN", "CUT"]:
        return 0
    try:
        return int(str(val).replace("+", ""))
    except:
        return 0

@st.cache_data(ttl=600)
def get_leaderboard_data():
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

# --- 4. MAIN APP ---
def run_app():
    st.markdown("<h1 style='color:#064E3B; font-family:Inter; font-weight:900;'>🏆 THE SYNDICATE DERBY</h1>", unsafe_allow_html=True)
    
    rows = get_leaderboard_data()
    
    if rows:
        # Create Player Map (Using 'total' key as per your working version)
        player_scores = {}
        for row in rows:
            fname = row.get('firstName', '').strip()
            lname = row.get('lastName', '').strip()
            full_name = f"{fname} {lname}".lower()
            raw_score = row.get('total', '0') 
            player_scores[full_name] = {
                "score": parse_score(raw_score),
                "thru": row.get('thru', 'F')
            }

        # Calculate Team Standings
        leaderboard_results = []
        for friend, roster in TEAMS.items():
            total_score = 0
            roster_html = ""
            for p_name in roster:
                p_data = player_scores.get(p_name.lower().strip(), {"score": 0, "thru": "N/A"})
                p_score = p_data["score"]
                total_score += p_score
                s_str = "E" if p_score == 0 else f"{'+' if p_score > 0 else ''}{p_score}"
                roster_html += f'<div class="player-row"><span>{p_name}</span><span><b>{s_str}</b> [{p_data["thru"]}]</span></div>'
            
            leaderboard_results.append({
                "User": friend,
                "Total": total_score,
                "HTML": roster_html
            })

        df = pd.DataFrame(leaderboard_results).sort_values(by="Total")

        # Display Top 3 Podium
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

        st.markdown("### FULL STANDINGS")
        display_df = df[["User", "Total"]].copy()
        display_df["Total"] = display_df["Total"].apply(lambda x: f"+{x}" if x > 0 else ("E" if x == 0 else x))
        st.table(display_df.set_index("User"))
    else:
        st.error("Could not fetch leaderboard data.")

run_app()
st.caption(f"Last Sync: {datetime.now().strftime('%H:%M:%S')}")
