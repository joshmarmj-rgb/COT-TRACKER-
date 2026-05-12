import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- SYSTEM CONFIG ---
st.set_page_config(page_title="NASDAQ QUANTUM V15", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #010101; color: #00f2ff; font-family: 'JetBrains Mono', monospace; }
    .card { background: #080808; border: 1px solid #1a1a1a; padding: 20px; border-radius: 4px; margin-bottom: 10px; }
    .jargon { color: #444; font-size: 11px; margin-top: 12px; border-top: 1px solid #111; padding-top: 8px; }
    .value { font-size: 38px; color: white; font-weight: 700; }
    .label { font-size: 11px; color: #00f2ff; text-transform: uppercase; letter-spacing: 2px; opacity: 0.6; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=3600)
def get_data():
    try:
        url = "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip"
        r = requests.get(url, timeout=10)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        df.columns = df.columns.str.strip()
        ndx = df[df['Market_and_Exchange_Names'].str.contains("NASDAQ-100", na=False)].copy()
        ndx['Date'] = pd.to_datetime(ndx['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
        ndx = ndx.sort_values('Date')
        ndx['Net'] = ndx['Lev_Money_Positions_Long_All'] - ndx['Lev_Money_Positions_Short_All']
        ndx['Z'] = (ndx['Net'] - ndx['Net'].rolling(26).mean()) / ndx['Net'].rolling(26).std()
        return ndx
    except: return None

# --- UI RENDER ---
df = get_data()
now = datetime.utcnow() + timedelta(hours=2) # CET Adjustment

if df is not None:
    curr = df.iloc[-1]
    
    st.markdown(f"## NASDAQ_QUANTUM_v15 <span style='font-size:12px; color:#333;'>// SYNC_TIME: {now.strftime('%H:%M:%S')}</span>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='card'><div class='label'>Net Power</div><div class='value'>{int(curr['Net']):,}</div><div class='jargon'>Institutionelles Delta. Negativ = Hedging-Überhang.</div></div>", unsafe_allow_html=True)
    with c2:
        z = curr['Z'] if not pd.isna(curr['Z']) else 0.0
        st.markdown(f"<div class='card'><div class='label'>Z-Score</div><div class='value'>{z:.2f} σ</div><div class='jargon'>Markt-Spannung. Alles zwischen -1 und +1 ist Grundrauschen.</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='card'><div class='label'>Data Node</div><div class='value'>{curr['Date'].strftime('%d.%m.%y')}</div><div class='jargon'>Letzter CoT-Report Release.</div></div>", unsafe_allow_html=True)

    # Verbessertes Gauge (Kein Kalibrierungs-Fehler mehr)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=curr['Net'],
        gauge={'axis': {'range': [df['Net'].min()*1.1, df['Net'].max()*1.1], 'tickcolor': "#444"},
               'bar': {'color': "#00f2ff"}, 'bgcolor': "black"}
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=280, margin=dict(t=20,b=20,l=50,r=50))
    st.plotly_chart(fig, use_container_width=True)

    # Signal Decoder
    sig = "NEUTRAL" if abs(z) < 1.5 else ("BULLISH_DIVERGENCE" if z < -1.5 else "BEARISH_EXHAUSTION")
    st.info(f"CORE_SIGNAL: {sig} // Das System empfiehlt: Keine überhasteten Trades. Warte auf Z-Score Ausbruch > 2.0.")

else:
    st.error("UPLINK_FAILURE")
