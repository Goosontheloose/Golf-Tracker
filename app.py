import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from collections import Counter      
from itertools import combinations    
import re

# --- 1. SETTINGS & BRANDING ---
st.set_page_config(page_title="The US OPEN 2026", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap');
    .stApp { background-color: #F5F5F4 !important; }
    h1, h2, h3, p, span, th, td, .stMarkdown { color: #064E3B !important; font-family: 'Inter', sans-serif; }
    .podium-card {
        padding: 1.2rem; border: 4px solid #064E3B; background-color: white !important; 
        box-shadow: 6px 6px 0px #064E3B; margin-bottom: 20px; display: flex; flex-direction: column;
    }
    .podium-score { font-weight: 900; color: #064E3B !important; font-size: 2.5rem; line-height: 1; margin: 5px 0; }
    .user-name { text-transform: uppercase; font-weight: 900; color: #064E3B !important; font-size: 1rem; }
    .player-row { font-size: 0.85rem; display: flex; justify-content: space-between; border-bottom: 1px solid #eee; padding: 6px 0; color: #333 !important; }
    .sentiment-box { background: white; border: 4px solid #064E3B; padding: 20px; box-shadow: 8px 8px 0px #EAB308; margin: 20px 0; }
    .s-row { margin-bottom: 15px; }
    .s-label { font-weight: 900; text-transform: uppercase; font-size: 0.8rem; display: flex; justify-content: space-between; margin-bottom: 4px; }
    .s-bar-bg { background: #eee; height: 12px; border: 1px solid #064E3B; width: 100%; }
    .s-bar-fill { background: #064E3B; height: 100%; }
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th { color: #064E3B !important; }
    @media (max-width: 768px) {
        [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; min-width: 100% !important; }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA PARSING ---
RAW_DATA = """
Ettienne Bedeker	Scottie Scheffler	Rory McIlroy	Alex Fitzpatrick
Brendon	Jon Rahm	Jake Knapp	Brooks Koepka
Heino Noeth	Rory McIlroy	Tommy Fleetwood	Joaquin Niemann
Thomas Potgieter	Scottie Scheffler	Russell Henley	Patrick Cantlay
Thomas Potgieter (1)	Tommy Fleetwood	Hideki Matsuyama	Corey Conners
Thomas Potgieter (2)	Rory McIlroy	Jon Rahm	Bryson DeChambeau
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
Corne van Wyk (1)	Scottie Scheffler	Xander Schauffele	Wyndham Clark
Reinhardt Uys	Tommy Fleetwood	Brooks Koepka	Jake Knapp
Tyronne	Cameron Young	Xander Schauffele	Wyndham Clark
Tyronne (1)	Cameron Young	Scottie Scheffler	Bryson DeChambeau
Tobie	Justin Rose	Ludvig Åberg	Bryson DeChambeau
Tereza Windell	Scottie Scheffler	Tommy Fleetwood	Bryson DeChambeau
Tereza Windell (1)	Rory McIlroy	Jon Rahm	Joaquin Niemann
Cornel Windell	Justin Rose	Aaron Rai	Jason Day
Cornel Windell (1)	Ludvig Åberg	Si Woo Kim	Patrick Cantlay
Theuns Greyling (1)	Jon Rahm	Scottie Scheffler	Bryson DeChambeau
Theuns Greyling (2)	Jon Rahm	Scottie Scheffler	Brooks Koepka
Jacobusp1	Rory McIlroy	Tommy Fleetwood	Keegan Bradley
Robert	Scottie Scheffler	Jon Rahm	Joaquin Niemann
Ettienne Bedeker (1)	Rory McIlroy	Jon Rahm	Cameron Smith
Anton 	Scottie Scheffler	Matt Fitzpatrick	Dustin Johnson
Anton (1)	Rory McIlroy	Tyrrell Hatton	Shane Lowry
Anton (2)	Justin Rose	Xander Schauffele	Bryson DeChambeau
Anton (3)	Scottie Scheffler	Rory McIlroy	Shane Lowry
Braam Greyling	Scottie Scheffler	Cameron Young	Bryson DeChambeau
Braam Greyling (1)	Rory McIlroy	Russell Henley	Wyndham Clark
Braam Greyling (2)	Matt Fitzpatrick	Tommy Fleetwood	Patrick Cantlay
Braam Greyling (3)	Scottie Scheffler	Rory McIlroy	Brooks Koepka
Braam Greyling (4)	Russell Henley	Tyrrell Hatton	Tom Kim
Robert (1)	Scottie Scheffler	Tyrrell Hatton	Patrick Cantlay
Pieter Rossouw	Tommy Fleetwood	Sam Burns	Bryson DeChambeau
AJ Hechter	Scottie Scheffler	Chris Gotterup	Cameron Smith
Ben Jones	Rory McIlroy	Ludvig Åberg	Corey Conners
Ben Jones (1)	Rory McIlroy	Cameron Young	Corey Conners
Ben Jones (2)	Russell Henley	Ludvig Åberg	Patrick Cantlay
Ben Jones (3)	Xander Schauffele	Aaron Rai	Wyndham Clark
Marina Jones	Rory McIlroy	Xander Schauffele	Kurt Kitayama
Marina Jones (1)	Rory McIlroy	Bryson DeChambeau	Kurt Kitayama
Benno vd Westhuizen	Scottie Scheffler	Cameron Young	Brooks Koepka
Benno vd Westhuizen (1)	Rory McIlroy	Cameron Young	Bryson DeChambeau
Rowan	Scottie Scheffler	Russell Henley	Shane Lowry
Rowan (1)	Xander Schauffele	Matt Fitzpatrick	Sahith Theegala
Gustav Smit	Patrick Reed	J.J. Spaun	Max Greyserman
Gustav Smit (1)	Rory McIlroy	Scottie Scheffler	Bryson DeChambeau
Gustav Smit (2)	Russell Henley	Tommy Fleetwood	Jordan Spieth
Hendri	Scottie Scheffler	Rory McIlroy	Brooks Koepka
Martin Roelofse	Tommy Fleetwood	Patrick Reed	Wyndham Clark
Gustav Smit (3)	Cameron Young	Sam Burns	Jason Day
Peet	Scottie Scheffler	Rory McIlroy	Rickie Fowler
Ben Ras	Scottie Scheffler	Matt Fitzpatrick	Wyndham Clark
Armand	Scottie Scheffler	Matt Fitzpatrick	Shane Lowry
Armand (1)	Cameron Young	Tommy Fleetwood	Brian Harman
Dean Steinhobel	Justin Rose	Xander Schauffele	Wyndham Clark
Dean Steinhobel (1)	Scottie Scheffler	Jon Rahm	Joaquin Niemann
Dean Steinhobel (2)	Justin Thomas	Dustin Johnson	Shane Lowry
Dean Steinhobel (3)	Jon Rahm	Jordan Spieth	Cameron Smith
Ben Ras (1)	Chris Gotterup	Cameron Young	Bryson DeChambeau
Fred Bezuidenhout	Cameron Young	Matt Fitzpatrick	Max Greyserman
Fred Bezuidenhout (1)	Tommy Fleetwood	Jon Rahm	Jake Knapp
Roy Coetser	Scottie Scheffler	Chris Gotterup	Jason Day
Kobus Rossouw	Scottie Scheffler	Rory McIlroy	Bryson DeChambeau
Kobus Rossouw (1)	Scottie Scheffler	Jon Rahm	Joaquin Niemann
Kobus Rossouw (2)	Scottie Scheffler	Ludvig Åberg	Min Woo Lee
Kobus Rossouw (3)	Rory McIlroy	Bryson DeChambeau	Joaquin Niemann
Kobus Rossouw (4)	Scottie Scheffler	Tommy Fleetwood	Shane Lowry
Tjaart	Cameron Young	Tyrrell Hatton	Alejandro Tosti
Leonie Coetser	Ludvig Åberg	Viktor Hovland	Shane Lowry
Martin Coetser	Scottie Scheffler	Matt Fitzpatrick	Brooks Koepka
Martin Coetser (1)	Rory McIlroy	Xander Schauffele	Bryson DeChambeau
Martin Coetser (2)	Jon Rahm	Tommy Fleetwood	Brooks Koepka
Martin Coetser (3)	Matt Fitzpatrick	Rory McIlroy	Alex Fitzpatrick
Pierre Rynners	Scottie Scheffler	Xander Schauffele	Brian Harman
Owen Rynners	Scottie Scheffler	Tommy Fleetwood	Shane Lowry
Owen Rynners (1)	Rory McIlroy	Russell Henley	Corey Conners
Shaun Rynners	Rory McIlroy	Tommy Fleetwood	Wyndham Clark
Michael	Rory McIlroy	Justin Rose	Bryson DeChambeau
Michael (1)	Scottie Scheffler	Cameron Young	Wyndham Clark
Etienne Roodt (1)	Jon Rahm	Xander Schauffele	Jordan Spieth
Deon Lappa	Justin Rose	Scottie Scheffler	Shane Lowry
Reon Cronje	Scottie Scheffler	Justin Rose	Nicolai Hojgaard
Kian	Scottie Scheffler	Ludvig Åberg	Bryson DeChambeau
Derik	Patrick Reed	Sam Burns	Cameron Smith
Derik (1)	Scottie Scheffler	Rory McIlroy	Bryson DeChambeau
Derik (2)	Scottie Scheffler	Matt Fitzpatrick	Bryson DeChambeau
ZT Project Management	Scottie Scheffler	Tommy Fleetwood	Shane Lowry
ZT Project Management (1)	Cameron Young	Matt Fitzpatrick	Cameron Smith
ZT Project Management (2)	Rory McIlroy	Justin Rose	Shane Lowry
ZT Project Management (3)	Tyrrell Hatton	Collin Morikawa	Min Woo Lee
ZT Project Management (4)	Jon Rahm	Ludvig Åberg	Shane Lowry
ZT Project Management (5)	Xander Schauffele	Patrick Reed	Cameron Smith
ZT Project Management (6)	Patrick Reed	Matt Fitzpatrick	Shane Lowry
ZT Project Management (7)	Jon Rahm	Justin Rose	Corey Conners
ZT Project Management (8)	Matt Fitzpatrick	Xander Schauffele	J.T. Poston
Nico Noeth	Rory McIlroy	Patrick Reed	Ryan Fox
Wynand	Scottie Scheffler	Tommy Fleetwood	Bryson DeChambeau
Pierre Rynners (1)	Justin Rose	Sam Burns	Jason Day
Edwin	Rory McIlroy	Matt Fitzpatrick	Brooks Koepka
Edwin (1)	Scottie Scheffler	Cameron Young	Bryson DeChambeau
Edwin (2)	Russell Henley	Justin Rose	Joaquin Niemann
Frederik	Rory McIlroy	Scottie Scheffler	Bryson DeChambeau
Ralf Grotsch	Tommy Fleetwood	Tyrrell Hatton	Brooks Koepka
Johann Lubbe	Tyrrell Hatton	Rory McIlroy	Shane Lowry
Johann Lubbe (1)	Tommy Fleetwood	Ludvig Åberg	Alex Smalley
Johann Lubbe (2)	Matt Fitzpatrick	Viktor Hovland	Nicolai Hojgaard
Dean	Matt Fitzpatrick	Rory McIlroy	Shane Lowry
Ralf Grotsch (1)	Cameron Young	Rory McIlroy	Bud Cauley
Jaco Greeff	Rory McIlroy	Scottie Scheffler	Brooks Koepka
Jaco Greeff (1)	Rory McIlroy	Cameron Young	Bryson DeChambeau
Jaco Greeff (2)	Scottie Scheffler	Jon Rahm	Wyndham Clark
Jaco Greeff (3)	Scottie Scheffler	Russell Henley	Wyndham Clark
Jaco Greeff (4)	Rory McIlroy	Scottie Scheffler	Wyndham Clark
Morne Howell	Rory McIlroy	Scottie Scheffler	Brooks Koepka
Morne Howell (1)	Tommy Fleetwood	Scottie Scheffler	Bryson DeChambeau
Johnny Lubbe	Scottie Scheffler	Rory McIlroy	Shane Lowry
Johnny Lubbe (1)	Scottie Scheffler	Tommy Fleetwood	Patrick Cantlay
Johnny Lubbe (2)	Rory McIlroy	Matt Fitzpatrick	Adam Scott
Johnny Lubbe (3)	Rory McIlroy	Jon Rahm	Joaquin Niemann
Donald	Scottie Scheffler	Tyrrell Hatton	Jayden Schaper
Donald (1)	Ludvig Åberg	Tommy Fleetwood	Bryson DeChambeau
Donald (2)	Viktor Hovland	Xander Schauffele	Chris Kirk
Wynand Kruger	Scottie Scheffler	Tommy Fleetwood	Bryson DeChambeau
Wynand Kruger (1)	Rory McIlroy	Ludvig Åberg	Patrick Cantlay
Micaela Jones	Cameron Young	Maverick McNealy	Jason Day
Eckhard Jones	Scottie Scheffler	Min Woo Lee	Patrick Cantlay
Maricell Jones	Ludvig Åberg	Adam Scott	Bryson DeChambeau
Theuns Greyling (3)	Scottie Scheffler	Rory McIlroy	Brooks Koepka
Dossa	Scottie Scheffler	Cameron Young	Brooks Koepka
Eugene	Scottie Scheffler	Xander Schauffele	Brooks Koepka
Eugene (1)	Rory McIlroy	Jon Rahm	Bryson DeChambeau
Eugene (2)	Cameron Young	Collin Morikawa	Wyndham Clark
Eugene (3)	Tommy Fleetwood	Ludvig Åberg	Joaquin Niemann
Owen Rynners (2)	Tyrrell Hatton	Jon Rahm	Bryson DeChambeau
Rikus Hattingh	Matt Fitzpatrick	Tommy Fleetwood	Gary Woodland
Eugene (4)	Justin Rose	Jayden Schaper	Hennie du Plessis
Christiaan Daniels	Patrick Reed	Justin Thomas	Keegan Bradley
Christiaan Daniels (1)	Scottie Scheffler	Sam Burns	Wyndham Clark
Lauren Coetser	Scottie Scheffler	Xander Schauffele	Joaquin Niemann
Johann Lubbe (3)	Scottie Scheffler	Rory McIlroy	Keegan Bradley
Derick Kunz	Scottie Scheffler	Rory McIlroy	Ben Kohles
AJ Hechter (1)	Matt Fitzpatrick	Tyrrell Hatton	Min Woo Lee
Duncan Stevens	Scottie Scheffler	Xander Schauffele	Bryson DeChambeau
Duncan Stevens (1)	Scottie Scheffler	Matt Fitzpatrick	Shane Lowry
Francois	Rory McIlroy	Tommy Fleetwood	Cameron Smith
William Bithrey	Rory McIlroy	Justin Rose	Bryson DeChambeau
Jason Bithrey	Scottie Scheffler	Rory McIlroy	Brooks Koepka
Deon Labuschagne	Scottie Scheffler	Rory McIlroy	Patrick Cantlay
Deon Labuschagne (1)	Scottie Scheffler	Xander Schauffele	Bryson DeChambeau
Amanda	Rory McIlroy	Tyrrell Hatton	Wyndham Clark
Amanda (1)	Scottie Scheffler	Cameron Young	Bryson DeChambeau
Armand (2)	Scottie Scheffler	Rory McIlroy	Gary Woodland
Billy Matthee	Scottie Scheffler	Ludvig Åberg	Kurt Kitayama
Johan Huyser	Rory McIlroy	Tommy Fleetwood	Jason Day
Gerhard	Tommy Fleetwood	Rory McIlroy	Shane Lowry
Gerhard (1)	Rory McIlroy	Scottie Scheffler	Patrick Cantlay
Christo Killian	Collin Morikawa	Akshay Bhatia	Patrick Cantlay
Christo Killian (1)	Akshay Bhatia	Sam Burns	Jason Day
Christiaan	Jon Rahm	Tyrrell Hatton	Joaquin Niemann
Christiaan (1)	Jon Rahm	Scottie Scheffler	Bryson DeChambeau
Christiaan (2)	Rory McIlroy	Ludvig Åberg	Joaquin Niemann
Ettienne Bedeker (2)	Sam Burns	Cameron Young	Brooks Koepka
Ettienne Bedeker (3)	Scottie Scheffler	Rory McIlroy	Brian Harman
Ettienne Bedeker (4)	Matt Fitzpatrick	Xander Schauffele	Cameron Smith
Tinus Steyn	Scottie Scheffler	Rory McIlroy	Bryson DeChambeau
Tinus Steyn (1)	Scottie Scheffler	Jon Rahm	Brooks Koepka
Tinus Steyn (2)	Rory McIlroy	Cameron Young	Bryson DeChambeau
Cornel Windell (2)	Scottie Scheffler	Rory McIlroy	Joaquin Niemann
Frederik (1)	Matt Fitzpatrick	Tyrrell Hatton	Joaquin Niemann
"""

def get_teams(raw_text):
    teams_dict = {}
    lines = raw_text.strip().split('\n')
    for line in lines:
        parts = re.split(r'\t|\s{2,}', line.strip())
        if len(parts) >= 2:
            user = parts[0].strip()
            golfers = [g.strip() for g in parts[1:] if g.strip()]
            teams_dict[user] = golfers
    return teams_dict

def parse_score(val):
    if val is None or str(val).upper() in ["E", "EVEN", "CUT", "-"]: return 0
    try: return int(str(val).replace("+", ""))
    except: return 0

def get_round_val(player_dict, round_num):
    rounds = player_dict.get('rounds', [])
    if len(rounds) >= round_num:
        val = rounds[round_num-1].get('scoreToPar')
        if val is None or str(val).upper() in ["-", "E", "EVEN"]: return 0
        return int(val)
    return 0

def get_round_dream_team(rows, round_num):
    scored_pros = []
    for r in rows:
        r_score = get_round_val(r, round_num)
        scored_pros.append({
            "name": f"{r.get('firstName', '')} {r.get('lastName', '')}",
            "score": r_score
        })
    return sorted(scored_pros, key=lambda x: x['score'])[:3]

@st.cache_data(ttl=300)
def get_data():
    # 1. Use /leaderboard instead of /schedule
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"
    
    # 2. Keep parameters here only
    params = {"orgId": "1", "tournId": "026", "year": "2026"}
    
    headers = {
        "X-RapidAPI-Key": "d67535ff26msh8cb52fc728cc02dp1a972djsnabc60d44defa",
        "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"
    }
    
    try:
        r = requests.get(url, headers=headers, params=params)
        return r.json().get('leaderboardRows', [])
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return []

TEAMS = get_teams(RAW_DATA)

def main():
    st.markdown("<h1>🏆 US OPEN 2026 PREDICTIONS</h1>", unsafe_allow_html=True)
    rows = get_data()
    
    if rows:
        player_map = {}
        pro_field = []
        all_picks = []

        for r in rows:
            f = r.get('firstName', '')
            l = r.get('lastName', '')
            name = f"{f} {l}".strip()
            score = parse_score(r.get('total', '0'))
            thru = r.get('thru', 'F')
            
            player_map[name.lower()] = {
                "score": score, "thru": thru,
                "r1": get_round_val(r, 1), "r2": get_round_val(r, 2),
                "r3": get_round_val(r, 3), "r4": get_round_val(r, 4)
            }
            pro_field.append({"Pos": r.get('position', '-'), "Player": name, "Score": score, "Thru": thru})

        results = []
        for user, roster in TEAMS.items():
            total = 0
            html_rows = ""
            for p in roster:
                all_picks.append(p)
                p_key = p.lower()
                if p_key in player_map:
                    p_data = player_map[p_key]
                    s_val = p_data['score']
                    total += s_val
                    s_txt = "E" if s_val == 0 else f"{'+' if s_val > 0 else ''}{s_val}"
                    t_txt = p_data['thru']
                else:
                    s_txt, t_txt = "???", "???"
                html_rows += f'<div class="player-row"><span>{p}</span><span><b>{s_txt}</b> <small>[{t_txt}]</small></span></div>'
            results.append({"User": user, "Total": total, "HTML": html_rows})

        df = pd.DataFrame(results).sort_values("Total")
        df.insert(0, 'Rank', range(1, len(df) + 1))

        # --- 1. PODIUM CARDS ---
        st.markdown("### TOP 5 LEADERS")
        cols = st.columns(5)
        for i, (_, r) in enumerate(df.head(5).iterrows()):
            with cols[i]:
                disp = "E" if r['Total'] == 0 else f"{'+' if r['Total'] > 0 else ''}{r['Total']}"
                st.markdown(f'<div class="podium-card"><div class="user-name">#{r["Rank"]} {r["User"]}</div><div class="podium-score">{disp}</div>{r["HTML"]}</div>', unsafe_allow_html=True)

        # --- 2. FULL STANDINGS TABLE ---
        st.markdown("### LEADERBOARD")
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

        # --- 3. PRO FIELD TABLE ---
        st.markdown("### ⛳ LIVE FIELD")
        st.dataframe(pd.DataFrame(pro_field), hide_index=True, use_container_width=True)

        # --- 4. ROUND ANALYSIS (MOVED UP) ---
        st.markdown("---")
        st.markdown("### 📊 ROUND ANALYSIS")
        selected_round = st.radio("Select Round", [1, 2, 3, 4], horizontal=True, format_func=lambda x: f"Round {x}")
        col_dream, col_burner = st.columns(2)
        
        with col_dream:
            st.write(f"**🌟 Round {selected_round} Dream Team (Pros)**")
            dream_pros = get_round_dream_team(rows, selected_round)
            for p in dream_pros:
                s_fmt = f"{p['score']:+}" if p['score'] != 0 else "E"
                st.success(f"⭐ **{p['name']}** ({s_fmt})")

        with col_burner:
            st.write(f"**🔥 Round {selected_round} Best Players(Participants)**")
            round_results = []
            for user, roster in TEAMS.items():
                r_total = 0
                for p_name in roster:
                    p_data = player_map.get(p_name.lower(), {})
                    r_total += p_data.get(f"r{selected_round}", 0)
                round_results.append({"User": user, "Score": r_total})
            st.dataframe(pd.DataFrame(round_results).sort_values("Score").head(5), hide_index=True, use_container_width=True)

        # --- 5. MARKET SENTIMENT ---
        st.markdown("---")
        st.markdown("### 📊 MARKET SENTIMENT")
        counts = pd.Series(all_picks).value_counts()
        m_val = counts.max()
        s_html = '<div class="sentiment-box">'
        for name, count in counts.items():
            w = int((count / m_val) * 100)
            s_html += f'<div class="s-row"><div class="s-label"><span>{name}</span><span>{count} PICKS</span></div><div class="s-bar-bg"><div class="s-bar-fill" style="width:{w}%;"></div></div></div>'
        s_html += '</div>'
        st.write(s_html, unsafe_allow_html=True)

        # --- 6. COMBINATIONS ---
        st.markdown("### 📊 MOST PICKED COMBINATIONS")
        col_a, col_b = st.columns(2)
        triplet_counts = Counter([tuple(sorted(players)) for players in TEAMS.values()])
        exact_triplets = {k: v for k, v in triplet_counts.items() if v > 1}
        all_duos = []
        for players in TEAMS.values():
            all_duos.extend(combinations(sorted(players), 2))
        duo_counts = Counter(all_duos).most_common(5)

        with col_a:
            st.write("**Exact Same Team (3/3)**")
            if exact_triplets:
                for players, count in exact_triplets.items():
                    st.info(f"**{count} people** picked: {', '.join(players)}")
            else: st.write("Every team is unique!")
        with col_b:
            st.write("**Most Common Pairings (2/3)**")
            for duo, count in duo_counts:
                st.success(f"🤝 **{count} people** paired: {duo[0]} + {duo[1]}")

    else:
        st.error("Waiting for tournament data...")

if __name__ == "__main__":
    main()
