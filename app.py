import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# App Titel & Layout
st.set_page_config(page_title="Nasdaq COT Tracker", layout="wide")
st.title("📊 Aktueller Nasdaq 100 COT Report")
st.info("Datenquelle: CFTC.gov (Traders in Financial Futures)")

@st.cache_data(ttl=3600)  # Speichert Daten für 1 Stunde zwischen, um die CFTC-Seite zu schonen
def get_cot_data():
    # URL für das aktuelle Jahr 2026 (basiert auf der Struktur in deinem Screenshot)
    url = "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip"
    
    response = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        # Die CSV-Datei im ZIP finden und laden
        fname = z.namelist()[0]
        with z.open(fname) as f:
            df = pd.read_csv(f, low_memory=False)
            
    # Spaltennamen bereinigen (Leerzeichen entfernen)
    df.columns = df.columns.str.strip()
    
    # Nasdaq filtern
    nasdaq = df[df['Market_and_Exchange_Names'].str.contains("NASDAQ-100", na=False)].copy()
    
    # Relevante Spalten für die Anzeige
    cols = {
        'As_of_Date_In_Form_YYMMDD': 'Datum',
        'NonComm_Positions_Long_All': 'Spekulanten Long',
        'NonComm_Positions_Short_All': 'Spekulanten Short',
        'Comm_Positions_Long_All': 'Commercials Long',
        'Comm_Positions_Short_All': 'Commercials Short'
    }
    nasdaq = nasdaq[list(cols.keys())].rename(columns=cols)
    
    # Netto-Positionen berechnen
    nasdaq['Netto Spekulanten'] = nasdaq['Spekulanten Long'] - nasdaq['Spekulanten Short']
    
    return nasdaq

try:
    data = get_cot_data()
    latest = data.iloc[0]

    # Metriken anzeigen
    col1, col2, col3 = st.columns(3)
    col1.metric("Letztes Update", str(latest['Datum']))
    col2.metric("Netto-Position Spekulanten", f"{int(latest['Netto Spekulanten']):,}")
    
    # Trend-Anzeige
    if len(data) > 1:
        change = latest['Netto Spekulanten'] - data.iloc[1]['Netto Spekulanten']
        col3.metric("Veränderung zur Vorwoche", f"{int(change):,}", delta=int(change))

    # Grafik
    st.subheader("Historischer Verlauf (Netto-Positionierung)")
    st.line_chart(data.set_index('Datum')['Netto Spekulanten'])

    # Rohdaten anzeigen
    if st.checkbox("Rohdaten anzeigen"):
        st.dataframe(data)

except Exception as e:
    st.error(f"Fehler beim Laden der Daten: {e}")
    st.write("Hinweis: Es kann sein, dass die CFTC-Server kurzzeitig nicht erreichbar sind.")
