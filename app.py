import streamlit as st
import pandas as pd
import requests
from streamlit_gsheets import GSheetsConnection

# --- 1. SETTINGS & PROFESSIONAL BRANDING ---
st.set_page_config(page_title="154th Open Championship Tracker", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Oswald:wght@700&display=swap');
    .main { background-color: #f8f9fa; color: #1a1a1a; }
    h1, h2, h3 { font-family: 'Oswald', sans-serif; color: #003366; }
    .stMetric { background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONFIGURATION & HARDCODED FIELD ---
API_KEY = st.secrets["api_key"]
SHEET_URL = st.secrets.get("sheet_url", "") # Defined in your secrets

# The Official 2026 Field provided by you
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

# Splitting lists
ELITE_30 = OFFICIAL_FIELD[:30]
WILDCARD_FIELD = OFFICIAL_FIELD[30:]

# --- 3. CORE FUNCTIONS ---
@st.cache_data(ttl=900)
def get_live_scores():
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"
    params = {"orgId": "1", "tournId": "100", "year": "2026"}
    headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
    try:
        r = requests.get(url, headers=headers, params=params)
        return r.json().get('leaderboardRows', [])
    except:
        return []

# --- 4. APP LAYOUT ---
st.title("🏆 154th Open Championship Leaderboard")
st.subheader("Royal Birkdale | 2026")

# Sidebar Entry Form
with st.sidebar:
    st.header("Team Entry")
    with st.form("entry_form"):
        name = st.text_input("Player Name")
        p1 = st.selectbox("Elite Pick 1", ELITE_30)
        p2 = st.selectbox("Elite Pick 2", [p for p in ELITE_30 if p != p1])
        p3 = st.selectbox("Wildcard Pick", WILDCARD_FIELD)
        submitted = st.form_submit_button("Submit Team")
        
        if submitted and name:
            # Logic to save to Google Sheets would go here
            st.success(f"Team {name} submitted!")

# Main Dashboard Content...
# (Score calculation and leaderboard logic follows below)
