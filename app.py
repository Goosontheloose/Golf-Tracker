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

# --- HELPER: UNICODE BOLD FOR DROPDOWNS ---
def bold_text(text):
    """Transforms standard text into Unicode Bold characters for UI display."""
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    bold_chars = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
    trans = str.maketrans(chars, bold_chars)
    return text.translate(trans)

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

# --- 3. CONFIG & FIELD DATA ---
API_KEY = st.secrets["api_key"]
YEAR, TOURN_ID = "2026", "100"

OFFICIAL_FIELD = ["Scottie Scheffler", "Rory McIlroy", "Matt Fitzpatrick", "Cameron Young", "Russell Henley", "Chris Gotterup", "Collin Morikawa", "Wyndham Clark", "Tommy Fleetwood", "Justin Rose", "Jon Rahm", "Viktor Hovland", "J.J. Spaun", "Xander Schauffele", "Robert MacIntyre", "Ben Griffin", "Aaron Rai", "Sam Burns", "Justin Thomas", "Ludvig Aberg", "Si Woo Kim", "Tyrrell Hatton", "Sepp Straka", "Min Woo Lee", "Alex Noren", "Patrick Reed", "Kristoffer Reitan", "Ryan Gerard", "Akshay Bhatia", "Jacob Bridgeman", "Hideki Matsuyama", "Harris English", "Tom Kim", "JT Poston", "Nicolai Hojgaard", "Kurt Kitayama", "Bryson DeChambeau", "Patrick Cantlay", "Maverick McNealy", "Bud Cauley", "Keegan Bradley", "Rickie Fowler", "Gary Woodland", "Alex Smalley", "Jake Knapp", "Shane Lowry", "Sam Stevens", "Joaquin Niemann", "Daniel Berger", "Marco Penge", "Jordan Spieth", "Nicolas Echavarria", "Corey Conners", "Jason Day", "Michael Kim", "Ryan Fox", "Adam Scott", "Eugenio Chacarra", "Michael Brennan", "Pierceson Coody", "Ryo Hisatsune", "Matt McCarty", "Brian Harman", "Alex Fitzpatrick", "David Puig", "Nick Taylor", "Keith Mitchell", "Andrew Novak", "Michael Thorbjornsen", "Eric Cole", "Matt Wallace", "Sami Valimaki", "Max Homa", "Harry Hall", "Max Greyserman", "Jordan Smith", "Thomas Detry", "Sahith Theegala", "Casey Jarvis", "Jayden Schaper", "Sungjae Im", "Rasmus Hojgaard", "Keita Nakajima", "Rasmus Neergaard-Petersen", "Shaun Norris", "John Parry", "Lucas Herbert", "Daniel Hillier", "Haotong Li", "Kota Kaneko", "Angel Ayora", "Jackson Suber", "Brooks Koepka", "Hennie du Plessis", "Andy Sullivan", "Adrien Saddier", "Jose Luis Ballester", "Tom McKibbin", "Daniel Brown", "Cameron Smith", "Laurie Canter", "Travis Smyth", "Michael Hollick", "Scott Vincent", "Dan Bradbury", "Bernd Wiesberger", "Joakim Lagergren", "Victor Perez", "Jesper Svensson", "Billy Horschel", "Martin Couvra", "Kazuki Higa", "Peter Uihlein", "Alistair Docherty", "Kazuma Kobori", "Antoine Rozner", "Francesco Laporta", "MJ Daffue", "Francesco Molinari", "Ren Yonezawa", "Frederic Lacroix", "Cameron John", "James Nicholas", "Caleb Surratt", "Matthew Jordan", "Naoyuki Kataoka", "Sam Bairstow", "Austen Truslow", "Jeongwoo Ham", "Louis Oosthuizen", "Matthew Southgate", "Ryutaro Nagano", "Jiho Yang", "Padraig Harrington", "Jack Buchanan", "Marcus Plunkett", "Matthew Baldwin", "Tiger Christensen", "Henrik Stenson", "Stewart Cink", "Stuart Grehan", "Darren Clarke", "Alejandro De Castro Piera", "Baard Bjoernevik Skogen", "David Duval", "David Howard", "Fifa Laopakdee", "Jack McDonald", "Johnny Keefer", "Lev Grinberg", "Mason Howell", "Mateo Pulcini", "Nevill Ruiter", "Tim Wiedemeyer", "Tom Sloman"]

ELITE_30 = OFFICIAL_FIELD[:30]
WILDCARD_FIELD = OFFICIAL_FIELD[30:]

# --- 4. DATA FETCHING ---
@st.cache_data(ttl=900)
def get_live_scores():
    try:
        url = "https://live-golf-data.p.rapidapi.com/leaderboard"
        headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
        params = {"orgId": "1", "tournId": TOURN_ID, "year": YEAR}
        res = requests.get(url, headers=headers, params=params)
        return res.json().get('leaderboardRows', [])
    except Exception as e:
        st.sidebar.error(f"API Sync Error: {e}")
        return []

