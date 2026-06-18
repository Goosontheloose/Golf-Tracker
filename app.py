import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from collections import Counter      
from itertools import combinations    

# --- 1. SETTINGS & BRANDING ---
st.set_page_config(page_title="The US OPEN 2026", layout="wide")

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

    /* Force Table Text Color */
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        color: #064E3B !important;
    }

    @media (max-width: 768px) {
        [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; min-width: 100% !important; }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA ---
RAW_DATA = """
Ettienne Bedeker	Scottie Scheffler	Rory McIlroy	Alex Fitzpatrick
Brendon	Jon Rahm	Jake Knapp	Brooks Koepka
Heino Noeth	Rory McIlroy	Tommy Fleetwood	Joaquin Niemann
Thomas Potgieter	Scottie Scheffler	Russell Henley	Patrick Cantlay
Thomas Potgieter	Tommy Fleetwood	Hideki Matsuyama	Corey Conners
Thomas Potgieter	Rory McIlroy	Jon Rahm	Bryson DeChambeau
Etienne Roodt	Scottie Scheffler	Rory McIlroy	Bryson DeChambeau
Hannes du Plessis	Rory McIlroy	Tyrrell Hatton	Brooks Koepka
Kobus du Plessis	Tyrrell Hatton	Matt Fitzpatrick	Corey Conners
Wimpie Barnard	Scottie Scheffler	Kristoffer Reitan	Wyndham Clark
Laurence	Scottie Scheffler	Rory McIlroy	Bryson DeChambeau
Werner Moolman	Scottie Scheffler	Cameron Young	Wyndham Clark
Ranon Fouche	Scottie Scheffler	Xander Schauffele	Bryson DeChambeau
Ruan Brits	Scottie Scheffler	Tommy Fleetwood	Shane Lowry
Corne van Wyk	Rory McIlroy	Tommy Fleetwood	Shane Lowry
Theuns Greyling	Scottie Scheffler	Matt Fitzpatrick	Bryson DeChambeau
Corne van Wyk	Scottie Scheffler	Xander Schauffele	Wyndham Clark
Reinhardt Uys	Tommy Fleetwood	Brooks Koepka	Jake Knapp
Tyronne	Cameron Young	Xander Schauffele	Wyndham Clark
Tyronne	Cameron Young	Scottie Scheffler	Bryson DeChambeau
Tobie	Justin Rose	Ludvig Åberg	Bryson DeChambeau
Tereza Windell	Scottie Scheffler	Tommy Fleetwood	Bryson DeChambeau
Tereza Windell	Rory McIlroy	Jon Rahm	Joaquin Niemann
Cornel Windell	Justin Rose	Aaron Rai	Jason Day
Cornel Windell	Ludvig Åberg	Si Woo Kim	Patrick Cantlay
Theuns Greyling	Jon Rahm	Scottie Scheffler	Bryson DeChambeau
Theuns Greyling	Jon Rahm	Scottie Scheffler	Brooks Koepka
Jacobusp1	Rory McIlroy	Tommy Fleetwood	Keegan Bradley
Robert	Scottie Scheffler	Jon Rahm	Joaquin Niemann
Ettienne Bedeker	Rory McIlroy	Jon Rahm	Cameron Smith
Anton 	Scottie Scheffler	Matt Fitzpatrick	Dustin Johnson
Anton	Rory McIlroy	Tyrrell Hatton	Shane Lowry
Anton	Justin Rose	Xander Schauffele	Bryson DeChambeau
Anton	Scottie Scheffler	Rory McIlroy	Shane Lowry
Braam Greyling	Scottie Scheffler	Cameron Young	Bryson DeChambeau
Braam Greyling	Rory McIlroy	Russell Henley	Wyndham Clark
Braam Greyling	Matt Fitzpatrick	Tommy Fleetwood	Patrick Cantlay
Braam Greyling	Scottie Scheffler	Rory McIlroy	Brooks Koepka
Braam Greyling	Russell Henley	Tyrrell Hatton	Tom Kim
Robert	Scottie Scheffler	Tyrrell Hatton	Patrick Cantlay
Pieter Rossouw	Tommy Fleetwood	Sam Burns	Bryson DeChambeau
AJ Hechter	Scottie Scheffler	Chris Gotterup	Cameron Smith
Ben Jones	Rory McIlroy	Ludvig Åberg	Corey Conners
Ben Jones	Rory McIlroy	Cameron Young	Corey Conners
Ben Jones	Russell Henley	Ludvig Åberg	Patrick Cantlay
Ben Jones	Xander Schauffele	Aaron Rai	Wyndham Clark
Marina Jones	Rory McIlroy	Xander Schauffele	Kurt Kitayama
Marina Jones	Rory McIlroy	Bryson DeChambeau	Kurt Kitayama
Benno vd Westhuizen	Scottie Scheffler	Cameron Young	Brooks Koepka
Benno vd Westhuizen	Rory McIlroy	Cameron Young	Bryson DeChambeau
Rowan	Scottie Scheffler	Russell Henley	Shane Lowry
Rowan	Xander Schauffele	Matt Fitzpatrick	Sahith Theegala
Gustav Smit	Patrick Reed	J.J. Spaun	Max Greyserman
Gustav Smit	Rory McIlroy	Scottie Scheffler	Bryson DeChambeau
Gustav Smit	Russell Henley	Tommy Fleetwood	Jordan Spieth
Hendri	Scottie Scheffler	Rory McIlroy	Brooks Koepka
Martin Roelofse	Tommy Fleetwood	Patrick Reed	Wyndham Clark
Gustav Smit	Cameron Young	Sam Burns	Jason Day
Peet	Scottie Scheffler	Rory McIlroy	Rickie Fowler
Ben Ras	Scottie Scheffler	Matt Fitzpatrick	Wyndham Clark
Armand	Scottie Scheffler	Matt Fitzpatrick	Shane Lowry
Armand	Cameron Young	Tommy Fleetwood	Brian Harman
Dean Steinhobel	Justin Rose	Xander Schauffele	Wyndham Clark
Dean Steinhobel	Scottie Scheffler	Jon Rahm	Joaquin Niemann
Dean Steinhobel	Justin Thomas	Dustin Johnson	Shane Lowry
Dean Steinhobel	Jon Rahm	Jordan Spieth	Cameron Smith
Ben Ras	Chris Gotterup	Cameron Young	Bryson DeChambeau
Fred Bezuidenhout	Cameron Young	Matt Fitzpatrick	Max Greyserman
Fred Bezuidenhout	Tommy Fleetwood	Jon Rahm	Jake Knapp
Roy Coetser	Scottie Scheffler	Chris Gotterup	Jason Day
Kobus Rossouw	Scottie Scheffler	Rory McIlroy	Bryson DeChambeau
Kobus Rossouw	Scottie Scheffler	Jon Rahm	Joaquin Niemann
Kobus Rossouw	Scottie Scheffler	Ludvig Åberg	Min Woo Lee
Kobus Rossouw	Rory McIlroy	Bryson DeChambeau	Joaquin Niemann
Kobus Rossouw	Scottie Scheffler	Tommy Fleetwood	Shane Lowry
Tjaart	Cameron Young	Tyrrell Hatton	Alejandro Tosti
Leonie Coetser	Ludvig Åberg	Viktor Hovland	Shane Lowry
Martin Coetser	Scottie Scheffler	Matt Fitzpatrick	Brooks Koepka
Martin Coetser	Rory McIlroy	Xander Schauffele	Bryson DeChambeau
Martin Coetser	Jon Rahm	Tommy Fleetwood	Brooks Koepka
Martin Coetser	Matt Fitzpatrick	Rory McIlroy	Alex Fitzpatrick
Pierre Rynners	Scottie Scheffler	Xander Schauffele	Brian Harman
Owen Rynners	Scottie Scheffler	Tommy Fleetwood	Shane Lowry
Owen Rynners	Rory McIlroy	Russell Henley	Corey Conners
Shaun Rynners	Rory McIlroy	Tommy Fleetwood	Wyndham Clark
Michael	Rory McIlroy	Justin Rose	Bryson DeChambeau
Michael	Scottie Scheffler	Cameron Young	Wyndham Clark
Etienne Roodt	Jon Rahm	Xander Schauffele	Jordan Spieth
Deon Lappa	Justin Rose	Scottie Scheffler	Shane Lowry
Reon Cronje	Scottie Scheffler	Justin Rose	Nicolai Hojgaard
Kian	Scottie Scheffler	Ludvig Åberg	Bryson DeChambeau
Derik	Patrick Reed	Sam Burns	Cameron Smith
Derik	Scottie Scheffler	Rory McIlroy	Bryson DeChambeau
Derik	Scottie Scheffler	Matt Fitzpatrick	Bryson DeChambeau
ZT Project Management	Scottie Scheffler	Tommy Fleetwood	Shane Lowry
ZT Project Management	Cameron Young	Matt Fitzpatrick	Cameron Smith
ZT Project Management	Rory McIlroy	Justin Rose	Shane Lowry
ZT Project Management	Tyrrell Hatton	Collin Morikawa	Min Woo Lee
ZT Project Management	Jon Rahm	Ludvig Åberg	Shane Lowry
ZT Project Management	Xander Schauffele	Patrick Reed	Cameron Smith
ZT Project Management	Patrick Reed	Matt Fitzpatrick	Shane Lowry
ZT Project Management	Jon Rahm	Justin Rose	Corey Conners
ZT Project Management	Matt Fitzpatrick	Xander Schauffele	J.T. Poston
Nico Noeth	Rory McIlroy	Patrick Reed	Ryan Fox
Wynand	Scottie Scheffler	Tommy Fleetwood	Bryson DeChambeau
Pierre Rynners	Justin Rose	Sam Burns	Jason Day
Edwin	Rory McIlroy	Matt Fitzpatrick	Brooks Koepka
Edwin	Scottie Scheffler	Cameron Young	Bryson DeChambeau
Edwin	Russell Henley	Justin Rose	Joaquin Niemann
Frederik	Rory McIlroy	Scottie Scheffler	Bryson DeChambeau
Ralf Grotsch	Tommy Fleetwood	Tyrrell Hatton	Brooks Koepka
Johann Lubbe	Tyrrell Hatton	Rory McIlroy	Shane Lowry
Johann Lubbe	Tommy Fleetwood	Ludvig Åberg	Alex Smalley
Johann Lubbe	Matt Fitzpatrick	Viktor Hovland	Nicolai Hojgaard
Dean	Matt Fitzpatrick	Rory McIlroy	Shane Lowry
Ralf Grotsch	Cameron Young	Rory McIlroy	Bud Cauley
Jaco Greeff	Rory McIlroy	Scottie Scheffler	Brooks Koepka
Jaco Greeff	Rory McIlroy	Cameron Young	Bryson DeChambeau
Jaco Greeff	Scottie Scheffler	Jon Rahm	Wyndham Clark
Jaco Greeff	Scottie Scheffler	Russell Henley	Wyndham Clark
Jaco Greeff	Rory McIlroy	Scottie Scheffler	Wyndham Clark
Morne Howell	Rory McIlroy	Scottie Scheffler	Brooks Koepka
Morne Howell	Tommy Fleetwood	Scottie Scheffler	Bryson DeChambeau
Johnny Lubbe	Scottie Scheffler	Rory McIlroy	Shane Lowry
Johnny Lubbe	Scottie Scheffler	Tommy Fleetwood	Patrick Cantlay
Johnny Lubbe	Rory McIlroy	Matt Fitzpatrick	Adam Scott
Johnny Lubbe	Rory McIlroy	Jon Rahm	Joaquin Niemann
Donald	Scottie Scheffler	Tyrrell Hatton	Jayden Schaper
Donald	Ludvig Åberg	Tommy Fleetwood	Bryson DeChambeau
Donald	Viktor Hovland	Xander Schauffele	Chris Kirk
Wynand Kruger	Scottie Scheffler	Tommy Fleetwood	Bryson DeChambeau
Wynand Kruger	Rory McIlroy	Ludvig Åberg	Patrick Cantlay
Micaela Jones	Cameron Young	Maverick McNealy	Jason Day
Eckhard Jones	Scottie Scheffler	Min Woo Lee	Patrick Cantlay
Maricell Jones	Ludvig Åberg	Adam Scott	Bryson DeChambeau
Theuns Greyling	Scottie Scheffler	Rory McIlroy	Brooks Koepka
Dossa	Scottie Scheffler	Cameron Young	Brooks Koepka
Eugene	Scottie Scheffler	Xander Schauffele	Brooks Koepka
Eugene	Rory McIlroy	Jon Rahm	Bryson DeChambeau
Eugene	Cameron Young	Collin Morikawa	Wyndham Clark
Eugene	Tommy Fleetwood	Ludvig Åberg	Joaquin Niemann
Owen Rynners	Tyrrell Hatton	Jon Rahm	Bryson DeChambeau
Rikus Hattingh	Matt Fitzpatrick	Tommy Fleetwood	Gary Woodland
Eugene	Justin Rose	Jayden Schaper	Hennie du Plessis
Christiaan Daniels	Patrick Reed	Justin Thomas	Keegan Bradley
Christiaan Daniels	Scottie Scheffler	Sam Burns	Wyndham Clark
Lauren Coetser	Scottie Scheffler	Xander Schauffele	Joaquin Niemann
Johann Lubbe	Scottie Scheffler	Rory McIlroy	Keegan Bradley
Derick Kunz	Scottie Scheffler	Rory McIlroy	Ben Kohles
AJ Hechter	Matt Fitzpatrick	Tyrrell Hatton	Min Woo Lee
Duncan Stevens	Scottie Scheffler	Xander Schauffele	Bryson DeChambeau
Duncan Stevens	Scottie Scheffler	Matt Fitzpatrick	Shane Lowry
Francois	Rory McIlroy	Tommy Fleetwood	Cameron Smith
William Bithrey	Rory McIlroy	Justin Rose	Bryson DeChambeau
Jason Bithrey	Scottie Scheffler	Rory McIlroy	Brooks Koepka
Deon Labuschagne	Scottie Scheffler	Rory McIlroy	Patrick Cantlay
Deon Labuschagne	Scottie Scheffler	Xander Schauffele	Bryson DeChambeau
Amanda	Rory McIlroy	Tyrrell Hatton	Wyndham Clark
Amanda	Scottie Scheffler	Cameron Young	Bryson DeChambeau
Armand	Scottie Scheffler	Rory McIlroy	Gary Woodland
Billy Matthee	Scottie Scheffler	Ludvig Åberg	Kurt Kitayama
Johan Huyser	Rory McIlroy	Tommy Fleetwood	Jason Day
Gerhard	Tommy Fleetwood	Rory McIlroy	Shane Lowry
Gerhard	Rory McIlroy	Scottie Scheffler	Patrick Cantlay
Christo Killian	Collin Morikawa	Akshay Bhatia	Patrick Cantlay
Christo Killian	Akshay Bhatia	Sam Burns	Jason Day
Christiaan	Jon Rahm	Tyrrell Hatton	Joaquin Niemann
Christiaan	Jon Rahm	Scottie Scheffler	Bryson DeChambeau
Christiaan	Rory McIlroy	Ludvig Åberg	Joaquin Niemann
Ettienne Bedeker	Sam Burns	Cameron Young	Brooks Koepka
Ettienne Bedeker	Scottie Scheffler	Rory McIlroy	Brian Harman
Ettienne Bedeker	Matt Fitzpatrick	Xander Schauffele	Cameron Smith
Tinus Steyn	Scottie Scheffler	Rory McIlroy	Bryson DeChambeau
Tinus Steyn	Scottie Scheffler	Jon Rahm	Brooks Koepka
Tinus Steyn	Rory McIlroy	Cameron Young	Bryson DeChambeau
Cornel Windell	Scottie Scheffler	Rory McIlroy	Joaquin Niemann
Frederik	Matt Fitzpatrick	Tyrrell Hatton	Joaquin Niemann


"""

import re

def get_teams(raw_text):
    teams_dict = {}
    lines = raw_text.strip().split('\n')
    for line in lines:
        # This regex looks for 2 or more spaces OR a tab as the separator
        parts = re.split(r'\t|\s{2,}', line.strip())
        
        if len(parts) >= 2:
            user = parts[0].strip()
            # The rest are the golfers
            golfers = [g.strip() for g in parts[1:] if g.strip()]
            
            # If the user already exists (like 'Braam Greyling'), we create a unique key
            # so we don't overwrite their other entries
            base_user = user
            counter = 1
            while user in teams_dict:
                user = f"{base_user} ({counter})"
                counter += 1
                
            teams_dict[user] = golfers
    return teams_dict

TEAMS = get_teams(RAW_DATA)

def parse_score(val):
    if not val or str(val).upper() in ["E", "EVEN", "CUT"]: return 0
    try: return int(str(val).replace("+", ""))
    except: return 0

@st.cache_data(ttl=900)
def get_data():
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"
    params = {"orgId":"1", "tournId":"026", "year":"2026"}
    headers = {"X-RapidAPI-Key": st.secrets["api_key"], "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
    try:
        r = requests.get(url, headers=headers, params=params)
        return r.json().get('leaderboardRows', [])
    except: return []

# --- 3. EXECUTION ---
def main():
    st.markdown("<h1>🏆 US OPEN 2026 PREDICTIONS</h1>", unsafe_allow_html=True)
    rows = get_data()
    
    if rows:
        # --- 1. PROCESS GLOBAL DATA ---
        player_map = {}
        pro_field = []
        all_picks = []

        for r in rows:
            name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip()
            score = parse_score(r.get('total', '0'))
            thru = r.get('thru', 'F')
            player_map[name.lower()] = {"score": score, "thru": thru}
            pro_field.append({
                "Pos": r.get('position', '-'), 
                "Player": name, 
                "Score": "E" if score == 0 else f"{'+' if score > 0 else ''}{score}", 
                "Thru": thru
            })

        results = []
        for user, roster in TEAMS.items():
            total = 0
            html = ""
            for p in roster:
                all_picks.append(p)
                if p.lower() in player_map:
                    p_data = player_map[p.lower()]
                    score_val = p_data['score']
                    thru_val = p_data['thru']
                    total += score_val
                    s = "E" if score_val == 0 else f"{'+' if score_val > 0 else ''}{score_val}"
                else:
                    s = "Not Found"
                    thru_val = "???"

                html += f'<div class="player-row"><span>{p}</span><span><b>{s}</b> <small>[{thru_val}]</small></span></div>'
            
            results.append({"User": user, "Total": total, "HTML": html})

        df = pd.DataFrame(results).sort_values("Total")
        df.insert(0, 'Rank', range(1, len(df) + 1))

        # --- 2. DISPLAY TOP 5 ---
        st.markdown("### TOP 5 LEADERS")
        cols = st.columns(5)
        for i, (_, r) in enumerate(df.head(5).iterrows()):
            with cols[i]:
                disp = "E" if r['Total'] == 0 else f"{'+' if r['Total'] > 0 else ''}{r['Total']}"
                st.markdown(f'<div class="podium-card"><div class="user-name">#{r["Rank"]} {r["User"]}</div><div class="podium-score">{disp}</div>{r["HTML"]}</div>', unsafe_allow_html=True)

        # --- 3. DISPLAY STANDINGS ---
        st.markdown("### STANDINGS")
        expanded_results = []
        for _, res in df.iterrows():
            row = {"Rank": res["Rank"], "User": res["User"], "Total": f"+{res['Total']}" if res['Total'] > 0 else ("E" if res['Total'] == 0 else res['Total'])}
            roster = TEAMS.get(res["User"], [])
            for i, p_name in enumerate(roster):
                p_key = p_name.lower()
                s_text = "-"
                if p_key in player_map:
                    s_val = player_map[p_key]['score']
                    s_text = "E" if s_val == 0 else f"{'+' if s_val > 0 else ''}{s_val}"
                row[f"Player {i+1}"] = f"{p_name} ({s_text})"
            expanded_results.append(row)

        st.dataframe(pd.DataFrame(expanded_results), hide_index=True, use_container_width=True)

        # --- 4. DISPLAY PRO LEADERBOARD ---
        st.markdown("### ⛳ US OPEN LIVE LEADERBOARD")
        st.dataframe(pd.DataFrame(pro_field).set_index("Pos"), use_container_width=True)

        # --- 5. MARKET SENTIMENT ---
        st.markdown("### 📊 WHO DID MOST PEOPLE BET ON?")
        counts = pd.Series(all_picks).value_counts()
        m_val = counts.max()
        s_html = '<div class="sentiment-box">'
        for name, count in counts.items():
            w = int((count / m_val) * 100)
            s_html += f'<div class="s-row"><div class="s-label"><span>{name}</span><span>{count} PICKS</span></div><div class="s-bar-bg"><div class="s-bar-fill" style="width:{w}%;"></div></div></div>'
        s_html += '</div>'
        st.write(s_html, unsafe_allow_html=True)

        # --- 6. THE HIVE MIND (MOVED TO BOTTOM) ---
        st.markdown("---")
        st.markdown("### 📊 MOST PICKED COMBINATIONS")
        col_a, col_b = st.columns(2)

        # Triplets logic
        triplet_counts = Counter([tuple(sorted(players)) for players in TEAMS.values()])
        exact_triplets = {k: v for k, v in triplet_counts.items() if v > 1}

        # Duos logic
        all_duos = []
        for players in TEAMS.values():
            all_duos.extend(combinations(sorted(players), 2))
        duo_counts = Counter(all_duos).most_common(5)

        with col_a:
            st.write("**Exact Same Team (3/3)**")
            if exact_triplets:
                for players, count in exact_triplets.items():
                    st.info(f"**{count} people** picked: {', '.join(players)}")
            else:
                st.write("Every team is unique!")

        with col_b:
            st.write("**Most Common Pairings (2/3)**")
            for duo, count in duo_counts:
                st.success(f"**{count} people** paired: {duo[0]} + {duo[1]}")
    else:
        st.error("Waiting for tournament data...")

if __name__ == "__main__":
    main()
    st.caption(f"Sync: {datetime.now().strftime('%H:%M:%S')}")
