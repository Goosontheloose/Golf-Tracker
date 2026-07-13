import streamlit as st
import pandas as pd
import requests
from streamlit_gsheets import GSheetsConnection
from collections import Counter
from itertools import combinations

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="154th Open Championship Tracker", layout="wide")

# Championship Branding CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Oswald:wght@700&display=swap');
    .main { background-color: #f0f2f6; color: #001A33; }
    h1, h2, h3 { font-family: 'Oswald', sans-serif; text-transform: uppercase; letter-spacing: 1px; }
    .stMetric { background-color: #ffffff; border: 2px solid #003366; border-radius: 4px; padding: 15px; }
    .card { background: white; padding: 20px; border-radius: 4px; border-left: 5px solid #C5A059; margin-bottom: 20px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    .score-under { color: #28a745; font-weight: bold; }
    .score-over { color: #dc3545; font-weight: bold; }
    .score-even { color: #6c757d; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONFIGURATION ---
API_KEY = st.secrets["api_key"]
SHEET_URL = st.secrets.get("sheet_url", "YOUR_SHEET_URL_HERE")
YEAR = "2026"
TOURN_ID = "100" # The Open Championship ID

# --- 3. HARDCODED OFFICIAL 2026 FIELD ---
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

# --- 4. DATA FETCHING ---
@st.cache_data(ttl=600)
def get_live_data():
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"
    params = {"orgId": "1", "tournId": TOURN_ID, "year": YEAR}
    headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
    try:
        res = requests.get(url, headers=headers, params=params)
        return res.json().get('leaderboardRows', [])
    except:
        return []

def format_score(val):
    if val == 0: return "E"
    return f"+{val}" if val > 0 else str(val)

# --- 5. MAIN APP INTERFACE ---
st.markdown(f"<h1>🏆 154th Open Championship Tracker</h1>", unsafe_allow_html=True)
st.markdown(f"### Royal Birkdale | {YEAR}")

# Setup Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# SIDEBAR: Entry & Connectivity
with st.sidebar:
    st.image("https://www.theopen.com/img/the-open-logo.png", width=150) # Generic placeholder
    st.header("Team Registration")
    
    with st.form("entry_form", clear_on_submit=True):
        user = st.text_input("Player / Team Name")
        sel_p1 = st.selectbox("Elite Choice 1", ELITE_30)
        sel_p2 = st.selectbox("Elite Choice 2", [p for p in ELITE_30 if p != sel_p1])
        sel_p3 = st.selectbox("Wildcard Choice", WILDCARD_FIELD)
        submit = st.form_submit_button("SUBMIT TEAM")
        
        if submit:
            if not user:
                st.error("Please enter a name.")
            else:
                try:
                    df = conn.read(spreadsheet=SHEET_URL, usecols=[0,1,2,3])
                    new_row = pd.DataFrame([{"User": user, "P1": sel_p1, "P2": sel_p2, "P3": sel_p3}])
                    updated = pd.concat([df, new_row], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, data=updated)
                    st.success("Entry recorded in Google Sheets!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Sync Error: {e}")

# DATA PROCESSING
rows = get_live_data()
player_map = {}
for r in rows:
    name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip()
    # Normalize name for matching
    player_map[name.lower()] = {
        "score": r.get('totalToPar', 0),
        "thru": r.get('thru', '-'),
        "pos": r.get('position', '-'),
        "rounds": {rd.get('roundId'): rd.get('scoreToPar', 0) for rd in r.get('rounds', [])}
    }

# LOAD LEAGUE TEAMS
try:
    teams_df = conn.read(spreadsheet=SHEET_URL, usecols=[0,1,2,3])
    teams = teams_df.to_dict('records')
except:
    teams = []

# --- 6. DISPLAY TABS ---
tab1, tab2, tab3 = st.tabs(["📊 League Leaderboard", "⛳ Full Field", "🔎 Analytics"])

with tab1:
    if not teams:
        st.info("No teams submitted yet. Use the sidebar to enter.")
    else:
        results = []
        for t in teams:
            user_total = 0
            roster_details = []
            for p_key in ['P1', 'P2', 'P3']:
                p_name = t[p_key]
                p_data = player_map.get(p_name.lower(), {"score": 0, "thru": "N/A"})
                user_total += p_data['score']
                roster_details.append(f"{p_name} ({format_score(p_data['score'])})")
            
            results.append({
                "User": t['User'],
                "Total": user_total,
                "Roster": " | ".join(roster_details)
            })
        
        leaderboard_df = pd.DataFrame(results).sort_values("Total")
        leaderboard_df.insert(0, "Rank", range(1, len(leaderboard_df) + 1))
        
        st.table(leaderboard_df)

with tab2:
    st.subheader("Official Tournament Board")
    pro_data = []
    for r in rows:
        pro_data.append({
            "Pos": r.get('position'),
            "Player": f"{r.get('firstName')} {r.get('lastName')}",
            "Score": format_score(r.get('totalToPar')),
            "Thru": r.get('thru')
        })
    st.dataframe(pd.DataFrame(pro_data), use_container_width=True, hide_index=True)

with tab3:
    col1, col2 = st.columns(2)
    
    # Ownership Stats
    with col1:
        st.subheader("Ownership Report")
        all_picks = []
        for t in teams:
            all_picks.extend([t['P1'], t['P2'], t['P3']])
        counts = Counter(all_picks)
        own_df = pd.DataFrame(counts.items(), columns=['Player', 'Picks']).sort_values('Picks', ascending=False)
        st.bar_chart(own_df.set_index('Player'))

    # Round Analysis (Dream Team)
    with col2:
        st.subheader("Round Analysis")
        rd_choice = st.radio("Select Round", [1, 2, 3, 4], horizontal=True)
        
        # Calculate best possible score for that round
        rd_scores = []
        for p, data in player_map.items():
            rd_val = data['rounds'].get(rd_choice)
            if rd_val is not None:
                rd_scores.append((p.title(), rd_val))
        
        if rd_scores:
            rd_scores.sort(key=lambda x: x[1])
            st.write(f"**Round {rd_choice} Dream Team:**")
            for i in range(min(3, len(rd_scores))):
                st.write(f"{i+1}. {rd_scores[i][0]} ({format_score(rd_scores[i][1])})")
        else:
            st.write("No round data available yet.")

st.markdown("---")
st.caption(f"Last synced with Royal Birkdale Feed: {pd.Timestamp.now().strftime('%H:%M:%S')}")
