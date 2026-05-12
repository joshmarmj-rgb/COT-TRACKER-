import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- TERMINAL OVERRIDE ---
st.set_page_config(page_title="NASDAQ QUANTUM", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #050505; color: #00f2ff; font-family: 'JetBrains Mono', monospace; }
    .card { background: #0a0a0a; border: 1px solid #1a1a1a; padding: 20px; border-radius: 5px; margin-bottom: 10px; }
    .jargon { color: #555; font-size: 11px; margin-top: 10px; border-top: 1px solid #1a1a1a; padding-top: 5px; }
    .value { font-size: 36px; color: white; font-weight: 700; }
    .label { font-size: 12px; color: #00f2ff; text-transform: uppercase; letter-spacing: 1px; }
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE ---
@st.cache_data(ttl=3600)
def get_quantum_data():
    try:
        # Direkter Zugriff auf die 2026er Rohdaten
        url = "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip"
        r = requests.get(url, timeout=10)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        df.columns = df.columns.str.strip()
        ndx = df[df['Market_and_Exchange_Names'].str.contains("NASDAQ-100", na=False)].copy()
        ndx['Date'] = pd.to_datetime(ndx['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
        ndx = ndx.sort_values('Date')
        # Berechnung der "Smart Money" Metriken
        ndx['Net'] = ndx['Lev_Money_Positions_Long_All'] - ndx['Lev_Money_Positions_Short_All']
        ndx['Z'] = (ndx['Net'] - ndx['Net'].rolling(26).mean()) / ndx['Net'].rolling(26).std()
        return ndx
    except: return None

# --- UI ---
# Zeitberechnung ohne pytz (Fix für den Fehler in Bildschirmfoto_12-5-2026_203449_cyzdddnva5dyqfbhq6iahv.streamlit.app.jpeg)
now_utc = datetime.utcnow()
local_ts = (now_utc + timedelta(hours=2)).strftime('%H:%M:%S')

data = get_quantum_data()

if data is not None:
    curr = data.iloc[-1]
    
    # Header
    st.markdown(f"# NASDAQ_QUANTUM_v13 // <span style='color:#555;'>SYSTEM_TIME: {local_ts}</span>", unsafe_allow_html=True)
    
    # KPI Matrix
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""<div class='card'><div class='label'>Net Exposure</div><div class='value'>{int(curr['Net']):,}</div>
        <div class='jargon'>[DECODED]: Der absolute Bias der Leveraged Funds. Positiv = Bull-Mode, Negativ = Bear-Mode.</div></div>""", unsafe_allow_html=True)
    
    with c2:
        st.markdown(f"""<div class='card'><div class='label'>Z-Score (26W)</div><div class='value'>{curr['Z']:.2f} σ</div>
        <div class='jargon'>[DECODED]: Zeigt Anomalien. >2 ist ein historischer 'Overbuy', <-2 ist ein massiver 'Panic-Sell'.</div></div>""", unsafe_allow_html=True)
    
    with c3:
        st.markdown(f"""<div class='card'><div class='label'>Data Integrity</div><div class='value'>{curr['Date'].strftime('%d.%m.%y')}</div>
        <div class='jargon'>[DECODED]: Letzter validierter Daten-Dump der CFTC (CoT-Report).</div></div>""", unsafe_allow_html=True)

    # Visualization
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=curr['Net'],
        number={'font': {'color': 'white', 'family': 'JetBrains Mono'}},
        gauge={'axis': {'range': [data['Net'].min(), data['Net'].max()], 'tickcolor': "#444"}, 
               'bar': {'color': "#00f2ff"}, 'bgcolor': "transparent"}
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(t=0,b=0,l=50,r=50))
    st.plotly_chart(fig, use_container_width=True)

    # Hacker-Stil Signal-Box
    st.markdown("### SIGNAL_OUTPUT")
    z = curr['Z']
    if z < -1.5:
        color, msg = "#ff2255", "LIQUIDITY_SQUEEZE_DETECTED // STRONG_REVERSAL_SIGNAL"
    elif z > 1.5:
        color, msg = "#00ff88", "OVERHEATED_MARKET // DISTRIBUTION_PHASE"
    else:
        color, msg = "#00f2ff", "NEUTRAL_FLOW // NO_MARKET_ANOMALY"

    st.markdown(f"""<div class='card' style='border-left: 5px solid {color};'>
        <div style='color:{color}; font-weight:700;'>{msg}</div>
        <div class='jargon'>Analyse: Das System gleicht die aktuelle Positionierung mit dem 6-Monats-Durchschnitt ab. Momentan liegt der Wert bei {z:.2f} Standardabweichungen.</div>
        </div>""", unsafe_allow_html=True)

else:
    st.error("UPLINK_FAILURE: No connection to CFTC node.")
