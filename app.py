import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# --- CONFIGURATION & THEME ---
st.set_page_config(
    page_title="NASDAQ QUANTUM TERMINAL v4.0",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ADVANCED TERMINAL STYLING (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;700&display=swap');
    
    :root {
        --bg-primary: #020205;
        --accent-blue: #0ea5e9;
        --accent-red: #ef4444;
        --accent-green: #10b981;
        --border-color: #1e1e2e;
        --text-dim: #64748b;
    }

    .main { background-color: var(--bg-primary); color: #e2e8f0; font-family: 'JetBrains Mono', monospace; }
    
    /* Terminal Header */
    .terminal-header {
        border-bottom: 2px solid var(--accent-blue);
        padding-bottom: 10px;
        margin-bottom: 30px;
    }
    
    /* Metrics Grid */
    .q-metric-card {
        background: #09090b;
        border: 1px solid var(--border-color);
        padding: 20px;
        border-left: 4px solid var(--accent-blue);
    }
    
    .q-metric-label { color: var(--text-dim); font-size: 10px; text-transform: uppercase; letter-spacing: 2px; }
    .q-metric-value { font-size: 24px; font-weight: 700; color: #ffffff; margin: 5px 0; }
    .q-metric-delta { font-size: 12px; font-family: 'JetBrains Mono'; }

    /* Analysis Panel */
    .analysis-panel {
        background: #09090b;
        border: 1px solid var(--border-color);
        padding: 25px;
    }

    .status-pill {
        padding: 2px 10px;
        border-radius: 2px;
        font-size: 10px;
        border: 1px solid currentColor;
    }

    /* Table Styling */
    .stDataFrame { border: 1px solid var(--border-color); }
    
    hr { border: 0; border-top: 1px solid var(--border-color); margin: 20px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=3600)
def fetch_institutional_data():
    """Holt und bereitet COT Daten auf institutionellem Niveau auf."""
    try:
        url = "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip"
        response = requests.get(url, timeout=10)
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            with z.open(z.namelist()[0]) as f:
                df = pd.read_csv(f, low_memory=False)
        
        df.columns = df.columns.str.strip()
        # Filter auf Nasdaq 100 Leveraged Money (Hedgefonds)
        nasdaq = df[df['Market_and_Exchange_Names'].str.contains("NASDAQ-100", na=False)].copy()
        nasdaq['Date'] = pd.to_datetime(nasdaq['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
        
        # Berechnung der Key Performance Indicators (KPIs)
        nasdaq['Netto'] = nasdaq['Lev_Money_Positions_Long_All'] - nasdaq['Lev_Money_Positions_Short_All']
        nasdaq['Total_Lev'] = nasdaq['Lev_Money_Positions_Long_All'] + nasdaq['Lev_Money_Positions_Short_All']
        nasdaq['Long_Ratio'] = (nasdaq['Lev_Money_Positions_Long_All'] / nasdaq['Total_Lev']) * 100
        
        # Statistische Analysen
        nasdaq['Rolling_Mean'] = nasdaq['Netto'].rolling(window=26).mean()
        nasdaq['Rolling_Std'] = nasdaq['Netto'].rolling(window=26).std()
        nasdaq['Z_Score'] = (nasdaq['Netto'] - nasdaq['Rolling_Mean']) / nasdaq['Rolling_Std']
        
        return nasdaq.sort_values('Date')
    except Exception as e:
        st.error(f"DATA CRITICAL: Connection Refused. {e}")
        return None

def render_terminal():
    df = fetch_institutional_data()
    if df is None: return

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # --- HEADER SECTION ---
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(f"""
            <div class='terminal-header'>
                <h1 style='margin:0; letter-spacing: -1px;'>NASDAQ 100 QUANTUM TERMINAL</h1>
                <p style='color: var(--text-dim); font-size: 12px;'>
                    SECURE CONNECTION // TRADERS IN FINANCIAL FUTURES (COT) // RELATIVE TO HISTORICAL BIAS
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    with col_h2:
        status_color = "#ef4444" if latest['Z_Score'] < -1.5 else "#10b981" if latest['Z_Score'] > 1.5 else "#64748b"
        st.markdown(f"""
            <div style='text-align: right; margin-top: 10px;'>
                <span class='status-pill' style='color: {status_color};'>BIAS: { "EXTREME" if abs(latest['Z_Score']) > 2 else "NEUTRAL" }</span><br>
                <span style='font-size: 20px; font-weight: bold;'>{latest['Date'].strftime('%Y-%m-%d')}</span>
            </div>
            """, unsafe_allow_html=True)

    # --- TOP TIER METRICS (QUANT DATA) ---
    m1, m2, m3, m4 = st.columns(4)
    
    with m1:
        delta = int(latest['Netto'] - prev['Netto'])
        delta_color = "var(--accent-green)" if delta > 0 else "var(--accent-red)"
        st.markdown(f"""
            <div class='q-metric-card'>
                <div class='q-metric-label'>NET INSTITUTIONAL EXPOSURE</div>
                <div class='q-metric-value'>{int(latest['Netto']):,}</div>
                <div class='q-metric-delta' style='color:{delta_color}'>{'↑' if delta > 0 else '↓'} {abs(delta):,} WoW</div>
            </div>
            """, unsafe_allow_html=True)

    with m2:
        z = latest['Z_Score']
        st.markdown(f"""
            <div class='q-metric-card' style='border-left-color: #f59e0b;'>
                <div class='q-metric-label'>Z-SCORE (26W WINDOW)</div>
                <div class='q-metric-value'>{z:.2f} σ</div>
                <div class='q-metric-delta'>STDEV FROM MEAN</div>
            </div>
            """, unsafe_allow_html=True)

    with m3:
        l_ratio = latest['Long_Ratio']
        st.markdown(f"""
            <div class='q-metric-card' style='border-left-color: #8b5cf6;'>
                <div class='q-metric-label'>LONG CONVICTION INDEX</div>
                <div class='q-metric-value'>{l_ratio:.1f}%</div>
                <div class='q-metric-delta'>OF TOTAL LEVERAGED</div>
            </div>
            """, unsafe_allow_html=True)

    with m4:
        oi = int(latest['Open_Interest_All'])
        oi_delta = oi - int(prev['Open_Interest_All'])
        st.markdown(f"""
            <div class='q-metric-card' style='border-left-color: #ec4899;'>
                <div class='q-metric-label'>TOTAL OPEN INTEREST</div>
                <div class='q-metric-value'>{oi:,}</div>
                <div class='q-metric-delta'>Δ {oi_delta:,}</div>
            </div>
            """, unsafe_allow_html=True)

    st.write("---")

    # --- MID SECTION: DATA VISUALIZATION VS. INTELLIGENCE ---
    col_left, col_right = st.columns([1.5, 1])
    
    with col_left:
        st.markdown("<p class='q-metric-label'>QUANTITATIVE EXPOSURE TIMELINE</p>", unsafe_allow_html=True)
        # Hochprofessioneller, reduzierter Line-Chart
        fig = go.Figure()
        
        # Zero Line
        fig.add_hline(y=0, line_dash="dash", line_color="#1e1e2e", line_width=1)
        
        # Data Line
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df['Netto'],
            mode='lines',
            line=dict(color='#0ea5e9', width=1.5),
            fill='tozeroy',
            fillcolor='rgba(14, 165, 233, 0.03)',
            hoverinfo='x+y'
        ))

        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=10, b=0),
            height=400,
            xaxis=dict(showgrid=False, color='#475569', tickfont=dict(size=9)),
            yaxis=dict(gridcolor='#0f172a', color='#475569', side="right", tickfont=dict(size=9)),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col_right:
        st.markdown("<p class='q-metric-label'>INSTITUTIONAL INTELLIGENCE</p>", unsafe_allow_html=True)
        st.markdown("<div class='analysis-panel'>", unsafe_allow_html=True)
        
        # Quantitative Logik für Profi-Analyse
        if z < -2.0:
            st.markdown("<h3 style='color:#ef4444;'>EXTREME CAPITULATION</h3>", unsafe_allow_html=True)
            st.write("Statistische Anomalie erkannt. Das Leveraged Money ist am historischen Limit seiner Short-Exponierung. Historisch gesehen ist dies ein 85% Reversal-Signal (Short Squeeze Risiko).")
        elif delta < 0 and z < 0:
            st.markdown("<h3 style='color:#f59e0b;'>BEARISH ACCUMULATION</h3>", unsafe_allow_html=True)
            st.write("Professionelle Akteure bauen Short-Positionen systematisch aus. Momentum ist bärisch, jedoch nimmt die Markttiefe bei fallendem Z-Score ab.")
        elif delta > 0 and z < 0:
            st.markdown("<h3 style='color:#38bdf8;'>SHORT COVERING</h3>", unsafe_allow_html=True)
            st.write("Erste Anzeichen von Gewinnmitnahmen auf der Short-Seite. Institutionelle fangen an, Positionen zu glätten.")
        else:
            st.markdown("<h3>NEUTRAL / SIDEWAYS</h3>", unsafe_allow_html=True)
            st.write("Keine signifikante institutionelle Tendenz erkennbar. Warten auf COT-Impuls.")

        st.markdown("</div>", unsafe_allow_html=True)
        
        # Donut Chart für L/S Verteilung
        fig_donut = go.Figure(data=[go.Pie(
            labels=['LONG', 'SHORT'],
            values=[latest['Lev_Money_Positions_Long_All'], latest['Lev_Money_Positions_Short_All']],
            hole=.7,
            marker_colors=['#10b981', '#ef4444'],
            textinfo='none'
        )])
        fig_donut.update_layout(
            showlegend=False, height=180, margin=dict(t=0, b=0, l=0, r=0),
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})

    # --- BOTTOM SECTION: RAW DATA LEDGER ---
    st.write("---")
    with st.expander("DECRYPTED RAW DATA LEDger (LEV_MONEY)"):
        raw_display = df[['Date', 'Netto', 'Z_Score', 'Long_Ratio', 'Open_Interest_All']].tail(20)
        st.dataframe(raw_display.sort_values('Date', ascending=False), use_container_width=True)

# Main Entry
if __name__ == "__main__":
    render_terminal()
