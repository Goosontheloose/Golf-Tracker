import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- APP CONFIG ---
st.set_page_config(page_title="The Syndicate Derby", layout="wide")

# Secure API Key
try:
    API_KEY = st.secrets["api_key"]
except KeyError:
    st.error("Secret 'api_key' not found. Please add it to your Streamlit Cloud settings.")
    st.stop()

# --- STYLING (PC & MOBILE) ---
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
    }
    .podium-score {
        font-family: 'Inter', sans-serif;
        font-weight: 900;
        color: #064E3B;
        font-size: clamp(2.5rem, 8vw, 4.5rem);
        line-height: 1;
    }
    .podium-card *, .full-field-row * { color: #064E3B !important; }
    @media (max-width: 767px) { .stColumn { margin-bottom: 12px; } }
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
@st.cache_data(ttl=300) # Reduced to 5 mins
def get_live_data():
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"
    # Using 2024 for testing as it has confirmed data
    params = {"orgId":"1", "tournId":"026", "year":"2024"}
    headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
    try:
        r = requests.get(url, headers=headers, params=params)
        return r.json().get('leaderboardRows', [])
    except Exception as e:
        st.error(f"API Error: {e}")
        return []

def process_standings():
    api_rows = get_live_data()
    if not api_rows:
        return None, [], []
    
    # 1. Build a robust Pro Lookup Map
    pro_map = {}
    for p in api_rows:
        # Check all possible name fields
        fname = p.get('firstName', '')
        lname = p.get('lastName', '')
        full_name = f"{fname} {lname}".strip().lower()
        if not full_name:
            full_name = p.get('name', '').strip().lower()
        
        # Check all possible score fields
        score = p.get('toParValue')
        if score is None: score = p.get('toPar')
        if score is None: score = p.get('total', 0) # Fallback to 0 if still nothing
        
        pro_map[full_name] = {
            "score": score,
            "thru": p.get('thru', 'F')
        }
    
    # 2. Parse Syndicate Teams
    results = []
    all_picks = []
    for line in RAW_EXCEL_DATA.strip().split('\n'):
        # Robust splitting for tabs or spaces
        parts = [p.strip() for p in line.split('\t') if p.strip()]
        if not parts: continue
        
        user = parts[0]
        picks = parts[1:]
        all_picks.extend(picks)
        
        u_total = 0
        u_details = []
        for pick in picks:
            # Match names flexibly
            data = pro_map.get(pick.lower(), {"score": 0, "thru": "-"})
            s = data['score']
            u_total += s
            txt_score = "E" if s == 0 else f"{'+' if s > 0 else ''}{s}"
            u_details.append(f"{pick} {txt_score} [{data['thru']}]")
            
        results.append({"User": user, "Total": u_total, "Picks": u_details})
    
    return pd.DataFrame(results).sort_values("Total"), all_picks, api_rows

# --- UI RENDERING ---
st.title("🏆 THE SYNDICATE DERBY")

df, picks, raw_api = process_standings()

if df is not None and not df.empty:
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

    # 2. Tabs
    tab1, tab2 = st.tabs(["📊 FULL STANDINGS", "🎯 MARKET SENTIMENT"])
    
    with tab1:
        # Full field list
        for _, row in df.iterrows():
            disp = "E" if row['Total'] == 0 else f"{'+' if row['Total'] > 0 else ''}{row['Total']}"
            st.markdown(f"**{row['User']}**: {disp}")
            st.caption(", ".join(row['Picks']))
            st.divider()

    with tab2:
        st.markdown("### MOST PICKED PLAYERS")
        if picks:
            counts = pd.Series(picks).value_counts().reset_index()
            counts.columns = ['Player', 'Selections']
            st.bar_chart(data=counts, x='Player', y='Selections', color="#064E3B")

else:
    st.warning("Data is currently loading or the API key is being rate-limited. Please wait 10 seconds and refresh.")

# --- THE ENGINE ROOM (DEBUGGER) ---
with st.expander("🛠️ DEBUG: ENGINE ROOM"):
    st.write("If scores are 0, check if the names below match your Excel data exactly:")
    if raw_api:
        debug_df = pd.DataFrame(raw_api)[['firstName', 'lastName', 'toParValue', 'thru']].head(10)
        st.write(debug_df)
    else:
        st.write("No API data received.")

st.caption(f"Refreshed: {datetime.now().strftime('%H:%M:%S')}")
