# ----Variablen aus UI Einagbe----
wohneinheiten: int = 2
wohnungen_verbrauch_kwh: float = 2_500.0  

pv_kwp: float = 10.0
speicher_kwh: float = 0.0

gewerbe_aktiv: bool = False
gewerbe_verbrauch_kwh: float = 0.0          

wp_aktiv: bool = False
wp_verbrauch_kwh: float = 0.0               

# ----Pv und Battrerie----
pv_form_exponent: float = 3.0 # PV Tageskurve 
ladeleistung: float = 3.0 # Max. Ladeleistung (kW) – konservativ
entladeleistung: float = 3.0 # Max. Endladeleistung (kW) – konservativ
wirkungsgrad_roundtrip: float = 0.85 # Gesamtwirkungsgrad Laden*Entladen
standby_watt: float = 20 # Optionale Standby‑/Eigenverbrauchsverluste des Speichers (W)
soc_start_kwh: float = 0.20 * speicher_kwh # Start‑Ladezustand (kWh)  

# ----Preise und Vergütung----
preis_pv_u10_kwp: float = 1500.0 # Pv Preis unter 10 kWp
preis_pv_10_20_kwp: float = 1100.0 # Pv Preis zwischen 10 - 20kWp
preis_pv_o20_kwp: float = 990.0 # Pv Preis über 20 kWp
speicherkosten: float  = 500 # Speicherkosten in € 
reststromkosten: float = 0.35 # Reststromkosten in € 
pv_stromkosten: float = 0.27 # PVstromksoten in € 
grundgebuehren: float = 10 # Grundgebühren in € 
mieterstromzuschlage = 0.0238 # EEG Mieterstromzuschlag in € 
strompreissteigerung_pa: float = 0.03 # Strompreissteigerung pro Jahr
einspeisevergütung_u10_kwp: float = 0.0786
einspeisevergütung_o10_kwp: float = 0.0688

def _tiered_avg_einspeise_satz(pv_kwp: float) -> float:
    """
    Liefert den kapazitätsgewichteten Durchschnittssatz in €/kWh
    für die gesamte Anlage gemäß EEG-Staffel (≤10, 10–40, 40–100, >100).
    Nutzt vorhandene Konfig-Variablen und fällt sinnvoll zurück.
    """

    # Raten aus configurations.py holen (Fallbacks, falls nicht definiert)
    r_u10  = getattr(C, "einspeisevergütung_u10_kwp", 0.0786)
    r_10_40 = getattr(C, "einspeisevergütung_10_40_kwp",
                      getattr(C, "einspeisevergütung_o10_kwp", 0.0688))
    r_40_100 = getattr(C, "einspeisevergütung_40_100_kwp", r_10_40)
    r_o100 = getattr(C, "einspeisevergütung_o100_kwp", r_40_100)

    tiers = [
        (10.0,     r_u10),    # bis 10 kWp
        (40.0,     r_10_40),  # >10 bis 40 kWp
        (100.0,    r_40_100), # >40 bis 100 kWp
        (float("inf"), r_o100)  # >100 kWp
    ]

    remaining = float(pv_kwp)
    prev_cap = 0.0
    weighted_sum = 0.0
    total_cap = max(float(pv_kwp), 1e-12)

    for cap, rate in tiers:
        band_width = cap - prev_cap
        take = max(min(remaining, band_width), 0.0)
        if take > 0:
            weighted_sum += take * float(rate)
            remaining -= take
        prev_cap = cap
        if remaining <= 0:
            break

    return weighted_sum / total_cap
 

# ----Betriebskosten---- 
abrechnungskosten: float = 70 # Abbrechnungssoftwarekosten 
zaehlergebuehren_we: float = 30 # POG Zählergebühren WE
zaehlergebuehren_pv: float = 50 # POG Zählergebühren PV/WP Zähler 

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

