# model.py
"""
Excel-Logik (8760h) in reinem Python.
- PV-Erzeugung über Gewichte^Exponent (normalisiert auf 950 kWh/kWp*a)
- Batterie mit Roundtrip-Wirkungsgrad (symmetrisch via sqrt(eta))
- Standby in W -> kWh/h
- Proportionale Verteilung EV auf Wohnung / WP / Gewerbe
- Wirtschaftlichkeit (Jahr 1), Cashflow, IRR

Abhängigkeiten:
- configurations.py (deine Variablennamen)
- profiles.py       (8760-Arrays: LASTPROFIL_WOHNUNG, LASTPROFIL_WP, LASTPROFIL_GEWERBE, PV_GEWICHT)
"""

from __future__ import annotations
from dataclasses import dataclass
from math import sqrt
from typing import Dict, Any
import numpy as np
import configurations as C
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
    return getattr(C, name, default)

def _einspeise_satz() -> float:
    f = getattr(C, "einspeiseverguetung_satz", None)
    if callable(f):
        return float(f(float(C.pv_kwp)))
    if hasattr(C, "einspeisevergütung_u10_kwp") and hasattr(C, "einspeisevergütung_o10_kwp"):
        return float(C.einspeisevergütung_u10_kwp if C.pv_kwp <= 10 else C.einspeisevergütung_o10_kwp)
    return 0.0688

def _preis_pv_kwp() -> float:
    f = getattr(C, "pv_preis_pro_kwp", None)
    if callable(f):
        return float(f(float(C.pv_kwp)))
    x = float(C.pv_kwp)
    if x < 10:
        return float(C.preis_pv_u10_kwp)
    elif x <= 20:
        return float(C.preis_pv_10_20_kwp)
    return float(C.preis_pv_o20_kwp)

