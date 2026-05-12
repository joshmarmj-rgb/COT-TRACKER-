import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go

st.set_page_config(page_title="Nasdaq COT Expert Terminal", layout="wide")

# --- DARK TERMINAL DESIGN ---
st.markdown("""
    <style>
    .main { background-color: #000000; }
    [data-testid="stMetricValue"] { font-size: 32px !important; font-weight: 700; }
    .status-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #334155;
        margin-bottom: 20px;
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
    
    # Header
    st.title("🏛️ Nasdaq Insider Terminal")
    
    # Metriken in einer Reihe
    c1, c2, c3 = st.columns(3)
    c1.metric("Netto-Position", f"{int(latest['Netto']):,}")
    c2.metric("Long Quote", f"{(latest['Lev_Money_Positions_Long_All']/(latest['Lev_Money_Positions_Long_All']+latest['Lev_Money_Positions_Short_All'])*100):.1f}%")
    c3.metric("Bericht vom", latest['Date_Obj'].strftime('%d.%m.%Y'))

    # --- DAS SCHÖNE DIAGRAMM (AREA CHART) ---
    st.subheader("Sentiment Trend")
    
    chart_df = data.tail(26) # Letzte 6 Monate
    
    fig = go.Figure()

    # Fläche mit Verlauf
    fig.add_trace(go.Scatter(
        x=chart_df['Date_Obj'], 
        y=chart_df['Netto'],
        fill='tozeroy',
        mode='lines+markers',
        line=dict(width=3, color='#3b82f6'),
        fillcolor='rgba(59, 130, 246, 0.2)',
        marker=dict(size=6, color='#60a5fa')
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=20, b=0),
        height=400,
        xaxis=dict(showgrid=False, color='#94a3b8'),
        yaxis=dict(showgrid=True, gridcolor='#1e293b', color='#94a3b8'),
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Info Bereich
    st.markdown(f"""
    <div class="status-card">
        <h3 style="margin-top:0; color:#f8fafc;">💡 Marktanalyse</h3>
        <p style="color:#cbd5e1; font-size:16px;">
        Die Hedgefonds sind aktuell mit <b>{int(latest['Netto']):,} Kontrakten</b> positioniert. 
        Ein fallender Trend im Chart bedeutet, dass das "Smart Money" zunehmend vorsichtiger wird oder aktiv auf fallende Kurse setzt. 
        Besonders die Geschwindigkeit des Abfalls in den letzten Wochen ist ein wichtiges Warnsignal.
        </p>
    </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Fehler: {e}")
