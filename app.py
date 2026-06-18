import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- 1. SETTINGS & RESPONSIVE STYLE ---
st.set_page_config(page_title="The Syndicate Derby", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap');
    
    /* Global Styles */
    .stApp { background-color: #F5F5F4; }
    h1 { color: #064E3B !important; font-family: 'Inter', sans-serif; font-weight: 900; }
    
    /* Podium Card - Desktop & Mobile */
    .podium-card { 
        padding: 1.5rem; 
        border: 4px solid #064E3B; 
        background-color: white; 
        box-shadow: 8px 8px 0px #064E3B; 
        margin-bottom: 20px;
        display: flex;
        flex-direction: column;
    }
    
    /* Responsive Score Text */
    .podium-score { 
        font-family: 'Inter', sans-serif; 
        font-weight: 900; 
        color: #064E3B; 
        /* clamp(min, preferred, max) */
        font-size: clamp(2.5rem, 10vw, 4.5rem); 
        line-height: 1; 
        margin: 10px 0; 
    }
    
    .user-name { 
        font-family: 'Inter', sans-serif; 
        text-transform: uppercase; 
        font-weight: 900; 
        color: #064E3B; 
        font-size: 1.2rem; 
    }

    .player-row { 
        font-size: 0.9rem; 
        display: flex; 
        justify-content: space-between; 
        border-bottom: 1px solid #eee; 
        padding: 6px 0; 
    }

    /* MOBILE SPECIFIC OVERRIDES */
    @media (max-width: 768px) {
        /* Force columns to stack vertically */
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }
        .podium-card {
            box-shadow: 4px 4px 0px #064E3B;
            padding: 1rem;
        }
        .player-row {
            font-size: 0.8rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA INPUT (Logic from yesterday) ---
TEAMS = {
    "Martin": ["Bryson DeChambeau", "Scottie Scheffler", "Rory McIlroy"],
    "Wynand": ["Patrick Cantlay", "Xander Schauffele", "Ludvig Aberg"],
    "Rupert": ["Collin Morikawa", "Hideki Matsuyama", "Brooks Koepka"],
    "Frederik": ["Jordan Spieth", "Viktor Hovland", "Tommy Fleetwood"]
}

def parse_score(val):
    if val is None or str(val).upper() in ["E", "EVEN", "CUT"]:
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

# --- 3. MAIN APP ---
def run_app():
    st.markdown("<h1>🏆 THE SYNDICATE DERBY</h1>", unsafe_allow_html=True)
    
    rows = get_leaderboard_data()
    
    if not rows:
        st.error("Waiting for API connection...")
        return

    # Create Player Map
    player_scores = {}
    for row in rows:
        fname = row.get('firstName', '').strip()
        lname = row.get('lastName', '').strip()
        full_name = f"{fname} {lname}".lower()
        # Using toParValue/totalToPar as the primary score source
        raw_score = row.get('totalToPar') or row.get('toParValue') or 0
        player_scores[full_name] = {
            "score": parse_score(raw_score),
            "thru": row.get('thru', 'F')
        }

    # Process Team Standings
    leaderboard_results = []
    all_picks = []
    for friend, roster in TEAMS.items():
        total_score = 0
        roster_html = ""
        for p_name in roster:
            all_picks.append(p_name)
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

    # --- 4. DISPLAY PODIUM ---
    cols = st.columns(3)
    for i, (_, row) in enumerate(df.head(3).iterrows()):
        with cols[min(i, 2)]:
            disp = "E" if row['Total'] == 0 else f"{'+' if row['Total'] > 0 else ''}{row['Total']}"
            st.markdown(f"""
                <div class="podium-card">
                    <div class="user-name">#{i+1} {row['User']}</div>
                    <div class="podium-score">{disp}</div>
                    {row['HTML']}
                </div>
            """, unsafe_allow_html=True)

    # --- 5. MARKET SENTIMENT (Ownership) ---
    st.markdown("### 📊 MARKET SENTIMENT")
    ownership = pd.Series(all_picks).value_counts().reset_index()
    ownership.columns = ['Player', 'Picks']
    st.bar_chart(ownership.set_index('Player'))

    # --- 6. FULL STANDINGS TABLE ---
    st.markdown("### FULL STANDINGS")
    display_df = df[["User", "Total"]].copy()
    display_df["Total"] = display_df["Total"].apply(lambda x: f"+{x}" if x > 0 else ("E" if x == 0 else x))
    st.table(display_df.set_index("User"))

run_app()
st.caption(f"Last Sync: {datetime.now().strftime('%H:%M:%S')}")