# ---------- Hauptsimulation ----------
def simulate_hourly() -> Dict[str, Any]:
    n = 8760
    P = np.array(LASTPROFIL_WOHNUNG[:n], dtype=float)
    S = np.array(LASTPROFIL_WP[:n], dtype=float)
    G = np.array(LASTPROFIL_GEWERBE[:n], dtype=float)
    Q = np.array(PV_GEWICHT[:n], dtype=float)

    sum_P = float(P.sum())
    sum_S = float(S.sum()) if C.wp_aktiv else 1.0
    sum_G = float(G.sum()) if C.gewerbe_aktiv else 1.0

    R = np.power(Q, float(C.pv_form_exponent))
    sum_R = float(R.sum())

    wohnung_total = float(C.wohnungen_verbrauch_kwh)
    wp_total = float(C.wp_verbrauch_kwh) if C.wp_aktiv else 0.0
    gew_total = float(C.gewerbe_verbrauch_kwh) if C.gewerbe_aktiv else 0.0

    wohnung_series  = wohnung_total * (P / sum_P)
    wp_series       = (wp_total * (S / sum_S)) if C.wp_aktiv else np.zeros(n)
    gewerbe_series  = (gew_total * (G / sum_G)) if C.gewerbe_aktiv else np.zeros(n)

    gesamtverbrauch = wohnung_series + wp_series + gewerbe_series

    pv_annual_yield = 950.0 * float(C.pv_kwp)
    pv_prod = pv_annual_yield * (R / sum_R)

    direkt     = np.minimum(gesamtverbrauch, pv_prod)
    ueberschuss= np.maximum(pv_prod - gesamtverbrauch, 0.0)
    defizit    = np.maximum(gesamtverbrauch - pv_prod, 0.0)

    eff = float(C.wirkungsgrad_roundtrip)
    rt = sqrt(eff)
    soc = np.zeros(n, dtype=float)
    charge = np.zeros(n, dtype=float)
    spill_after_charge = np.zeros(n, dtype=float)
    discharge = np.zeros(n, dtype=float)
    batt_to_load = np.zeros(n, dtype=float)
    standby_kwh = float(C.standby_watt) / 1000.0

    for i in range(n):
        prev_soc = soc[i - 1] if i > 0 else float(C.soc_start_kwh)

        charge[i] = min(
            min(ueberschuss[i], float(C.ladeleistung)) * eff,
            max(float(C.speicher_kwh) - prev_soc, 0.0),
        )

        spill_after_charge[i] = ueberschuss[i] - (charge[i] / rt)

        discharge[i] = min(
            min(defizit[i], float(C.entladeleistung)) / rt,
            prev_soc + charge[i],
        )

        batt_to_load[i] = discharge[i] * rt

        soc[i] = max((prev_soc + charge[i]) - discharge[i] - standby_kwh, 0.0)

    eigenverbrauch = direkt + batt_to_load
    netzeinspeisung = spill_after_charge
    netzbezug = defizit - batt_to_load

    with np.errstate(divide="ignore", invalid="ignore"):
        share_wohnung = np.divide(wohnung_series, np.maximum(gesamtverbrauch, 1e-12))
        share_wp      = np.divide(wp_series,       np.maximum(gesamtverbrauch, 1e-12))
        share_gewerbe = np.divide(gewerbe_series,  np.maximum(gesamtverbrauch, 1e-12))

    pv_to_wohnung = eigenverbrauch * share_wohnung
    pv_to_wp      = eigenverbrauch * share_wp
    pv_to_gewerbe = eigenverbrauch * share_gewerbe

    jahresverbrauch = float(gesamtverbrauch.sum())
    pv_erzeugung    = float(pv_prod.sum())
    eigenv_sum      = float(eigenverbrauch.sum())
    einspeisung_sum = float(netzeinspeisung.sum())
    netzbezug_sum   = float(netzbezug.sum())

    ev_quote = (eigenv_sum / pv_erzeugung) if pv_erzeugung > 0 else 0.0
    autarkie = (eigenv_sum / jahresverbrauch) if jahresverbrauch > 0 else 0.0

    ev_wohnung = float(pv_to_wohnung.sum())
    ev_wp      = float(pv_to_wp.sum())
    ev_gewerbe = float(pv_to_gewerbe.sum())

    rest_wohnung = float(wohnung_series.sum() - ev_wohnung)
    rest_wp      = float(wp_series.sum()      - ev_wp)
    rest_gewerbe = float(gewerbe_series.sum() - ev_gewerbe)

    out = Ergebnisse(
        jahresverbrauch_kwh=jahresverbrauch,
        pv_erzeugung_kwh=pv_erzeugung,
        eigenverbrauch_kwh=eigenv_sum,
        netzeinspeisung_kwh=einspeisung_sum,
        netzbezug_kwh=netzbezug_sum,
        eigenverbrauchsquote=ev_quote,
        autarkiegrad=autarkie,
        eigenverbrauch_wohnung_kwh=ev_wohnung,
        eigenverbrauch_wp_kwh=ev_wp,
        eigenverbrauch_gewerbe_kwh=ev_gewerbe,
        reststrombedarf_wohnung_kwh=rest_wohnung,
        reststrombedarf_wp_kwh=rest_wp,
        reststrombedarf_gewerbe_kwh=rest_gewerbe,
    )

    return {
        "reihen": {
            "gesamtverbrauch": gesamtverbrauch,
            "pv_prod": pv_prod,
            "direkt": direkt,
            "ueberschuss": ueberschuss,
            "defizit": defizit,
            "charge": charge,
            # (Originalzustand) – hier stand die nach dem Fix geänderte Zeile:
            "spill_after_charge": netzeinspeisung,
            "discharge": discharge,
            "batt_to_load": batt_to_load,
            "soc": soc,
            "eigenverbrauch": eigenverbrauch,
            "netzeinspeisung": netzeinspeisung,
            "netzbezug": netzbezug,
            "wohnung_series": wohnung_series,
            "wp_series": wp_series,
            "gewerbe_series": gewerbe_series,
            "pv_to_wohnung": pv_to_wohnung,
            "pv_to_wp": pv_to_wp,
            "pv_to_gewerbe": pv_to_gewerbe,
        },
        "summen": out,
    }

# ---------- CAPEX ----------
def capex_pv() -> float:
    return float(C.pv_kwp) * _preis_pv_kwp()

def capex_speicher() -> float:
    return float(C.speicher_kwh) * float(_get("speicherkosten", 500.0))

