import streamlit as st

# ----Seiteneinstellungen----
st.set_page_config(page_title="Mieterstrom Rechner", page_icon="⚡", layout="centered")
st.title("⚡ Mieterstrom - Renditerechner")

# ----Konstante----
PV_Form_Exponent = 3 # PV Tageskurve 
Ladeleistung_kW = 3 # Max. Ladeleistung (kW) – konservativ
Entladeleistung_kW = 3 # Max. Endladeleistung (kW) – konservativ
Wirkungsgrad_Roundtrip = 0.85 # Gesamtwirkungsgrad Laden*Entladen
Standby_Watt = 20 # Optionale Standby‑/Eigenverbrauchsverluste des Speichers (W)
SOC_Start_kWh = "Speichergröße"*20% # Start‑Ladezustand (kWh)  
PV-Anlage & Speicher = if("PV_Anlage"<10, "PV_Anlage"*1500, if(and("PV_Anlage">=10, "PV_Anlage"<=20), "PV_Anlage"*1100, if("PV_Anlage">=20, "PV_Anlage"*990)))
Speicherksoten  = 500 # Speicherkosten in € 
Reststromksoten = 0.35 # Reststromkosten in € 
PV-Stromksoten = 0.27 # PVstromksoten in € 
Grundgebühren = 10 # Grundgebühren in € 
Mieterstromzuschlage = 0.0238 # EEG Mieterstromzuschlag in € 
Einspeisevergütung = 0.0688 # Einspeisevergütung in €
Abrechnungskosten = 70 # Abbrechnungssoftwarekosten 
Zählergebühren WE = 30 # POG Zählergebühren 
Zählergebühren PV = 50 # POG Zählergebühren PV/WP Zähler 
