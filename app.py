import streamlit as st
import pandas as pd
import requests
import io
import zipfile

st.set_page_config(page_title="Nasdaq COT Tracker", layout="wide")
st.title("📊 Aktueller Nasdaq 100 COT Report (TFF)")

@st.cache_data(ttl=3600)
def get_cot_data():
    url = "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip"
    response = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        fname = z.namelist()[0]
        with z.open(fname) as f:
            df = pd.read_csv(f, low_memory=False)
    
    # Spaltennamen säubern
    df.columns = df.columns.str.strip()
    
    # Nasdaq filtern
    nasdaq = df[df['Market_and_Exchange_Names'].str.contains("NASDAQ-100", na=False)].copy()
    
    # In Financial Futures (TFF) sind 'Leveraged Funds' die Spekulanten
    cols_mapping = {
        'As_of_Date_In_Form_YYMMDD': 'Datum',
        'Lev_Money_Positions_Long_All': 'Hedgefonds_Long',
        'Lev_Money_Positions_Short_All': 'Hedgefonds_Short',
        'Asset_Mgr_Positions_Long_All': 'Insti_Long',
        'Asset_Mgr_Positions_Short_All': 'Insti_Short'
    }
    
    # Nur vorhandene Spalten nehmen
    active_cols = [c for c in cols_mapping.keys() if c in nasdaq.columns]
    nasdaq = nasdaq[active_cols].rename(columns=cols_mapping)
    
    # Netto-Position der Hedgefonds (Leveraged Money) berechnen
    if 'Hedgefonds_Long' in nasdaq.columns:
        nasdaq['Netto_Hedgefonds'] = nasdaq['Hedgefonds_Long'] - nasdaq['Hedgefonds_Short']
    
    return nasdaq

try:
    data = get_cot_data()
    if not data.empty:
        latest = data.iloc[0]
        
        col1, col2 = st.columns(2)
        col1.metric("Bericht vom", str(latest['Datum']))
        if 'Netto_Hedgefonds' in latest:
            col2.metric("Netto Hedgefonds (Lev Money)", f"{int(latest['Netto_Hedgefonds']):,}")
            
            st.subheader("Verlauf: Netto-Positionierung der Hedgefonds")
            st.line_chart(data.set_index('Datum')['Netto_Hedgefonds'])
        
        st.write("### Detaildaten")
        st.dataframe(data)
    else:
        st.error("Keine Nasdaq-Daten gefunden.")
except Exception as e:
    st.error(f"Fehler: {e}")