# ---------- Wirtschaftlichkeit Jahr 1 (Original-Logik) ----------
def wirtschaftlichkeit_j1() -> Dict[str, float]:
    sim = simulate_hourly()
    S: Ergebnisse = sim["summen"]
    
    # Preise/Parameter aus configurations.py
    p_pv   = float(_get("pv_stromkosten", 0.27))          # Verkaufspreis PV-Mieterstrom
    p_rest = float(_get("reststromkosten", 0.32))          # Einkauf = Verkauf (neutral)
    gg_mon = float(_get("grundgebuehren", 10.0))           # €/Monat (ein Anschluss)
    ms_z   = float(_get("mieterstromzuschlage", 0.0238))   # €/kWh
    eins   = _einspeise_satz()
    
    # PV-Eigenverbrauch je Sektor
    ev_we = float(S.eigenverbrauch_wohnung_kwh)
    ev_ge = float(S.eigenverbrauch_gewerbe_kwh) if getattr(C, "gewerbe_aktiv", False) else 0.0
    ev_wp = float(S.eigenverbrauch_wp_kwh)       if getattr(C, "wp_aktiv", False)       else 0.0

    # Reststrommengen 
    rest_we = float(S.reststrombedarf_wohnung_kwh)
    rest_ge = float(S.reststrombedarf_gewerbe_kwh) if getattr(C, "gewerbe_aktiv", False) else 0.0
    rest_wp = float(S.reststrombedarf_wp_kwh)      if getattr(C, "wp_aktiv", False)       else 0.0
    rest_sum = rest_we + rest_ge + rest_wp

    # --- Einnahmen ---
    verkauf_pv  = p_pv * (ev_we + ev_ge + ev_wp)             # PV-Verkauf an alle Kunden
    ms_einnahme = ms_z * (ev_we + ev_ge + ev_wp)             # Zuschlag auf PV-Mieterstrom
    einspeise   = eins  * float(S.netzeinspeisung_kwh)
    rest_rev    = p_rest * rest_sum                          # Reststrom (neutral)

    einnahmen = verkauf_pv + ms_einnahme + einspeise + rest_rev

    # --- Kosten ---
    zaehler = (
        float(_get("zaehlergebuehren_we", 30.0)) * int(getattr(C, "wohneinheiten", 1))
        + float(_get("zaehlergebuehren_pv", 50.0)) * 1.0
    )
    abrechnung        = float(_get("abrechnungskosten", 70.0))
    grundgebuehr_jahr = 12.0 * gg_mon                         # nur als Kosten, nicht als Einnahme
    rest_costs        = p_rest * rest_sum                     # Reststrom (neutral)

    kosten = zaehler + abrechnung + grundgebuehr_jahr + rest_costs

    return {
        "einnahmen_j1": float(einnahmen),
        "kosten_j1": float(kosten),
        "gewinn_j1": float(einnahmen - kosten),
    }

# ---------- Cashflow & IRR (Original-Variante) ----------
def cashflow_n(jahre: int = 20):
    invest = float(capex_pv() + capex_speicher())
    j1 = wirtschaftlichkeit_j1()
    ein = float(j1.get("einnahmen_j1", 0.0))
    kos = float(j1.get("kosten_j1", 0.0))
    escal = float(_get("strompreissteigerung_pa", 0.03))

    cf = [-invest]
    for y in range(jahre):
        factor = (1.0 + escal) ** y
        cf.append(ein * factor - kos * factor)
    return cf

def irr(cashflows) -> float:
    c = list(map(float, cashflows))
    def npv(rate: float) -> float:
        return sum(v / ((1.0 + rate) ** i) for i, v in enumerate(c))
    r = 0.08
    for _ in range(100):
        f = npv(r)
        df = sum(-i * v / ((1.0 + r) ** (i + 1)) for i, v in enumerate(c[1:], start=1))
        if abs(df) < 1e-12:
            break
        step = f / df
        r -= step
        if abs(step) < 1e-8:
            break
    return float(r)

def payback_years(cashflows) -> float | None:
    cf = list(map(float, cashflows))
    cum = cf[0]
    for y in range(1, len(cf)):
        prev = cum
        cum += cf[y]
        if cum >= 0:
            return (y - 1) + (0.0 - prev) / cf[y] if cf[y] != 0 else float(y)
    return None

def wirtschaftlichkeit_kpis(jahre: int = 20) -> Dict[str, float]:
    capex = float(capex_pv() + capex_speicher())
    j1 = wirtschaftlichkeit_j1()
    cf = cashflow_n(jahre=jahre)
    try:
        irr_pct = irr(cf) * 100.0
    except Exception:
        irr_pct = float("nan")
    pb = payback_years(cf)
    return {
        "capex": capex,
        "irr_pct": irr_pct,
        "payback_years": pb,
        "einnahmen_j1": float(j1.get("einnahmen_j1", 0.0)),
        "kosten_j1": float(j1.get("kosten_j1", 0.0)),
        "gewinn_j1": float(j1.get("gewinn_j1", 0.0)),
    }
