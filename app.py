import streamlit as st
import pandas as pd
import requests
from streamlit_gsheets import GSheetsConnection
from collections import Counter

# --- 1. SETTINGS & PROFESSIONAL BRANDING ---
st.set_page_config(page_title="154th Open Championship Tracker", layout="wide")

# Theme: "Links Performance" (Midnight Atlantic & Championship Gold)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Oswald:wght@700&display=swap');
    
    .main { background-color: #f8f9fa; color: #001A33; }
    h1, h2, h3 { font-family: 'Oswald', sans-serif; text-transform: uppercase; color: #003366; letter-spacing: 0.5px; }
    
    /* Metrics & Cards Styling */
    [data-testid="stMetricValue"] { font-family: 'Oswald', sans-serif; color: #C5A059; }
    .stTable { background-color: white; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    
    /* Custom Sidebar */
    .css-1d391kg { background-color: #001A33; }
    .sidebar-text { color: white !important; }
    
    /* Score colors */
    .under-par { color: #28a745; font-weight: bold; }
    .over-par { color: #dc3545; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONFIGURATION ---
API_KEY = st.secrets["api_key"]
SHEET_URL = st.secrets.get("sheet_url", "")
YEAR = "2026"
TOURN_ID = "100" # Open Championship

# --- 3. THE OFFICIAL 2026 FIELD (156 PLAYERS) ---
OFFICIAL_FIELD = [
    "Scottie Scheffler", "Rory McIlroy", "Matt Fitzpatrick", "Cameron Young", "Russell Henley",
    "Chris Gotterup", "Collin Morikawa", "Wyndham Clark", "Tommy Fleetwood", "Justin Rose",
    "Jon Rahm", "Viktor Hovland", "J.J. Spaun", "Xander Schauffele", "Robert MacIntyre",
    "Ben Griffin", "Aaron Rai", "Sam Burns", "Justin Thomas", "Ludvig Aberg",
    "Si Woo Kim", "Tyrrell Hatton", "Sepp Straka", "Min Woo Lee", "Alex Noren",
    "Patrick Reed", "Kristoffer Reitan", "Ryan Gerard", "Akshay Bhatia", "Jacob Bridgeman",
    "Hideki Matsuyama", "Harris English", "Tom Kim", "JT Poston", "Nicolai Hojgaard",
    "Kurt Kitayama", "Bryson DeChambeau", "Patrick Cantlay", "Maverick McNealy", "Bud Cauley",
    "Keegan Bradley", "Rickie Fowler", "Gary Woodland", "Alex Smalley", "Jake Knapp",
    "Shane Lowry", "Sam Stevens", "Joaquin Niemann", "Daniel Berger", "Marco Penge",
    "Jordan Spieth", "Nicolas Echavarria", "Corey Conners", "Jason Day", "Michael Kim",
    "Ryan Fox", "Adam Scott", "Eugenio Chacarra", "Michael Brennan", "Pierceson Coody",
    "Ryo Hisatsune", "Matt McCarty", "Brian Harman", "Alex Fitzpatrick", "David Puig",
    "Nick Taylor", "Keith Mitchell", "Andrew Novak", "Michael Thorbjornsen", "Eric Cole",
    "Matt Wallace", "Sami Valimaki", "Max Homa", "Harry Hall", "Max Greyserman",
    "Jordan Smith", "Thomas Detry", "Sahith Theegala", "Casey Jarvis", "Jayden Schaper",
    "Sungjae Im", "Rasmus Hojgaard", "Keita Nakajima", "Rasmus Neergaard-Petersen", "Shaun Norris",
    "John Parry", "Lucas Herbert", "Daniel Hillier", "Haotong Li", "Kota Kaneko",
    "Angel Ayora", "Jackson Suber", "Brooks Koepka", "Hennie du Plessis", "Andy Sullivan",
    "Adrien Saddier", "Jose Luis Ballester", "Tom McKibbin", "Daniel Brown", "Cameron Smith",
    "Laurie Canter", "Travis Smyth", "Michael Hollick", "Scott Vincent", "Dan Bradbury",
    "Bernd Wiesberger", "Joakim Lagergren", "Victor Perez", "Jesper Svensson", "Billy Horschel",
    "Martin Couvra", "Kazuki Higa", "Peter Uihlein", "Alistair Docherty", "Kazuma Kobori",
    "Antoine Rozner", "Francesco Laporta", "MJ Daffue", "Francesco Molinari", "Ren Yonezawa",
    "Frederic Lacroix", "Cameron John", "James Nicholas", "Caleb Surratt", "Matthew Jordan",
    "Naoyuki Kataoka", "Sam Bairstow", "Austen Truslow", "Jeongwoo Ham", "Louis Oosthuizen",
    "Matthew Southgate", "Ryutaro Nagano", "Jiho Yang", "Padraig Harrington", "Jack Buchanan",
    "Marcus Plunkett", "Matthew Baldwin", "Tiger Christensen", "Henrik Stenson", "Stewart Cink",
    "Stuart Grehan", "Darren Clarke", "Alejandro De Castro Piera", "Baard Bjoernevik Skogen", "David Duval",
    "David Howard", "Fifa Laopakdee", "Jack McDonald", "Johnny Keefer", "Lev Grinberg",
    "Mason Howell", "Mateo Pulcini", "Nevill Ruiter", "Tim Wiedemeyer", "Tom Sloman"
]

ELITE_30 = OFFICIAL_FIELD[:30]
WILDCARD_FIELD = OFFICIAL_FIELD[30:]

# --- 4. DATA FUNCTIONS ---
@st.cache_data(ttl=900)
def get_live_scores():
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"
    params = {"orgId": "1", "tournId": TOURN_ID, "year": YEAR}
    headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
    try:
        r = requests.get(url, headers=headers, params=params)
        return r.json().get('leaderboardRows', [])
    except:
        return []

def format_score(val):
    try:
        v = int(val)
        if v == 0: return "E"
        return f"+{v}" if v > 0 else str(v)
    except:
        return "E"

# --- 5. INITIALIZE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 6. SIDEBAR: ENTRY FORM ---
with st.sidebar:
    st.title("Registration")
    st.markdown("Select 2 Elite (Top 30) and 1 Wildcard.")
    
    with st.form("entry_form", clear_on_submit=True):
        u_name = st.text_input("Your Name / Team")
        p1 = st.selectbox("Elite Pick 1", ELITE_30)
        p2 = st.selectbox("Elite Pick 2", [p for p in ELITE_30 if p != p1])
        p3 = st.selectbox("Wildcard Pick", WILDCARD_FIELD)
        submitted = st.form_submit_button("LOCK IN TEAM")
        
        if submitted:
            if not u_name:
                st.error("Please enter a name.")
            else:
                try:
                    # Fetch current data safely
                    try:
                        existing_data = conn.read(spreadsheet=SHEET_URL)
                        existing_data = existing_data[["User", "P1", "P2", "P3"]]
                    except:
                        existing_data = pd.DataFrame(columns=["User", "P1", "P2", "P3"])

                    new_entry = pd.DataFrame([{"User": u_name, "P1": p1, "P2": p2, "P3": p3}])
                    updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
                    
                    conn.update(spreadsheet=SHEET_URL, data=updated_df)
                    st.success(f"Confirmed: {u_name} is in!")
                    st.balloons()
                    st.cache_data.clear() # Force refresh for the leaderboard
                except Exception as e:
                    st.error(f"Sync Error: {e}")

# --- 7. DATA PROCESSING ---
rows = get_live_scores()
player_map = {}
for r in rows:
    full_name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip().lower()
    player_map[full_name] = {
        "score": r.get('totalToPar', 0),
        "thru": r.get('thru', '-'),
        "pos": r.get('position', '-'),
        "rounds": {rd.get('roundId'): rd.get('scoreToPar', 0) for rd in r.get('rounds', [])}
    }

# --- 8. MAIN DASHBOARD ---
st.title("🏆 154th Open Championship")
st.subheader("Royal Birkdale | Official Tournament Tracker")

tab1, tab2, tab3 = st.tabs(["📊 League Table", "⛳ The Field", "🔎 Statistics"])

with tab1:
    try:
        teams_df = conn.read(spreadsheet=SHEET_URL)
        if not teams_df.empty:
            league_results = []
            for _, row in teams_df.iterrows():
                u = row['User']
                total_score = 0
                picks_status = []
                
                for col in ['P1', 'P2', 'P3']:
                    p_name = row[col]
                    p_info = player_map.get(p_name.lower(), {"score": 0, "thru": "-"})
                    score_val = p_info['score']
                    total_score += score_val
                    picks_status.append(f"{p_name} ({format_score(score_val)})")
                
                league_results.append({
                    "Team": u,
                    "Total": total_score,
                    "Roster Details": " | ".join(picks_status)
                })
            
            final_ldb = pd.DataFrame(league_results).sort_values("Total")
            final_ldb.insert(0, "Rank", range(1, len(final_ldb) + 1))
            st.table(final_ldb)
        else:
            st.info("Waiting for first entry...")
    except:
        st.warning("Connect your Google Sheet to see the league table.")

with tab2:
    st.subheader("Official Leaderboard")
    field_list = []
    for r in rows:
        field_list.append({
            "Pos": r.get('position', '-'),
            "Player": f"{r.get('firstName')} {r.get('lastName')}",
            "Score": format_score(r.get('totalToPar')),
            "Thru": r.get('thru', '-')
        })
    st.dataframe(pd.DataFrame(field_list), use_container_width=True, hide_index=True)

with tab3:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Ownership")
        try:
            all_picks = []
            for _, row in teams_df.iterrows():
                all_picks.extend([row['P1'], row['P2'], row['P3']])
            counts = Counter(all_picks)
            own_df = pd.DataFrame(counts.items(), columns=['Player', 'Picks']).sort_values('Picks', ascending=False)
            st.bar_chart(own_df.set_index('Player'))
        except:
            st.write("No data available.")

    with col2:
        st.subheader("Daily Round Best")
        rd = st.radio("Round", [1, 2, 3, 4], horizontal=True)
        rd_data = []
        for name, data in player_map.items():
            s = data['rounds'].get(rd)
            if s is not None:
                rd_data.append({"Player": name.title(), "RoundScore": s})
        
        if rd_data:
            rd_df = pd.DataFrame(rd_data).sort_values("RoundScore").head(5)
            st.write(f"Top 5 Players in Round {rd}:")
            st.table(rd_df)
        else:
            st.write("Round data not yet live.")

st.divider()
st.caption(f"Syncing Live with Birkdale Feed... Last update: {pd.Timestamp.now().strftime('%H:%M:%S')}")
