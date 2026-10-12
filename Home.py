import streamlit as st

st.set_page_config(page_title="Hotel Bookings — Home", page_icon="🏨")

st.title("Hotel Bookings")
st.write(
    "Welcome! This is the Home page for the Hotel Bookings demo. "
    "Use the button below to open the App page (located in the pages folder)."
)

st.write("")

if st.button("Open App"):
    try:
        st.query_params(page="app")
        st.rerun()
    except Exception:
        st.markdown("[Open App](?page=app)")

st.info("If the App page doesn't open, open it from the sidebar (Pages) or ensure your pages/app.py exists.")
