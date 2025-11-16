# ----Variablen aus UI Einagbe----
wohneinheiten: int = 2
wohnungen_verbrauch_kwh: float = 2_500.0  

pv_kwp: float = 10.0
speicher_kwh: float = 0.0

gewerbe_aktiv: bool = False
gewerbe_verbrauch_kwh: float = 0.0          

wp_aktiv: bool = False
wp_verbrauch_kwh: float = 0.0     

# --- Modellwahl: EEG-Mieterstrom vs. GGV ---
modell: str = "EEG" 

# ----Pv und Battrerie----
pv_form_exponent: float = 3.0 # PV Tageskurve 
ladeleistung: float = 3.0 # Max. Ladeleistung (kW) – konservativ
entladeleistung: float = 3.0 # Max. Endladeleistung (kW) – konservativ
wirkungsgrad_roundtrip: float = 0.85 # Gesamtwirkungsgrad Laden*Entladen
standby_watt: float = 20 # Optionale Standby‑/Eigenverbrauchsverluste des Speichers (W)
soc_start_kwh: float = 0.20 * speicher_kwh # Start‑Ladezustand (kWh)  

# ----Preise und Vergütung----
preis_pv_u10_kwp: float = 1300.0 # Pv Preis unter 10 kWp
preis_pv_10_20_kwp: float = 1100.0 # Pv Preis zwischen 10 - 20kWp
preis_pv_o20_kwp: float = 1000.0 # Pv Preis über 20 kWp
speicherkosten: float  = 500 # Speicherkosten in € 
reststromkosten: float = 0.32 # Reststromkosten in € 
pv_stromkosten: float = 0.25 # PVstromksoten in € 
grundgebuehren: float = 10 # Grundgebühren in € 
messtechnik: float = 178.0  # Einmalige Messtechnik-Kosten
mieterstromzuschlage = 0.0238 # EEG Mieterstromzuschlag in € 
strompreissteigerung_pa: float = 0.03 # Strompreissteigerung pro Jahr
einspeisevergütung_u10_kwp: float = 0.0786 # Einspeisevergütung bis 10 kWp
einspeisevergütung_o10_kwp: float = 0.0688 # Einspeisevergütung über 10 kWp


def einspeiseverguetung_satz(pv_kwp_value: float) -> float:
    return einspeisevergütung_u10_kwp if pv_kwp_value <= 10 else einspeisevergütung_o10_kwp

# ----Betriebskosten---- 
abrechnungskosten: float = 70 # Abbrechnungssoftwarekosten 
zaehlergebuehren_we: float = 30 # POG Zählergebühren WE
zaehlergebuehren_pv: float = 50 # POG Zählergebühren PV/WP Zähler 
msb_kosten: float = 65.0    # Jährliche Messstellenbetriebskosten je WE

def pv_preis_pro_kwp(pv_kwp_value: float) -> float:
    if pv_kwp_value < 10:
        return preis_pv_u10_kwp
    elif pv_kwp_value <= 20:
        return preis_pv_10_20_kwp
    else:
        return preis_pv_o20_kwp

# Optional: Plausibilitätschecks aus Configurations aufrufen
def validate() -> None:
    assert pv_kwp >= 0
    assert speicher_kwh >= 0
    assert 0.0 <= wirkungsgrad_roundtrip <= 1.0
    assert ladeleistung >= 0 and entladeleistung >= 0
    assert standby_watt >= 0
    if wp_aktiv: assert wp_verbrauch_kwh > 0
    if gewerbe_aktiv: assert gewerbe_verbrauch_kwh > 0

