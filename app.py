import streamlit as st
import requests
import pandas as pd
from datetime import datetime

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
AJ Hechter 1	Matt Fitzpatrick	Tyrrell Hatton	Min Woo Lee
AJ Hechter 2	Scottie Scheffler	Chris Gotterup	Cameron Smith
Anton (Entry 1)	Scottie Scheffler	Matt Fitzpatrick	Dustin Johnson
Anton (Entry 2)	Rory McIlroy	Tyrrell Hatton	Shane Lowry
Anton (Entry 3)	Justin Rose	Xander Schauffele	Bryson DeChambeau
Anton (Entry 4)	Scottie Scheffler	Rory McIlroy	Shane Lowry
Armand Entry 1	Scottie Scheffler	Rory McIlroy	Gary Woodland
Armand (Entry 3)	Scottie Scheffler	Matt Fitzpatrick	Shane Lowry
Armand (Entry 2)	Cameron Young	Tommy Fleetwood	Brian Harman
Bedekers 2	Rory McIlroy	Jon Rahm	Cameron Smith
Ben Jones (Entry 1)	Rory McIlroy	Ludvig Åberg	Corey Conners
Ben Jones (Entry 2)	Rory McIlroy	Cameron Young	Corey Conners
Ben Jones (Entry 3)	Russell Henley	Ludvig Åberg	Patrick Cantlay
Ben Jones(Entry 4)	Xander Schauffele	Aaron Rai	Wyndham Clark
Ben Ras (Entry 1)	Scottie Scheffler	Matt Fitzpatrick	Wyndham Clark
Ben Ras (Entry 2)	Chris Gotterup	Cameron Young	Bryson DeChambeau
Benno vd Westhuizen (Entry 1)	Scottie Scheffler	Cameron Young	Brooks Koepka
Benno vd Westhuizen (Entry 2)	Rory McIlroy	Bryson DeChambeau	Cameron Young
Billy Matthee	Scottie Scheffler	Ludvig Åberg	Kurt Kitayama
Braam Greyling 1	Scottie Scheffler	Cameron Young	Bryson DeChambeau
Braam Greyling 2	Rory McIlroy	Russell Henley	Wyndham Clark
Braam Greyling 3	Matt Fitzpatrick	Tommy Fleetwood	Patrick Cantlay
Braam Greyling 4	Scottie Scheffler	Rory McIlroy	Brooks Koepka
Braam Greyling 5	Russell Henley	Tyrrell Hatton	Tom Kim
Christiaan Daniels 1	Patrick Reed	Justin Thomas	Keegan Bradley
Christiaan Daniels 2	Scottie Scheffler	Sam Burns	Wyndham Clark
Corne van Wyk 1	Rory McIlroy	Tommy Fleetwood	Shane Lowry
Corne van Wyk 2	Scottie Scheffler	Xander Schauffele	Wyndham Clark
Cornel 1	Scottie Scheffler	Tommy Fleetwood	Bryson DeChambeau
Cornel 2	Rory McIlroy	Jon Rahm	Joaquin Niemann
Dean	Matt Fitzpatrick	Rory McIlroy	Shane Lowry
Dean Steinhobel (Entry 1)	Justin Rose	Xander Schauffele	Wyndham Clark
Dean Steinhobel (Entry 2)	Scottie Scheffler	Jon Rahm	Joaquin Niemann
Dean Steinhobel (Entry 3)	Justin Thomas	Dustin Johnson	Shane Lowry
Dean Steinhobel (Entry 4)	Jon Rahm	Jordan Spieth	Cameron Smith
Deon 1	Scottie Scheffler	Rory McIlroy	Patrick Cantlay
Deon 2	Scottie Scheffler	Xander Schauffele	Bryson DeChambeau
Amanda 1	Rory McIlroy	Tyrrell Hatton	Wyndham Clark
Deon Lappa	Shane Lowry	Justin Rose	Scottie Scheffler
Derick Kunz	Scottie Scheffler	Ben Kohles	Rory McIlroy
Derik (Entry 1)	Patrick Reed	Cameron Smith	Sam Burns
Derik (Entry 2)	Scottie Scheffler	Rory McIlroy	Bryson DeChambeau
Derik (Entry 3)	Scottie Scheffler	Matt Fitzpatrick	Justin Rose
Amanda 2	Scottie Scheffler	Cameron Young	Bryson DeChambeau
Donald (Entry 1)	Scottie Scheffler	Tyrrell Hatton	Jayden Schaper
Donald (Entry 2)	Bryson DeChambeau	Ludvig Åberg	Tommy Fleetwood
Donald (Entry 3)	Chris Kirk	Viktor Hovland	Xander Schauffele
DOSSA	Scottie Scheffler	Cameron Young	Brooks Koepka
Duncan (Entry 1)	Scottie Scheffler	Bryson DeChambeau	Xander Schauffele
Duncan (Entry 2)	Scottie Scheffler	Matt Fitzpatrick	Shane Lowry
Eckhard Jones	Scottie Scheffler	Min Woo Lee	Patrick Cantlay
Edwin (Entry 1)	Rory McIlroy	Matt Fitzpatrick	Brooks Koepka
Edwin (Entry 2)	Scottie Scheffler	Cameron Young	Bryson DeChambeau
Edwin (Entry 3)	Russell Henley	Justin Rose	Joaquin Niemann
Etienne Roodt	Jon Rahm	Xander Schauffele	Jordan Spieth
Eugene (Entry 1)	Scottie Scheffler	Xander Schauffele	Brooks Koepka
Eugene (Entry 2)	Rory McIlroy	Jon Rahm	Bryson DeChambeau
Eugene (Entry 3)	Cameron Young	Collin Morikawa	Wyndham Clark
Eugene (Entry 4)	Tommy Fleetwood	Ludvig Åberg	Joaquin Niemann
Eugene (Entry 5)	Justin Rose	Jayden Schaper	Du Plessis
Francois	Rory McIlroy	Tommy Fleetwood	Cameron Smith
Fred Bezuidenhout (Span 1)	Cameron Young	Matt Fitzpatrick	Max Greyserman
Fred Bezuidenhout (Span 2)	Tommy Fleetwood	Jon Rahm	Jake Knapp
Gerhard 1	Tommy Fleetwood	Rory McIlroy	Shane Lowry
Gerhard 2	Rory McIlroy	Scottie Scheffler	Patrick Cantlay
Gustav (Entry 1)	Patrick Reed	J.J. Spaun	Max Greyserman
Gustav (Entry 2)	Bryson DeChambeau	Rory McIlroy	Scottie Scheffler
Gustav (Entry 3)	Russell Henley	Tommy Fleetwood	Jordan Spieth
Gustav Smit	Cameron Young	Sam Burns	Jason Day
Hendri	Scottie Scheffler	Rory McIlroy	Brooks Koepka
Jaco Greeff (Entry 1)	Rory McIlroy	Scottie Scheffler	Brooks Koepka
Jaco Greeff (Entry 2)	Rory McIlroy	Cameron Young	Bryson DeChambeau
Jaco Greeff (Entry 3)	Scottie Scheffler	Jon Rahm	Wyndham Clark
Jaco Greeff (Entry 4)	Scottie Scheffler	Russell Henley	Wyndham Clark
Jaco Greeff (Entry 5)	Rory McIlroy	Scottie Scheffler	Wyndham Clark
Jacobus P	Rory McIlroy	Tommy Fleetwood	Keegan Bradley
Jason Bithrey	Scottie Scheffler	Rory McIlroy	Brooks Koepka
Johan Huyser	Rory McIlroy	Tommy Fleetwood	Jason Day
Johann Lubbe (Entry 1)	Tyrrell Hatton	Rory McIlroy	Shane Lowry
Johann Lubbe (Entry 2)	Tommy Fleetwood	Ludvig Åberg	Alex Smalley
Johann Lubbe (Entry 3)	Matt Fitzpatrick	Viktor Hovland	Nicolai Højgaard
Johann Lubbe (Entry 4)	Scottie Scheffler	Rory McIlroy	Keegan Bradley
Johnny Lubbe (Entry 1)	Scottie Scheffler	Rory McIlroy	Shane Lowry
Johnny Lubbe (Entry 2)	Scottie Scheffler	Tommy Fleetwood	Patrick Cantlay
Johnny Lubbe (Entry 3)	Rory McIlroy	Matt Fitzpatrick	Adam Scott
Johnny Lubbe (Entry 4)	Rory McIlroy	Jon Rahm	Joaquin Niemann
Kian	Scottie Scheffler	Ludvig Åberg	Bryson DeChambeau
Kobus Rossouw (Entry 1)	Scottie Scheffler	Rory McIlroy	Bryson DeChambeau
Kobus Rossouw (Entry 2)	Scottie Scheffler	Jon Rahm	Joaquin Niemann
Kobus Rossouw (Entry 3)	Scottie Scheffler	Ludvig Åberg	Min Woo Lee
Kobus Rossouw (Entry 4)	Rory McIlroy	Bryson DeChambeau	Joaquin Niemann
Kobus Rossouw (Entry 5)	Scottie Scheffler	Tommy Fleetwood	Shane Lowry
Lauren Coetser	Scottie Scheffler	Xander Schauffele	Joaquin Niemann
Leonie 	Ludvig Åberg	Viktor Hovland	Shane Lowry
Maricell Jones	Ludvig Åberg	Adam Scott	Bryson DeChambeau
Marina Jones (Entry 1)	Rory McIlroy	Xander Schauffele	Kurt Kitayama
Marina Jones (Entry 2)	Rory McIlroy	Bryson DeChambeau	Kurt Kitayama
Martin (1)	Scottie Scheffler	Matt Fitzpatrick	Brooks Koepka
Martin (2)	Rory McIlroy	Xander Schauffele	Bryson DeChambeau
Martin (3)	Jon Rahm	Tommy Fleetwood	Brooks Koepka
Martin (4)	Matt Fitzpatrick	Rory McIlroy	Alex Fitzpatrick
Martin Roelofse	Tommy Fleetwood	Patrick Reed	Wyndham Clark
Micaela Jones	Cameron Young	Maverick McNealy	Jason Day
Michael (Entry 1)	Rory McIlroy	Justin Rose	Bryson DeChambeau
Michael (Entry 2)	Scottie Scheffler	Cameron Young	Wyndham Clark
Morne Howell (Entry 1)	Rory McIlroy	Scottie Scheffler	Brooks Koepka
Morne Howell (Entry 2)	Tommy Fleetwood	Scottie Scheffler	Bryson DeChambeau
Nico Noeth	Rory McIlroy	Patrick Reed	Ryan Fox
Owen Rynners 1	Tyrrell Hatton	Jon Rahm	Bryson DeChambeau
Owen Rynners 3	Scottie Scheffler	Tommy Fleetwood	Shane Lowry
Owen Rynners 2	Rory McIlroy	Russell Henley	Corey Conners
Peet 1	Scottie Scheffler	Rory McIlroy	Patrick Reed
Peet 2	Scottie Scheffler	Rory McIlroy	Brooks Koepka
Pierre Rynners (Entry 1)	Scottie Scheffler	Xander Schauffele	Brian Harman
Pierre Rynners (Entry 2)	Justin Rose	Sam Burns	Jason Day
Pieter Rossouw	Tommy Fleetwood	Bryson DeChambeau	Sam Burns
Ralf Grotsch (Entry 4)	J.J. Spaun	Sam Burns	Scottie Scheffler
Ralf Grötsch (Entry 1)	Brooks Koepka	Tommy Fleetwood	Tyrrell Hatton
Ralf Grötsch (Entry 2)	Scottie Scheffler	Xander Schauffele	Jon Rahm
Ralf Grötsch (Entry 3)	Cameron Young	Bud Cauley	Rory McIlroy
Ranon Fouche	Scottie Scheffler	Xander Schauffele	Bryson DeChambeau
Reinhardt Uys	Tommy Fleetwood	Brooks Koepka	Jake Knapp
Reon Cronje	Scottie Scheffler	Justin Rose	Nicolai Højgaard
Rikus Hattingh	Matt Fitzpatrick	Tommy Fleetwood	Gary Woodland
Robert	Scottie Scheffler	J.J. Spaun	Rory McIlroy
Robert 2	Scottie Scheffler	Jon Rahm	Joaquin Niemann
Robert 3	Scottie Scheffler	Tyrrell Hatton	Patrick Cantlay
Rowan (Entry 1)	Scottie Scheffler	Russell Henley	Shane Lowry
Rowan (Entry 2)	Xander Schauffele	Matt Fitzpatrick	Sahith Theegala
Roy Coetser	Scottie Scheffler	Chris Gotterup	Jason Day
Ruan Brits	Scottie Scheffler	Tommy Fleetwood	Shane Lowry
Shaun Rynners	Rory McIlroy	Tommy Fleetwood	Wyndham Clark
Tereza (Entry 1)	Justin Rose	Aaron Rai	Jason Day
Tereza (Entry 2)	Ludvig Åberg	Si Woo Kim	Patrick Cantlay
Theuns (Entry 2)	Jon Rahm	Scottie Scheffler	Bryson DeChambeau
Theuns (Entry 3)	Scottie Scheffler	Jon Rahm	Brooks Koepka
Theuns Greyling	Scottie Scheffler	Rory McIlroy	Brooks Koepka
Theuns Greyling	Scottie Scheffler	Matt Fitzpatrick	Bryson DeChambeau
Tjaart	Cameron Young	Tyrrell Hatton	Alejandro Tosti
Tobie	Justin Rose	Ludvig Åberg	Bryson DeChambeau
Tyrone 1	Cameron Young	Wyndham Clark	Xander Schauffele
Tyrone 2	Cameron Young	Scottie Scheffler	Bryson DeChambeau
William Bithrey	Rory McIlroy	Justin Rose	Bryson DeChambeau
Wynand Kruger (Entry 1)	Scottie Scheffler	Tommy Fleetwood	Bryson DeChambeau
Wynand Kruger (Entry 2)	Rory McIlroy	Ludvig Åberg	Patrick Cantlay
ZT Project (Entry 1)	Scottie Scheffler	Tommy Fleetwood	Shane Lowry
ZT Project (Entry 2)	Cameron Young	Matt Fitzpatrick	Cameron Smith
ZT Project (Entry 3)	Rory McIlroy	Justin Rose	Shane Lowry
ZT Project (Entry 4)	Tyrrell Hatton	Collin Morikawa	Min Woo Lee
ZT Project (Entry 5)	Jon Rahm	Ludvig Åberg	Shane Lowry
ZT Project (Entry 6)	Xander Schauffele	Patrick Reed	Cameron Smith
ZT Project (Entry 7)	Patrick Reed	Matt Fitzpatrick	Shane Lowry
ZT Project (Entry 8)	Jon Rahm	Justin Rose	Corey Conners
ZT Project (Entry 9)	Matt Fitzpatrick	Xander Schauffele	J.T. Poston
Frederik	Rory McIlroy	Bryson DeChambeau	Scottie Scheffler

