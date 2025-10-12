import streamlit as st
import configurations as C
import importlib
import model
M = importlib.reload(model)
import profiles as P
import numpy as np
import pandas as pd
from urllib.parse import quote
from datetime import datetime

# ----Seiteneinstellungen----
st.set_page_config(page_title="Mieterstrom Rechner", page_icon="⚡", layout="medium")
st.title("Mieterstrom - Renditerechner")

# ---- UI: Eingabe----
with st.sidebar:
    st.header("Immobilien Informationen")
    
    # Wohneinheiten & Jahresverbrauch 
    we = st.slider("Anzahl Wohneinheiten", min_value=0, max_value=25, value=2, step=1)
    we_verbrauch = st.number_input("Jahresverbrauch Wohnungen (kWh)", min_value=1000, max_value=100000, value=2500, step=100)

    # Wenn Gewerbeeinheiten vorhanden 
    has_ge = st.toggle("Gewerbeeinheiten vorhanden?", value=False)
    if has_ge: #
        ge_verbrauch = st.number_input("Jahresverbrauch Gewerbeeinheiten (kWh)", min_value=2500, max_value=100000, value=2500, step=100)  
   
    # PV Anlage ] Speicher 
    pv = st.slider("PV-Anlage (kWp)", min_value=1, max_value=100, value=10, step=1)
    speicher = st.slider("Speichergröße (kWh)", min_value=0, max_value=100, value=0, step=1)

    # Wenn Wärmepumpe vorhanden 
    has_wp = st.toggle("Wärmepumpe vorhanden?", value=False)   
    if has_wp: #
        wp_verbrauch = st.number_input("Wärmepumpenverbrauch (kWh)", min_value=1000, max_value=100000, value=2500, step=100)  

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

st.header("Unabhängigkeit")

def metric_card(col, label, value, delta=None):
    with col.container(border=True):
        st.metric(label, value, delta)

row1 = st.columns(2, gap="medium")
row2 = st.columns(2, gap="medium")

metric_card(row1[0], "Autarkiegrad", f"{S.autarkiegrad*100:,.1f} %")
metric_card(row1[1], "Eigenverbrauchsquote", f"{S.eigenverbrauchsquote*100:,.1f} %")

st.markdown("***")

# ---- Wirtschaftlichkeitsrechnung----
k = M.wirtschaftlichkeit_kpis(jahre=20)
st.header("Wirtschaftlichkeit")

col1, col2 = st.columns(2)
col1.metric("Rendite (IRR)", f"{k['irr_pct']:,.1f} %")
col2.metric("Laufzeit (Amortisation)", "—" if k["payback_years"] is None else f"{k['payback_years']:,.1f} Jahre")

# --- Dialog / Formular ---
TO = "simon.wedeking@gmx.de"

def send_via_mailto(subject: str, body: str):
    url = f"mailto:{TO}?subject={quote(subject)}&body={quote(body)}"
    st.link_button("E-Mail in Mailprogramm öffnen", url, use_container_width=True)

@st.dialog("Mieterstrom – Projektanmeldung")
def lead_dialog():
    # Alles im Formular halten (wichtig für st.form_submit_button)
    with st.form("lead_form", clear_on_submit=True):
        # --- Kontakt
        colA, colB = st.columns(2)
        with colA:
            name  = st.text_input("Ihr Name *")
            email = st.text_input("Ihre E-Mail *")
            tel   = st.text_input("Telefon")
        with colB:
            strasse = st.text_input("Objekt Straße & Hausnummer *")
            plz     = st.text_input("Objekt PLZ *", max_chars=5)
            ort     = st.text_input("Ort *")

        # --- Mieterstrom-Daten (read-only aus der Sidebar, aufklappbar)
        with st.expander("Mieterstrom Daten", expanded=False):
            st.caption("Diese Werte kommen aus der linken Seitenleiste und sind hier schreibgeschützt.")

            st.number_input(
                "Wohneinheiten",
                value=int(st.session_state.get("lead_we", 0)),
                disabled=True, key="ro_we"
            )
            st.number_input(
                "Jahresverbrauch Wohnungen (kWh)",
                value=int(st.session_state.get("lead_verb", 0)),
                disabled=True, key="ro_verb"
            )
            st.number_input(
                "PV-Anlage (kWp)",
                value=float(st.session_state.get("lead_pv", 0.0)),
                disabled=True, key="ro_pv"
            )
            st.number_input(
                "Speicher (kWh)",
                value=float(st.session_state.get("lead_sp", 0.0)),
                disabled=True, key="ro_sp"
            )

            ge_active = bool(st.session_state.get("lead_has_ge", False))
            if ge_active:
                ge_form = st.number_input(
                    "Jahresverbrauch Gewerbe (kWh)",
                    value=int(st.session_state.get("lead_ge", 0)),
                    disabled=True, key="ro_ge"
                )
            else:
                ge_form = 0
                st.caption("Gewerbe: nicht aktiviert")

            wp_active = bool(st.session_state.get("lead_has_wp", False))
            if wp_active:
                wp_form = st.number_input(
                    "Wärmepumpenverbrauch (kWh)",
                    value=int(st.session_state.get("lead_wp", 0)),
                    disabled=True, key="ro_wp"
                )
            else:
                wp_form = 0
                st.caption("Wärmepumpe: nicht aktiviert")

        # --- Nachricht & Einwilligung
        msg     = st.text_area("Nachricht (optional)")
        consent = st.checkbox("Ich stimme der Speicherung meiner Angaben zu. *")

        can_submit = all([name, email, strasse, plz, ort, consent])
        submitted = st.form_submit_button(
            "Anfrage senden", type="primary", use_container_width=True, disabled=not can_submit
        )

        if submitted:
            # Werte aus Session State (von open_lead_dialog gesetzt)
            we_val    = int(st.session_state.get("lead_we", 0))
            verb_val  = int(st.session_state.get("lead_verb", 0))
            pv_val    = float(st.session_state.get("lead_pv", 0.0))
            sp_val    = float(st.session_state.get("lead_sp", 0.0))
            ge_active = bool(st.session_state.get("lead_has_ge", False))
            wp_active = bool(st.session_state.get("lead_has_wp", False))
            ge_val    = int(st.session_state.get("lead_ge", 0))
            wp_val    = int(st.session_state.get("lead_wp", 0))

            subject = f"Mieterstrom-Anmeldung: {strasse}, {plz} {ort}"
            body = f"""Kontakt
- Name: {name}
- E-Mail: {email}
- Telefon: {tel}

Objekt
- Adresse: {strasse}, {plz} {ort}
- Wohneinheiten: {we_val}
- Jahresverbrauch Wohnungen: {verb_val} kWh
- PV-Anlage: {pv_val} kWp
- Speicher: {sp_val} kWh
- Gewerbe aktiv: {"Ja" if ge_active else "Nein"}{f" (Verbrauch: {ge_val} kWh)" if ge_active else ""}
- Wärmepumpe aktiv: {"Ja" if wp_active else "Nein"}{f" (Verbrauch: {wp_val} kWh)" if wp_active else ""}

Nachricht
{msg}

Meta
- Timestamp: {datetime.now().isoformat()}
"""

            st.success("Danke! Öffne dein Mailprogramm, um die Nachricht zu senden.")
            send_via_mailto(subject, body)
            st.stop()

