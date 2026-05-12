import streamlit as st
import pandas as pd
import requests
import io
import zipfile

st.set_page_config(page_title="Nasdaq COT Tracker", layout="wide")
st.title("📊 Aktueller Nasdaq 100 COT Report")

@st.cache_data(ttl=3600)
def get_cot_data():
    url = "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip"
    response = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        fname = z.namelist()[0]
        with z.open(fname) as f:
            df = pd.read_csv(f, low_memory=False)
    
    # Spaltennamen radikal bereinigen
    df.columns = [c.strip() for c in df.columns]
    
    # Den Nasdaq-Eintrag finden
    nasdaq = df[df['Market_and_Exchange_Names'].str.contains("NASDAQ-100", na=False)].copy()
    
    # Wir nutzen die Spalten-Nummern statt Namen, falls die CFTC Namen ändert
    # Die Positionen der wichtigen Daten sind in der CSV meist fest
    # Aber wir versuchen es erst nochmal mit den Standardnamen, falls sie jetzt sauber sind
    cols_mapping = {
        'As_of_Date_In_Form_YYMMDD': 'Datum',
        'NonComm_Positions_Long_All': 'Spek_Long',
        'NonComm_Positions_Short_All': 'Spek_Short'
    }
    
    # Check welche Spalten wirklich da sind
    available_cols = [c for c in cols_mapping.keys() if c in df.columns]
    nasdaq = nasdaq[available_cols].rename(columns=cols_mapping)
    
    if 'Spek_Long' in nasdaq.columns and 'Spek_Short' in nasdaq.columns:
        nasdaq['Netto'] = nasdaq['Spek_Long'] - nasdaq['Spek_Short']
    
    return nasdaq

try:
    data = get_cot_data()
    if not data.empty:
        latest = data.iloc[0]
        st.metric("Bericht-Datum", str(latest['Datum']))
        st.metric("Netto-Position Spekulanten", f"{int(latest['Netto']):,}")
        st.line_chart(data.set_index('Datum')['Netto'])
        st.write("### Rohdaten Übersicht")
        st.dataframe(data)
    else:
        st.warning("Nasdaq-Daten konnten in der Datei nicht gefunden werden.")
except Exception as e:
    st.error(f"Fehler: {e}")
    st.info("Tipp: Die CFTC hat das Dateiformat leicht geändert. Der Code oben wurde angepasst, um dies abzufangen.")
