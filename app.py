import streamlit as st
import pandas as pd
import requests
import gspread
from google.oauth2.service_account import Credentials
from collections import Counter
from itertools import combinations

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="154th Open Championship Tracker", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0B1221; color: #F1E9DB; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1E293B;
        border: 1px solid #D4AF37;
        padding: 10px 20px;
        color: #D4AF37;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] { background-color: #D4AF37 !important; color: #0B1221 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. AUTHENTICATION ---
@st.cache_resource
def get_sheet():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = {
        "type": st.secrets["connections"]["gsheets"]["type"],
        "project_id": st.secrets["connections"]["gsheets"]["project_id"],
        "private_key_id": st.secrets["connections"]["gsheets"]["private_key_id"],
        "private_key": st.secrets["connections"]["gsheets"]["private_key"],
        "client_email": st.secrets["connections"]["gsheets"]["client_email"],
        "client_id": st.secrets["connections"]["gsheets"]["client_id"],
        "auth_uri": st.secrets["connections"]["gsheets"]["auth_uri"],
        "token_uri": st.secrets["connections"]["gsheets"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["connections"]["gsheets"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["connections"]["gsheets"]["client_x509_cert_url"],
    }
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client.open("British Open Sheet").sheet1 

# --- 3. CONFIG & FIELD ---
API_KEY = st.secrets["api_key"]
YEAR, TOURN_ID = "2026", "100"

OFFICIAL_FIELD = ["Scottie Scheffler", "Rory McIlroy", "Matt Fitzpatrick", "Cameron Young", "Russell Henley", "Chris Gotterup", "Collin Morikawa", "Wyndham Clark", "Tommy Fleetwood", "Justin Rose", "Jon Rahm", "Viktor Hovland", "J.J. Spaun", "Xander Schauffele", "Robert MacIntyre", "Ben Griffin", "Aaron Rai", "Sam Burns", "Justin Thomas", "Ludvig Aberg", "Si Woo Kim", "Tyrrell Hatton", "Sepp Straka", "Min Woo Lee", "Alex Noren", "Patrick Reed", "Kristoffer Reitan", "Ryan Gerard", "Akshay Bhatia", "Jacob Bridgeman", "Hideki Matsuyama", "Harris English", "Tom Kim", "JT Poston", "Nicolai Hojgaard", "Kurt Kitayama", "Bryson DeChambeau", "Patrick Cantlay", "Maverick McNealy", "Bud Cauley", "Keegan Bradley", "Rickie Fowler", "Gary Woodland", "Alex Smalley", "Jake Knapp", "Shane Lowry", "Sam Stevens", "Joaquin Niemann", "Daniel Berger", "Marco Penge", "Jordan Spieth", "Nicolas Echavarria", "Corey Conners", "Jason Day", "Michael Kim", "Ryan Fox", "Adam Scott", "Eugenio Chacarra", "Michael Brennan", "Pierceson Coody", "Ryo Hisatsune", "Matt McCarty", "Brian Harman", "Alex Fitzpatrick", "David Puig", "Nick Taylor", "Keith Mitchell", "Andrew Novak", "Michael Thorbjornsen", "Eric Cole", "Matt Wallace", "Sami Valimaki", "Max Homa", "Harry Hall", "Max Greyserman", "Jordan Smith", "Thomas Detry", "Sahith Theegala", "Casey Jarvis", "Jayden Schaper", "Sungjae Im", "Rasmus Hojgaard", "Keita Nakajima", "Rasmus Neergaard-Petersen", "Shaun Norris", "John Parry", "Lucas Herbert", "Daniel Hillier", "Haotong Li", "Kota Kaneko", "Angel Ayora", "Jackson Suber", "Brooks Koepka", "Hennie du Plessis", "Andy Sullivan", "Adrien Saddier", "Jose Luis Ballester", "Tom McKibbin", "Daniel Brown", "Cameron Smith", "Laurie Canter", "Travis Smyth", "Michael Hollick", "Scott Vincent", "Dan Bradbury", "Bernd Wiesberger", "Joakim Lagergren", "Victor Perez", "Jesper Svensson", "Billy Horschel", "Martin Couvra", "Kazuki Higa", "Peter Uihlein", "Alistair Docherty", "Kazuma Kobori", "Antoine Rozner", "Francesco Laporta", "MJ Daffue", "Francesco Molinari", "Ren Yonezawa", "Frederic Lacroix", "Cameron John", "James Nicholas", "Caleb Surratt", "Matthew Jordan", "Naoyuki Kataoka", "Sam Bairstow", "Austen Truslow", "Jeongwoo Ham", "Louis Oosthuizen", "Matthew Southgate", "Ryutaro Nagano", "Jiho Yang", "Padraig Harrington", "Jack Buchanan", "Marcus Plunkett", "Matthew Baldwin", "Tiger Christensen", "Henrik Stenson", "Stewart Cink", "Stuart Grehan", "Darren Clarke", "Alejandro De Castro Piera", "Baard Bjoernevik Skogen", "David Duval", "David Howard", "Fifa Laopakdee", "Jack McDonald", "Johnny Keefer", "Lev Grinberg", "Mason Howell", "Mateo Pulcini", "Nevill Ruiter", "Tim Wiedemeyer", "Tom Sloman"]
ELITE_30, WILDCARD = OFFICIAL_FIELD[:30], OFFICIAL_FIELD[30:]

# --- 4. DATA FETCHING ---
@st.cache_data(ttl=900)
def get_scores():
    try:
        url = "https://live-golf-data.p.rapidapi.com/leaderboard"
        headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
        res = requests.get(url, headers=headers, params={"orgId": "1", "tournId": TOURN_ID, "year": YEAR})
        return res.json().get('leaderboardRows', [])
    except:
        return []

# --- 5. MAIN UI ---
st.title("🏆 154th Open Championship")

tab1, tab2, tab3, tab4 = st.tabs(["✍️ Register Team", "📊 Leaderboard", "🧠 Field Intelligence", "⛳ Live Field"])

# TAB 1: REGISTRATION
with tab1:
    st.header("Register Your Team")
    with st.form("main_entry_form", clear_on_submit=True):
        u_name = st.text_input("Your Full Name")
        col1, col2, col3 = st.columns(3)
        with col1: p1 = st.selectbox("Elite Choice 1", ELITE_30)
        with col2: p2 = st.selectbox("Elite Choice 2", [p for p in ELITE_30 if p != p1])
        with col3: p3 = st.selectbox("Wildcard Choice", WILDCARD)
        
        if st.form_submit_button("LOCK IN TEAM"):
            if u_name:
                try:
                    get_sheet().append_row([u_name, p1, p2, p3])
                    st.success(f"Successfully Registered: {u_name}")
                    st.balloons()
                except Exception as e: st.error(f"Error: {e}")
            else:
                st.warning("Please enter your name.")

# TAB 2: LEADERBOARD (LIVE SCORES)
with tab2:
    try:
        rows = get_scores()
        # Map player names to their live scores
        score_dict = {f"{r.get('firstName', '')} {r.get('lastName', '')}".strip().lower(): r.get('totalToPar', 0) for r in rows}
        
        entries = get_sheet().get_all_records()
        if entries:
            results = []
            for entry in entries:
                # Calculate scores (Fallback to 0 if not found)
                s1 = score_dict.get(entry['P1'].lower(), 0)
                s2 = score_dict.get(entry['P2'].lower(), 0)
                s3 = score_dict.get(entry['P3'].lower(), 0)
                total = s1 + s2 + s3
                
                results.append({
                    "User": entry['User'],
                    "P1": f"{entry['P1']} ({s1})",
                    "P2": f"{entry['P2']} ({s2})",
                    "P3": f"{entry['P3']} ({s3})",
                    "Total": total
                })
            
            df_res = pd.DataFrame(results).sort_values("Total")
            
            # Summary Table (Entry Counts)
            st.subheader("Syndicate Entry Tracker")
            summary = df_res['User'].value_counts().reset_index()
            summary.columns = ['Participant', 'Teams Submitted']
            st.table(summary)
            
            # Full Standings
            st.subheader("Live Standings")
            st.dataframe(df_res, hide_index=True, use_container_width=True)
        else:
            st.info("No entries yet.")
    except Exception as e: st.error(f"Leaderboard Error: {e}")

# TAB 3: FIELD INTELLIGENCE
with tab3:
    st.header("Syndicate Data Analysis")
    try:
        entries = get_sheet().get_all_records()
        if entries:
            all_picks = []
            team_combos = []
            duo_combos = []
            
            for row in entries:
                team = sorted([row['P1'], row['P2'], row['P3']])
                all_picks.extend(team)
                team_combos.append(tuple(team))
                duo_combos.extend(list(combinations(team, 2)))

            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Most Picked Players")
                st.write(pd.DataFrame(Counter(all_picks).most_common(10), columns=['Player', 'Picks']))
            with c2:
                st.subheader("The Hive Mind (Pairs)")
                st.write(pd.DataFrame([{"Pair": f"{d[0]} + {d[1]}", "Count": c} for d, c in Counter(duo_combos).most_common(5)]))

            st.subheader("Full Roster Clones (Triplets)")
            st.write(pd.DataFrame([{"Team": f"{t[0]}, {t[1]}, {t[2]}", "Count": c} for t, c in Counter(team_combos).most_common(5)]))
    except Exception as e: st.error(f"Analysis Error: {e}")

# TAB 4: LIVE FIELD
with tab4:
    st.header("Tournament Master Board")
    rows = get_scores()
    if rows:
        f_data = [{"Pos": r.get('position'), "Player": f"{r.get('firstName')} {r.get('lastName')}", "Thru": r.get('thru'), "Score": r.get('totalToPar')} for r in rows]
        st.dataframe(pd.DataFrame(f_data), hide_index=True, use_container_width=True)
    else:
        st.info("Waiting for tournament to commence...")
