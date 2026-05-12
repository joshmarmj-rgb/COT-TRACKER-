import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# --- TERMINAL KONFIGURATION ---
st.set_page_config(page_title="MakroBase_DE", layout="wide")
st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500&display=swap');
    * { background-color: #000 !important; color: #00ff41 !important; font-family: 'JetBrains Mono', monospace !important; }
    .stTable, table { border: 1px solid #00ff41 !important; }
    thead tr th { background-color: #002200 !important; color: #00ff41 !important; }
</style>""", unsafe_allow_html=True)

# --- DATENABFRAGE ---
@st.cache_data(ttl=600)
def daten_laden():
    url = "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip"
    r = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
    df.columns = df.columns.str.strip()
    # Nur E-Mini Nasdaq 100
    df = df[df['Market_and_Exchange_Names'].str.contains("E-MINI NASDAQ-100", na=False)].copy()
    df['Datum'] = pd.to_datetime(df['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
    return df.sort_values('Datum', ascending=False)

df = daten_laden()
aktuell = df.iloc[0]

# --- BERECHNUNGEN (DEUTSCH) ---
kauf = int(aktuell['Lev_Money_Positions_Long_All'])
verkauf = int(aktuell['Lev_Money_Positions_Short_All'])
netto = kauf - verkauf
gesamt_markt = int(aktuell['Open_Interest_All'])
anteil_verkauf = (verkauf / gesamt_markt) * 100

# --- AUSGABE ---
st.write(f"STAND: {aktuell['Datum'].strftime('%d.%m.%Y')} // MARKT: NASDAQ_E_MINI")
st.write("---")

# Spalte 1: Die nackten Zahlen
c1, c2, c3, c4 = st.columns(4)
c1.metric("NETTO-POWER", f"{netto:,}")
c2.metric("KAUF-POSITIONEN", f"{kauf:,}")
c3.metric("VERKAUF-POSITIONEN", f"{verkauf:,}")
c4.metric("MARKT-GRÖSSE", f"{gesamt_markt:,}")

# Spalte 2: Die Auswertung
st.write("---")
st.write("DATEN-ANALYSE:")
st.write(f"AKTUELLE_STRATEGIE: {'EXTREME ABSICHERUNG (SHORT)' if netto < -150000 else 'NEUTRAL'}")
st.write(f"VERKAUFS-ANTEIL AM MARKT: {anteil_verkauf:.2f}%")
st.write(f"RISIKO_ERHOLUNGSSCHUB: {'SEHR HOCH (Squeeze-Gefahr)' if anteil_verkauf > 35 else 'NORMAL'}")
st.write("---")

# Spalte 3: Historische Liste
st.write("HISTORISCHER_DATEN_STROM:")
historie = df[['Datum', 'Lev_Money_Positions_Long_All', 'Lev_Money_Positions_Short_All']].copy()
historie['NETTO'] = historie['Lev_Money_Positions_Long_All'] - historie['Lev_Money_Positions_Short_All']
historie['Datum'] = historie['Datum'].dt.strftime('%d.%m.%Y')
historie.columns = ['DATUM', 'KAUFEN (Long)', 'VERKAUFEN (Short)', 'NETTO-DIFFERENZ']
st.table(historie.head(15))
