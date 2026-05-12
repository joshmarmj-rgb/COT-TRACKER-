import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# --- TERMINAL OPTIK (Besser strukturiert) ---
st.set_page_config(page_title="MakroBase_V28", layout="wide")
st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500&display=swap');
    * { background-color: #000 !important; color: #00ff41 !important; font-family: 'JetBrains Mono', monospace !important; }
    .stMetric { border: 1px solid #00ff41; padding: 15px; border-radius: 10px; }
    .status-alert { border: 2px solid #ff0000; padding: 20px; text-align: center; font-size: 20px; margin: 10px 0; }
    .status-ok { border: 2px solid #00ff41; padding: 20px; text-align: center; font-size: 20px; margin: 10px 0; }
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def fetch_data(url):
    try:
        r = requests.get(url, timeout=10)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# Lade Daten
nasdaq_raw = fetch_data("https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip")
gold_raw = fetch_data("https://www.cftc.gov/files/dea/history/fut_disagg_txt_2026.zip")

# Filter
nasdaq = nasdaq_raw[nasdaq_raw['Market_and_Exchange_Names'].str.contains("MICRO E-MINI NASDAQ-100", na=False)].copy()
gold = gold_raw[gold_raw['Market_and_Exchange_Names'].str.contains("GOLD - COMMODITY EXCHANGE", na=False)].copy()

if nasdaq.empty or gold.empty:
    st.error("!!! VERBINDUNGSFEHLER ZUR ZENTRALE !!!")
else:
    # Berechnungen
    n_net = int(nasdaq.iloc[0]['Lev_Money_Positions_Long_All']) - int(nasdaq.iloc[0]['Lev_Money_Positions_Short_All'])
    g_net = int(gold.iloc[0]['M_Money_Positions_Long_All']) - int(gold.iloc[0]['M_Money_Positions_Short_All'])

    # --- ÜBERSCHRIFT ---
    st.title("🖥️ MAKRO_BASE // GLOBAL_MONITOR")
    st.write(f"SYSTEM_CHECK: ONLINE // DATEN_STAND: {nasdaq.iloc[0]['As_of_Date_In_Form_YYMMDD']}")
    st.write("---")

    # --- ABSCHNITT 1: DIE MARKT-AMPEL (Für Kinder verständlich) ---
    st.subheader("STRATEGIE_CHECK")
    
    if n_net < -150000 and g_net > 50000:
        st.markdown("<div class='status-alert'>🔴 GEFAHR: GROSSE FIRMEN HABEN ANGST!<br>Aktien werden verkauft, Gold wird als Schutz gekauft.</div>", unsafe_allow_html=True)
    elif n_net > 0:
        st.markdown("<div class='status-ok'>🟢 ALLES GUT: POSITIVE STIMMUNG<br>Die Mehrheit glaubt an steigende Kurse.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='border: 2px solid #ffff00; padding: 20px; text-align: center; color: #ffff00 !important;'>🟡 WARNUNG: KEINE KLARE RICHTUNG<br>Der Markt wartet ab.</div>", unsafe_allow_html=True)

    st.write("---")

    # --- ABSCHNITT 2: DIE ZAHLEN (Einfach präsentiert) ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 📈 AKTIEN-MARKT (Nasdaq)")
        st.metric("POWER-LEVEL", f"{n_net:,}", "ANGST" if n_net < 0 else "LAUNE")
        st.write("Erklärung: Minus bedeutet, die Profis wetten gegen Aktien.")

    with col2:
        st.write("### 💰 GOLD-MARKT")
        st.metric("POWER-LEVEL", f"{g_net:,}", "SICHERHEIT" if g_net > 0 else "KEIN INTERESSE")
        st.write("Erklärung: Plus bedeutet, die Profis suchen Schutz im Gold.")

    st.write("---")

    # --- ABSCHNITT 3: TABELLEN (Nur das Nötigste) ---
    st.subheader("HISTORISCHER_DATEN_STROM")
    auswahl = st.selectbox("WELCHEN MARKT ZEIGEN?", ["NASDAQ", "GOLD"])
    
    if auswahl == "NASDAQ":
        h = nasdaq[['As_of_Date_In_Form_YYMMDD', 'Lev_Money_Positions_Long_All', 'Lev_Money_Positions_Short_All']].head(10)
        h.columns = ['DATUM', 'KÄUFER', 'VERKÄUFER']
        st.table(h)
    else:
        h = gold[['As_of_Date_In_Form_YYMMDD', 'M_Money_Positions_Long_All', 'M_Money_Positions_Short_All']].head(10)
        h.columns = ['DATUM', 'KÄUFER', 'VERKÄUFER']
        st.table(h)
