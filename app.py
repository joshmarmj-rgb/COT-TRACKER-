import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import time

# --- SYSTEM CONFIGURATION ---
st.set_page_config(
    page_title="NASDAQ QUANTUM | Institutional Grade",
    page_icon="📟",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- TERMINAL STYLING (EXTENDED CSS ENGINE) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;500&family=Inter:wght@200;400;700&display=swap');
    
    :root {
        --bg-color: #030303;
        --surface-color: #0a0b0d;
        --border-color: #1a1c1f;
        --accent-color: #00e5ff;
        --bull-color: #00ffaa;
        --bear-color: #ff3366;
        --text-main: #e2e8f0;
        --text-dim: #64748b;
    }

    .main { background-color: var(--bg-color); color: var(--text-main); font-family: 'Inter', sans-serif; }
    .stApp { background-color: var(--bg-color); }

    /* Layout Containers */
    .terminal-card {
        background: var(--surface-color);
        border: 1px solid var(--border-color);
        padding: 24px;
        position: relative;
        transition: border 0.4s ease;
    }
    .terminal-card:hover { border-color: var(--accent-color); }
    
    .status-bar {
        font-family: 'Fira Code', monospace;
        font-size: 10px;
        color: var(--text-dim);
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 10px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
    }

    /* Typography */
    .label { font-family: 'Fira Code', monospace; font-size: 10px; text-transform: uppercase; letter-spacing: 2px; color: var(--text-dim); }
    .value-large { font-family: 'Fira Code', monospace; font-size: 36px; font-weight: 500; margin: 10px 0; color: #ffffff; }
    .delta-positive { color: var(--bull-color); font-family: 'Fira Code', monospace; font-size: 12px; }
    .delta-negative { color: var(--bear-color); font-family: 'Fira Code', monospace; font-size: 12px; }

    /* Indicators */
    .pixel-border { border-left: 3px solid var(--accent-color); padding-left: 15px; }
    .pulse {
        height: 6px; width: 6px; background: var(--bull-color); border-radius: 50%;
        display: inline-block; margin-right: 8px; box-shadow: 0 0 8px var(--bull-color);
    }

    /* Scrollbar & Streamlit Overrides */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-thumb { background: var(--border-color); }
    .stDataFrame { border: 1px solid var(--border-color) !important; }
    button[kind="primary"] { background-color: transparent; border: 1px solid var(--accent-color); color: var(--accent-color); }
    </style>
    """, unsafe_allow_html=True)

# --- ANALYTICS CORE ---
class QuantumEngine:
    def __init__(self):
        self.target_patterns = ["NASDAQ-100", "NDX", "NASDAQ 100 STOCK"]
        self.year = 2026

    @st.cache_data(ttl=3600)
    def get_institutional_flow(_self):
        url = f"https://www.cftc.gov/files/dea/history/fut_fin_txt_{_self.year}.zip"
        try:
            r = requests.get(url, timeout=15)
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                with z.open(z.namelist()[0]) as f:
                    df = pd.read_csv(f, low_memory=False)
            
            df.columns = df.columns.str.strip()
            pattern = '|'.join(_self.target_patterns)
            ndx = df[df['Market_and_Exchange_Names'].str.contains(pattern, na=False, case=False)].copy()
            
            if ndx.empty: return None

            ndx['Date'] = pd.to_datetime(ndx['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
            ndx = ndx.sort_values('Date')

            # Quantitative Metrics
            ndx['Net'] = ndx['Lev_Money_Positions_Long_All'] - ndx['Lev_Money_Positions_Short_All']
            ndx['Total'] = ndx['Lev_Money_Positions_Long_All'] + ndx['Lev_Money_Positions_Short_All']
            ndx['Conviction'] = (ndx['Lev_Money_Positions_Long_All'] / ndx['Total']) * 100
            
            # Statistics (52-Week Window)
            ndx['MA_52'] = ndx['Net'].rolling(52, min_periods=1).mean()
            ndx['STD_52'] = ndx['Net'].rolling(52, min_periods=1).std()
            ndx['Z_Score'] = (ndx['Net'] - ndx['MA_52']) / ndx['STD_52']
            
            # Momentum
            ndx['Net_Change'] = ndx['Net'].diff()
            ndx['Conv_Change'] = ndx['Conviction'].diff()
            
            return ndx
        except: return None

# --- UI COMPONENTS ---
def draw_top_bar():
    st.markdown(f"""
        <div class="status-bar">
            <div><span class="pulse"></span> SYSTEM_LIVE // NODE_01_BRD</div>
            <div>UTC {datetime.utcnow().strftime('%H:%M:%S')} // 2026-Q2</div>
        </div>
    """, unsafe_allow_html=True)

def render_metric_box(title, value, raw_delta, suffix="", is_percent=False):
    delta_class = "delta-positive" if raw_delta >= 0 else "delta-negative"
    sign = "+" if raw_delta >= 0 else ""
    formatted_delta = f"{sign}{raw_delta:.2f}%" if is_percent else f"{sign}{int(raw_delta):,}"
    
    st.markdown(f"""
        <div class="terminal-card">
            <div class="label">{title}</div>
            <div class="value-large">{value}</div>
            <div class="{delta_class}">{formatted_delta} <span style="color:var(--text-dim)">{suffix}</span></div>
        </div>
    """, unsafe_allow_html=True)

def render_expert_panel(curr, df):
    st.write("")
    col_a, col_b = st.columns([1.2, 1])
    
    with col_a:
        st.markdown('<div class="label" style="margin-bottom:15px;">Alpha Intelligence Output</div>', unsafe_allow_html=True)
        z = curr['Z_Score']
        change = curr['Net_Change']
        
        # Expert System Logic
        if z < -2.2:
            status, color, advice = "EXTREME CAPITULATION", "var(--bear-color)", "Institutionelle Short-Positionierung auf historischem Extrem. Hohes Risiko für einen 'Vertical Squeeze'. Alle Shorts decken."
        elif z < -1.0 and change < 0:
            status, color, advice = "BEARISH TREND REINFORCEMENT", "var(--text-dim)", "Hedgefonds bauen Shorts systematisch aus. Das Momentum liegt bei den Verkäufern. Trendfortsetzung wahrscheinlich."
        elif z > 1.8:
            status, color, advice = "DISTRIBUTION OVERHEAT", "var(--bull-color)", "Long-Exponierung nähert sich dem Erschöpfungspunkt. Risiko für plötzliche Gewinnmitnahmen steigt massiv."
        elif change > 15000:
            status, color, advice = "INSTITUTIONAL REVERSAL", "var(--accent-color)", "Massives Short-Covering detektiert. Das Smart Money wechselt die Richtung. Möglicher lokaler Boden."
        else:
            status, color, advice = "NEUTRAL FLOW", "white", "Keine statistische Anomalie detektiert. Markt bewegt sich im Rahmen der normalen Volatilität."

        st.markdown(f"""
            <div class="terminal-card pixel-border" style="min-height: 280px;">
                <h2 style="color:{color}; font-family:'Fira Code'; margin-top:0;">{status}</h2>
                <p style="font-size:16px; line-height:1.6;">{advice}</p>
                <div style="margin-top:30px; border-top:1px solid var(--border-color); padding-top:15px;">
                    <span class="label">Volatility Regime:</span> <span style="font-family:'Fira Code'; color:var(--accent-color);">{'HIGH' if abs(z) > 1.5 else 'NORMAL'}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="label" style="margin-bottom:15px;">Historical Context Gauge</div>', unsafe_allow_html=True)
        fig = go.Figure(go.Indicator(
            mode = "gauge+number", value = curr['Net'],
            number = {'font': {'color': 'white', 'family': 'Fira Code', 'size': 30}, 'valueformat': ','},
            gauge = {
                'axis': {'range': [df['Net'].min(), df['Net'].max()], 'tickcolor': "#475569", 'tickfont': {'size': 8}},
                'bar': {'color': "var(--accent-color)", 'thickness': 0.15},
                'bgcolor': "rgba(0,0,0,0)",
                'steps': [
                    {'range': [df['Net'].min(), df['MA_52'] - df['STD_52']], 'color': 'rgba(255, 51, 102, 0.1)'},
                    {'range': [df['MA_52'] + df['STD_52'], df['Net'].max()], 'color': 'rgba(0, 255, 170, 0.1)'}
                ],
                'threshold': {'line': {'color': "white", 'width': 2}, 'value': curr['Net']}
            }
        ))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(t=20, b=0, l=30, r=30))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# --- MAIN EXECUTION ---
def main():
    # Header
    st.markdown('<h1 style="color:white; margin-bottom:5px; font-weight:700;">NASDAQ <span style="color:var(--accent-color)">QUANTUM</span></h1>', unsafe_allow_html=True)
    draw_top_bar()

    engine = QuantumEngine()
    data = engine.get_institutional_flow()
    
    if data is not None:
        latest = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else latest
        
        # Grid System
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            render_metric_box("Net Positioning", f"{int(latest['Net']):,}", latest['Net_Change'], "Contracts")
        with c2:
            render_metric_box("Statistical Bias", f"{latest['Z_Score']:.2f} σ", latest['Z_Score'] - prev['Z_Score'], "StDev")
        with c3:
            render_metric_box("Long Conviction", f"{latest['Conviction']:.1f}%", latest['Conv_Change'], "WoW", is_percent=True)
        with c4:
            oi_change = latest['Open_Interest_All'] - prev['Open_Interest_All']
            render_metric_box("Open Interest", f"{int(latest['Open_Interest_All']):,}", oi_change, "Contracts")

        # Analysis
        render_expert_panel(latest, data)
        
        # Ledger Section
        st.write("---")
        with st.expander("DECRYPTED RAW DATA LEDGER"):
            display_df = data[['Date', 'Net', 'Net_Change', 'Z_Score', 'Conviction', 'Open_Interest_All']].copy()
            display_df = display_df.sort_values('Date', ascending=False).head(25)
            display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
        st.markdown(f'<div style="text-align:center; color:var(--text-dim); font-size:10px; margin-top:50px;">PROTOTYPE_V8_STABLE // HASH_KEY: {hash(str(latest["Date"]))}</div>', unsafe_allow_html=True)
    else:
        st.error("FAILURE: Data stream interrupted. Check CFTC Connectivity.")
        if st.button("REBOOT SYSTEM", kind="primary"): st.rerun()

if __name__ == "__main__":
    main()
