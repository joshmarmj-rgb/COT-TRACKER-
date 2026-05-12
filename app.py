import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# --- RAW TERMINAL STYLE ---
st.set_page_config(page_title="MakroBase RAW", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #000; color: #fff; font-family: 'JetBrains Mono', monospace; }
    .header { color: #00f2ff; border-bottom: 2px solid #00f2ff; padding-bottom: 10px; margin-bottom: 20px; }
    .metric-box { border: 1px solid #333; padding: 20px; background: #050505; }
    .label { color: #00f2ff; font-size: 12px; }
    .val { font-size: 48px; font-weight: bold; }
    .interpretation { color: #ff2255; font-size: 14px; margin-top: 10px; border-top: 1px solid #222; padding-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def fetch_raw_cot():
    try:
        # Direkter Zugriff auf die 2026er Rohdaten der CFTC
        url = "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip"
        r = requests.get(url, timeout=15)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        df.columns = df.columns.str.strip()
        # Fokus auf den E-Mini Nasdaq-100
        ndx = df[df['Market_and_Exchange_Names'].str.contains("E-MINI NASDAQ-100", na=False)].copy()
        ndx['Date'] = pd.to_datetime(ndx['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
        ndx = ndx.sort_values('Date', ascending=False)
        return ndx
    except: return None

df = fetch_raw_cot()

if df is not None:
    # Die aktuellsten Daten (Top of the List)
    latest = df.iloc[0]
    
    st.markdown("<h1 class='header'>MakroBase // LIVE_COT_FEED</h1>", unsafe_allow_html=True)
    
    # ECHTE DATEN SECTION
    c1, c2, c3 = st.columns(3)
    
    longs = int(latest['Lev_Money_Positions_Long_All'])
    shorts = int(latest['Lev_Money_Positions_Short_All'])
    net = longs - shorts
    
    with c1:
        st.markdown(f"""<div class='metric-box'><div class='label'>LONG POSITIONS (HEDGEFUNDS)</div><div class='val'>{longs:,}</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class='metric-box'><div class='label'>SHORT POSITIONS (HEDGEFUNDS)</div><div class='val'>{shorts:,}</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class='metric-box'><div class='label'>NET POWER (OVERALL BIAS)</div><div class='val' style='color:#00f2ff;'>{net:,}</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    
    # WAS BEDEUTET DAS?
    st.subheader("DATA_INTERPRETATION")
    if net < -150000:
        desc = "EXTREME_SHORT_POSITIONING: Die Hedgefonds sind massiv 'short'. Historisch gesehen ist das oft ein Zeichen für eine Markt-Bodenbildung, da fast jeder bereits verkauft hat (Short Squeeze Gefahr)."
    elif net > 50000:
        desc = "EXTREME_LONG_POSITIONING: Die Hedgefonds sind übermütig. Das Risiko für einen Rücksetzer steigt massiv."
    else:
        desc = "NEUTRAL_FLOW: Keine extremen Ungleichgewichte zwischen Bullen und Bären."
    
    st.info(f"STATUS_REPORT: {desc}")

    # DER HISTORISCHE LOG (Zahlen ohne Schnickschnack)
    st.markdown("### HISTORICAL_RAW_LOGS")
    history = df[['Date', 'Lev_Money_Positions_Long_All', 'Lev_Money_Positions_Short_All']].copy()
    history['NET_POSITION'] = history['Lev_Money_Positions_Long_All'] - history['Lev_Money_Positions_Short_All']
    history['Date'] = history['Date'].dt.strftime('%d.%m.%Y')
    
    # Umbenennung für maximale Klarheit
    history.columns = ['DATUM', 'LONGS (Fonds)', 'SHORTS (Fonds)', 'NETTO_BIAS']
    st.table(history.head(10))

else:
    st.error("UPLINK_FAILURE: Keine Verbindung zum CFTC-Server.")
