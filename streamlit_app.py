import streamlit as st

# ----Seiteneinstellungen----
st.set_page_config(page_title="Mieterstrom Rechner", page_icon="⚡", layout="centered")
st.title("⚡ Mieterstrom - RenditeRechner")

# ---- UI: Eingabe----
st.header("Eingabe")
with st.select_slider(
    "Anzahl Wohneinheiten", min_value:1, max_value:25, value:2, steps: 1)
