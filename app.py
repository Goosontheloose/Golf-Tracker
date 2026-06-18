import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- 1. SETTINGS & BRANDING ---
st.set_page_config(page_title="The Syndicate Derby", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap');
    .stApp { background-color: #F5F5F4 !important; }
    h1, h2, h3, p, span, th, td, .stMarkdown { color: #064E3B !important; font-family: 'Inter', sans-serif; }

    /* Team Cards */
    .podium-card { 
        padding: 1.2rem; border: 4px solid #064E3B; background-color: white !important; 
        box-shadow: 6px 6px 0px #064E3B; margin-bottom: 20px; display: flex; flex-direction: column;
    }
    .podium-score { font-weight: 900; color: #064E3B !important; font-size: 2.5rem; line-height: 1; margin: 5px 0; }
    .user-name { text-transform: uppercase; font-weight: 900; color: #064E3B !important; font-size: 1rem; }
    .player-row { font-size: 0.85rem; display: flex; justify-content: space-between; border-bottom: 1px solid #eee; padding: 6px 0; color: #333 !important; }

    /* Market Sentiment Fix */
    .sentiment-box { background: white; border: 4px solid #064E3B; padding: 20px; box-shadow: 8px 8px 0px #EAB308; margin: 20px 0; }
    .s-row { margin-bottom: 15px; }
    .s-label { font-weight: 900; text-transform: uppercase; font-size: 0.8rem; display: flex; justify-content: space-between; margin-bottom: 4px; }
    .s-bar-bg { background: #eee; height: 12px; border: 1px solid #064E3B; width: 100%; }
    .s-bar-fill { background: #064E3B; height: 100%; }

    [data-testid="stTable"] { background-color: white !important; border: 2px solid #064E3B !important; }

    @media (max-width: 768px) {
        [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; min-width: 100% !important; }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA ---
TEAMS = {
    "Martin": ["Bryson DeChambeau", "Scottie Scheffler", "Rory McIlroy"],
    "Wynand": ["Patrick Cantlay", "Xander Schauffele", "Ludvig Aberg"],
    "Rupert": ["Collin Morikawa", "Hideki Matsuyama", "Brooks Koepka"],
    "Frederik": ["Jordan Spieth", "Viktor Hovland", "Tommy Fleetwood"],
    "Gustav": ["Jon Rahm", "Tyrrell Hatton", "Cameron Smith"]
}

def parse_score(val):
    if not val or str(val).upper() in ["E", "EVEN", "CUT"]: return 0
    try: return int(str(val).replace("+", ""))
    except: return 0

@st.cache_data(ttl=600)
def get_data():
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"
    params = {"orgId":"1", "tournId":"026", "year":"2024"}
    headers = {"X-RapidAPI-Key": st.secrets["api_key"], "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
    try:
        r = requests.get(url, headers=headers, params=params)
        return r.json().get('leaderboardRows', [])
    except: return []

# --- 3. EXECUTION ---
def main():
    st.markdown("<h1>🏆 THE SYNDICATE DERBY</h1>", unsafe_allow_html=True)
    rows = get_data()
    
    if rows:
        player_map = {}
        pro_field = []
        all_picks = []

        for r in rows:
            name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip()
            score = parse_score(r.get('total', '0'))
            thru = r.get('thru', 'F')
            player_map[name.lower()] = {"score": score, "thru": thru}
            pro_field.append({"Pos": r.get('position', '-'), "Player": name, "Score": "E" if score == 0 else f"{'+' if score > 0 else ''}{score}", "Thru": thru})

        results = []
        for user, roster in TEAMS.items():
            total = 0
            html = ""
            for p in roster:
                all_picks.append(p)
                p_data = player_map.get(p.lower(), {"score": 0, "thru": "N/A"})
                total += p_data["score"]
                s = "E" if p_data['score'] == 0 else f"{'+' if p_data['score'] > 0 else ''}{p_data['score']}"
                html += f'<div class="player-row"><span>{p}</span><span><b>{s}</b> <small>[{p_data["thru"]}]</small></span></div>'
            results.append({"User": user, "Total": total, "HTML": html})

        df = pd.DataFrame(results).sort_values("Total")
        df['Rank'] = range(1, len(df) + 1)

        # TOP 5
        st.markdown("### CHAMPIONSHIP FLIGHT")
        cols = st.columns(5)
        for i, (_, r) in enumerate(df.head(5).iterrows()):
            with cols[i]:
                disp = "E" if r['Total'] == 0 else f"{'+' if r['Total'] > 0 else ''}{r['Total']}"
                st.markdown(f'<div class="podium-card"><div class="user-name">#{r["Rank"]} {r["User"]}</div><div class="podium-score">{disp}</div>{r["HTML"]}</div>', unsafe_allow_html=True)

        # MARKET SENTIMENT (Strict Render Fix)
        st.markdown("### 📊 MARKET SENTIMENT")
        counts = pd.Series(all_picks).value_counts()
        m_val = counts.max()
        
        s_html = '<div class="sentiment-box">'
        for name, count in counts.items():
            w = int((count / m_val) * 100)
            s_html += f'<div class="s-row"><div class="s-label"><span>{name}</span><span>{count} PICKS</span></div><div class="s-bar-bg"><div class="s-bar-fill" style="width:{w}%;"></div></div></div>'
        s_html += '</div>'
        st.write(s_html, unsafe_allow_html=True)

        # STANDINGS
        st.markdown("### DERBY STANDINGS")
        standings_df = df[["Rank", "User", "Total"]].copy()
        standings_df["Total"] = standings_df["Total"].apply(lambda x: f"+{x}" if x > 0 else ("E" if x == 0 else x))
        st.table(standings_df.set_index("Rank"))

        # PRO FIELD
        st.markdown("### ⛳ MASTER FIELD LEADERBOARD")
        st.dataframe(pd.DataFrame(pro_field).set_index("Pos"), use_container_width=True)
    else:
        st.error("Waiting for tournament data...")

if __name__ == "__main__":
    main()
    st.caption(f"Sync: {datetime.now().strftime('%H:%M:%S')}")
