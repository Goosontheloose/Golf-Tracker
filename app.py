import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- 1. SETTINGS & VISIBILITY FIXES ---
st.set_page_config(page_title="The Syndicate Derby", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap');
    
    .stApp { background-color: #F5F5F4 !important; }
    
    h1, h2, h3, p, span, th, td, .stMarkdown { 
        color: #064E3B !important; 
        font-family: 'Inter', sans-serif;
    }

    .podium-card { 
        padding: 1.2rem; 
        border: 4px solid #064E3B; 
        background-color: white !important; 
        box-shadow: 6px 6px 0px #064E3B; 
        margin-bottom: 20px;
        display: flex;
        flex-direction: column;
    }

    .podium-score { 
        font-weight: 900; 
        color: #064E3B !important; 
        font-size: clamp(2rem, 10vw, 3rem); 
        line-height: 1; 
        margin: 5px 0; 
    }

    .user-name { 
        text-transform: uppercase; 
        font-weight: 900; 
        color: #064E3B !important; 
        font-size: 1rem; 
    }

    .player-row { 
        font-size: 0.85rem; 
        display: flex; 
        justify-content: space-between; 
        border-bottom: 1px solid #eee; 
        padding: 6px 0; 
        color: #333 !important;
    }

    [data-testid="stTable"] {
        background-color: white !important;
        border: 2px solid #064E3B !important;
    }

    /* MOBILE: Force vertical stack */
    @media (max-width: 768px) {
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA INPUT ---
TEAMS = {
    "Martin": ["Bryson DeChambeau", "Scottie Scheffler", "Rory McIlroy"],
    "Wynand": ["Patrick Cantlay", "Xander Schauffele", "Ludvig Aberg"],
    "Rupert": ["Collin Morikawa", "Hideki Matsuyama", "Brooks Koepka"],
    "Frederik": ["Jordan Spieth", "Viktor Hovland", "Tommy Fleetwood"],
    "Gustav": ["Jon Rahm", "Tyrrell Hatton", "Cameron Smith"]
}

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

# --- 3. MAIN APP ---
def run_app():
    st.markdown("<h1>🏆 THE SYNDICATE DERBY</h1>", unsafe_allow_html=True)
    
    rows = get_leaderboard_data()
    
    if rows:
        player_scores = {}
        all_pro_list = []
        all_picks = []

        # Create Player Map and Master Leaderboard Data
        for row in rows:
            fname = row.get('firstName', '').strip()
            lname = row.get('lastName', '').strip()
            full_name = f"{fname} {lname}".strip()
            raw_score = row.get('total', '0')
            
            p_score = parse_score(raw_score)
            p_thru = row.get('thru', 'F')
            
            player_scores[full_name.lower()] = {"score": p_score, "thru": p_thru}
            
            all_pro_list.append({
                "Pos": row.get('position', '-'),
                "Player": full_name,
                "Score": "E" if p_score == 0 else f"{'+' if p_score > 0 else ''}{p_score}",
                "Thru": p_thru
            })

        # Calculate Team Totals
        leaderboard_results = []
        for friend, roster in TEAMS.items():
            total_score = 0
            roster_html = ""
            for p_name in roster:
                all_picks.append(p_name)
                p_data = player_scores.get(p_name.lower().strip(), {"score": 0, "thru": "N/A"})
                p_score = p_data["score"]
                total_score += p_score
                s_str = "E" if p_score == 0 else f"{'+' if p_score > 0 else ''}{p_score}"
                roster_html += f'<div class="player-row"><span>{p_name}</span><span><b>{s_str}</b> <small>[{p_data["thru"]}]</small></span></div>'
            
            leaderboard_results.append({"User": friend, "Total": total_score, "HTML": roster_html})

        df = pd.DataFrame(leaderboard_results).sort_values(by="Total")
        df['Rank'] = range(1, len(df) + 1)

        # --- A. TOP 5 COLUMNS ---
        st.markdown("### CHAMPIONSHIP FLIGHT")
        cols = st.columns(5)
        for i, (_, row) in enumerate(df.head(5).iterrows()):
            with cols[i]:
                disp = "E" if row['Total'] == 0 else f"{'+' if row['Total'] > 0 else ''}{row['Total']}"
                st.markdown(f"""
                    <div class="podium-card">
                        <div class="user-name">#{row['Rank']} {row['User']}</div>
                        <div class="podium-score">{disp}</div>
                        {row['HTML']}
                    </div>
                """, unsafe_allow_html=True)

        # --- B. FULL STANDINGS TABLE ---
        st.markdown("### DERBY STANDINGS")
        display_df = df[["Rank", "User", "Total"]].copy()
        display_df["Total"] = display_df["Total"].apply(lambda x: f"+{x}" if x > 0 else ("E" if x == 0 else x))
        st.table(display_df.set_index("Rank"))

        # --- C. MARKET SENTIMENT ---
        st.markdown("### 📊 MARKET SENTIMENT")
        sentiment = pd.Series(all_picks).value_counts().reset_index()
        sentiment.columns = ['Player', 'Selection Count']
        st.bar_chart(sentiment.set_index('Player'))

        # --- D. REAL TOURNAMENT LEADERBOARD ---
        st.markdown("### ⛳ MASTER FIELD LEADERBOARD")
        pro_df = pd.DataFrame(all_pro_list)
        st.dataframe(pro_df.set_index("Pos"), use_container_width=True)

    else:
        st.error("Connecting to live tournament data...")

run_app()
st.caption(f"Last Sync: {datetime.now().strftime('%H:%M:%S')}")
