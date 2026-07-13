import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 1. DATABASE CONNECTION ---
# This uses the secrets you just pasted into the Streamlit Dashboard
conn = st.connection("gsheets", type=GSheetsConnection)

# Replace this with your ACTUAL Google Sheet URL
SHEET_URL = "YOUR_SHEET_URL_HERE"

# --- 2. READ EXISTING DATA ---
# This replaces the old "get_teams(RAW_DATA)" function
try:
    # We read the sheet into a DataFrame
    existing_data = conn.read(spreadsheet=SHEET_URL)
    # Convert the Sheet rows into the TEAM format your app expects
    # We assume columns are: User, Player 1, Player 2, Player 3
    TEAMS = {}
    for _, row in existing_data.iterrows():
        TEAMS[row['User']] = [row['P1'], row['P2'], row['P3']]
except Exception as e:
    st.error("Could not connect to Google Sheets. Check your URL and Secrets.")
    TEAMS = {}

# --- 3. THE BETTING FORM (Sidebar) ---
# We put this in the sidebar so it doesn't clutter the leaderboard
with st.sidebar:
    st.header("🏆 ENTER THE SYNDICATE")
    
    # We fetch the pro list from your API so users can only pick real golfers
    # (Assumes your 'rows' variable from the API is already loaded)
    pro_names = [r.get('playerName', 'Unknown') for r in rows] if 'rows' in locals() else []
    pro_names.sort()

    with st.form("bet_form", clear_on_submit=True):
        u_name = st.text_input("Your Name / Entry Name")
        p1 = st.selectbox("Select Golfer 1", pro_names)
        p2 = st.selectbox("Select Golfer 2", pro_names)
        p3 = st.selectbox("Select Golfer 3", pro_names)
        
        submit = st.form_submit_button("Lock In Team")
        
        if submit:
            if u_name and p1 and p2 and p3:
                # Create a new row
                new_entry = pd.DataFrame([{
                    "User": u_name,
                    "P1": p1,
                    "P2": p2,
                    "P3": p3
                }])
                
                # Add to existing data and upload
                updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, data=updated_df)
                
                st.success(f"Team {u_name} is locked in!")
                st.balloons()
                st.rerun()
            else:
                st.warning("Please fill in all fields.")

# --- 4. REST OF YOUR APP ---
# Your existing scoring logic will now use the 'TEAMS' dict 
# we created in Step 2 above.
