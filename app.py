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

# --- HELPER: DATA PARSING & FORMATTING ---
def parse_score_to_int(val):
    if isinstance(val, dict):
        return int(val.get('$numberInt', 0))
    try:
        return int(val) if val is not None else 0
    except:
        return 0

def format_score_val(val):
    if val == 0: return "E"
    if val > 0: return f"+{val}"
    return str(val)

def bold_text(text):
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

OFFICIAL_FIELD = ["Scottie Scheffler", "Rory McIlroy", "Matt Fitzpatrick", "Cameron Young", "Russell Henley", "Chris Gotterup", "Collin Morikawa", "Wyndham Clark", "Tommy Fleetwood", "Justin Rose", "Jon Rahm", "Viktor Hovland", "J.J. Spaun", "Xander Schauffele", "Robert MacIntyre", "Ben Griffin", "Aaron Rai", "Sam Burns", "Justin Thomas", "Ludvig Aberg", "Si Woo Kim", "Tyrrell Hatton", "Sepp Straka", "Min Woo Lee", "Alex Noren", "Patrick Reed", "Kristoffer Reitan", "Ryan Gerard", "Akshay Bhatia", "Jacob Bridgeman", "Hideki Matsuyama", "Harris English", "Tom Kim", "JT Poston", "Nicolai Hojgaard", "Kurt Kitayama", "Bryson DeChambeau", "Patrick Cantlay", "Maverick McNealy", "Bud Cauley", "Keegan Bradley", "Rickie Fowler", "Gary Woodland", "Alex Smalley", "Jake Knapp", "Shane Lowry", "Sam Stevens", "Joaquin Niemann", "Daniel Berger", "Marco Penge", "Jordan Spieth", "Nicolas Echavarria", "Corey Conners", "Jason Day", "Michael Kim", "Ryan Fox", "Adam Scott", "Eugenio Chacarra", "Michael Brennan", "Pierceson Coody", "Ryo Hisatsune", "Matt McCarty", "Brian Harman", "Alex Fitzpatrick", "David Puig", "Nick Taylor", "Keith Mitchell", "Andrew Novak", "Michael Thorbjornsen", "Eric Cole", "Matt Wallace", "Sami Valimaki", "Max Homa", "Harry Hall", "Max Greyserman", "Jordan Smith", "Thomas Detry", "Sahith Theegala", "Casey Jarvis", "Jayden Schaper", "Sungjae Im", "Rasmus Hojgaard", "Keita Nakajima", "Rasmus Neergaard-Petersen", "Shaun Norris", "John Parry", "Lucas Herbert", "Daniel Hillier", "Haotong Li", "Kota Kaneko", "Angel Ayora", "Jackson Suber", "Brooks Koepka", "Hennie du Plessis", "Andy Sullivan", "Adrien Saddier", "Jose Luis Ballester", "Tom McKibbin", "Daniel Brown", "Cameron Smith", "Laurie Canter", "Travis Smyth", "Michael Hollick", "Scott Vincent", "Dan Bradbury", "Bernd Wiesberger", "Joakim Lagergren", "Victor Perez", "Jesper Svensson", "Billy Horschel", "Martin Couvra", "Kazuki Higa", "Peter Uihlein", "Alistair Docherty", "Kazuma Kobori", "Antoine Rozner", "Francesco Laporta", "MJ Daffue", "Francesco Molinari", "Ren Yonezawa", "Frederic Lacroix", "Cameron John", "James Nicholas", "Caleb Surratt", "Matthew Jordan", "Naoyuki Kataoka", "Sam Bairstow", "Austen Truslow", "Jeongwoo Ham", "Aldrich Potgieter", "Matthew Southgate", "Ryutaro Nagano", "Jiho Yang", "Padraig Harrington", "Jack Buchanan", "Marcus Plunkett", "Matthew Baldwin", "Tiger Christensen", "Henrik Stenson", "Stewart Cink", "Stuart Grehan", "Darren Clarke", "Alejandro De Castro Piera", "Baard Bjoernevik Skogen", "David Duval", "David Howard", "Fifa Laopakdee", "Jack McDonald", "Johnny Keefer", "Lev Grinberg", "Mason Howell", "Mateo Pulcini", "Nevill Ruiter", "Tim Wiedemeyer", "Tom Sloman"]
ELITE_30 = OFFICIAL_FIELD[:30]
WILDCARD_FIELD = OFFICIAL_FIELD[30:]

# --- 4. DATA FETCHING ---
@st.cache_data(ttl=600)
def get_live_data():
    try:
        url = "https://live-golf-data.p.rapidapi.com/leaderboard"
        headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
        params = {"orgId": "1", "tournId": TOURN_ID, "year": YEAR}
        res = requests.get(url, headers=headers, params=params)
        data = res.json()
        return data.get('leaderboardRows', data.get('leaderboard', data.get('players', [])))
    except Exception as e:
        st.sidebar.error(f"API Sync Error: {e}")
        return []

# --- 5. MISSED CUT & PENALTY LOGIC ---
live_rows = get_live_data()
registry_data = get_sheet().get_all_records()

# Calculate Field Averages for Penalty (Rounds 3 & 4)
def get_round_averages(rows):
    avgs = {2: 0, 3: 0} # index for R3 and R4
    for idx in [2, 3]:
        scores = []
        for r in rows:
            rds = r.get('rounds', [])
            if len(rds) > idx:
                scores.append(parse_score_to_int(rds[idx].get('scoreToPar')))
        if scores:
            avgs[idx] = round(sum(scores) / len(scores))
    return avgs

round_penalties = get_round_averages(live_rows)

