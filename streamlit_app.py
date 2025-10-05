import streamlit as st

# ----Seiteneinstellungen----
st.set_page_config(page_title="Mieterstrom Rechner", page_icon="⚡", layout="centered")
st.title("⚡ Mieterstrom - RenditeRechner")

# ---- UI: Eingabe----

with st.sidebar:
    st.header("Immobilien Informationen")

    we = st.slider("Anzahl Wohneinheiten", min_value=1, max_value=25, value=2, step=1)
    verbrauch_WE = st.number_input("Jahresverbauch Wohnungen", min_value=1500, max_value=100000, value=2500, step=100)
    has_GE = st.toggle("Gewerbeeinheiten vorhanden?", value=False)

    # Wenn Gewerbeeinheiten vorhanden 
    if has_GE: #
        st.markdown("**Gewerbeeinheiten**") 
        has_GE = st.number_input("Jahresverbrauch Gewerbeeinheiten", min_value=2500, max_value=100000, value=2500, step=100)  
   
    pv = st.slider("PV-Anlage", min_value=1, max_value=100, value=10, step=1)
    speicher = st.slider("Speichergröße", min_value=0, max_value=100, value=0, step=1)
    has_WP = st.toggle("Wärmepumpe vorhanden?", value=False)   

# Wenn Wärmepumpe vorhanden 
    if has_WP: #
        st.markdown("**Wärmepumpe**") 
        has_WP = st.number_input("Wärmepumpenverbrauch", min_value=1000, max_value=100000, value=2500, step=100)  
