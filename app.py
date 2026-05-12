import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import time

# --- INITIALIZATION & GLOBAL SETTINGS ---
st.set_page_config(
    page_title="NASDAQ ELITE TERMINAL v5.0",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- TERMINAL STYLING ENGINE (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;600&family=Inter:wght@300;400;700&display=swap');
    
    :root {
        --terminal-bg: #030303;
        --card-bg: #0a0a0f;
        --accent-primary: #38bdf8;
        --accent-secondary: #818cf8;
        --danger: #f43f5e;
        --success: #10b981;
        --border: #1e1e2e;
        --text-muted: #94a3b8;
    }

    .main { background-color: var(--terminal-bg); color: #f1f5f9; font-family: 'Inter', sans-serif; }
    
    /* Global Card Styles */
    .glass-card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 4px;
        padding: 20px;
        margin-bottom: 15px;
    }

    /* Professional Metrics */
    .metric-title { font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: var(--text-muted); letter-spacing: 1.5px; text-transform: uppercase; }
    .metric-value { font-family: 'IBM Plex Mono', monospace; font-size: 28px; font-weight: 600; margin: 8px 0; color: #ffffff; }
    .metric-sub { font-size: 12px; font-family: 'IBM Plex Mono', monospace; }

    /* Analysis Badges */
    .badge {
        padding: 2px 8px;
        border-radius: 2px;
        font-size: 10px;
        font-weight: bold;
        border: 1px solid;
    }
    
    /* Code/Terminal Look */
    .mono { font-family: 'IBM Plex Mono', monospace; }
    
    /* Table Styling */
    .stDataFrame { border: 1px solid var(--border) !important; }
    
    /* Removing standard Streamlit elements for cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CORE DATA ENGINE ---
class COTDataEngine:
    def __init__(self):
        self.url = "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip"
        
    @st.cache_data(ttl=3600)
    def fetch_and_process(_self):
        try:
            res = requests.get(_self.url, timeout=15)
            with zipfile.ZipFile(io.BytesIO(res.content)) as z:
                with z.open(z.namelist()[0]) as f:
                    df = pd.read_csv(f, low_memory=False)
            
            df.columns = df.columns.str.strip()
            # Deep Filter: NASDAQ-100 (CME) - Leveraged Money
            target = "NASDAQ-100 STOCK INDEX"
            nasdaq = df[df['Market_and_Exchange_Names'].str.contains(target, na=False, case=False)].copy()
            nasdaq['Date'] = pd.to_datetime(nasdaq['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
            nasdaq = nasdaq.sort_values('Date')

            # Quantitative Calculations
            nasdaq['Netto'] = nasdaq['Lev_Money_Positions_Long_All'] - nasdaq['Lev_Money_Positions_Short_All']
            nasdaq['Total_Pos'] = nasdaq['Lev_Money_Positions_Long_All'] + nasdaq['Lev_Money_Positions_Short_All']
            nasdaq['Long_Ratio'] = (nasdaq['Lev_Money_Positions_Long_All'] / nasdaq['Total_Pos']) * 100
            
            # Statistical Scoring (Z-Score & Percentile)
            window = 52 # 1 Year Lookback
            nasdaq['Mean'] = nasdaq['Netto'].rolling(window=window).mean()
            nasdaq['Std'] = nasdaq['Netto'].rolling(window=window).std()
            nasdaq['Z_Score'] = (nasdaq['Netto'] - nasdaq['Mean']) / nasdaq['Std']
            
            # Change Analysis
            nasdaq['Net_Change'] = nasdaq['Netto'].diff()
            nasdaq['OI_Change'] = nasdaq['Open_Interest_All'].diff()
            
            return nasdaq
        except Exception as e:
            st.error(f"SYSTEM FAILURE: Data Acquisition Interrupted. {e}")
            return None

# --- UI COMPONENTS ---
def render_header(latest_date):
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
            <div style='margin-bottom: 20px;'>
                <h1 style='color: white; margin: 0; font-size: 32px; font-weight: 700;'>NASDAQ 100 ALPHA CORE</h1>
                <p style='color: var(--text-muted); font-family: "IBM Plex Mono"; font-size: 12px;'>
                    <span style='color: var(--accent-primary);'>●</span> SYSTEM_READY // AUTH_LEVEL: INSTITUTIONAL // DATA_SYNC: {latest_date.strftime('%Y-%m-%d')}
                </p>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div style='text-align: right; border-left: 1px solid var(--border); padding-left: 20px;'>
                <p class='metric-title'>Terminal Status</p>
                <p style='color: var(--success); font-weight: bold; font-family: "IBM Plex Mono";'>LIVE_FEED_ACTIVE</p>
            </div>
        """, unsafe_allow_html=True)

def render_top_metrics(latest, prev):
    m1, m2, m3, m4 = st.columns(4)
    
    with m1:
        net = int(latest['Netto'])
        change = int(latest['Net_Change'])
        color = "var(--success)" if change > 0 else "var(--danger)"
        st.markdown(f"""
            <div class='glass-card'>
                <p class='metric-title'>Net Exposure</p>
                <p class='metric-value'>{net:,}</p>
                <p class='metric-sub' style='color:{color}'>{'▲' if change > 0 else '▼'} {abs(change):,} WoW</p>
            </div>
        """, unsafe_allow_html=True)

    with m2:
        z = latest['Z_Score']
        z_color = "var(--danger)" if z < -1.5 else "var(--success)" if z > 1.5 else "var(--text-muted)"
        st.markdown(f"""
            <div class='glass-card'>
                <p class='metric-title'>Statistical Bias (Z)</p>
                <p class='metric-value' style='color:{z_color}'>{z:.2f} σ</p>
                <p class='metric-sub'>SD FROM 52W MEAN</p>
            </div>
        """, unsafe_allow_html=True)

    with m3:
        ratio = latest['Long_Ratio']
        st.markdown(f"""
            <div class='glass-card'>
                <p class='metric-title'>Long Conviction</p>
                <p class='metric-value'>{ratio:.1f}%</p>
                <div style='background: #1e1e2e; height: 4px; width: 100%; border-radius: 2px; margin-top: 10px;'>
                    <div style='background: var(--accent-primary); height: 4px; width: {ratio}%; border-radius: 2px;'></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with m4:
        oi = int(latest['Open_Interest_All'])
        oi_ch = int(latest['OI_Change'])
        st.markdown(f"""
            <div class='glass-card'>
                <p class='metric-title'>Open Interest</p>
                <p class='metric-value'>{oi:,}</p>
                <p class='metric-sub' style='color:var(--accent-secondary)'>Δ {oi_ch:,} CONTRACTS</p>
            </div>
        """, unsafe_allow_html=True)

def render_intel_section(latest, df):
    st.write("---")
    c_left, c_right = st.columns([1, 1])
    
    with c_left:
        st.markdown("<p class='metric-title'>Institutional Flow Intelligence</p>", unsafe_allow_html=True)
        # Deep Logic for Market Assessment
        z = latest['Z_Score']
        net_ch = latest['Net_Change']
        
        assessment = ""
        risk_lvl = ""
        
        if z < -2.0:
            assessment = "🚨 CRITICAL OVEREXTENSION: Hedgefonds sind historisch massiv Short. Die Wahrscheinlichkeit einer Kapitulations-Rallye (Short Squeeze) ist extrem hoch. Institutionelle 'Dry Powder' Kapazität ist erschöpft."
            risk_lvl = "HIGH VOLATILITY / REVERSAL"
        elif z < -1.0 and net_ch < 0:
            assessment = "📉 BEARISH CONTINUATION: Die Verkäufer kontrollieren den Flow. Trotz bereits niedriger Positionierung bauen Institutionelle ihre Shorts weiter aus. Momentum ist intakt."
            risk_lvl = "TREND PERSISTENCE"
        elif net_ch > 10000:
            assessment = "⚡ AGGRESSIVE ACCUMULATION: Signifikanter Rückkauf von Short-Positionen. Das Smart Money beginnt, das Risiko zu reduzieren – oft ein Vorbote für eine lokale Bodenbildung."
            risk_lvl = "ACCUMULATION"
        else:
            assessment = "⚖️ NEUTRAL CONSOLIDATION: Keine signifikante Richtungsänderung im institutionellen Sektor. Der Markt sucht nach einem neuen Katalysator."
            risk_lvl = "LOW CONVICTION"

        st.markdown(f"""
            <div class='glass-card' style='border-left: 4px solid var(--accent-secondary); height: 300px;'>
                <p class='metric-title'>Logic Engine Output</p>
                <h4 style='color: white;'>{risk_lvl}</h4>
                <p style='color: var(--text-muted); font-size: 14px; line-height: 1.6;'>{assessment}</p>
                <hr>
                <p class='metric-title'>Probability of Squeeze</p>
                <p style='color: var(--accent-primary); font-family: "IBM Plex Mono"; font-weight: bold;'>{ "85%" if z < -2 else "60%" if z < -1 else "25%" }</p>
            </div>
        """, unsafe_allow_html=True)

    with c_right:
        st.markdown("<p class='metric-title'>Sentiment Structure Analysis</p>", unsafe_allow_html=True)
        # Professional Gauge without the "ugly" blue bar
        val = latest['Netto']
        min_v = df['Netto'].min()
        max_v = df['Netto'].max()
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = val,
            number = {'font': {'color': 'white', 'family': 'IBM Plex Mono', 'size': 32}, 'valueformat': ','},
            gauge = {
                'axis': {'range': [min_v, max_v], 'tickwidth': 1, 'tickcolor': "#475569", 'tickfont': {'size': 8}},
                'bar': {'color': "white", 'thickness': 0.1},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 1,
                'bordercolor': "#1e1e2e",
                'steps': [
                    {'range': [min_v, min_v*0.5], 'color': '#4c0519'},
                    {'range': [min_v*0.5, 0], 'color': '#451a03'},
                    {'range': [0, max_v], 'color': '#064e3b'}
                ],
                'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.8, 'value': val}
            }
        ))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(t=0, b=0, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def render_advanced_table(df):
    st.write("---")
    st.markdown("<p class='metric-title'>Decrypted Institutional Ledger (Last 15 Records)</p>", unsafe_allow_html=True)
    
    ledger = df[['Date', 'Netto', 'Net_Change', 'Z_Score', 'Long_Ratio', 'Open_Interest_All']].copy()
    ledger = ledger.sort_values('Date', ascending=False).head(15)
    
    # Formatting for professional look
    ledger['Date'] = ledger['Date'].dt.strftime('%Y-%m-%d')
    ledger['Netto'] = ledger['Netto'].map('{:,.0f}'.format)
    ledger['Z_Score'] = ledger['Z_Score'].map('{:,.2f} σ'.format)
    ledger['Long_Ratio'] = ledger['Long_Ratio'].map('{:,.1f}%'.format)
    
    st.dataframe(ledger, use_container_width=True)

# --- MAIN EXECUTION ---
def main():
    engine = COTDataEngine()
    df = engine.fetch_and_process()
    
    if df is not None:
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # UI Execution
        render_header(latest['Date'])
        render_top_metrics(latest, prev)
        render_intel_section(latest, df)
        render_advanced_table(df)
        
        # Final Footer Info
        st.markdown(f"""
            <div style='text-align: center; color: #475569; font-size: 10px; margin-top: 50px; font-family: "IBM Plex Mono";'>
                END_OF_TRANSMISSION // COT_REPORT_TYPE: TFF_FUTURES_ONLY // NODE: {time.strftime('%H:%M:%S')}
            </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
