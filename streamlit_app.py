import streamlit as st
import configurations as C
import model as M
import profiles as P

# ----Seiteneinstellungen----
st.set_page_config(page_title="Mieterstrom Rechner", page_icon="⚡", layout="centered")
st.title("⚡ Mieterstrom - RenditeRechner")

# ---- UI: Eingabe----

with st.sidebar:
    st.header("Immobilien Informationen")
    
    # Wohneinheiten & Jahresverbrauch 
    we = st.slider("Anzahl Wohneinheiten", min_value=1, max_value=25, value=2, step=1)
    we_verbrauch = st.number_input("Jahresverbrauch Wohnungen", min_value=1500, max_value=100000, value=2500, step=100)

    # Wenn Gewerbeeinheiten vorhanden 
    has_ge = st.toggle("Gewerbeeinheiten vorhanden?", value=False)
    if has_ge: #
        ge_verbrauch = st.number_input("Jahresverbrauch Gewerbeeinheiten", min_value=2500, max_value=100000, value=2500, step=100)  
   
    # PV Anlage ] Speicher 
    pv = st.slider("PV-Anlage", min_value=1, max_value=100, value=10, step=1)
    speicher = st.slider("Speichergröße", min_value=0, max_value=100, value=0, step=1)

    # Wenn Wärmepumpe vorhanden 
    has_wp = st.toggle("Wärmepumpe vorhanden?", value=False)   
    if has_wp: #
        wp_verbrauch = st.number_input("Wärmepumpenverbrauch", min_value=1000, max_value=100000, value=2500, step=100)  

# ----Mapping in Configurations.py---
C.wohneinheiten = int(we)
C.wohnungen_verbrauch_kwh = float(we_verbrauch)
C.gewerbe_aktiv = bool(has_ge)
C.gewerbe_verbrauch_kwh = float(ge_verbrauch) if has_ge else 0.0
C.pv_kwp = float(pv)
C.speicher_kwh = float(speicher)
C.soc_start_kwh = 0.20 * C.speicher_kwh
C.wp_aktiv = bool(has_wp)
C.wp_verbrauch_kwh = float(wp_verbrauch) if has_wp else 0.0

# ----Simulation & KPIs----
sim = M.simulate_hourly()
S = sim["summen"]

col1, col2, col3 = st.columns(3)
col1.metric("PV-Erzeugung", f"{S.pv_erzeugung_kwh:,.0f} kWh")
col2.metric("Eigenverbrauchsquote", f"{S.eigenverbrauchsquote*100:,.1f} %")
col3.metric("Autarkiegrad", f"{S.autarkiegrad*100:,.1f} %")

st.write("Netzeinspeisung:", f"{S.netzeinspeisung_kwh:,.0f} kWh")
st.write("Netzbezug:", f"{S.netzbezug_kwh:,.0f} kWh")

st.caption("Profiles geladen (Anzahl Werte):")
st.write(len(P.LASTPROFIL_WOHNUNG), len(P.LASTPROFIL_WP), len(P.LASTPROFIL_GEWERBE), len(P.PV_GEWICHT))

# ----UI Outcome----

st.header("Mieterstrom Ergebnisse")