"""
def get_teams(raw_text):
    teams_dict = {}
    lines = raw_text.strip().split('\n')
    for line in lines:
        parts = line.split('\t') # Split by Excel tabs
        if len(parts) >= 2:
            user = parts[0].strip()
            # Everything after the first column is a golfer
            golfers = [g.strip() for g in parts[1:] if g.strip()]
            teams_dict[user] = golfers
    return teams_dict

TEAMS = get_teams(RAW_DATA)
def parse_score(val):
    if not val or str(val).upper() in ["E", "EVEN", "CUT"]: return 0
    try: return int(str(val).replace("+", ""))
    except: return 0

@st.cache_data(ttl=600)
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
                
                # 1. Check if the player actually exists in the API data
                if p.lower() in player_map:
                    p_data = player_map[p.lower()]
                    score_val = p_data['score']
                    thru_val = p_data['thru']
                    total += score_val # Add to team total
                    # Format the score display
                    s = "E" if score_val == 0 else f"{'+' if score_val > 0 else ''}{score_val}"
                else:
                    # 2. If NOT found, set display to "Not Found" and thru to "???"
                    s = "Not Found"
                    thru_val = "???"
                    # (Note: total stays the same, effectively treating them as 0/Even)

                html += f'<div class="player-row"><span>{p}</span><span><b style="color: {"red" if s == "Not Found" else "inherit"}">{s}</b> <small>[{thru_val}]</small></span></div>'
            
            results.append({"User": user, "Total": total, "HTML": html})

        df = pd.DataFrame(results).sort_values("Total")
        df.insert(0, 'Rank', range(1, len(df) + 1))

        # 1. CHAMPIONSHIP FLIGHT (TOP 5)
        st.markdown("### TOP 5 LEADERS")
        cols = st.columns(5)
        for i, (_, r) in enumerate(df.head(5).iterrows()):
            with cols[i]:
                disp = "E" if r['Total'] == 0 else f"{'+' if r['Total'] > 0 else ''}{r['Total']}"
                st.markdown(f'<div class="podium-card"><div class="user-name">#{r["Rank"]} {r["User"]}</div><div class="podium-score">{disp}</div>{r["HTML"]}</div>', unsafe_allow_html=True)

        # 2. DERBY STANDINGS (Cleaned Table)
            st.markdown("### STANDINGS")
        
        expanded_results = []
        # CHANGE: We now use 'df.iterrows()' to get the data that includes the Rank
        for _, res in df.iterrows():
            row = {
                "Rank": res["Rank"],
                "User": res["User"],
                "Total": f"+{res['Total']}" if res['Total'] > 0 else ("E" if res['Total'] == 0 else res['Total'])
            }
            
            # Get the roster for this user
            roster = TEAMS.get(res["User"], [])
            for i, p_name in enumerate(roster):
                p_key = p_name.lower()
                if p_key in player_map:
                    p_data = player_map[p_key]
                    s_val = p_data['score']
                    s_text = "E" if s_val == 0 else f"{'+' if s_val > 0 else ''}{s_val}"
                else:
                    s_text = "-"
                row[f"Player {i+1}"] = f"{p_name} ({s_text})"
            
            expanded_results.append(row)

        standings_df = pd.DataFrame(expanded_results)
        st.dataframe(standings_df, hide_index=True, use_container_width=True)

        # 3. MASTER FIELD LEADERBOARD
        st.markdown("### ⛳ US OPEN LIVE LEADERBOARD")
        st.dataframe(pd.DataFrame(pro_field).set_index("Pos"), use_container_width=True)

        # 4. MARKET SENTIMENT (Bottom Section)
        st.markdown("### 📊 WHO DID MOST PEOPLE BET ON?")
        counts = pd.Series(all_picks).value_counts()
        m_val = counts.max()
        
        s_html = '<div class="sentiment-box">'
        for name, count in counts.items():
            w = int((count / m_val) * 100)
            s_html += f'<div class="s-row"><div class="s-label"><span>{name}</span><span>{count} PICKS</span></div><div class="s-bar-bg"><div class="s-bar-fill" style="width:{w}%;"></div></div></div>'
        s_html += '</div>'
        st.write(s_html, unsafe_allow_html=True)

    else:
        st.error("Waiting for tournament data...")

if __name__ == "__main__":
    main()
    st.caption(f"Sync: {datetime.now().strftime('%H:%M:%S')}")
