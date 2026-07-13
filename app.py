import streamlit as st
import pandas as pd
import requests
import gspread
from google.oauth2.service_account import Credentials

# --- 1. SETTINGS ---
st.set_page_config(page_title="154th Open Championship Tracker", layout="wide")

# --- 2. AUTHENTICATION ---
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
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"
    headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
    res = requests.get(url, headers=headers, params={"orgId": "1", "tournId": TOURN_ID, "year": YEAR})
    return res.json().get('leaderboardRows', [])

# --- 5. MAIN UI ---
st.title("🏆 154th Open Championship")

# Moved Registration into the main Tabs for mobile visibility
tab1, tab2, tab3 = st.tabs(["📊 Leaderboard", "✍️ Register Team", "⛳ Live Field"])

with tab2:
    st.header("Register Your Team")
    with st.form("main_entry_form", clear_on_submit=True):
        u_name = st.text_input("Your Full Name")
        col1, col2, col3 = st.columns(3)
        with col1:
            p1 = st.selectbox("Elite Choice 1", ELITE_30)
        with col2:
            p2 = st.selectbox("Elite Choice 2", [p for p in ELITE_30 if p != p1])
        with col3:
            p3 = st.selectbox("Wildcard Choice", WILDCARD)
        
        if st.form_submit_button("LOCK IN TEAM"):
            if u_name:
                try:
                    sheet = get_sheet()
                    sheet.append_row([u_name, p1, p2, p3])
                    st.success(f"Successfully Registered: {u_name}")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please enter your name.")

with tab1:
    try:
        rows = get_scores()
        player_map = {f"{r.get('firstName', '')} {r.get('lastName', '')}".strip().lower(): r.get('totalToPar', 0) for r in rows}
        
        sheet = get_sheet()
        entries = sheet.get_all_records()
        
        if entries:
            df_entries = pd.DataFrame(entries)
            # Count entries per person
            summary = df_entries['User'].value_counts().reset_index()
            summary.columns = ['Participant', 'Teams Submitted']
            
            st.subheader("Syndicate Standings (Entry Counts)")
            st.table(summary)
            
            with st.expander("Show All Team Roster Details"):
                st.dataframe(df_entries, hide_index=True)
        else:
            st.info("The field is empty. Be the first to register!")
    except Exception as e:
        st.error(f"Data Connection Error: {e}")

with tab3:
    if rows:
        f_data = [{"Pos": r.get('position'), "Player": f"{r.get('firstName')} {r.get('lastName')}", "Score": r.get('totalToPar')} for r in rows]
        st.dataframe(pd.DataFrame(f_data), hide_index=True, use_container_width=True)
