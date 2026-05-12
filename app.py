import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import time

# --- SYSTEM INITIALIZATION ---
# Wir setzen das Layout auf Wide und verbergen das Standard-Menü für den Terminal-Look.
st.set_page_config(
    page_title="NASDAQ QUANTUM | Institutional Terminal",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- PROFESSIONAL TERMINAL CSS ENGINE ---
# Wir nutzen über 80 Zeilen CSS, um das Standard-Streamlit-Design komplett zu überschreiben.
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@100;400;700&display=swap');
    
    :root {
        --bg-main: #010101;
        --panel-bg: #080808;
        --border-dim: #161616;
        --cyan-glow: #00f2ff;
        --bull-green: #00ff88;
        --bear-red: #ff2255;
        --text-silver: #c0c0c8;
        --text-dim: #44444a;
    }

    /* Global Overrides */
    .stApp { background-color: var(--bg-main); color: var(--text-silver); }
    .main { background-color: var(--bg-main); font-family: 'JetBrains Mono', monospace; }
    
    /* Terminal Panels */
    .quantum-card {
        background: var(--panel-bg);
        border: 1px solid var(--border-dim);
        padding: 25px;
        position: relative;
        overflow: hidden;
        margin-bottom: 20px;
    }
    
    .quantum-card::after {
        content: ""; position: absolute; top: 0; left: 0; width: 2px; height: 100%;
        background: var(--cyan-glow); opacity: 0.5;
    }

    /* Metrics & Typography */
    .t-label { color: var(--text-dim); font-size: 10px; letter-spacing: 2px; text-transform: uppercase; font-weight: 700; }
    .t-value { color: #ffffff; font-size: 34px; font-weight: 100; margin: 12px 0; }
    .t-delta { font-size: 11px; font-family: 'JetBrains Mono'; }
    .t-bull { color: var(--bull-green); }
    .t-bear { color: var(--bear-red); }

    /* Custom UI Elements */
    .status-pill {
        display: inline-block; padding: 2px 10px; border: 1px solid var(--text-dim);
        font-size: 9px; color: var(--text-dim); border-radius: 2px;
    }
    .pulse {
        height: 6px; width: 6px; background-color: var(--bull-green); border-radius: 50%;
        display: inline-block; margin-right: 8px; box-shadow: 0 0 10px var(--bull-green);
    }

    /* DataFrame Styling */
    .stDataFrame { border: 1px solid var(--border-dim) !important; background: var(--panel-bg); }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CORE DATA & ANALYTICS ENGINE ---
class QuantumDataEngine:
    """Zentrale Einheit für Datenbeschaffung, Filterung und mathematische Analyse."""
    
    def __init__(self):
        self.year = 2026
        # Wir decken alle Namensvarianten ab, um Filterfehler zu vermeiden.
        self.valid_names = ["NASDAQ-100", "NDX", "NASDAQ 100", "NASDAQ-100 STOCK INDEX"]

    @st.cache_data(ttl=3600)
    def fetch_stream(_self):
        url = f"https://www.cftc.gov/files/dea/history/fut_fin_txt_{_self.year}.zip"
        try:
            response = requests.get(url, timeout=10)
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                with z.open(z.namelist()[0]) as f:
                    df = pd.read_csv(f, low_memory=False)
            
            df.columns = df.columns.str.strip()
            # Robuste Filterlogik
            mask = df['Market_and_Exchange_Names'].str.contains('|'.join(_self.valid_names), na=False, case=False)
            ndx = df[mask].copy()
            
            if ndx.empty:
                return None
            
            ndx['Date'] = pd.to_datetime(ndx['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
            ndx = ndx.sort_values('Date')

            # Quantitative Transformationen
            ndx['Netto'] = ndx['Lev_Money_Positions_Long_All'] - ndx['Lev_Money_Positions_Short_All']
            ndx['Total_Ex'] = ndx['Lev_Money_Positions_Long_All'] + ndx['Lev_Money_Positions_Short_All']
            ndx['Conviction'] = (ndx['Lev_Money_Positions_Long_All'] / ndx['Total_Ex']) * 100
            
            # Statistische Glättung (26 Wochen Fenster)
            window = 26
            ndx['Net_MA'] = ndx['Netto'].rolling(window).mean()
            ndx['Net_STD'] = ndx['Netto'].rolling(window).std()
            ndx['Z_Score'] = (ndx['Netto'] - ndx['Net_MA']) / ndx['Net_STD']
            
            # Differenzen für Delta-Analyse
            ndx['Net_Change'] = ndx['Netto'].diff()
            ndx['OI_Change'] = ndx['Open_Interest_All'].diff()
            
            return ndx
        except Exception:
            return None

# --- UI COMPONENT LIBRARY ---
def draw_header(current_date):
    """Rendered den Terminal-Header mit Status-Informationen."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
            <div style='margin-bottom: 30px;'>
                <div class='t-label' style='color:var(--cyan-glow)'>QUANTUM ANALYTICS // NODE_01</div>
                <h1 style='margin:0; font-size: 48px; font-weight: 100; color: white; letter-spacing: -2px;'>
                    NASDAQ <span style='font-weight: 700; color:var(--cyan-glow)'>100</span> CORE
                </h1>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div style='text-align: right; padding-top: 10px;'>
                <div class='status-pill'><span class='pulse'></span> SYSTEM_UP_STREAM</div>
                <div style='font-size: 22px; font-weight: 700; margin-top: 5px;'>{current_date.strftime('%Y-%m-%d')}</div>
                <div class='t-label'>UTC: {datetime.utcnow().strftime('%H:%M:%S')}</div>
            </div>
        """, unsafe_allow_html=True)

def render_kpi(label, value, delta, is_zscore=False):
    """Generiert eine einzelne KPI-Karte mit intelligenter Farbsteuerung."""
    # Stabile Farblogik ohne Typ-Umwandlungsfehler
    if is_zscore:
        color_class = "t-bull" if delta > 0 else "t-bear"
        delta_str = f"{delta:+.2f} σ"
    else:
        color_class = "t-bull" if delta >= 0 else "t-bear"
        delta_str = f"{int(delta):+,}" if not is_zscore else ""

    st.markdown(f"""
        <div class='quantum-card'>
            <div class='t-label'>{label}</div>
            <div class='t-value'>{value}</div>
            <div class='t-delta {color_class}'>{delta_str} <span style='color:var(--text-dim)'>vs PREV</span></div>
        </div>
    """, unsafe_allow_html=True)

def render_intelligence_panel(curr, df):
    """Berechnet und zeigt das Markt-Regime und die Gauges an."""
    col_l, col_r = st.columns([1, 1.2])
    
    with col_l:
        st.markdown("<div class='t-label' style='margin-bottom:15px;'>Decision Matrix</div>", unsafe_allow_html=True)
        z = curr['Z_Score']
        
        # Expert Logic Matrix
        if z < -2.1:
            title, mood, border = "CRITICAL_OVERSOLD", "Hedgefonds am historischen Verkaufslimit. Hohe Squeeze-Wahrscheinlichkeit.", "var(--bear-red)"
        elif z < -1.0:
            title, mood, border = "BEARISH_FLOW", "Trend ist intakt. Institutionelle erhöhen Short-Exposition moderat.", "var(--text-dim)"
        elif z > 1.8:
            title, mood, border = "OVERBOUGHT_LIMIT", "Markt ist überhitzt. Institutionelle beginnen mit Distribution.", "var(--bull-green)"
        else:
            title, mood, border = "NEUTRAL_STANCE", "Seitwärts-Momentum. Keine signifikante Abweichung vom Mittelwert.", "white"

        st.markdown(f"""
            <div class='quantum-card' style='border-right: 4px solid {border}; min-height: 280px;'>
                <h2 style='color:white; margin-top:0;'>{title}</h2>
                <p style='color:var(--text-silver); font-size:16px; line-height:1.6;'>{mood}</p>
                <div style='margin-top:40px;'>
                    <div class='t-label'>Volatility Regime</div>
                    <div style='background:var(--border-dim); height:4px; margin-top:10px;'>
                        <div style='background:var(--cyan-glow); width:{abs(z)*20}%; height:4px;'></div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_r:
        st.markdown("<div class='t-label' style='margin-bottom:15px;'>Relative Exposure Index</div>", unsafe_allow_html=True)
        # Stabile Plotly-Implementierung ohne 'config'-Argument für maximale Kompatibilität
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = curr['Netto'],
            number = {'font': {'color': 'white', 'family': 'JetBrains Mono', 'size': 32}, 'valueformat': ','},
            gauge = {
                'axis': {'range': [df['Netto'].min(), df['Netto'].max()], 'tickcolor': "#44444a"},
                'bar': {'color': "var(--cyan-glow)", 'thickness': 0.1},
                'bgcolor': "rgba(0,0,0,0)",
                'steps': [
                    {'range': [df['Netto'].min(), 0], 'color': 'rgba(255, 34, 85, 0.1)'},
                    {'range': [0, df['Netto'].max()], 'color': 'rgba(0, 255, 136, 0.1)'}
                ],
                'threshold': {'line': {'color': "white", 'width': 3}, 'value': curr['Netto']}
            }
        ))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=280, margin=dict(t=0, b=0, l=40, r=40))
        st.plotly_chart(fig, use_container_width=True) # FIX: config entfernt für Bildschirmfoto_12-5-2026_202517_cyzdddnva5dyqfbhq6iahv.streamlit.app.jpg

# --- BOOTSTRAP PROCESS ---
def main():
    engine = QuantumDataEngine()
    df = engine.fetch_stream()
    
    if df is not None:
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        # 1. Header
        draw_header(latest['Date'])
        
        # 2. Top Metrics Grid
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_kpi("Net Positioning", f"{int(latest['Netto']):,}", latest['Net_Change'])
        with c2:
            render_kpi("Z-Score (26W)", f"{latest['Z_Score']:.2f}", latest['Z_Score'] - prev['Z_Score'], is_zscore=True)
        with c3:
            # Conviction Delta
            render_kpi("Long Conviction", f"{latest['Conviction']:.1f}%", latest['Conviction'] - prev['Conviction'])
        with c4:
            render_kpi("Open Interest", f"{int(latest['Open_Interest_All']):,}", latest['OI_Change'])

        # 3. Main Analysis Section
        render_intelligence_panel(latest, df)
        
        # 4. Raw Data Ledger
        st.write("---")
        with st.expander("DECRYPTED RAW DATA LEDGER (SYSTEM_ACCESS)"):
            ledger = df[['Date', 'Netto', 'Net_Change', 'Z_Score', 'Conviction', 'Open_Interest_All']].copy()
            ledger = ledger.sort_values('Date', ascending=False).head(30)
            ledger['Date'] = ledger['Date'].dt.strftime('%Y-%m-%d')
            st.dataframe(ledger, use_container_width=True, hide_index=True)
            
        # 5. Bottom System Log
        st.markdown(f"""
            <div style='text-align: center; color: var(--text-dim); font-size: 9px; margin-top: 50px; font-family: "JetBrains Mono";'>
                END_OF_LINE // PROTOCOL: COT_TFF // HASH: {hash(str(latest['Netto']))} // SECURE_LINK_ACTIVE
            </div>
        """, unsafe_allow_html=True)
    else:
        st.error("FAILURE: Data Stream corrupted or CFTC Server unreachable.")
        if st.button("REINITIALIZE SYSTEM"): st.rerun()

if __name__ == "__main__":
    main()
