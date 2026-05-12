import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
import numpy as np

# Pro-Konfiguration
st.set_page_config(page_title="Nasdaq Institutional Terminal", layout="wide", initial_sidebar_state="collapsed")

# --- HIGH-END CSS STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');
    
    .main { background-color: #020617; color: #f8fafc; font-family: 'Roboto Mono', monospace; }
    .stMetric { background: #0f172a; border: 1px solid #1e293b; padding: 20px; border-radius: 4px; }
    .terminal-card {
        border: 1px solid #1e293b;
        background-color: #0f172a;
        padding: 24px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    .status-tag {
        font-size: 10px;
        padding: 2px 8px;
        border-radius: 12px;
        background: #1e293b;
        color: #94a3b8;
        border: 1px solid #334155;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_cot_data():
    url = "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip"
    response = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        fname = z.namelist()[0]
        with z.open(fname) as f:
            df = pd.read_csv(f, low_memory=False)
    df.columns = df.columns.str.strip()
    nasdaq = df[df['Market_and_Exchange_Names'].str.contains("NASDAQ-100", na=False)].copy()
    nasdaq['Netto'] = nasdaq['Lev_Money_Positions_Long_All'] - nasdaq['Lev_Money_Positions_Short_All']
    nasdaq['Date_Obj'] = pd.to_datetime(nasdaq['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
    return nasdaq.sort_values('Date_Obj')

try:
    df = get_cot_data()
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # --- PROFESSIONELLE ANALYTIK ---
    netto = int(latest['Netto'])
    delta = netto - int(prev['Netto'])
    
    # Z-Score Berechnung (Abweichung vom Normalwert)
    mean_netto = df['Netto'].mean()
    std_netto = df['Netto'].std()
    z_score = (netto - mean_netto) / std_netto
    
    # Header
    st.markdown("### <span class='status-tag'>LIVE FEED</span>", unsafe_allow_html=True)
    st.title("NASDAQ-100 INSTITUTIONAL COMMAND")
    st.markdown(f"TERMINAL ID: COT-2026-X // PERIOD: {latest['Date_Obj'].strftime('%d.%m.%Y')}")
    st.write("---")

    # --- ROW 1: CORE METRICS ---
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.metric("NET EXPOSURE", f"{netto:,}", f"{delta:,}")
    with c2:
        # Z-Score zeigt wie extrem die Lage statistisch ist
        st.metric("STATISTICAL BIAS (Z)", f"{z_score:.2f} SD")
    with c3:
        long_ratio = (latest['Lev_Money_Positions_Long_All'] / (latest['Lev_Money_Positions_Long_All'] + latest['Lev_Money_Positions_Short_All'])) * 100
        st.metric("LONG CONVICTION", f"{long_ratio:.1f}%")
    with c4:
        oi_change = int(latest['Open_Interest_All']) - int(prev['Open_Interest_All'])
        st.metric("OPEN INTEREST", f"{int(latest['Open_Interest_All']):,}", f"{oi_change:,}")

    # --- ROW 2: VISUAL INTELLIGENCE ---
    col_chart, col_intel = st.columns([2, 1])

    with col_chart:
        # Ein professioneller "Stepline" Chart (zeigt Beständigkeit)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Date_Obj'].tail(52), y=df['Netto'].tail(52),
            mode='lines', line=dict(color='#38bdf8', width=2),
            fill='tozeroy', fillcolor='rgba(56, 189, 248, 0.05)',
            name="Net Exposure"
        ))
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0), height=400,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#475569'),
            yaxis=dict(gridcolor='#1e293b', color='#475569', side="right")
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_intel:
        st.markdown("<div class='terminal-card'>", unsafe_allow_html=True)
        st.markdown("#### 🧠 AI ANALYTICS")
        
        # Logik-Engine für Profi-Urteil
        if z_score < -2:
            st.error("⚠️ CRITICAL OVEREXTENTION (SHORT)")
            st.write("Die Positionierung ist statistisch gesehen am Limit. Die Wahrscheinlichkeit einer Kapitulation der Shorts (Squeeze) ist extrem hoch.")
        elif delta < 0 and netto < 0:
            st.warning("📉 AGGRESSIVE BEARISH MOMENTUM")
            st.write("Institutionelle Gelder fließen aktiv aus dem Markt. Der Verkaufsdruck nimmt zu.")
        else:
            st.info("⚖️ NEUTRAL CONSOLIDATION")
            st.write("Keine signifikante Akkumulation von Risiko erkennbar.")
        
        st.markdown("</div>", unsafe_allow_html=True)

    # --- ROW 3: RAW DATA GRID ---
    with st.expander("VIEW INSTITUTIONAL RAW LEDGER"):
        st.dataframe(
            df[['Date_Obj', 'Netto', 'Lev_Money_Positions_Long_All', 'Lev_Money_Positions_Short_All', 'Open_Interest_All']].tail(10),
            use_container_width=True
        )

except Exception as e:
    st.error(f"SYSTEM CRITICAL ERROR: {e}")
