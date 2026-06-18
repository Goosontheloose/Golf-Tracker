import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- APP CONFIG ---
st.set_page_config(page_title="The Syndicate Derby", layout="wide")

# Securely pull API Key exactly as you have it named
try:
    RAPID_API_KEY = st.secrets["api_key"]
except KeyError:
    st.error("Secret 'api_key' not found. Please check your Streamlit Cloud settings.")
    st.stop()

# --- MOBILE-FIRST CSS (Fixed for scaling and visibility) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap');
    .stApp { background-color: #F5F5F4; }
    
    .podium-card {
        padding: 1.5rem;
        border: 4px solid #064E3B;
        background-color: white;
        box-shadow: 6px 6px 0px #064E3B;
        margin-bottom: 20px;
        min-height: 250px;
        display: flex;
        flex-direction: column;
    }

    .podium-score {
        font-family: 'Inter', sans-serif;
        font-weight: 900;
        color: #064E3B;
        /* Responsive font: Big on PC, scales down on Mobile */
        font-size: clamp(2.5rem, 10vw, 5rem);
        line-height: 1;
        margin: 10px 0;
    }

    .podium-card *, .full-field-row * {
        color: #064E3B !important;
    }

    /* Fix for mobile stacking */
    @media (max-width: 767px) {
        .stColumn { margin-bottom: 10px; }
        .podium-card { padding: 1rem; min-height: auto; }
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
    # Using 2024 US Open Data (Tourn 026)
    querystring = {"orgId":"1","tournId":"026","year":"2024"}
    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    return response.json()

def parse_data():
    data = get_leaderboard_data()
    # Correcting the data mapping back to what worked yesterday
    if not data or 'leaderboardRows' not in data:
        return None, []
    
    pro_scores = {}
    all_picks = []
    for row in data['leaderboardRows']:
        # Match names exactly as they appear in the API
        fname = row.get('firstName', '')
        lname = row.get('lastName', '')
        full_name = f"{fname} {lname}".strip().lower()
        
        # Use toParValue for the numerical score
        pro_scores[full_name] = {
            "score": row.get('toParValue', 0),
            "thru": row.get('thru', 'F')
        }
    
    syndicate_results = []
    for line in RAW_EXCEL_DATA.strip().split('\n'):
        parts = line.split('\t')
        user_name = parts[0]
        picks = parts[1:]
        all_picks.extend(picks)
        
        total_score = 0
        details = []
        for pick in picks:
            # Check for the pro in our dictionary
            match = pro_scores.get(pick.lower(), {"score": 0, "thru": "-"})
            score_val = match['score']
            total_score += score_val
            
            # Format display string (e.g., "-4 [F]")
            sign = "+" if score_val > 0 else ""
            disp_score = "E" if score_val == 0 else f"{sign}{score_val}"
            details.append(f"{pick} {disp_score} [{match['thru']}]")
        
        syndicate_results.append({
            "User": user_name,
            "Total": total_score,
            "Picks": details
        })
    
    df = pd.DataFrame(syndicate_results).sort_values("Total")
    return df, all_picks

# --- MAIN UI ---
st.title("🏆 THE SYNDICATE DERBY")

results_df, picks_list = parse_data()

if results_df is not None:
    # Top 3 Podium
    cols = st.columns(3)
    top_3 = results_df.head(3)
    for i, (idx, row) in enumerate(top_3.iterrows()):
        with cols[i]:
            score_display = "E" if row['Total'] == 0 else f"{'+' if row['Total'] > 0 else ''}{row['Total']}"
            st.markdown(f"""
                <div class="podium-card">
                    <div style="font-weight:900; text-transform:uppercase;">#{i+1} {row['User']}</div>
                    <div class="podium-score">{score_display}</div>
                    <div style="font-size:0.9rem;">{"<br>".join(row['Picks'])}</div>
                </div>
            """, unsafe_allow_html=True)

    # Tabs for Standings and Market Sentiment
    tab1, tab2 = st.tabs(["📊 FULL STANDINGS", "🎯 MARKET SENTIMENT"])
    with tab1:
        st.dataframe(results_df[["User", "Total"]], use_container_width=True, hide_index=True)
    with tab2:
        counts = pd.Series(picks_list).value_counts()
        st.bar_chart(counts)
else:
    st.warning("No data found. Check your API key and connection.")

st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
