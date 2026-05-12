import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Nasdaq COT Expert Terminal", layout="wide")

# --- CUSTOM CSS FÜR TERMINAL-LOOK ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; color: #ffffff; }
    .main { background-color: #000000; }
    .status-box {
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #374151;
        background-color: #111827;
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
    return nasdaq.sort_values('Date_Obj', ascending=True)

try:
    data = get_cot_data()
    latest = data.iloc[-1]
    
    # BERECHNUNGEN FÜR MEHR INFO
    netto_val = int(latest['Netto'])
    long_pos = int(latest['Lev_Money_Positions_Long_All'])
    short_pos = int(latest['Lev_Money_Positions_Short_All'])
    total_pos = long_pos + short_pos
    long_ratio = (long_pos / total_pos) * 100
    
    # Sentiment Score (0 = Max Short, 100 = Max Long der Historie)
    min_n = data['Netto'].min()
    max_n = data['Netto'].max()
    score = ((netto_val - min_n) / (max_n - min_n)) * 100

    # --- HEADER BEREICH ---
    st.title("🏛️ Nasdaq 100 Insider Terminal")
    st.write(f"Datenstand: {latest['Date_Obj'].strftime('%d.%m.%Y')} | Quelle: CFTC Traders in Financial Futures")

    # --- TOP METRIKEN ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Netto-Position", f"{netto_val:,}")
    c2.metric("Sentiment Score", f"{score:.1f}%")
    c3.metric("Long Quote", f"{long_ratio:.1f}%")
    c4.metric("Open Interest", f"{int(latest['Open_Interest_All']):,}")

    st.write("---")

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("📊 Positionierungs-Trend")
        chart_df = data.tail(20).copy()
        chart_df['Farbe'] = ['#ef4444' if x < 0 else '#10b981' for x in chart_df['Netto']]
        fig = px.bar(chart_df, x='Date_Obj', y='Netto', color='Farbe', 
                     color_discrete_map={'#ef4444':'#ef4444', '#10b981':'#10b981'})
        fig.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("🎯 Insider-Check")
        
        # Logik-basierte Analyse
        if score < 20:
            st.error("🚨 EXTREMER PESSIMISMUS\nHedgefonds sind am Limit ihrer Short-Wetten. Historisch gesehen folgt hier oft eine heftige Gegenbewegung (Short Squeeze).")
        elif score > 80:
            st.success("🔥 EXTREME GIER\nAlle sind Long. Vorsicht, der Markt ist 'overcrowded'. Rückschlaggefahr!")
        else:
            st.info("⚖️ NEUTRALE ZONE\nKeine extremen Positionierungen erkennbar. Der Trend ist stabil.")

        # Donut Chart für Long/Short Verteilung
        fig_pie = go.Figure(data=[go.Pie(labels=['Long', 'Short'], 
                                       values=[long_pos, short_pos], 
                                       hole=.6,
                                       marker_colors=['#10b981', '#ef4444'])])
        fig_pie.update_layout(showlegend=False, height=250, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- DATEN-TABELLE ---
    with st.expander("📄 Komplette Datenhistorie einsehen"):
        st.dataframe(data[['Date_Obj', 'Netto', 'Lev_Money_Positions_Long_All', 'Lev_Money_Positions_Short_All']].sort_values('Date_Obj', ascending=False))

except Exception as e:
    st.error(f"Fehler bei der Datenverarbeitung: {e}")
