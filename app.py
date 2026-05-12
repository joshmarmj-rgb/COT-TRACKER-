import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- SETUP ---
st.set_page_config(page_title="MakroBase | Institutional Intelligence", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #010101; color: #d1d5db; font-family: 'JetBrains Mono', monospace; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #080808; border: 1px solid #1a1a1a;
        padding: 10px 20px; color: #555; border-radius: 4px 4px 0 0;
    }
    .stTabs [aria-selected="true"] { color: #00f2ff !important; border-color: #00f2ff !important; }
    .card { background: #080808; border: 1px solid #1a1a1a; padding: 25px; border-radius: 4px; margin-bottom: 15px; }
    .h-val { font-size: 42px; color: white; font-weight: 700; margin: 10px 0; }
    .label { font-size: 11px; color: #00f2ff; text-transform: uppercase; letter-spacing: 2px; }
    .explainer { color: #888; font-size: 13px; line-height: 1.6; border-left: 2px solid #333; padding-left: 15px; }
    .log-interpretation { font-size: 12px; padding: 4px 8px; border-radius: 3px; font-weight: bold; }
    .neutral { background: #333; color: #fff; }
    .bullish { background: #004d2c; color: #00ff88; }
    .bearish { background: #4d0016; color: #ff2255; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ---
@st.cache_data(ttl=3600)
def get_data():
    try:
        url = "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip"
        r = requests.get(url, timeout=10)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        df.columns = df.columns.str.strip()
        ndx = df[df['Market_and_Exchange_Names'].str.contains("NASDAQ-100", na=False)].copy()
        ndx['Date'] = pd.to_datetime(ndx['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
        ndx = ndx.sort_values('Date')
        
        ndx['Net'] = ndx['Lev_Money_Positions_Long_All'] - ndx['Lev_Money_Positions_Short_All']
        window = 26
        ndx['Mean'] = ndx['Net'].rolling(window).mean()
        ndx['Std'] = ndx['Net'].rolling(window).std()
        ndx['Z'] = (ndx['Net'] - ndx['Mean']) / ndx['Std']
        
        # Log-Interpretation hinzufügen
        def interpret(z):
            if z > 1.5: return "EXTREM_EUFORIE"
            if z < -1.5: return "EXTREM_PANIK"
            if z > 0.5: return "LEICHT_BULLISCH"
            if z < -0.5: return "LEICHT_BÄRISCH"
            return "NEUTRAL"
        
        ndx['Interpretation'] = ndx['Z'].apply(interpret)
        return ndx
    except: return None

df = get_data()

if df is not None:
    curr = df.iloc[-1]
    
    st.markdown(f"# MakroBase // <span style='color:#00f2ff;'>Intelligence Node</span>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 DASHBOARD", "🧬 QUANT_LOGIC", "📜 HISTORICAL_LOGS", "📖 MANUAL"])
    
    with tab1:
        st.markdown("### CURRENT MARKET STATE")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"<div class='card'><div class='label'>Net Power</div><div class='h-val'>{int(curr['Net']):,}</div><p class='explainer'>Hedgefonds-Positionierung im Nasdaq.</p></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='card'><div class='label'>Z-Score Bias</div><div class='h-val'>{curr['Z']:.2f} σ</div><p class='explainer'>Aktuelle Spannung im System.</p></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='card'><div class='label'>Market Sentiment</div><div class='h-val' style='font-size:28px; color:#00f2ff;'>{curr['Interpretation']}</div><p class='explainer'>Automatisierte Logik-Auswertung.</p></div>", unsafe_allow_html=True)
            
        fig = go.Figure(go.Scatter(x=df['Date'], y=df['Net'], line=dict(color='#00f2ff', width=2), fill='tozeroy', name="Net Power"))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#555", height=400, margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("### MARKT-MECHANIK")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"""
            <div class='card'>
                <div class='label'>Net Power: Der Treibstoff</div>
                <div class='explainer' style='border:none;'>
                    In <b>Bildschirmfoto_12-5-2026_204055_cyzdddnva5dyqfbhq6iahv.streamlit.app.jpeg</b> sahen wir -56k. 
                    Das ist die Differenz zwischen Hedgefonds, die kaufen, und Hedgefonds, die shorten. <br><br>
                    - <b>Positiv:</b> Institutionelle kaufen den Markt.<br>
                    - <b>Negativ:</b> Institutionelle nutzen den Markt zur Absicherung (Shorts).
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_b:
            st.markdown(f"""
            <div class='card'>
                <div class='label'>Z-Score: Das Thermometer</div>
                <div class='explainer' style='border:none;'>
                    Der Z-Score sagt uns, wie "normal" die -56k sind. <br><br>
                    - <b>0 bis ±1:</b> Business as usual. Kein Signal.<br>
                    - <b>±2 oder höher:</b> Der Markt ist "überdehnt". Hier entstehen die profitabelsten Trading-Chancen, weil die Profis zu weit in eine Richtung gerannt sind.
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        st.markdown("### HISTORICAL DATA INTELLIGENCE")
        st.markdown("""
            <div class='explainer' style='margin-bottom:20px;'>
                Diese Liste zeigt die historische Entwicklung. Achte auf die Spalte <b>INTERPRETATION</b>. 
                Wenn diese von 'NEUTRAL' auf 'EXTREM' wechselt, ist das dein Warnsignal.
            </div>
        """, unsafe_allow_html=True)
        
        # Daten für Tabelle aufbereiten
        log_df = df[['Date', 'Net', 'Z', 'Interpretation']].copy()
        log_df = log_df.sort_values('Date', ascending=False)
        log_df['Net'] = log_df['Net'].apply(lambda x: f"{int(x):,}")
        log_df['Z'] = log_df['Z'].apply(lambda x: f"{x:.2f} σ")
        
        st.dataframe(log_df, use_container_width=True, height=500)

    with tab4:
        st.markdown("### OPERATION MANUAL")
        st.info("MakroBase ist dein Kompass für institutionelle Kapitalströme.")
        st.markdown("""
        1. **Die Regel:** Wir traden nicht gegen die Hedgefonds, außer sie sind am **Extrempunkt**.
        2. **Der Filter:** Ignoriere alle Signale, wenn der Z-Score zwischen -1.5 und +1.5 liegt.
        3. **Das Setup:** Wenn Z-Score < -2.0 (Panik) UND die Net Power beginnt zu steigen -> **Strong Buy Signal**.
        """)

else:
    st.error("UPLINK FAILURE")
