import streamlit as st

# ----Seiteneinstellungen----
st.set_page_config(page_title="Mieterstrom Rechner", page_icon="⚡", layout="centered")
st.title("⚡ Mieterstrom - Renditerechner")

# ----Pv und Battrerie----
pv_form_exponent = 3 # PV Tageskurve 
ladeleistung = 3 # Max. Ladeleistung (kW) – konservativ
entladeleistung = 3 # Max. Endladeleistung (kW) – konservativ
wirkungsgrad_roundtrip = 0.85 # Gesamtwirkungsgrad Laden*Entladen
standby_watt = 20 # Optionale Standby‑/Eigenverbrauchsverluste des Speichers (W)
soc_start_kwh = "Speichergröße"*20% # Start‑Ladezustand (kWh)  

# ----Preise und Vergütung----
preis_pv_u10_kwp = 1500.0
preis_pv_10_20_kwp = 1100.0
preis_pv_o20_kwp = 990.0
speicherksoten  = 500 # Speicherkosten in € 
reststromksoten = 0.35 # Reststromkosten in € 
pv_stromksoten = 0.27 # PVstromksoten in € 
grundgebuehren = 10 # Grundgebühren in € 
mieterstromzuschlage = 0.0238 # EEG Mieterstromzuschlag in € 
einspeiseverguetung = 0.0688 # Einspeisevergütung in €
strompreissteigerung_pa: float = 0.03 # Strompreissteigerung pro Jahr 

# ----Betriebskosten---- 
abrechnungskosten = 70 # Abbrechnungssoftwarekosten 
zaehlergebuehren_we = 30 # POG Zählergebühren WE
zaehlergebuehren_pv = 50 # POG Zählergebühren PV/WP Zähler 

def pv_preis_pro_kwp(pv_kwp: float, c: Konstanten) -> float:
    if pv_kwp < 10:
        return c.preis_pv_u10_eur_kwp
    elif pv_kwp <= 20:
        return c.preis_pv_10_20_eur_kwp
    else:
        return c.preis_pv_o20_eur_kwp
