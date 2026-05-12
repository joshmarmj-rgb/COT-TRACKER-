import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- SETUP ---
st.set_page_config(page_title="NASDAQ QUANTUM V17", layout="wide")

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
        
        # Kalkulationen
        ndx['Net'] = ndx['Lev_Money_Positions_Long_All'] - ndx['Lev_Money_Positions_Short_All']
        window = 26
        ndx['Mean'] = ndx['Net'].rolling(window).mean()
        ndx['Std'] = ndx['Net'].rolling(window).std()
        ndx['Z'] = (ndx['Net'] - ndx['Mean']) / ndx['Std']
        return ndx
    except: return None

df = get_data()

if df is not None:
    curr = df.iloc[-1]
    
    st.markdown(f"## NASDAQ_QUANTUM_CORE // v17.0")
    
    # --- TABS ---
    tab1, tab2, tab3, tab4 = st.tabs(["DRIVE_DASHBOARD", "QUANT_THEORY", "HISTORICAL_LOGS", "SYSTEM_MANUAL"])
    
    with tab1:
        st.markdown("### CURRENT MARKET STATE")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""<div class='card'><div class='label'>Net Position</div><div class='h-val'>{int(curr['Net']):,}</div>
            <p class='explainer'>Die aktuelle Wettschuld der Hedgefonds. Negativ bedeutet, sie sind 'Net Short'.</p></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class='card'><div class='label'>Z-Score Bias</div><div class='h-val'>{curr['Z']:.2f} σ</div>
            <p class='explainer'>Abweichung vom Normalwert. 0.0 ist der Durchschnitt der letzten 6 Monate.</p></div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class='card'><div class='label'>Open Interest</div><div class='h-val'>{int(curr['Open_Interest_All']):,}</div>
            <p class='explainer'>Gesamtzahl der aktiven Kontrakte. Zeigt die Liquidität im Nasdaq-Future.</p></div>""", unsafe_allow_html=True)
            
        fig = go.Figure(go.Scatter(x=df['Date'], y=df['Net'], line=dict(color='#00f2ff', width=2), fill='tozeroy'))
        fig.update_layout(title="Net Power Trend (Leveraged Funds)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#555", height=400)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("### DIE MATHEMATIK HINTER DEN SIGNALEN")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"""
            <div class='card'>
                <div class='label'>Was ist die Net Power?</div>
                <div class='explainer' style='border:none;'>
                    Im CoT-Report (Commitment of Traders) werden Teilnehmer in Gruppen unterteilt. 
                    Wir tracken die <b>'Leveraged Money'</b> Gruppe (Hedgefonds).<br><br>
                    <b>Formel:</b> $Longs (Kaufverträge) - Shorts (Verkaufsverträge) = Net Power$<br><br>
                    Aktuell: {int(curr['Lev_Money_Positions_Long_All']):,} Long vs. {int(curr['Lev_Money_Positions_Short_All']):,} Short.
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_b:
            st.markdown(f"""
            <div class='card'>
                <div class='label'>Was ist der Z-Score?</div>
                <div class='explainer' style='border:none;'>
                    Der Z-Score macht Zahlen vergleichbar. Er sagt uns, wie weit der aktuelle Wert vom Durchschnitt entfernt ist, gemessen in Standardabweichungen ($σ$).<br><br>
                    <b>Berechnung:</b><br>
                    1. Berechne den Schnitt der letzten 26 Wochen.<br>
                    2. Berechne die typische Schwankung (StdDev).<br>
                    3. $Z = (Aktuell - Schnitt) / Schwankung$<br><br>
                    <b>Interpretation:</b><br>
                    - Über +2.0: "Crowded Long" (Gefahr)<br>
                    - Unter -2.0: "Crowded Short" (Chance)
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        st.markdown("### RAW CFTC DATA FEED")
        # Nur die wichtigsten Spalten anzeigen
        display_cols = ['Date', 'Net', 'Z', 'Lev_Money_Positions_Long_All', 'Lev_Money_Positions_Short_All', 'Open_Interest_All']
        st.dataframe(df[display_cols].sort_values('Date', ascending=False), use_container_width=True)

    with tab4:
        st.markdown("### BENUTZERHANDBUCH")
        st.info("Dieses Terminal dient zur Identifikation von institutionellen Extrempunkten.")
        st.markdown("""
        1. **Check Z-Score:** Ist der Wert zwischen -1 und +1? -> Markt ist im Gleichgewicht (kein Trade).
        2. **Check Z-Score:** Ist der Wert > +2.0? -> Institutionelle Euphorie. Erwarte einen Rücksetzer im Nasdaq.
        3. **Check Z-Score:** Ist der Wert < -2.0? -> Institutionelle Panik. Erwarte eine starke Erholung (Short Squeeze).
        4. **Net Power:** Beachte den Trend. Steigt die Net Power bei fallenden Kursen? -> Akkumulation (Bullisch).
        """)

else:
    st.error("UPLINK FAILURE // CFTC DATA NOT REACHABLE")
