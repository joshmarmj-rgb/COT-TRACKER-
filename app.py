import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- SETUP ---
st.set_page_config(page_title="MakroBase | V19", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #010101; color: #d1d5db; font-family: 'JetBrains Mono', monospace; }
    .card { background: #080808; border: 1px solid #1a1a1a; padding: 25px; border-radius: 4px; margin-bottom: 15px; }
    .h-val { font-size: 42px; color: white; font-weight: 700; margin: 10px 0; }
    .label { font-size: 11px; color: #00f2ff; text-transform: uppercase; letter-spacing: 2px; }
    .explainer { color: #888; font-size: 13px; line-height: 1.6; border-left: 2px solid #333; padding-left: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA HUB (FIXED FILTER) ---
@st.cache_data(ttl=3600)
def get_clean_data():
    try:
        url = "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip"
        r = requests.get(url, timeout=10)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        
        df.columns = df.columns.str.strip()
        
        # PRÄZISER FILTER: Nur E-MINI NASDAQ-100
        # Das verhindert die Dubletten aus Bildschirmfoto_12-5-2026_231817_cyzdddnva5dyqfbhq6iahv.streamlit.app.jpg
        ndx = df[df['Market_and_Exchange_Names'].str.contains("E-MINI NASDAQ-100", na=False, case=False)].copy()
        
        ndx['Date'] = pd.to_datetime(ndx['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
        ndx = ndx.sort_values('Date').drop_duplicates(subset=['Date']) # Sicherheitshalber Dubletten-Check
        
        # Metriken
        ndx['Net'] = ndx['Lev_Money_Positions_Long_All'] - ndx['Lev_Money_Positions_Short_All']
        ndx['Z'] = (ndx['Net'] - ndx['Net'].rolling(26).mean()) / ndx['Net'].rolling(26).std()
        
        def interpret(z):
            if pd.isna(z): return "CALIBRATING"
            if z > 1.8: return "EXTREM_EUFORIE"
            if z < -1.8: return "EXTREM_PANIK"
            return "NEUTRAL"
        
        ndx['Interpretation'] = ndx['Z'].apply(interpret)
        return ndx
    except: return None

df = get_clean_data()

if df is not None:
    curr = df.iloc[-1]
    st.markdown(f"# MakroBase // <span style='color:#00f2ff;'>Intelligence Node</span>", unsafe_allow_html=True)
    
    t1, t2, t3 = st.tabs(["📊 DASHBOARD", "📜 HISTORICAL_LOGS", "🧬 LOGIC"])
    
    with t1:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"<div class='card'><div class='label'>Net Power (E-MINI)</div><div class='h-val'>{int(curr['Net']):,}</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='card'><div class='label'>Z-Score</div><div class='h-val'>{curr['Z']:.2f} σ</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='card'><div class='label'>Signal</div><div class='h-val' style='color:#00f2ff; font-size:26px;'>{curr['Interpretation']}</div></div>", unsafe_allow_html=True)

        fig = go.Figure(go.Scatter(x=df['Date'], y=df['Net'], line=dict(color='#00f2ff', width=2), fill='tozeroy'))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#555", height=400)
        st.plotly_chart(fig, use_container_width=True)

    with t2:
        st.markdown("### CLEAN DATA LOG (SINGLE ENTRY PER WEEK)")
        # Schöne Formatierung für die Historie
        log_display = df[['Date', 'Net', 'Z', 'Interpretation']].copy().sort_values('Date', ascending=False)
        log_display['Date'] = log_display['Date'].dt.strftime('%d.%m.%Y')
        log_display['Net'] = log_display['Net'].apply(lambda x: f"{int(x):,}")
        log_display['Z'] = log_display['Z'].apply(lambda x: f"{x:.2f} σ" if not pd.isna(x) else "N/A")
        
        st.table(log_display.head(20)) # Table ist oft klarer als Dataframe für statische Logs

    with t3:
        st.markdown("### SYSTEM_LOGIC_UPDATE")
        st.info("Dubletten-Bereinigung aktiv: Filter wurde auf 'E-MINI NASDAQ-100' fixiert.")
        st.write("Durch die Beschränkung auf den E-mini Kontrakt erhalten wir die präziseste Abbildung der Hedgefonds-Aktivität. Die Daten aus den Logs sind nun eindeutig und mathematisch korrekt für die Z-Score Berechnung.")

else:
    st.error("DATA_SYNC_FAILED")
