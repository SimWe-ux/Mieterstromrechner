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

# ----Mapping: Sidebar----
# (Alle Typen sauber setzen; nichts mehr überschreiben wie vorher bei has_GE/has_WP)
C.wohneinheiten = int(we)
C.wohnungen_verbrauch_kwh = float(verbrauch_we)

C.gewerbe_aktiv = bool(has_ge)
C.gewerbe_verbrauch_kwh = float(ge_verbrauch) if has_ge else 0.0

C.pv_kwp = float(pv)
C.speicher_kwh = float(speicher)
C.soc_start_kwh = 0.20 * C.speicher_kwh  # Excel-Logik: 20% Start-SOC

C.wp_aktiv = bool(has_wp)
C.wp_verbrauch_kwh = float(wp_verbrauch) if has_wp else 0.0

# Optional: Plausibilitätschecks aus Configurations aufrufen
if hasattr(C, "validate"):
    C.validate()

# ----Simulation & KPIs----
sim = M.simulate_hourly()
S = sim["summen"]

col1, col2, col3 = st.columns(3)
col1.metric("PV-Erzeugung", f"{S.pv_erzeugung_kwh:,.0f} kWh")
col2.metric("Eigenverbrauchsquote", f"{S.eigenverbrauchsquote*100:,.1f} %")
col3.metric("Autarkiegrad", f"{S.autarkiegrad*100:,.1f} %")

st.write("Netzeinspeisung:", f"{S.netzeinspeisung_kwh:,.0f} kWh")
st.write("Netzbezug:", f"{S.netzbezug_kwh:,.0f} kWh")
