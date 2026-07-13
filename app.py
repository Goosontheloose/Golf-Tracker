# --- 6. LEADERBOARD: ENTRY TRACKER ---
st.title("🏆 154th Open Championship")

try:
    sheet = get_sheet()
    entries = sheet.get_all_records()
    
    if entries:
        df_entries = pd.DataFrame(entries)
        
        # COUNT how many times each 'User' appears
        entry_counts = df_entries['User'].value_counts().reset_index()
        entry_counts.columns = ['User', 'Total Entries']
        
        st.subheader("Syndicate Entry Tracker")
        st.table(entry_counts)
        
        # OPTIONAL: Show the actual teams below the counts
        with st.expander("View All Submitted Rosters"):
            st.dataframe(df_entries, hide_index=True)
            
    else:
        st.info("No entries yet.")
except Exception as e:
    st.error(f"Cannot read sheet: {e}")
