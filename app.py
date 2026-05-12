import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# --- DESIGN: ULTRA-DARK SUBMARINE (STRENG & CLEAN) ---
st.set_page_config(page_title="MakroBase_Terminal", layout="wide")
st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Hintergrund: Fast 100% Schwarz */
    .stApp { background-color: #000205; color: #00ff41; font-family: 'JetBrains Mono', monospace; }
    
    /* Container Design */
    .data-card { 
        padding: 30px; 
        border-radius: 10px; 
        border: 1px solid #001d3d; 
        background-color: #00050a;
        text-align: center;
    }
    
    /* Farb-Definitionen */
    .pos-green { color: #00ff41 !important; font-weight: bold; font-size: 42px; }
    .neg-red { color: #ff4136 !important; font-weight: bold; font-size: 42px; }
    .label-blue { color: #8ecae6 !important; font-size: 14px; text-transform: uppercase; letter-spacing: 2px; }
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_cftc_data(url):
    try:
        r = requests.get(url, timeout=20)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# Daten-Akquise
nasdaq_raw = load_cftc_data("https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip")
gold_raw = load_cftc_data("https://www.cftc.gov/files/dea/history/fut_disagg_txt_2026.zip")

# Filterung
n_data = nasdaq_raw[nasdaq_raw['Market_and_Exchange_Names'].str.contains("MICRO E-MINI NASDAQ-100", na=False)].copy()
g_data = gold_raw[gold_raw['Market_and_Exchange_Names'].str.contains("GOLD - COMMODITY EXCHANGE", na=False)].copy()

if not n_data.empty and not g_data.empty:
    # Datum Formatierung
    d_raw = str(n_data.iloc[0]['As_of_Date_In_Form_YYMMDD'])
    clean_date = f"{d_raw[4:6]}.{d_raw[2:4]}.20{d_raw[0:2]}"

    # Kalkulationen
    n_long = int(n_data.iloc[0]['Lev_Money_Positions_Long_All'])
    n_short = int(n_data.iloc[0]['Lev_Money_Positions_Short_All'])
    n_net = n_long - n_short

    g_long = int(g_data.iloc[0]['M_Money_Positions_Long_All'])
    g_short = int(g_data.iloc[0]['M_Money_Positions_Short_All'])
    g_net = g_long - g_short

    # --- SIDEBAR NAVI ---
    st.sidebar.markdown("### ⚓ NAVIGATION")
    page = st.sidebar.radio("MODUS", ["DASHBOARD", "TRADE-IDEEN"])

    if page == "DASHBOARD":
        st.title("🚢 OPERATIVES DASHBOARD")
        st.write(f"SYSTEM_ZEIT: {clean_date} | STATUS: SCANNING_MARKETS")
        st.write("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""<div class='data-card'>
                <p class='label-blue'>NASDAQ KONTRAKTE (NETTO)</p>
                <p class='{"pos-green" if n_net > 0 else "neg-red"}'>{n_net:,}</p>
                <p style='color:white;'>Was das heißt: {'Die Profis kaufen Aktien.' if n_net > 0 else 'Die Profis setzen auf fallende Preise.'}</p>
            </div>""", unsafe_allow_html=True)

        with col2:
            st.markdown(f"""<div class='data-card'>
                <p class='label-blue'>GOLD KONTRAKTE (NETTO)</p>
                <p class='{"pos-green" if g_net > 0 else "neg-red"}'>{g_net:,}</p>
                <p style='color:white;'>Was das heißt: {'Angst im Markt - Profis suchen Schutz.' if g_net > 0 else 'Ruhe im Markt - Gold wird nicht gebraucht.'}</p>
            </div>""", unsafe_allow_html=True)

        st.write("---")
        st.subheader("DETAIL-AUSWERTUNG")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("NASDAQ KÄUFER", f"{n_long:,}")
        c2.metric("NASDAQ VERKÄUFER", f"{n_short:,}")
        c3.metric("GOLD KÄUFER", f"{g_long:,}")
        c4.metric("GOLD VERKÄUFER", f"{g_short:,}")

    elif page == "TRADE-IDEEN":
        st.title("💡 STRATEGISCHE LOGIK")
        st.write("Analyse der aktuellen Machtverhältnisse:")
        st.write("---")

        if n_net < -150000 and g_net > 50000:
            st.error("### 🚨 WARNUNG: FLUCHT-MODUS AKTIV")
            st.write("Fast alle Profis verkaufen Nasdaq und kaufen Gold. Das ist wie bei einem Gewitter: Alle rennen unter ein Dach. Sei extrem vorsichtig mit Käufen!")
        elif n_net > 50000 and g_net < 0:
            st.success("### 🚀 SIGNAL: VOLLGAS-MODUS")
            st.write("Die Profis werfen ihr Gold weg und kaufen Nasdaq. Das bedeutet: Sie haben keine Angst und vertrauen in steigende Kurse.")
        else:
            st.info("### ⚖️ SIGNAL: ABWARTEN")
            st.write("Es gibt kein klares Übergewicht. Weder die Käufer noch die Verkäufer haben die volle Kontrolle. Ein guter Kapitän bleibt im Hafen, bis der Wind klar weht.")
