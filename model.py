# model.py
"""
Excel-Logik (8760h) in reinem Python.
- PV-Erzeugung über Gewichte^Exponent (normalisiert auf 950 kWh/kWp*a)
- Batterie mit Roundtrip-Wirkungsgrad (symmetrisch via sqrt(eta))
- Standby in W -> kWh/h
- Proportionale Verteilung EV auf Wohnung / WP / Gewerbe
- Wirtschaftlichkeit (Jahr 1), Cashflow, IRR

Abhängigkeiten:
- Configurations.py (deine Variablennamen)
- profiles.py       (8760-Arrays: LASTPROFIL_WOHNUNG, LASTPROFIL_WP, LASTPROFIL_GEWERBE, PV_GEWICHT)
"""

from __future__ import annotations
from dataclasses import dataclass
from math import sqrt
from typing import Dict, Any
import numpy as np
import Configurations as C
from profiles import (
    LASTPROFIL_WOHNUNG,
    LASTPROFIL_WP,
    LASTPROFIL_GEWERBE,
    PV_GEWICHT,
)

# ---------- Ergebnisstruktur ----------
@dataclass
class Ergebnisse:
    jahresverbrauch_kwh: float
    pv_erzeugung_kwh: float
    eigenverbrauch_kwh: float
    netzeinspeisung_kwh: float
    netzbezug_kwh: float
    eigenverbrauchsquote: float
    autarkiegrad: float
    eigenverbrauch_wohnung_kwh: float
    eigenverbrauch_wp_kwh: float
    eigenverbrauch_gewerbe_kwh: float
    reststrombedarf_wohnung_kwh: float
    reststrombedarf_wp_kwh: float
    reststrombedarf_gewerbe_kwh: float

# ---------- kleine Helper ----------
def _get(name: str, default):
    """Robustes Lesen aus Config (unterstützt ggf. Alias-Namen)."""
    return getattr(C, name, default)

def _einspeise_satz() -> float:
    # bevorzugt deine Funktion (mit Umlaut-Variablen)
    f = getattr(C, "einspeiseverguetung_satz", None)
    if callable(f):
        return float(f(float(C.pv_kwp)))
    # Fallback über Variablen
    if hasattr(C, "einspeisevergütung_u10_kwp") and hasattr(C, "einspeisevergütung_o10_kwp"):
        return float(C.einspeisevergütung_u10_kwp if C.pv_kwp <= 10 else C.einspeisevergütung_o10_kwp)
    # letzte Sicherung
    return 0.0688

def _preis_pv_kwp() -> float:
    f = getattr(C, "pv_preis_pro_kwp", None)
    if callable(f):
        return float(f(float(C.pv_kwp)))
    # Falls Funktion fehlt, manuell staffeln
    x = float(C.pv_kwp)
    if x < 10:
        return float(C.preis_pv_u10_kwp)
    elif x <= 20:
        return float(C.preis_pv_10_20_kwp)
    return float(C.preis_pv_o20_kwp)

# ---------- Hauptsimulation ----------
