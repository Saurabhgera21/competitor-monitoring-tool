import streamlit as st
from database import create_database, get_tracked_competitors
create_database()
st.set_page_config(page_title="App Diagnostic")
st.title("Competitor Monitor Diagnostic")
st.write("Database connection successful")
st.write("Tracked websites:", get_tracked_competitors())