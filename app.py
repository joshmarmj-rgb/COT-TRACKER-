import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- TERMINAL SETUP ---
st.set_page_config(page_title="NASDAQ QUANTUM V16", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #010101; color: #00f2ff; font-family: 'JetBrains Mono', monospace; }
    .card { background: #080808; border: 1px solid #1a1a1a; padding: 20px; border-radius: 4px; }
    .desc { color: #888; font-size: 12px; margin-top: 10px; line-height: 1.5; }
    .value { font-size: 40px; color: white; font-weight: 700; }
    .highlight { color: #00f2ff; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA HUB ---
@st.cache_data(ttl=3600)
def fetch_quantum_data():
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

# --- RENDER ---
df = fetch_quantum_data()
if df is not None:
    curr = df.iloc[-1]
    st.title("QUANTUM_INTELLIGENCE_NODE_v16")
    
    st.markdown("### 1. PRIMÄRE MARKT-METRIKEN")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown(f"""
        <div class='card'>
            <div style='color:#00f2ff; font-size:12px;'>NET INSTITUTIONAL POWER</div>
            <div class='value'>{int(curr['Net']):,}</div>
            <div class='desc'>
                <span class='highlight'>Definition:</span> Die Netto-Position der Hedgefonds. <br>
                Deine Zahl bedeutet: Es gibt aktuell <b>{abs(int(curr['Net']))} mehr Short-Kontrakte</b> als Long-Kontrakte. 
                Die Profis sichern sich gegen fallende Kurse ab.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""
        <div class='card'>
            <div style='color:#00f2ff; font-size:12px;'>Z-SCORE (ABWEICHUNG)</div>
            <div class='value'>{curr['Z']:.2f} σ</div>
            <div class='desc'>
                <span class='highlight'>Definition:</span> Misst, wie "extrem" die Stimmung ist. <br>
                Ein Wert von <b>0.25</b> ist neutral. Erst ab <b>±2.0</b> wird es kritisch. 
                Es signalisiert, dass die aktuelle Positionierung völlig im Rahmen der Norm liegt.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Visualizer
    st.write("")
    st.markdown("### 2. SENTIMENT GAUGE")
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=curr['Net'],
        gauge={'axis': {'range': [df['Net'].min(), df['Net'].max()]},
               'bar': {'color': "#00f2ff"}, 'bgcolor': "#080808"}
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=300)
    st.plotly_chart(fig, use_container_width=True)

    st.success(f"SYSTEM_READY // Letztes Daten-Update: {curr['Date'].strftime('%d.%m.%Y')}")

else:
    st.error("UPLINK_OFFLINE")
