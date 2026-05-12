import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
from datetime import datetime

# Konfiguration
st.set_page_config(page_title="Alpha Terminal V2", layout="wide")

# --- RADIKALES MINIMAL-DESIGN (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=JetBrains+Mono&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Inter', sans-serif; 
        background-color: #000000; 
        color: #e2e8f0;
    }
    
    .metric-container {
        background: #0a0a0a;
        border: 1px solid #1a1a1a;
        padding: 1.5rem;
        border-radius: 8px;
    }
    
    .status-badge {
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
        background: #1e293b;
    }

    .description-text {
        color: #94a3b8;
        font-size: 14px;
        line-height: 1.6;
    }
    
    h1, h2, h3 { font-family: 'Inter', sans-serif; letter-spacing: -0.02em; }
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
    
    # --- HEADER & STATUS ---
    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        st.title("NASDAQ 100 ALPHA TERMINAL")
        st.markdown(f"**DATEN-FEED:** CFTC TFF Report // **STAND:** {latest['Date_Obj'].strftime('%d.%m.%Y')}")
    
    with col_t2:
        sentiment = "EXTREME SHORT" if int(latest['Netto']) < -100000 else "BEARISH"
        st.markdown(f"<div style='text-align:right; margin-top:20px;'><span class='status-badge' style='color:#fb7185; border:1px solid #fb7185;'>{sentiment}</span></div>", unsafe_allow_html=True)

    st.write("---")

    # --- DIE ZAHLEN VERSTÄNDLICH ERKLÄRT ---
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.metric("NET EXPOSURE", f"{int(latest['Netto']):,}")
        st.markdown("""
            <p class='description-text'>
            <b>Was das ist:</b> Die Differenz zwischen Kauf- (Long) und Verkaufsverträgen (Short).<br>
            <b>Bedeutung:</b> Ein negativer Wert zeigt, dass Hedgefonds netto auf fallende Kurse wetten.
            </p>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        long_p = int(latest['Lev_Money_Positions_Long_All'])
        short_p = int(latest['Lev_Money_Positions_Short_All'])
        ratio = long_p / short_p if short_p != 0 else 0
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.metric("L/S RATIO", f"{ratio:.2f}")
        st.markdown(f"""
            <p class='description-text'>
            <b>Was das ist:</b> Das Verhältnis von Long- zu Short-Kontrakten.<br>
            <b>Bedeutung:</b> Bei {ratio:.2f} kommen auf 1 Short-Kontrakt nur {ratio:.2f} Longs. Die Übermacht der Bären ist massiv.
            </p>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        oi = int(latest['Open_Interest_All'])
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.metric("OPEN INTEREST", f"{oi:,}")
        st.markdown("""
            <p class='description-text'>
            <b>Was das ist:</b> Die Gesamtzahl aller offenen Kontrakte im Markt.<br>
            <b>Bedeutung:</b> Hohes Open Interest bei fallenden Netto-Positionen bestätigt einen starken Abwärtstrend der Profis.
            </p>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- CLEANER CHART ---
    st.write("### SENTIMENT HISTORIE (26 WOCHEN)")
    chart_df = data.tail(26)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=chart_df['Date_Obj'], y=chart_df['Netto'],
        mode='lines+markers',
        line=dict(width=2, color='#38bdf8'),
        marker=dict(size=4, color='#38bdf8'),
        fill='tozeroy',
        fillcolor='rgba(56, 189, 248, 0.05)'
    ))
    
    fig.add_hline(y=0, line_color="#334155", line_width=1)
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0), height=350,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, color='#475569'),
        yaxis=dict(gridcolor='#1a1a1a', color='#475569', side="right"),
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- TRADING LOGIK ---
    with st.expander("🛡️ HANDLUNGS-PROTOKOLL LESEN"):
        st.info("""
        **1. Kontra-Indikator (Short Squeeze):**
        Hedgefonds liegen oft richtig, aber an Extrempunkten (sehr tiefe Netto-Werte) liegen sie oft falsch. Wenn alle 'Short' sind, gibt es niemanden mehr, der verkaufen kann. Ein kleiner Kursanstieg zwingt sie dann zum Rückkauf -> der Kurs explodiert nach oben.
        
        **2. Smart Money Flow:**
        Beobachte die Richtung der Linie. Sinkt sie, während der Nasdaq-Preis steigt? Das nennt man Divergenz. Die Profis sichern sich gegen einen Fall ab, während der Rest der Welt noch kauft.
        """)

except Exception as e:
    st.error(f"Fehler: {e}")
