import streamlit as st
import pandas as pd
import requests
import io
import zipfile

st.set_page_config(page_title="Nasdaq COT Tracker", layout="wide")
st.title("📊 Aktueller Nasdaq 100 COT Report")

@st.cache_data(ttl=60) # Cache auf 1 Minute reduziert für Fehlersuche
def get_cot_data():
    url = "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip"
    response = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        fname = z.namelist()[0]
        with z.open(fname) as f:
            # Wir laden die Daten ohne Header-Check, um Namen-Fehler zu umgehen
            df = pd.read_csv(f, low_memory=False)
    
    # Bereinigung der Spaltennamen (entfernt unsichtbare Zeichen)
    df.columns = df.columns.str.strip()
    
    # Nasdaq finden (Name ist stabil, Spaltenüberschriften oft nicht)
    nasdaq = df[df['Market_and_Exchange_Names'].str.contains("NASDAQ-100", na=False)].copy()
    
    return nasdaq

try:
    df_nasdaq = get_cot_data()
    
    if not df_nasdaq.empty:
        # Wir greifen auf die Daten zu, egal wie die Spalte genau heißt
        # 'As_of_Date_In_Form_YYMMDD' ist meistens Spalte 2
        # 'NonComm_Positions_Long_All' ist meistens Spalte 7 etc.
        
        # Um ganz sicher zu gehen, lassen wir uns die verfügbaren Spalten anzeigen
        all_cols = df_nasdaq.columns.tolist()
        
        # Suche die Spalten dynamisch
        date_col = [c for c in all_cols if "Date" in c][0]
        long_col = [c for c in all_cols if "NonComm_Positions_Long_All" in c][0]
        short_col = [c for c in all_cols if "NonComm_Positions_Short_All" in c][0]
        
        latest = df_nasdaq.iloc[0]
        netto = int(latest[long_col]) - int(latest[short_col])
        
        col1, col2 = st.columns(2)
        col1.metric("Bericht vom (YYMMDD)", latest[date_col])
        col2.metric("Netto-Position Spekulanten", f"{netto:,}")
        
        # Verlaufsdaten für den Chart
        chart_data = df_nasdaq.copy()
        chart_data['Netto'] = chart_data[long_col].astype(int) - chart_data[short_col].astype(int)
        st.line_chart(chart_data.set_index(date_col)['Netto'])
        
        st.write("### Rohdaten-Check")
        st.dataframe(df_nasdaq[[date_col, long_col, short_col]])
    else:
        st.error("Keine Nasdaq-Daten in der Datei gefunden.")
        
except Exception as e:
    st.error(f"Technischer Fehler: {e}")
    st.write("Verfügbare Spalten in der Datei:", all_cols if 'all_cols' in locals() else "Konnte Datei nicht lesen")
