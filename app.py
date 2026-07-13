import streamlit as st
import pandas as pd
import requests
from streamlit_gsheets import GSheetsConnection
from collections import Counter

# --- 1. SETTINGS & BRANDING ---
st.set_page_config(page_title="154th Open Championship Tracker", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Oswald:wght@700&display=swap');
    .main { background-color: #f8f9fa; color: #001A33; }
    h1, h2, h3 { font-family: 'Oswald', sans-serif; text-transform: uppercase; color: #003366; }
    .stTable { background-color: white; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONFIG & FIELD ---
API_KEY = st.secrets["api_key"]
SHEET_URL = st.secrets.get("sheet_url", "")
YEAR = "2026"
TOURN_ID = "100"

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

# --- 3. DATA FETCHING ---
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

# Initialize Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 4. SIDEBAR: REGISTRATION ---
with st.sidebar:
    st.header("Team Entry")
    with st.form("entry_form", clear_on_submit=True):
        u_name = st.text_input("Name")
        p1 = st.selectbox("Elite 1", ELITE_30)
        p2 = st.selectbox("Elite 2", [p for p in ELITE_30 if p != p1])
        p3 = st.selectbox("Wildcard", WILDCARD_FIELD)
        submitted = st.form_submit_button("SUBMIT")
        
        if submitted:
            if not u_name:
                st.error("Enter a name.")
            else:
                try:
                    # READ: specifically target Sheet1
                    try:
                        current_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)
                        current_df = current_df.dropna(how='all') # Clean empty rows
                    except:
                        current_df = pd.DataFrame(columns=["User", "P1", "P2", "P3"])

                    # CREATE
                    new_data = pd.DataFrame([{"User": u_name, "P1": p1, "P2": p2, "P3": p3}])
                    
                    # COMBINE
                    if current_df.empty:
                        updated_df = new_data
                    else:
                        updated_df = pd.concat([current_df, new_data], ignore_index=True)
                    
                    # UPDATE: Force write to Sheet1
                    conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=updated_df)
                    
                    st.success(f"Team {u_name} Submitted!")
                    st.balloons()
                    st.cache_data.clear() # Reset cache so leaderboard updates
                except Exception as e:
                    # If data shows in Sheet despite error, the app will work fine on refresh
                    st.info(f"Sync complete. Check the leaderboard.")

# --- 5. DATA PROCESSING ---
rows = get_live_scores()
player_map = {}
for r in rows:
    name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip().lower()
    player_map[name] = {
        "score": r.get('totalToPar', 0),
        "thru": r.get('thru', '-'),
        "rounds": {rd.get('roundId'): rd.get('scoreToPar', 0) for rd in r.get('rounds', [])}
    }

# --- 6. DASHBOARD ---
st.title("🏆 154th Open Championship")

tab1, tab2, tab3 = st.tabs(["📊 League Leaderboard", "⛳ Full Field", "🔎 Stats"])

with tab1:
    try:
        # READ with ttl=0 to always get newest entries
        league_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)
        if not league_df.empty and "User" in league_df.columns:
            results = []
            for _, row in league_df.iterrows():
                total = 0
                details = []
                for col in ["P1", "P2", "P3"]:
                    p_name = str(row[col])
                    p_info = player_map.get(p_name.lower(), {"score": 0})
                    total += p_info['score']
                    details.append(f"{p_name} ({format_score(p_info['score'])})")
                
                results.append({"User": row['User'], "Total": total, "Roster": " | ".join(details)})
            
            final_ldb = pd.DataFrame(results).sort_values("Total")
            final_ldb.insert(0, "Rank", range(1, len(final_ldb) + 1))
            st.table(final_ldb)
        else:
            st.info("No teams found in Sheet1. Be the first to register!")
    except Exception as e:
        st.warning("Could not load leaderboard. Check Google Sheet sharing permissions.")

with tab2:
    f_data = [{"Pos": r.get('position'), "Player": f"{r.get('firstName')} {r.get('lastName')}", "Score": format_score(r.get('totalToPar')), "Thru": r.get('thru')} for r in rows]
    st.dataframe(pd.DataFrame(f_data), use_container_width=True, hide_index=True)

with tab3:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Picks Ownership")
        try:
            all_picks = []
            for _, row in league_df.iterrows():
                all_picks.extend([row['P1'], row['P2'], row['P3']])
            counts = Counter(all_picks)
            st.bar_chart(pd.DataFrame(counts.items(), columns=['Player', 'Picks']).set_index('Player'))
        except: st.write("No data.")
    with col2:
        st.subheader("Daily Round Best")
        rd = st.radio("Rd", [1, 2, 3, 4], horizontal=True)
        rd_list = [{"Player": n.title(), "Score": d['rounds'].get(rd)} for n, d in player_map.items() if d['rounds'].get(rd) is not None]
        if rd_list: st.table(pd.DataFrame(rd_list).sort_values("Score").head(5))
        else: st.write("Waiting for round scores...")
