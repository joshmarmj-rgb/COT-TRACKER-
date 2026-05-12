import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# --- TERMINAL KONFIGURATION ---
st.set_page_config(page_title="MakroBase_INTELLIGENCE", layout="wide")
st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500&display=swap');
    * { background-color: #000 !important; color: #00ff41 !important; font-family: 'JetBrains Mono', monospace !important; }
    .stTable, table { border: 1px solid #00ff41 !important; }
    .stSelectbox div[data-baseweb="select"] { border: 1px solid #00ff41 !important; }
    .status-box { border: 1px solid #00ff41; padding: 15px; margin: 10px 0; }
</style>""", unsafe_allow_html=True)

# --- ENGINE ---
@st.cache_data(ttl=600)
def get_market_data():
    try:
        url = "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip"
        r = requests.get(url, timeout=10)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        df.columns = df.columns.str.strip()
        return df
    except: return None

raw_df = get_market_data()

def safe_process(search_term):
    if raw_df is None: return pd.DataFrame()
    # Flexible Suche, um den Fehler aus Bildschirmfoto_12-5-2026_235514... zu vermeiden
    data = raw_df[raw_df['Market_and_Exchange_Names'].str.contains(search_term, na=False, case=False)].copy()
    if not data.empty:
        data['Date'] = pd.to_datetime(data['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
        return data.sort_values('Date', ascending=False)
    return pd.DataFrame()

# Daten laden (Nasdaq = TFF Bericht / Gold = Legacy Bericht)
nasdaq = safe_process("MICRO E-MINI NASDAQ-100")
gold = safe_process("GOLD - COMMODITY EXCHANGE")

# --- NAVIGATION ---
st.sidebar.title("MakroBase // NAV")
auswahl = st.sidebar.radio("MODUS", ["KORRELATION", "NASDAQ_DETAILS", "GOLD_DETAILS"])

if nasdaq.empty or gold.empty:
    st.error("DATEN_LADE_FEHLER: Einer der Märkte wurde nicht gefunden.")
else:
    # Aktuelle Werte extrahieren
    # Nasdaq (Leveraged Funds)
    n_l, n_s = int(nasdaq.iloc[0]['Lev_Money_Positions_Long_All']), int(nasdaq.iloc[0]['Lev_Money_Positions_Short_All'])
    n_net = n_l - n_s
    
    # Gold (Non-Commercials)
    g_l, g_s = int(gold.iloc[0]['NonComm_Positions_Long_All']), int(gold.iloc[0]['NonComm_Positions_Short_All'])
    g_net = g_l - g_s

    if auswahl == "KORRELATION":
        st.header("STRATEGISCHE_ANALYSE")
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"NASDAQ_NETTO: {n_net:,}")
            st.write(f"BIAS: {'GEFAHR' if n_net < 0 else 'STABIL'}")
        with c2:
            st.write(f"GOLD_NETTO: {g_net:,}")
            st.write(f"BIAS: {'SICHERHEIT' if g_net > 0 else 'NEUTRAL'}")
        
        st.write("---")
        # Knallharte Korrelations-Logik
        if n_net < -150000 and g_net > 150000:
            st.markdown("<div class='status-box' style='color:#ff2255 !important;'>ALARM: RISK-OFF MODUS<br>Hedgefonds flüchten aus Tech in Gold. Crashgefahr erhöht.</div>", unsafe_allow_html=True)
        elif n_net > 0 and g_net < 0:
            st.markdown("<div class='status-box'>ALARM: RISK-ON MODUS<br>Geld fließt in Tech, Gold wird ignoriert. Bullenmarkt aktiv.</div>", unsafe_allow_html=True)
        else:
            st.write("STATUS: KEINE_KLARE_FLUCHTBEWEGUNG")

    elif auswahl == "GOLD_DETAILS":
        st.header("GOLD_NODE_ANALYSE")
        g_oi = int(gold.iloc[0]['Open_Interest_All'])
        g_ratio = (g_s / g_oi) * 100
        
        c1, c2, c3 = st.columns(3)
        c1.metric("GOLD_NETTO", f"{g_net:,}")
        c2.metric("KAUF (LONG)", f"{g_l:,}")
        c3.metric("VERKAUF (SHORT)", f"{g_s:,}")
        
        st.write("---")
        st.write(f"VERKAUFS_ANTEIL_GOLD: {g_ratio:.2f}%")
        st.table(gold[['Date', 'NonComm_Positions_Long_All', 'NonComm_Positions_Short_All']].head(10))

    elif auswahl == "NASDAQ_DETAILS":
        st.header("NASDAQ_NODE_ANALYSE")
        st.metric("NETTO_POWER", f"{n_net:,}")
        st.table(nasdaq[['Date', 'Lev_Money_Positions_Long_All', 'Lev_Money_Positions_Short_All']].head(10))