pro_map = {}
for r in live_rows:
    p_name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip() or r.get('playerName', 'Unknown')
    status = str(r.get('status', '')).upper()
    
    # Calculate base score from available rounds
    calc_total = 0
    rounds = r.get('rounds', [])
    for rd in rounds:
        calc_total += parse_score_to_int(rd.get('scoreToPar'))
        
    # Apply penalties for MC/WD/DQ for R3 and R4 if they happened
    is_cut = status in ['CUT', 'MC', 'WD', 'DQ']
    if is_cut:
        if len(rounds) <= 2: calc_total += round_penalties[2] # R3 Penalty
        if len(rounds) <= 3: calc_total += round_penalties[3] # R4 Penalty

    pro_map[p_name] = {
        "score": calc_total,
        "thru": r.get('thru', 'CUT' if is_cut else '-'),
        "pos": r.get('position', 'CUT' if is_cut else '-'),
        "is_cut": is_cut
    }

# --- 6. APP LAYOUT ---
st.title("🏆 154th Open Championship Tracker")

tab_reg, tab_lead, tab_intel, tab_master, tab_winners, tab_registry = st.tabs([
    "✍️ Registration", "📊 Standings", "🧠 Field Intel", "⛳ Master Board", "🥇 Round Winners", "📂 Registry"
])

# TAB: REGISTRATION
with tab_reg:
    st.header("Enter Your Team")
    user_name = st.text_input("Participant Name")
    col1, col2, col3 = st.columns(3)
    with col1: p1 = st.selectbox("Player 1", OFFICIAL_FIELD, format_func=lambda x: bold_text(x) if x in ELITE_30 else x)
    with col2: p2 = st.selectbox("Player 2", [p for p in OFFICIAL_FIELD if p != p1], format_func=lambda x: bold_text(x) if x in ELITE_30 else x)
    with col3: p3 = st.selectbox("Wildcard", [p for p in WILDCARD_FIELD if p not in [p1, p2]])
    if st.button("LOCK IN TEAM"):
        if user_name:
            get_sheet().append_row([user_name, p1, p2, p3])
            st.success("Team Locked!")
        else: st.warning("Enter a name.")

# TAB: STANDINGS
with tab_lead:
    st.header("Syndicate Standings")
    if round_penalties[2] != 0 or round_penalties[3] != 0:
        st.info(f"Penalty for Cut Players: R3 (+{round_penalties[2]}), R4 (+{round_penalties[3]})")
        
    user_results = []
    for row in registry_data:
        p_list = [row.get('P1'), row.get('P2'), row.get('P3')]
        total_score = 0
        p_details = []
        for p in p_list:
            p_info = pro_map.get(p, {"score": 0, "is_cut": False})
            score = p_info['score']
            total_score += score
            label = f"{p} ({format_score_val(score)})"
            if p_info['is_cut']: label += " (MC)"
            p_details.append(label)
            
        user_results.append({"User": row.get('User'), "P1": p_details[0], "P2": p_details[1], "P3": p_details[2], "Total": total_score})
    
    df_standings = pd.DataFrame(user_results).sort_values("Total")
    df_standings.insert(0, "Rank", range(1, len(df_standings) + 1))
    df_standings["Total"] = df_standings["Total"].apply(format_score_val)
    st.dataframe(df_standings, hide_index=True, use_container_width=True)

# TAB: FIELD INTEL
with tab_intel:
    st.header("Field Intelligence")
    all_picks, triplets, duos = [], [], []
    for row in registry_data:
        team = sorted([row['P1'], row['P2'], row['P3']])
        all_picks.extend(team)
        triplets.append(tuple(team))
        duos.extend(list(combinations(team, 2)))
    ca, cb = st.columns(2)
    with ca:
        st.subheader("Most Picked Players")
        df_p = pd.DataFrame(Counter(all_picks).most_common(10), columns=['Golfer', 'Count'])
        st.dataframe(df_p, hide_index=True)
    with cb:
        st.subheader("Popular Pairs")
        df_d = pd.DataFrame([{"Pair": f"{d[0]} & {d[1]}", "Count": c} for d, c in Counter(duos).most_common(5)])
        st.dataframe(df_d, hide_index=True)

# TAB: MASTER BOARD
with tab_master:
    st.header("Official Leaderboard")
    master_list = []
    for name, d in pro_map.items():
        master_list.append({
            "Pos": d['pos'], 
            "Golfer": name + (" (MC)" if d['is_cut'] else ""), 
            "Thru": d['thru'], 
            "Score": format_score_val(d['score']), 
            "Sort": d['score']
        })
    sorted_m = sorted(master_list, key=lambda x: x['Sort'])
    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    for i, p in enumerate(sorted_m[:5]):
        [sc1, sc2, sc3, sc4, sc5][i].metric(p['Golfer'], p['Score'], p['Pos'])
    st.divider()
    st.dataframe(pd.DataFrame(sorted_m)[["Pos", "Golfer", "Thru", "Score"]], hide_index=True, use_container_width=True)

# TAB: ROUND WINNERS
with tab_winners:
    st.header("Daily Performance")
    rs = st.radio("Round", ["Round 1", "Round 2", "Round 3", "Round 4"], horizontal=True)
    ri = int(rs[-1]) - 1
    dl = []
    for r in live_rows:
        rds = r.get('rounds', [])
        if len(rds) > ri:
            ds = parse_score_to_int(rds[ri].get('scoreToPar'))
            name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip() or r.get('playerName', 'Unknown')
            dl.append({"Golfer": name, "Score": ds})
    if dl:
        df_day = pd.DataFrame(dl).sort_values("Score")
        st.dataframe(df_day, hide_index=True, use_container_width=True)

# TAB: REGISTRY
with tab_registry:
    st.header("Registry Data")
    st.dataframe(pd.DataFrame(registry_data), use_container_width=True)
