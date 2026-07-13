# --- 3. CONNECTION SETUP ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 4. SIDEBAR ENTRY FORM ---
with st.sidebar:
    st.header("Team Entry")
    with st.form("entry_form", clear_on_submit=True):
        u_name = st.text_input("Your Name / Team Name")
        p1 = st.selectbox("Elite Pick 1", ELITE_30)
        p2 = st.selectbox("Elite Pick 2", [p for p in ELITE_30 if p != p1])
        p3 = st.selectbox("Wildcard Pick", WILDCARD_FIELD)
        submitted = st.form_submit_button("SUBMIT TEAM")
        
        if submitted:
            if not u_name:
                st.error("Please enter a name.")
            else:
                try:
                    # 1. Fetch current data
                    existing_data = conn.read(spreadsheet=SHEET_URL, usecols=[0][1](https://docs.streamlit.io/develop/api-reference/connections/st.connection.gsheets "inline-citation")[2][3])
                    
                    # 2. Create the new row
                    new_entry = pd.DataFrame([{
                        "User": u_name,
                        "P1": p1,
                        "P2": p2,
                        "P3": p3
                    }])
                    
                    # 3. Combine and Update
                    updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, data=updated_df)
                    
                    st.success(f"Team {u_name} is locked in!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error saving to Google Sheets: {e}")
