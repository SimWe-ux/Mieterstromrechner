import streamlit as st

# ----Seiteneinstellungen----
st.set_page_config(page_title="Mieterstrom Rechner", page_icon="⚡", layout="centered")
st.title("⚡ Mieterstrom - RenditeRechner")

# ---- UI: Eingabe----

with st.sidebar:
    st.header("Immobilien Informationen")

    we = st.slider("Anzahl Wohneinheiten", min_value=1, max_value=25, value=2, step=1)
    number = st.number_input("Gesamtverbrauch", min_value=1500, max_value=100000, value=2500, step=100)
    has_GE = st.toggle("Gewerbeeinheiten vorhanden?", value=False)
# Wenn Gewerbeeinheiten vorhanden 
    if has_GE: #
        st.markdown("---")
        st.markdown("**Gewerbeeinheiten**") 
        has_GE = st.number_input("Verbrauch Gewerbeeinheiten", min_value=2500, max_value=100000 value=2500, step=100)    
