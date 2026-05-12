import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
from datetime import datetime
import pytz

# --- SYSTEM CONFIG ---
st.set_page_config(
    page_title="NASDAQ QUANTUM | V11",
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
            url = f"https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip"
            r = requests.get(url, timeout=10)
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
            df.columns = df.columns.str.strip()
            ndx = df[df['Market_and_Exchange_Names'].str.contains("NASDAQ-100", na=False, case=False)].copy()
            if ndx.empty: return None
            ndx['Date'] = pd.to_datetime(ndx['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
            ndx = ndx.sort_values('Date')
            ndx['Net'] = ndx['Lev_Money_Positions_Long_All'] - ndx['Lev_Money_Positions_Short_All']
            ndx['Z'] = (ndx['Net'] - ndx['Net'].rolling(26).mean()) / ndx['Net'].rolling(26).std()
            return ndx
        except: return None

# --- UI ---
def main():
    # Time Logic (CET/CEST)
    try:
        local_tz = pytz.timezone('Europe/Berlin')
        now = datetime.now(local_tz)
    except:
        now = datetime.now() # Fallback

    engine = QuantumEngine()
    df = engine.fetch_data()

    if df is not None:
        curr = df.iloc[-1]
        
        # Header
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"<div style='font-size:42px; font-weight:700; color:white;'>NASDAQ_<span style='color:var(--cyan)'>QUANTUM</span>_V11</div>", unsafe_allow_html=True)
            st.markdown("<div class='meta'>ACCESS_LEVEL: ARCHITECT // STATUS: STABLE</div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div style='text-align:right;'><div class='meta'>SYSTEM_TIME</div><div style='color:var(--cyan);'>{now.strftime('%H:%M:%S')}</div></div>", unsafe_allow_html=True)

        st.write("")
        
        # KPI Grid
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='terminal-box'><div class='meta'>Net Position</div><div class='kpi-val'>{int(curr['Net']):,}</div><div class='hacker-manual'>Aggregierte Power der Institutionen.</div></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='terminal-box'><div class='meta'>Z-Score</div><div class='kpi-val'>{curr['Z']:.2f} σ</div><div class='hacker-manual'>Abweichung vom 26-Wochen-Schnitt.</div></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='terminal-box'><div class='meta'>Data Date</div><div class='kpi-val'>{curr['Date'].strftime('%Y-%m-%d')}</div><div class='hacker-manual'>Letztes offizielles CFTC Release.</div></div>", unsafe_allow_html=True)

        # Gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=curr['Net'],
            number={'font': {'color': 'white', 'family': 'JetBrains Mono'}},
            gauge={'axis': {'range': [df['Net'].min(), df['Net'].max()], 'tickcolor': "#222"}, 'bar': {'color': "var(--cyan)"}, 'bgcolor': "transparent"}
        ))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(t=0,b=0,l=50,r=50))
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("BOOT_ERROR: Could not establish data link.")

if __name__ == "__main__":
    main()