def open_lead_dialog():
    st.session_state["lead_we"]    = int(we)
    st.session_state["lead_verb"]  = int(we_verbrauch)
    st.session_state["lead_pv"]    = float(pv)
    st.session_state["lead_sp"]    = float(speicher)

    st.session_state["lead_has_ge"] = bool(has_ge)
    st.session_state["lead_ge"]     = int(ge_verbrauch) if has_ge else 0

    st.session_state["lead_has_wp"] = bool(has_wp)
    st.session_state["lead_wp"]     = int(wp_verbrauch) if has_wp else 0

    lead_dialog()
    
st.button("Mieterstromangebot anfragen",
          type="primary", use_container_width=True, on_click=open_lead_dialog)

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

with st.expander("Weitere Ergebnisse"):
    cols = st.columns(4)
    
    cols[0].metric("Invest (CAPEX)", f"{k['capex']:,.0f} €")
    cols[1].metric("Einnahmen Jahr 1", f"{k['einnahmen_j1']:,.0f} €")
    cols[2].metric("Kosten Jahr 1",    f"{k['kosten_j1']:,.0f} €")
    cols[3].metric("Gewinn Jahr 1",    f"{k['gewinn_j1']:,.0f} €")
    
st.markdown("***")

# ---- Abbildung Jahresverlauf----
R = sim["reihen"]  # stündliche Reihen aus dem Modell

def monthly_sum(series):
    idx = pd.date_range("2021-01-01", periods=len(series), freq="H")  # 2021 = Nicht-Schaltjahr
    s = pd.Series(series, index=idx, dtype=float)
    return s.resample("M").sum()  # 12 Summen Jan..Dez
    
gesamt_m  = monthly_sum(R["gesamtverbrauch"])
pv_m      = monthly_sum(R["pv_prod"])
ev_m      = monthly_sum(R["eigenverbrauch"])
batt_outm = monthly_sum(R["batt_to_load"])    # Entladung (AC zur Last)
feedin_m  = monthly_sum(R["netzeinspeisung"])
grid_m    = monthly_sum(R["netzbezug"])

df_m = pd.concat(
    [
        gesamt_m.rename("Gesamtverbrauch[kWh]"),
        pv_m.rename("PV-Erzeugung[kWh]"),
        ev_m.rename("Eigenverbrauch[kWh]"),
        batt_outm.rename("Batterie-Entladung[kWh]"),
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

st.subheader("Monatswerte – Jahresverlauf")
st.line_chart(df_m)
st.subheader("Jahreswerte im Überblick")

def metric_card(col, label, value, delta=None):
    with col.container(border=True):
        st.metric(label, value, delta)

row1 = st.columns(2, gap="medium")
row2 = st.columns(2, gap="medium")

metric_card(row1[0], "PV-Erzeugung",        f"{S.pv_erzeugung_kwh:,.0f} kWh")
metric_card(row1[1], "Eigenverbrauch (Jahr)", f"{S.eigenverbrauch_kwh:,.0f} kWh")
metric_card(row2[0], "Netzeinspeisung",     f"{S.netzeinspeisung_kwh:,.0f} kWh")
metric_card(row2[1], "Netzbezug",           f"{S.netzbezug_kwh:,.0f} kWh")


with st.expander("Weitere Ergebnisse"):
    cols = st.columns(3)
    
    # immer
    cols[0].metric("Eigenverbrauch Wohnungen", f"{S.eigenverbrauch_wohnung_kwh:,.0f} kWh")

    # optional: Gewerbe
    if getattr(C, "gewerbe_aktiv", False):
        cols[1].metric("Eigenverbrauch Gewerbe", f"{S.eigenverbrauch_gewerbe_kwh:,.0f} kWh")

    # optional: Wärmepumpe
    if getattr(C, "wp_aktiv", False):
        cols[2].metric("Eigenverbrauch Wärmepumpe", f"{S.eigenverbrauch_wp_kwh:,.0f} kWh")

        
st.markdown("***")
