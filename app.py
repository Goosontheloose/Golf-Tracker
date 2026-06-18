import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- APP CONFIG ---
st.set_page_config(page_title="The Syndicate Derby", layout="wide")

# Secure API Key call
try:
    API_KEY = st.secrets["api_key"]
except KeyError:
    st.error("Secret 'api_key' not found in Streamlit settings.")
    st.stop()

# --- CHAMPIONSHIP BRUTALISM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap');
    .stApp { background-color: #F5F5F4; }
    
    /* Podium & Layout */
    .podium-card {
        padding: 1.5rem;
        border: 4px solid #064E3B;
        background-color: white;
        box-shadow: 6px 6px 0px #064E3B;
        margin-bottom: 20px;
    }
    .podium-score {
        font-family: 'Inter', sans-serif;
        font-weight: 900;
        color: #064E3B;
        font-size: clamp(2.5rem, 8vw, 4.5rem);
        line-height: 1;
    }
    .podium-card *, .full-field-row * { color: #064E3B !important; }
    
    /* Desktop vs Mobile Columns */
    @media (max-width: 767px) {
        .stColumn { margin-bottom: 12px; }
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

def process_standings():
    rows = get_live_data()
    if not rows: return None, []
    
    # Map pros to their scores/thru
    pro_map = {}
    for p in rows:
        name = f"{p.get('firstName','')} {p.get('lastName','')}".strip().lower()
        pro_map[name] = {"score": p.get('toParValue', 0), "thru": p.get('thru', '-')}
    
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
            data = pro_map.get(pick.lower(), {"score": 0, "thru": "-"})
            s = data['score']
            u_total += s
            txt_score = "E" if s == 0 else f"{'+' if s > 0 else ''}{s}"
            u_details.append(f"{pick} {txt_score} [{data['thru']}]")
            
        results.append({"User": user, "Total": u_total, "Picks": u_details})
    
    return pd.DataFrame(results).sort_values("Total"), all_picks

# --- UI RENDERING ---
st.title("🏆 THE SYNDICATE DERBY")
df, picks = process_standings()

if df is not None:
    # 1. Top 3 Podium
    st.markdown("### 🥇 CHAMPIONSHIP FLIGHT")
    cols = st.columns(3)
    for i, (_, row) in enumerate(df.head(3).iterrows()):
        with cols[i]:
            disp = "E" if row['Total'] == 0 else f"{'+' if row['Total'] > 0 else ''}{row['Total']}"
            st.markdown(f"""
                <div class="podium-card">
                    <div style="font-weight:900;">#{i+1} {row['User']}</div>
                    <div class="podium-score">{disp}</div>
                    <div style="font-size:0.85rem; line-height:1.4;">{"<br>".join(row['Picks'])}</div>
                </div>
            """, unsafe_allow_html=True)

    # 2. Main Standings & Sentiment
    tab1, tab2 = st.tabs(["📊 MAIN LEADERBOARD", "🎯 MARKET SENTIMENT"])
    
    with tab1:
        # Beautifully formatted full list
        display_df = df[["User", "Total"]].copy()
        display_df['Total'] = display_df['Total'].apply(lambda x: f"+{x}" if x > 0 else ("E" if x == 0 else x))
        st.table(display_df)

    with tab2:
        st.markdown("### MOST PICKED PROS")
        sentiment = pd.Series(picks).value_counts().reset_index()
        sentiment.columns = ['Player', 'Selections']
        st.bar_chart(data=sentiment, x='Player', y='Selections', color="#064E3B")
else:
    st.error("API Error: No data returned. Please verify your API Key and network.")

st.caption(f"Refreshed: {datetime.now().strftime('%H:%M:%S')}")
