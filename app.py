# --- NEW: Fetch Full Field for Dropdowns ---
@st.cache_data(ttl=3600) # Only refresh the roster once an hour
def get_full_field():
    url = "https://live-golf-data.p.rapidapi.com/tournament"
    # Using 2024 US Open (026) as placeholder until 2025/2026 data is live
    params = {"orgId": "1", "tournId": "026", "year": "2024"}
    headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        # Extract full names from the players list
        players = [f"{p['firstName']} {p['lastName']}".strip() for p in data.get('players', [])]
        return sorted(list(set(players))) # Remove duplicates and sort
    except:
        return ["Rory McIlroy", "Scottie Scheffler", "Xander Schauffele"] # Fallback

# --- UPDATED SIDEBAR ---
full_field = get_full_field()
# Filter out Top 30 from the wildcard list to keep it organized
wildcard_options = [p for p in full_field if p not in TOP_30]

with st.sidebar:
    st.header("THE TERMINAL")
    st.info("Pick 2 from the Top 30. Pick 1 Wildcard from the full field.")
    
    with st.form("entry_form"):
        u_name = st.text_input("Entry Name")
        
        st.write("---")
        st.subheader("Elite Picks (Top 30)")
        p1 = st.selectbox("Elite Player 1", TOP_30)
        p2 = st.selectbox("Elite Player 2", [p for p in TOP_30 if p != p1])
        
        st.write("---")
        st.subheader("The Wildcard")
        # Now a dropdown instead of a text box
        p3 = st.selectbox("Wildcard Selection", wildcard_options if wildcard_options else ["No players found"])
        
        submit = st.form_submit_button("LOCK IN SYNDICATE")
        
        if submit and u_name:
            current_df = conn.read(spreadsheet=SHEET_URL)
            new_row = pd.DataFrame([{"User": u_name, "P1": p1, "P2": p2, "P3": p3}])
            updated_df = pd.concat([current_df, new_row], ignore_index=True)
            conn.update(spreadsheet=SHEET_URL, data=updated_df)
            st.success(f"Confirmed: {u_name} is locked in!")
            st.cache_data.clear()
