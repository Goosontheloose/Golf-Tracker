import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- APP CONFIG ---
st.set_page_config(page_title="The Syndicate Derby", layout="wide")

# Secure API Key - exactly as you requested
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
@st.cache_data(ttl=300)
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
    api_rows = get_live_data()
    if not api_rows:
        return None, [], []
    
    # 1. Build a robust Pro Lookup Map
    pro_map = {}
    for p in api_rows:
        fname = p.get('firstName', '')
        lname = p.get('lastName', '')
        full_name = f"{fname} {lname}".strip().lower()
        
        # SCORE SAFETY: Force score to be an integer
        raw_score = p.get('toParValue')
        try:
            # If it's a number, use it. If it's "E" or None, make it 0.
            clean_score = int(raw_score) if raw_score is not None else 0
        except (ValueError, TypeError):
            clean_score = 0
            
        pro_map[full_name] = {
            "score": clean_score,
            "thru": p.get('thru', 'F')
        }
    
    # 2. Parse Syndicate Teams
    results = []
    all_picks = []
    for line in RAW_EXCEL_DATA.strip().split('\n'):
        parts = [p.strip() for p in line.split('\t') if p.strip()]
        if not parts: continue
        
        user = parts[0]
        picks = parts[1:]
        all_picks.extend(picks)
        
        u_total = 0
        u_details = []
        for pick in picks:
            data = pro_map.get(pick.lower(), {"score": 0, "thru": "-"})
            s = data['score']
            
            # MATH SAFETY: Ensure u_total stays a number
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
        # Restored simple leaderboard table
        display_df = df[["User", "Total"]].copy()
        display_df["Total"] = display_df["Total"].apply(lambda x: f"+{x}" if x > 0 else ("E" if x == 0 else x))
        st.table(display_df)

    with tab2:
        st.markdown("### MOST PICKED PLAYERS")
        if picks:
            counts = pd.Series(picks).value_counts().reset_index()
            counts.columns = ['Player', 'Selections']
            st.bar_chart(data=counts, x='Player', y='Selections', color="#064E3B")

else:
    st.warning("Data is loading. If scores stay 0, check the 'Engine Room' below.")

# --- ENGINE ROOM (DEBUGGER) ---
with st.expander("🛠️ DEBUG: ENGINE ROOM"):
    if raw_api:
        st.write("First 5 Pros from API:")
        st.write(pd.DataFrame(raw_api)[['firstName', 'lastName', 'toParValue', 'thru']].head())
    else:
        st.write("No connection to API.")

st.caption(f"Refreshed: {datetime.now().strftime('%H:%M:%S')}")