# --- 5. APP TABS ---
st.title("🏆 154th Open Championship Tracker")

tab_reg, tab_lead, tab_intel, tab_field = st.tabs([
    "✍️ Team Registration", 
    "📊 Leaderboard", 
    "🧠 Field Intelligence", 
    "⛳ Official Master Board"
])

# TAB 1: REGISTRATION
with tab_reg:
    st.header("Enter Your Team")
    user_name = st.text_input("Participant Name")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        pick1 = st.selectbox(
            "Player Choice 1", 
            OFFICIAL_FIELD, 
            format_func=lambda x: bold_text(x) if x in ELITE_30 else x
        )
    with col2:
        # Strict Uniqueness: Removes pick1
        pick2 = st.selectbox(
            "Player Choice 2", 
            [p for p in OFFICIAL_FIELD if p != pick1], 
            format_func=lambda x: bold_text(x) if x in ELITE_30 else x
        )
    with col3:
        # Strict Uniqueness: Removes pick1 and pick2
        pick3 = st.selectbox(
            "Wildcard Choice (Outside Top 30)", 
            [p for p in WILDCARD_FIELD if p not in [pick1, pick2]]
        )
        
    if st.button("LOCK IN TEAM"):
        if user_name:
            try:
                get_sheet().append_row([user_name, pick1, pick2, pick3])
                st.success(f"Team Locked! Good luck, {user_name}.")
                st.balloons()
            except Exception as e:
                st.error(f"Submission Failed: {e}")
        else:
            st.warning("Please provide a name for the entry.")

# TAB 2: LEADERBOARD
with tab_lead:
    st.header("Standings")
    try:
        live_rows = get_live_scores()
        score_map = {f"{r.get('firstName', '')} {r.get('lastName', '')}".strip().lower(): r.get('totalToPar', 0) for r in live_rows}
        
        entries = get_sheet().get_all_records()
        if entries:
            final_data = []
            for entry in entries:
                s1 = score_map.get(str(entry['P1']).lower(), 0)
                s2 = score_map.get(str(entry['P2']).lower(), 0)
                s3 = score_map.get(str(entry['P3']).lower(), 0)
                
                final_data.append({
                    "User": entry['User'],
                    "P1": f"{entry['P1']} ({s1})",
                    "P2": f"{entry['P2']} ({s2})",
                    "P3": f"{entry['P3']} ({s3})",
                    "Total Score": s1 + s2 + s3
                })
            
            df_standings = pd.DataFrame(final_data).sort_values("Total Score")
            st.subheader("Entries per Participant")
            entry_counts = df_standings['User'].value_counts().reset_index()
            entry_counts.columns = ['Participant', 'Total Entries']
            st.table(entry_counts)
            
            st.subheader("Live Standings")
            st.dataframe(df_standings, hide_index=True, use_container_width=True)
        else:
            st.info("No entries found in the Google Sheet.")
    except Exception as e:
        st.error(f"Failed to load leaderboard: {e}")

# TAB 3: FIELD INTELLIGENCE
with tab_intel:
    st.header("Trends & Analysis")
    try:
        entries = get_sheet().get_all_records()
        if entries:
            all_picks, triplets, duos = [], [], []
            for row in entries:
                team = sorted([row['P1'], row['P2'], row['P3']])
                all_picks.extend(team)
                triplets.append(tuple(team))
                duos.extend(list(combinations(team, 2)))
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("Most Selected Players")
                st.write(pd.DataFrame(Counter(all_picks).most_common(10), columns=['Golfer', 'Selections']))
            with col_b:
                st.subheader("Most Popular Pairs")
                st.write(pd.DataFrame([{"Pair": f"{d[0]} & {d[1]}", "Count": c} for d, c in Counter(duos).most_common(5)]))
            st.subheader("Identical Teams")
            st.write(pd.DataFrame([{"Full Roster": f"{t[0]}, {t[1]}, {t[2]}", "Count": c} for t, c in Counter(triplets).most_common(5)]))
    except Exception as e:
        st.error(f"Intelligence Error: {e}")

# TAB 4: OFFICIAL MASTER BOARD
with tab_field:
    st.header("Official 154th Open Leaderboard")
    live_rows = get_live_scores()
    if live_rows:
        master_data = [{
            "Pos": r.get('position'), 
            "Golfer": f"{r.get('firstName')} {r.get('lastName')}", 
            "Thru": r.get('thru'), 
            "Score": r.get('totalToPar')
        } for r in live_rows]
        st.dataframe(pd.DataFrame(master_data), hide_index=True, use_container_width=True)
    else:
        st.info("Official scores will appear here when play begins.")
