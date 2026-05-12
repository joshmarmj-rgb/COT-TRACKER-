import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# --- UI REDESIGN: HARD DATA ONLY ---
st.set_page_config(page_title="MakroBase CORE", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #000; color: #fff; font-family: 'JetBrains Mono', monospace; }
    .data-line { border-left: 3px solid #00f2ff; padding-left: 15px; margin-bottom: 20px; }
    .status-critical { color: #ff2255; font-weight: bold; }
    .status-ok { color: #00ff88; font-weight: bold; }
    table { border: 1px solid #222 !important; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_raw_feed():
    url = "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip"
    r = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
    df.columns = df.columns.str.strip()
    ndx = df[df['Market_and_Exchange_Names'].str.contains("E-MINI NASDAQ-100", na=False)].copy()
    ndx['Date'] = pd.to_datetime(ndx['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
    return ndx.sort_values('Date', ascending=False)

df = get_raw_feed()
if df is not None:
    latest = df.iloc[0]
    longs, shorts = int(latest['Lev_Money_Positions_Long_All']), int(latest['Lev_Money_Positions_Short_All'])
    net = longs - shorts
    oi = int(latest['Open_Interest_All'])
    short_ratio = (shorts / oi) * 100

    st.markdown("### [ SYSTEM_CORE_DATA_V21 ]")
    
    # Knallharte Verarbeitung
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class='data-line'>
            <span style='color:#00f2ff'>RAW_NET:</span> {net:,}<br>
            <span style='color:#00f2ff'>LONG_VAL:</span> {longs:,}<br>
            <span style='color:#00f2ff'>SHORT_VAL:</span> {shorts:,}<br>
            <span style='color:#00f2ff'>OI_TOTAL:</span> {oi:,}
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        # Logik-Prüfung statt Sätze
        status = "CRITICAL_SHORT" if net < -180000 else "NORMAL_BIAS"
        squeeze_risk = "HIGH" if short_ratio > 35 else "LOW"
        
        st.markdown(f"""
        <div class='data-line'>
            <span style='color:#00f2ff'>SIGNAL_CODE:</span> <span class='status-critical'>{status}</span><br>
            <span style='color:#00f2ff'>SHORT_RATIO:</span> {short_ratio:.2f}%<br>
            <span style='color:#00f2ff'>SQUEEZE_PROB:</span> {squeeze_risk}<br>
            <span style='color:#00f2ff'>DYN_BIAS:</span> DECREASING_EXPOSURE
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### [ HISTORICAL_LOGS ]")
    history = df[['Date', 'Lev_Money_Positions_Long_All', 'Lev_Money_Positions_Short_All']].copy()
    history['NET'] = history['Lev_Money_Positions_Long_All'] - history['Lev_Money_Positions_Short_All']
    history['Date'] = history['Date'].dt.strftime('%Y-%m-%d')
    st.table(history.head(15))
