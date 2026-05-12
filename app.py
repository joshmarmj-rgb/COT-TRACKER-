import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# --- TERMINAL CONFIG ---
st.set_page_config(page_title="MakroBase_RAW", layout="wide")
st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500&display=swap');
    * { background-color: #000 !important; color: #00ff41 !important; font-family: 'JetBrains Mono', monospace !important; }
    .stTable, table { border: 1px solid #00ff41 !important; }
    thead tr th { background-color: #003311 !important; color: #00ff41 !important; }
    .css-1offfwp { display: none; } /* Remove Streamit Header */
</style>""", unsafe_allow_html=True)

# --- ENGINE ---
@st.cache_data(ttl=600)
def get_matrix_data():
    url = "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip"
    r = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
    df.columns = df.columns.str.strip()
    # Hard-Filter: E-Mini Nasdaq 100
    df = df[df['Market_and_Exchange_Names'].str.contains("E-MINI NASDAQ-100", na=False)].copy()
    df['Date'] = pd.to_datetime(df['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
    return df.sort_values('Date', ascending=False)

df = get_matrix_data()
current = df.iloc[0]

# --- CALCULATIONS ---
l, s = int(current['Lev_Money_Positions_Long_All']), int(current['Lev_Money_Positions_Short_All'])
net = l - s
oi = int(current['Open_Interest_All'])
ratio = (s / oi) * 100
bias_code = "ALPHA_SHORT_EXTREME" if net < -150000 else "BETA_NEUTRAL"

# --- OUTPUT ---
st.write(f"SYSTEM_TIME: {current['Date'].strftime('%Y-%m-%d')} // NODE: NASDAQ_E_MINI")
st.write("---")

# Row 1: Hard Metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("NET_POWER", f"{net:,}")
c2.metric("LONG_VAL", f"{l:,}")
c3.metric("SHORT_VAL", f"{s:,}")
c4.metric("OI_TOTAL", f"{oi:,}")

# Row 2: Logic Processing
st.write("---")
st.write(f"PROCESSED_BIAS: {bias_code}")
st.write(f"SHORT_EXPOSURE: {ratio:.2%}")
st.write(f"SQUEEZE_THRESHOLD: {'> 35% (CRITICAL)' if ratio > 35 else 'STABLE'}")
st.write("---")

# Row 3: Raw Historical Log
st.write("HISTORICAL_FEED_RAW:")
history = df[['Date', 'Lev_Money_Positions_Long_All', 'Lev_Money_Positions_Short_All']].copy()
history['NET'] = history['Lev_Money_Positions_Long_All'] - history['Lev_Money_Positions_Short_All']
history.columns = ['TIMESTAMP', 'LONGS', 'SHORTS', 'NET_DELTA']
st.table(history.head(15))
