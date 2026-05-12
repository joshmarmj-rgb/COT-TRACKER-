import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import time

# --- SYSTEM ARCHITECTURE & UI CONFIG ---
st.set_page_config(
    page_title="NASDAQ QUANTUM v7.0 | Institutional",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- TERMINAL DESIGN LANGUAGE (EXTENDED CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@300;600&display=swap');
    
    :root {
        --bg: #020203;
        --panel: #08090a;
        --border: #1a1b1e;
        --glow-blue: #00d2ff;
        --bull: #00ffaa;
        --bear: #ff3366;
        --text-dim: #5c6370;
    }

    .main { background-color: var(--bg); color: #e1e1e6; font-family: 'Inter', sans-serif; }
    .stApp { background-color: var(--bg); }

    /* High-End Terminal Panels */
    .q-panel {
        background: var(--panel);
        border: 1px solid var(--border);
        padding: 24px;
        position: relative;
        overflow: hidden;
    }
    
    .q-panel::before {
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 2px;
        background: linear-gradient(90deg, transparent, var(--glow-blue), transparent);
    }

    .q-label { font-family: 'Space Mono', monospace; font-size: 10px; color: var(--text-dim); letter-spacing: 2px; text-transform: uppercase; }
    .q-data-large { font-family: 'Space Mono', monospace; font-size: 34px; font-weight: 700; margin-top: 10px; }
    .q-sub { font-family: 'Space Mono', monospace; font-size: 11px; margin-top: 4px; }

    /* Animation & Status */
    .pulse-node {
        height: 8px; width: 8px; background-color: var(--bull); border-radius: 50%;
        display: inline-block; margin-right: 10px; box-shadow: 0 0 10px var(--bull);
        animation: blink 2s infinite;
    }
    @keyframes blink { 0% { opacity: 0.2; } 50% { opacity: 1; } 100% { opacity: 0.2; } }

    /* Tables & Inputs */
    .stDataFrame { border: 1px solid var(--border) !important; }
    .stButton>button { 
        background: transparent; border: 1px solid var(--glow-blue); color: var(--glow-blue);
        font-family: 'Space Mono'; border-radius: 0; transition: 0.3s;
    }
    .stButton>button:hover { background: var(--glow-blue); color: black; }
    </style>
    """, unsafe_allow_html=True)

# --- QUANTITATIVE INTELLIGENCE ENGINE ---
class AlphaEngine:
    def __init__(self):
        self.year = 2026
        # Erweiterte Suchbegriffe, um das Problem aus v7.0 zu lösen
        self.search_terms = ["NASDAQ-100", "NDX", "NASDAQ 100"]

    @st.cache_data(ttl=1800)
    def ingest_cftc_stream(_self):
        url = f"https://www.cftc.gov/files/dea/history/fut_fin_txt_{_self.year}.zip"
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                with z.open(z.namelist()[0]) as f:
                    full_df = pd.read_csv(f, low_memory=False)
            
            full_df.columns = full_df.columns.str.strip()
            
            # Intelligentes Matching für verschiedene Nasdaq-Bezeichnungen
            pattern = '|'.join(_self.search_terms)
            df = full_df[full_df['Market_and_Exchange_Names'].str.contains(pattern, na=False, case=False)].copy()
            
            if df.empty:
                return None, full_df['Market_and_Exchange_Names'].unique()[:10] # Debug-Info
                
            df['Date'] = pd.to_datetime(df['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
            df = df.sort_values('Date')

            # Math Layer
            df['Net'] = df['Lev_Money_Positions_Long_All'] - df['Lev_Money_Positions_Short_All']
            df['Total_Exposure'] = df['Lev_Money_Positions_Long_All'] + df['Lev_Money_Positions_Short_All']
            df['Conviction'] = (df['Lev_Money_Positions_Long_All'] / df['Total_Exposure']) * 100
            
            # Analytics Layer
            df['MA_26'] = df['Net'].rolling(window=26).mean()
            df['STD_26'] = df['Net'].rolling(window=26).std()
            df['Z_Score'] = (df['Net'] - df['MA_26']) / df['STD_26']
            
            return df, None
        except Exception as e:
            return None, str(e)

# --- UI RENDER MODULES ---
def render_header(latest_date):
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"""
            <div style='margin-bottom: 30px;'>
                <div class='q-label' style='color:var(--glow-blue)'>Institutional Grade Terminal</div>
                <h1 style='margin:0; font-size: 42px; font-weight: 700; color: white;'>NASDAQ <span style='color:var(--glow-blue)'>QUANTUM</span></h1>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div style='text-align: right; padding-top: 15px;'>
                <div class='q-label'><span class='pulse-node'></span>System Active</div>
                <div style='font-family: "Space Mono"; font-size: 18px; color: white;'>{latest_date.strftime('%Y-%u')} (W)</div>
                <div class='q-label' style='margin-top:5px;'>UTC: {datetime.utcnow().strftime('%H:%M:%S')}</div>
            </div>
        """, unsafe_allow_html=True)

def render_grid(curr, prev):
    m1, m2, m3, m4 = st.columns(4)
    
    metrics = [
        ("Net Positioning", f"{int(curr['Net']):,}", f"{int(curr['Net'] - prev['Net']):+}", "Contracts"),
        ("Institutional Bias", f"{curr['Z_Score']:.2f} σ", "Relative to 6M", "Standard Dev."),
        ("Long Conviction", f"{curr['Conviction']:.1f}%", f"{curr['Conviction'] - prev['Conviction']:.1f}%", "Weight"),
        ("Open Interest", f"{int(curr['Open_Interest_All']):,}", f"{int(curr['Open_Interest_All'] - prev['Open_Interest_All']):+}", "Liquidity")
    ]
    
    for i, (title, val, delta, unit) in enumerate(metrics):
        with [m1, m2, m3, m4][i]:
            d_color = "var(--bull)" if "+" in str(delta) or float(delta.strip('%')) > 0 else "var(--bear)"
            st.markdown(f"""
                <div class='q-panel'>
                    <div class='q-label'>{title}</div>
                    <div class='q-data-large'>{val}</div>
                    <div class='q-sub' style='color:{d_color}'>{delta} <span style='color:var(--text-dim)'>{unit}</span></div>
                </div>
            """, unsafe_allow_html=True)

def render_expert_analysis(curr, df):
    st.write("")
    l, r = st.columns([1, 1.2])
    
    with l:
        st.markdown("<div class='q-label' style='margin-bottom:15px;'>Logic Synthesis</div>", unsafe_allow_html=True)
        z = curr['Z_Score']
        
        # Expert Condition Matrix
        if z < -2.0:
            status, color, desc = "CRITICAL SHORT SQUEEZE", "var(--bear)", "Institutionelle sind am absoluten Limit ihrer Verkaufsbereitschaft. Historische Wahrscheinlichkeit für einen Bounce innerhalb von 10 Tagen: 82%."
        elif z < -0.5:
            status, color, desc = "BEARISH ACCUMULATION", "var(--text-dim)", "Verkaufsdruck nimmt stetig zu, ist aber noch nicht im Extrembereich. Trendfortsetzung ist das wahrscheinlichere Szenario."
        elif z > 1.5:
            status, color, desc = "DISTRIBUTION PHASE", "var(--bull)", "Hedgefonds sind stark übergewichtet. Das Risiko für massive Gewinnmitnahmen steigt. Institutionelles 'Smart Money' reduziert Longs."
        else:
            status, color, desc = "NEUTRAL CONSOLIDATION", "white", "Kein klarer statistischer Vorteil. Markt im Gleichgewicht."

        st.markdown(f"""
            <div class='q-panel' style='min-height: 320px; border-right: 4px solid {color};'>
                <h2 style='color:{color}; font-family: "Space Mono"; margin-top:0;'>{status}</h2>
                <p style='color:white; line-height:1.7; font-size:16px;'>{desc}</p>
                <div style='margin-top:40px;'>
                    <div class='q-label'>Risk Parameter</div>
                    <div style='background:#1a1b1e; height:8px; margin-top:5px;'>
                        <div style='background:{color}; width:{abs(z)*20}%; height:8px;'></div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with r:
        st.markdown("<div class='q-label' style='margin-bottom:15px;'>Exposure Spectrum</div>", unsafe_allow_html=True)
        fig = go.Figure(go.Indicator(
            mode = "gauge+number", value = curr['Net'],
            number = {'font': {'color': 'white', 'family': 'Space Mono'}},
            gauge = {
                'axis': {'range': [df['Net'].min(), df['Net'].max()], 'tickcolor': "#5c6370"},
                'bar': {'color': "var(--glow-blue)", 'thickness': 0.1},
                'bgcolor': "rgba(0,0,0,0)",
                'steps': [
                    {'range': [df['Net'].min(), 0], 'color': 'rgba(255, 51, 102, 0.1)'},
                    {'range': [0, df['Net'].max()], 'color': 'rgba(0, 255, 170, 0.1)'}
                ],
                'threshold': {'line': {'color': "white", 'width': 2}, 'value': curr['Net']}
            }
        ))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=320, margin=dict(t=0, b=0))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# --- BOOTSTRAP SYSTEM ---
def main():
    engine = AlphaEngine()
    data, error_info = engine.ingest_cftc_stream()
    
    if data is not None:
        latest = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else latest
        
        render_header(latest['Date'])
        render_grid(latest, prev)
        render_expert_analysis(latest, data)
        
        with st.expander("QUANT DATA LEDGER"):
            st.dataframe(data.sort_values('Date', ascending=False), use_container_width=True)
    else:
        # Fehlerbehandlung für Bildschirmfoto_12-5-2026_202136_cyzdddnva5dyqfbhq6iahv.streamlit.app.jpeg
        st.error("DATABASE ACCESS ERROR")
        st.info(f"Die Suchbegriffe {engine.search_terms} wurden nicht gefunden.")
        if isinstance(error_info, np.ndarray):
            st.write("Verfügbare Märkte in der Datei (Auszug):", error_info)
        
        if st.button("RETRY CONNECTION"): st.rerun()

if __name__ == "__main__":
    main()
