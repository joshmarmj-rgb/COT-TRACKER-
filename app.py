import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
from datetime import datetime

# Setup
st.set_page_config(page_title="Nasdaq Alpha Terminal", layout="wide", initial_sidebar_state="collapsed")

# --- CORE DESIGN (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'JetBrains Mono', monospace; background-color: #050505; }
    .stMetric { background-color: #0f172a; border: 1px solid #1e293b; padding: 20px; border-radius: 4px; }
    div[data-testid="stMetricValue"] { color: #38bdf8; font-family: 'JetBrains Mono'; }
    .analysis-card {
        border-left: 4px solid #38bdf8;
        background-color: #0f172a;
        padding: 20px;
        margin: 20px 0;
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
    nasdaq['Date_Obj'] = pd.to_datetime(nasdaq['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
    nasdaq['Netto'] = nasdaq['Lev_Money_Positions_Long_All'] - nasdaq['Lev_Money_Positions_Short_All']
    return nasdaq.sort_values('Date_Obj')

try:
    data = get_cot_data()
    latest = data.iloc[-1]
    netto = int(latest['Netto'])
    
    # --- HEADER ---
    st.markdown(f"<h1 style='text-align: center; color: white; letter-spacing: 2px;'>NASDAQ 100 COT INSIDER</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #64748b;'>TERMINAL ACCESS VERIFIED // SYSTEM DATE: {datetime.now().strftime('%d.%m.%Y')}</p>", unsafe_allow_html=True)
    st.write("---")

    # --- TOP KPIs ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("NET POSITION", f"{netto:,}")
    
    # Sentiment Intensity Score
    max_ever = data['Netto'].max()
    min_ever = data['Netto'].min()
    intensity = ((netto - min_ever) / (max_ever - min_ever)) * 100
    c2.metric("SENTIMENT INTENSITY", f"{intensity:.1f}%")
    
    long_p = int(latest['Lev_Money_Positions_Long_All'])
    short_p = int(latest['Lev_Money_Positions_Short_All'])
    c3.metric("LONG/SHORT RATIO", f"{long_p/short_p:.2f}")
    c4.metric("REPORT DATE", latest['Date_Obj'].strftime('%d.%m.%Y'))

    # --- THE "MASTER" CHART ---
    chart_df = data.tail(30)
    
    fig = go.Figure()

    # Gradient-like Area Chart mit flüssigen Farben
    fig.add_trace(go.Scatter(
        x=chart_df['Date_Obj'], y=chart_df['Netto'],
        mode='lines',
        line=dict(width=4, color='#38bdf8'),
        fill='tozeroy',
        fillcolor='rgba(56, 189, 248, 0.1)',
        name="Net Exposure"
    ))

    # Nulllinie hervorheben
    fig.add_hline(y=0, line_dash="dash", line_color="#475569")

    fig.update_layout(
        plot_bgcolor='#050505', paper_bgcolor='#050505',
        margin=dict(l=0, r=0, t=20, b=0),
        height=500,
        xaxis=dict(showgrid=False, color='#64748b', tickfont=dict(size=10)),
        yaxis=dict(gridcolor='#1e293b', color='#64748b', tickfont=dict(size=10), side="right"),
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- INTELLIGENT ANALYSIS ENGINE ---
    st.markdown("<div class='analysis-card'>", unsafe_allow_html=True)
    st.markdown("### ⚡ ANALYSE-PROTOKOLL")
    
    if netto < -100000:
        st.write(f"**STATUS: EXTREMES SHORT-EXTREM.** Die Hedgefonds sind in einer historisch bärischen Zone. Das Risiko für einen massiven Short-Squeeze (plötzlicher Kursanstieg) ist auf Stufe **KRITISCH**.")
    elif netto < 0:
        st.write(f"**STATUS: BEARISH BIAS.** Die professionellen Spekulanten bevorzugen die Short-Seite. Der Markt zeigt strukturelle Schwäche.")
    else:
        st.write(f"**STATUS: BULLISH BIAS.** Das 'Smart Money' ist netto-long positioniert und stützt den Aufwärtstrend.")
        
    st.write(f"**DETAIL:** Die Long-Positionen liegen bei {long_p:,} Kontrakten, während {short_p:,} Kontrakte auf fallende Kurse wetten.")
    st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"TERMINAL ERROR: {e}")
