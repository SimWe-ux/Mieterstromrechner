import streamlit as st
import configurations as C
import model as M
import profiles as P
import numpy as np
import pandas as pd

# ----Seiteneinstellungen----
st.set_page_config(page_title="Mieterstrom Rechner", page_icon="⚡", layout="centered")
st.title("⚡ Mieterstrom - Renditerechner")

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

# ----OUTPUT----

# ----Eigenverbrauchsquote & Autarkiegard----

sim = M.simulate_hourly() 
S = sim["summen"]

col1, col2 = st.columns(2)
col1.metric("Autarkiegrad", f"{S.autarkiegrad*100:,.1f} %")
col2.metric("Eigenverbrauchsquote", f"{S.eigenverbrauchsquote*100:,.1f} %")    

# ---- Abbildung Jahresverlauf----
R = sim["reihen"]  # stündliche Reihen aus dem Modell

def monthly_sum(series):
    idx = pd.date_range("2021-01-01", periods=len(series), freq="H")  # 2021 = Nicht-Schaltjahr
    s = pd.Series(series, index=idx, dtype=float)
    return s.resample("M").sum()  # 12 Summen Jan..Dez

pv_m      = monthly_sum(R["pv_prod"])
ev_m      = monthly_sum(R["eigenverbrauch"])
batt_outm = monthly_sum(R["batt_to_load"])    # Entladung (AC zur Last)
batt_inm  = monthly_sum(R["charge"])          # Ladung (in den Speicher)
feedin_m  = monthly_sum(R["netzeinspeisung"])
grid_m    = monthly_sum(R["netzbezug"])

df_m = pd.concat(
    [
        pv_m.rename("PV-Erzeugung[kWh]"),
        ev_m.rename("Eigenverbrauch[kWh]"),
        batt_outm.rename("Batterie-Entladung[kWh]"),
        batt_inm.rename("Batterie-Ladung[kWh]"),
        feedin_m.rename("Netzeinspeisung[kWh]"),
        grid_m.rename("Netzbezug[kWh]"),
    ],
    axis=1,
)
labels = {1:"Jan",2:"Feb",3:"Mär",4:"Apr",5:"Mai",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Okt",11:"Nov",12:"Dez"}
df_plot = df_m.copy()
df_plot["MonatNum"] = df_plot.index.month
df_plot["Monat"] = df_plot["MonatNum"].map(labels)

df_long = df_plot.reset_index(drop=True).melt(
    id_vars=["MonatNum","Monat"],
    var_name="Serie",
    value_name="kWh"
)
col1, col2 = st.columns(2)
col1.metric("PV-Erzeugung", f"{S.pv_erzeugung_kwh:,.0f} kWh")
col2.metric("Netzeinspeisung:", f"{S.netzeinspeisung_kwh:,.0f} kWh")
col2.metric("Netzbezug:", f"{S.netzbezug_kwh:,.0f} kWh")

# ---- Wirtschaftlichkeitsrechnung----
st.subheader("Monatswerte – Jahresverlauf")
st.line_chart(df_m)

st.subheader("Wirtschaftlichkeit")

c1, c2 = st.columns(2)
c1.metric("Invest (CAPEX)", f"{k['capex']:,.0f} €")
c1.metric("Rendite (IRR)", f"{k['irr_pct']:,.1f} %")
c1.metric("Laufzeit (Amortisation)", "—" if k["payback_years"] is None else f"{k['payback_years']:,.1f} Jahre")

c2.metric("Einnahmen Jahr 1", f"{k['einnahmen_j1']:,.0f} €")
c2.metric("Kosten Jahr 1",    f"{k['kosten_j1']:,.0f} €")
c2.metric("Gewinn Jahr 1",    f"{k['gewinn_j1']:,.0f} €")

# --- Abbildung Cashflows über 20 Jahre----
cf = M.cashflow_n(jahre=20)                 # [-Invest, CF1, CF2, ...]
cum = np.cumsum(cf).astype(float)           # kumulierte Cashflows

# Jahresachse (Start = aktuelles Jahr)
start_year = pd.Timestamp.today().year
years_idx = pd.Index(range(start_year, start_year + len(cum)), name="Jahr")

# Positive kumulierte Werte als "Einnahmen", negative als "Ausgaben"
df_amort = pd.DataFrame({
    "Einnahmen kumuliert [€]": np.where(cum > 0, cum, 0.0),
    "Ausgaben kumuliert [€]":  np.where(cum < 0, cum, 0.0),
}, index=years_idx)

st.subheader("Amortisation über 20 Jahre")
st.bar_chart(df_amort)   # zwei Farben: oben (Einnahmen), unten (Ausgaben)

