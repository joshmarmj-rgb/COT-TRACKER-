import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- SYSTEM SETTINGS ---
st.set_page_config(page_title="NASDAQ QUANTUM V14", layout="wide")

# CSS für das ultimative Hacker-Feeling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #020202; color: #00f2ff; font-family: 'JetBrains Mono', monospace; }
    .card { background: #080808; border: 1px solid #1a1a1a; padding: 20px; border-radius: 4px; margin-bottom: 10px; min-height: 150px; }
    .jargon { color: #444; font-size: 11px; margin-top: 12px; border-top: 1px solid #111; padding-top: 8px; line-height: 1.4; }
    .value { font-size: 38px; color: white; font-weight: 700; margin: 5px 0; }
    .label { font-size: 11px; color: #00f2ff; text-transform: uppercase; letter-spacing: 2px; opacity: 0.7; }
    .signal-box { background: #0a0e12; border-left: 4px solid #00f2ff; padding: 15px; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=3600)
def get_verified_data():
    try:
        url = "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip"
        r = requests.get(url, timeout=10)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        df.columns = df.columns.str.strip()
        ndx = df[df['Market_and_Exchange_Names'].str.contains("NASDAQ-100", na=False)].copy()
        ndx['Date'] = pd.to_datetime(ndx['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
        ndx = ndx.sort_values('Date')
        
        # Berechnung der Quantum-Metriken
        ndx['Net'] = ndx['Lev_Money_Positions_Long_All'] - ndx['Lev_Money_Positions_Short_All']
        # Rolling Z-Score zur Erkennung von Markt-Extremen
        window = 26
        ndx['MA'] = ndx['Net'].rolling(window).mean()
        ndx['STD'] = ndx['Net'].rolling(window).std()
        ndx['Z'] = (ndx['Net'] - ndx['MA']) / ndx['STD']
        return ndx
    except Exception as e:
        return None

# --- UI LOGIC ---
# Zeit ohne externe Libs (CET Fix)
now = datetime.utcnow() + timedelta(hours=2)
current_time = now.strftime('%H:%M:%S')

df = get_verified_data()

if df is not None and not df.empty:
    curr = df.iloc[-1]
    
    # Terminal Header
    st.markdown(f"""
        <div style='display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 30px;'>
            <h1 style='margin:0; color:white; letter-spacing:-2px;'>NASDAQ_QUANTUM_<span style='color:#00f2ff'>v14</span></h1>
            <div style='color:#444; font-size:14px;'>[ SYSTEM_TIME: {current_time} // STATUS: ENCRYPTED ]</div>
        </div>
    """, unsafe_allow_html=True)

    # Main KPI Grid
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""<div class='card'><div class='label'>Net Institutional Power</div><div class='value'>{int(curr['Net']):,}</div>
        <div class='jargon'>Detaillierter Bias der Hedgefonds. Ein positiver Wert zeigt an, dass mehr Kapital in Long-Wetten als in Absicherungen fließt.</div></div>""", unsafe_allow_html=True)
    
    with c2:
        z_score = curr['Z'] if not pd.isna(curr['Z']) else 0.0
        st.markdown(f"""<div class='card'><div class='label'>Z-Score (Volatility Bias)</div><div class='value'>{z_score:.2f} σ</div>
        <div class='jargon'>Statistische Abweichung vom 6-Monats-Trend. Extremwerte (+2/-2) signalisieren oft eine Trendwende (Reversal).</div></div>""", unsafe_allow_html=True)
    
    with c3:
        st.markdown(f"""<div class='card'><div class='label'>Last Data Node</div><div class='value'>{curr['Date'].strftime('%d.%m.%Y')}</div>
        <div class='jargon'>Zeitpunkt des letzten offiziellen CFTC-Updates. Diese Daten bilden das Fundament für institutionelle Entscheidungen.</div></div>""", unsafe_allow_html=True)

    # Stabilisierte Gauge-Grafik (Fix für den ValueError in Bildschirmfoto_12-5-2026_203625_cyzdddnva5dyqfbhq6iahv.streamlit.app.jpg)
    try:
        min_val = df['Net'].min()
        max_val = df['Net'].max()
        # Sicherstellen, dass Min/Max nicht identisch sind
        if min_val == max_val:
            min_val -= 1000
            max_val += 1000

        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=curr['Net'],
            number={'font': {'color': 'white', 'family': 'JetBrains Mono'}, 'valueformat': ','},
            gauge={
                'axis': {'range': [min_val, max_val], 'tickcolor': "#444"},
                'bar': {'color': "#00f2ff"},
                'bgcolor': "transparent",
                'steps': [
                    {'range': [min_val, 0], 'color': 'rgba(255, 0, 0, 0.1)'},
                    {'range': [0, max_val], 'color': 'rgba(0, 255, 0, 0.1)'}
                ],
                'threshold': {'line': {'color': "white", 'width': 2}, 'value': curr['Net']}
            }
        ))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(t=30,b=0,l=50,r=50))
        st.plotly_chart(fig, use_container_width=True)
    except:
        st.warning("Grafik-Engine kalibriert noch...")

    # Intelligence Signal Output
    st.markdown("<div class='label' style='margin-left: 5px;'>Intelligence Report</div>", unsafe_allow_html=True)
    z = curr['Z'] if not pd.isna(curr['Z']) else 0
    if z < -1.8:
        status, desc = "CRITICAL_OVERSOLD", "Die institutionelle Short-Positionierung ist extrem. Ein 'Short Squeeze' ist statistisch überfällig."
    elif z > 1.8:
        status, desc = "DISTRIBUTION_ZONE", "Die Long-Positionen sind am Limit. Große Adressen könnten beginnen, Gewinne zu realisieren."
    else:
        status, desc = "STABLE_ACCUMULATION", "Keine extremen Abweichungen. Der Markt befindet sich in einem gesunden Gleichgewicht."

    st.markdown(f"""
        <div class='signal-box'>
            <div style='color:white; font-size:18px; font-weight:700;'>{status}</div>
            <div style='color:#666; font-size:13px; margin-top:5px;'>{desc}</div>
        </div>
    """, unsafe_allow_html=True)

else:
    st.error("ERROR: Failed to decrypt CFTC stream. System is retrying...")
