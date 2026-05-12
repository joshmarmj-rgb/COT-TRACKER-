import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import pytz

# --- CORE CONFIG ---
st.set_page_config(
    page_title="QUANTUM TERMINAL | ARCHITECT",
    page_icon="🕶️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ADVANCED HACKER UI ENGINE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@100;400;700&display=swap');
    
    :root {
        --bg-main: #020202;
        --panel-bg: #0a0a0b;
        --border-cyan: #00f2ff;
        --border-dim: #1e1e1e;
        --bull: #00ff88;
        --bear: #ff2255;
        --text-main: #d1d5db;
    }

    .stApp { background-color: var(--bg-main); color: var(--text-main); }
    .main { font-family: 'JetBrains Mono', monospace; }

    /* Terminal Containers */
    .terminal-box {
        background: var(--panel-bg);
        border: 1px solid var(--border-dim);
        padding: 20px;
        margin-bottom: 15px;
        position: relative;
    }
    .terminal-box:hover { border-color: var(--border-cyan); }

    /* Typography */
    .meta-tag { font-size: 10px; color: #555; letter-spacing: 1px; text-transform: uppercase; }
    .glitch-header { font-size: 42px; font-weight: 700; color: white; letter-spacing: -2px; }
    .kpi-val { font-size: 32px; font-weight: 100; color: #fff; margin: 8px 0; }
    
    /* Help Tooltips Simulation */
    .hacker-manual {
        font-size: 11px; color: #00f2ff; border-left: 2px solid #00f2ff;
        padding-left: 10px; margin-top: 10px; opacity: 0.7;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 3px; }
    ::-webkit-scrollbar-thumb { background: var(--border-cyan); }
    
    /* System Elements */
    .stTooltipIcon { display: none; } /* Hide default icon */
    </style>
    """, unsafe_allow_html=True)

# --- BACKEND LOGIC ---
class IntelligenceEngine:
    def __init__(self):
        self.year = 2026
        self.names = ["NASDAQ-100", "NDX", "NASDAQ 100"]

    @st.cache_data(ttl=3600)
    def fetch_payload(_self):
        try:
            url = f"https://www.cftc.gov/files/dea/history/fut_fin_txt_{_self.year}.zip"
            r = requests.get(url, timeout=12)
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
            
            df.columns = df.columns.str.strip()
            pattern = '|'.join(_self.names)
            ndx = df[df['Market_and_Exchange_Names'].str.contains(pattern, na=False, case=False)].copy()
            
            if ndx.empty: return None

            ndx['Date'] = pd.to_datetime(ndx['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
            ndx = ndx.sort_values('Date')

            # Calculation Matrix
            ndx['Net'] = ndx['Lev_Money_Positions_Long_All'] - ndx['Lev_Money_Positions_Short_All']
            ndx['OI'] = ndx['Open_Interest_All']
            ndx['Conv'] = (ndx['Lev_Money_Positions_Long_All'] / (ndx['Lev_Money_Positions_Long_All'] + ndx['Lev_Money_Positions_Short_All'])) * 100
            
            # Stat Anomaly detection
            ndx['Z'] = (ndx['Net'] - ndx['Net'].rolling(26).mean()) / ndx['Net'].rolling(26).std()
            
            # Deltas
            ndx['dNet'] = ndx['Net'].diff()
            ndx['dZ'] = ndx['Z'].diff()
            ndx['dConv'] = ndx['Conv'].diff()
            ndx['dOI'] = ndx['OI'].diff()

            return ndx
        except: return None

# --- UI COMPONENTS ---
def draw_header(data_date):
    # Time Sync: Europe/Berlin
    tz = pytz.timezone('Europe/Berlin')
    now = datetime.now(tz)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
            <div class='glitch-header'>NASDAQ_<span style='color:var(--border-cyan)'>QUANTUM</span>_v10</div>
            <div class='meta-tag'>STATUS: ARCHITECT_LEVEL_ACCESS // NODE_01_ACTIVE</div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div style='text-align: right; border-left: 1px solid var(--border-dim); padding-left: 20px;'>
                <div class='meta-tag'>DATA_TIMESTAMP</div>
                <div style='font-size: 18px; color:white;'>{data_date.strftime('%Y-%m-%d')}</div>
                <div class='meta-tag' style='margin-top:10px;'>LOCAL_SYSTEM_TIME</div>
                <div style='font-size: 14px; color:var(--border-cyan);'>{now.strftime('%H:%M:%S')} (CET)</div>
            </div>
        """, unsafe_allow_html=True)

def render_kpi(label, value, delta, manual_text, is_z=False):
    color = "var(--bull)" if delta >= 0 else "var(--bear)"
    sym = "+" if delta >= 0 else ""
    d_str = f"{sym}{delta:.2f}" if is_z else f"{sym}{int(delta):,}"
    
    st.markdown(f"""
        <div class='terminal-box'>
            <div class='meta-tag'>{label}</div>
            <div class='kpi-val'>{value}</div>
            <div style='color:{color}; font-size:11px;'>{d_str} <span style='color:#444'>vs PREV</span></div>
            <div class='hacker-manual'>DECODED: {manual_text}</div>
        </div>
    """, unsafe_allow_html=True)

# --- MAIN LOOP ---
def main():
    engine = IntelligenceEngine()
    df = engine.fetch_payload()
    
    if df is not None:
        curr = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else curr
        
        draw_header(curr['Date'])
        st.write("")

        # Metrics Layer
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_kpi("Net Positioning", f"{int(curr['Net']):,}", curr['dNet'], 
                       "Die Netto-Power der Big Player. Negativ = Short-Dominanz.")
        with c2:
            render_kpi("Z-Score (26W)", f"{curr['Z']:.2f} σ", curr['dZ'], 
                       "Statistisches Rauschen. >2 oder <-2 signalisiert Anomalien.", True)
        with c3:
            render_kpi("Long Conviction", f"{curr['Conv']:.1f}%", curr['dConv'], 
                       "Prozentualer Anteil der Long-Positionen am Gesamtvolumen.")
        with c4:
            render_kpi("Open Interest", f"{int(curr['OI']):,}", curr['dOI'], 
                       "Gesamtliquidität im Markt. Steigendes OI bestätigt den Trend.")

        # Intelligence Panel
        st.write("")
        col_l, col_r = st.columns([1.5, 1])
        
        with col_l:
            st.markdown("<div class='meta-tag'>Signal Matrix</div>", unsafe_allow_html=True)
            z = curr['Z']
            if z < -2: state, hint = "FORCE_BUY", "Historisches Short-Level erreicht. Erwarte massives Short-Covering (Squeeze)."
            elif z > 2: state, hint = "FORCE_EXIT", "Long-Exponierung am Limit. Gefahr von Liquidations-Kaskaden."
            else: state, hint = "HOLD_POSITION", "Markt bewegt sich innerhalb der statistischen Erwartung."
            
            st.markdown(f"""
                <div class='terminal-box' style='border-left: 5px solid var(--border-cyan); min-height: 200px;'>
                    <h2 style='color:white; margin:0;'>{state}</h2>
                    <p style='color:#888; font-size:14px; margin-top:10px;'>{hint}</p>
                    <div class='hacker-manual' style='margin-top:30px;'>
                        ANALYSIS: Das System korreliert Z-Score Abweichungen mit dem 'Net Change'. 
                        Ein steigender Z-Score bei fallenden Preisen indiziert 'Divergence'.
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with col_r:
            st.markdown("<div class='meta-tag'>Liquidity Gauge</div>", unsafe_allow_html=True)
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=curr['Net'],
                number={'font': {'color': 'white', 'family': 'JetBrains Mono'}},
                gauge={
                    'axis': {'range': [df['Net'].min(), df['Net'].max()], 'tickcolor': "#222"},
                    'bar': {'color': "var(--border-cyan)"},
                    'bgcolor': "rgba(0,0,0,0)",
                    'steps': [{'range': [df['Net'].min(), 0], 'color': 'rgba(255,0,0,0.05)'}]
                }
            ))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=220, margin=dict(t=0,b=0,l=20,r=20))
            st.plotly_chart(fig, use_container_width=True)

        # Footer Ledger
        with st.expander("ACCESS_RAW_LOGS"):
            st.dataframe(df.sort_values('Date', ascending=False).head(20), use_container_width=True)
            
        st.markdown(f"<div style='text-align:center; margin-top:50px;' class='meta-tag'>END_OF_TRANSMISSION // UID: {hash(str(curr['Date']))}</div>", unsafe_allow_html=True)

    else:
        st.error("CONNECTION_ERROR: CFTC_SERVER_NOT_RESPONDING")

if __name__ == "__main__":
    main()
