import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- SYSTEM CONFIG ---
st.set_page_config(
    page_title="NASDAQ QUANTUM | V12",
    page_icon="🕶️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- TERMINAL STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@100;400;700&display=swap');
    :root { --cyan: #00f2ff; --bg: #020202; --panel: #0a0a0b; --bull: #00ff88; --bear: #ff2255; }
    .stApp { background-color: var(--bg); color: #d1d5db; font-family: 'JetBrains Mono', monospace; }
    .terminal-box { background: var(--panel); border: 1px solid #1e1e1e; padding: 20px; margin-bottom: 15px; }
    .meta { font-size: 10px; color: #555; letter-spacing: 1px; text-transform: uppercase; }
    .kpi-val { font-size: 32px; font-weight: 100; color: #fff; margin: 8px 0; }
    .hacker-manual { font-size: 11px; color: var(--cyan); border-left: 2px solid var(--cyan); padding-left: 10px; margin-top: 10px; opacity: 0.8; }
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE ---
class QuantumEngine:
    @st.cache_data(ttl=3600)
    def fetch_data(_self):
        try:
            # Wir greifen auf die 2026er Daten zu
            url = "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip"
            r = requests.get(url, timeout=10)
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
            
            df.columns = df.columns.str.strip()
            # Robuste Filterung
            ndx = df[df['Market_and_Exchange_Names'].str.contains("NASDAQ-100", na=False, case=False)].copy()
            
            if ndx.empty: return None
            
            ndx['Date'] = pd.to_datetime(ndx['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
            ndx = ndx.sort_values('Date')
            
            # Kern-Metriken
            ndx['Net'] = ndx['Lev_Money_Positions_Long_All'] - ndx['Lev_Money_Positions_Short_All']
            # Z-Score Berechnung (26-Wochen-Fenster)
            ndx['Z'] = (ndx['Net'] - ndx['Net'].rolling(26).mean()) / ndx['Net'].rolling(26).std()
            
            return ndx
        except:
            return None

# --- MAIN INTERFACE ---
def main():
    # Zeitberechnung ohne pytz (CET ist UTC+2 im Mai wegen Sommerzeit)
    # Wir nutzen den UTC-Offset direkt
    utc_now = datetime.utcnow()
    local_time = utc_now + timedelta(hours=2) 

    engine = QuantumEngine()
    df = engine.fetch_data()

    if df is not None:
        curr = df.iloc[-1]
        
        # Header
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown("<div style='font-size:42px; font-weight:700; color:white;'>NASDAQ_<span style='color:var(--cyan)'>QUANTUM</span>_V12</div>", unsafe_allow_html=True)
            st.markdown("<div class='meta'>ACCESS_LEVEL: ARCHITECT // STATUS: DEPLOYED_STABLE</div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div style='text-align:right;'><div class='meta'>SYSTEM_TIME (CET)</div><div style='color:var(--cyan);'>{local_time.strftime('%H:%M:%S')}</div></div>", unsafe_allow_html=True)

        st.write("")
        
        # KPI GRID MIT DEKODIERUNG
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
                <div class='terminal-box'>
                    <div class='meta'>Net Position</div>
                    <div class='kpi-val'>{int(curr['Net']):,}</div>
                    <div class='hacker-manual'>DECODED: Das ist die Summe der Long- abzüglich der Short-Kontrakte. Ein hoher positiver Wert bedeutet, die Big Boys setzen auf steigende Kurse.</div>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div class='terminal-box'>
                    <div class='meta'>Z-Score (Volatility)</div>
                    <div class='kpi-val'>{curr['Z']:.2f} σ</div>
                    <div class='hacker-manual'>DECODED: Misst, wie "ungewöhnlich" die Positionierung ist. Werte über 2 oder unter -2 deuten auf eine massive Übertreibung hin.</div>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
                <div class='terminal-box'>
                    <div class='meta'>Last Release</div>
                    <div class='kpi-val'>{curr['Date'].strftime('%Y-%m-%d')}</div>
                    <div class='hacker-manual'>DECODED: Das Datum des letzten offiziellen Berichts der CFTC. Die Daten kommen immer mit einer leichten Verzögerung.</div>
                </div>
            """, unsafe_allow_html=True)

        # GAUGE VISUALIZATION
        fig = go.Figure(go.Indicator(
            mode="gauge+number", 
            value=curr['Net'],
            number={'font': {'color': 'white', 'family': 'JetBrains Mono'}, 'valueformat': ','},
            gauge={
                'axis': {'range': [df['Net'].min(), df['Net'].max()], 'tickcolor': "#444"},
                'bar': {'color': "var(--cyan)"},
                'bgcolor': "transparent",
                'steps': [
                    {'range': [df['Net'].min(), 0], 'color': 'rgba(255, 34, 85, 0.1)'},
                    {'range': [0, df['Net'].max()], 'color': 'rgba(0, 255, 136, 0.1)'}
                ]
            }
        ))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=350, margin=dict(t=20,b=20,l=50,r=50))
        st.plotly_chart(fig, use_container_width=True)

        # SIGNAL OUTPUT
        st.markdown("<div class='meta'>Logic Analysis</div>", unsafe_allow_html=True)
        z_val = curr['Z']
        if z_val < -2:
            signal = "EXTREME_SHORT_EXPOSURE // REVERSAL_PROBABLE"
        elif z_val > 2:
            signal = "EXTREME_LONG_EXPOSURE // COOLOFF_EXPECTED"
        else:
            signal = "MARKET_EQUILIBRIUM // NO_ANOMALY"
            
        st.markdown(f"""
            <div class='terminal-box' style='border-left: 4px solid var(--cyan);'>
                <div style='color:white; font-size:18px;'>{signal}</div>
                <div class='hacker-manual'>Die statistische Analyse sieht momentan keine extremen Ausreißer. Der Markt folgt dem regulären Kapitalfluss.</div>
            </div>
        """, unsafe_allow_html=True)

    else:
        st.error("BOOT_ERROR: Neural Link to CFTC failed. Check Uplink.")

if __name__ == "__main__":
    main()
