import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# --- DESIGN: DEEP MIDNIGHT BLUE ---
st.set_page_config(page_title="MakroBase_DeepBlue", layout="wide")
st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Extrem dunkles Blau (fast Schwarz) */
    .stApp { background-color: #000814; color: #00ff41; font-family: 'JetBrains Mono', monospace; }
    
    /* Karten-Design */
    .status-card { 
        padding: 25px; 
        border-radius: 12px; 
        border: 1px solid #003566; 
        margin-bottom: 25px;
        background-color: #001d3d;
    }
    
    [data-testid="stMetricValue"] { color: #00ff41 !important; font-size: 35px; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #8ecae6 !important; font-size: 16px; }
    .stTable { border: 1px solid #003566 !important; }
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_cftc_bundle(url):
    try:
        r = requests.get(url, timeout=20)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# Daten laden
nasdaq_raw = load_cftc_bundle("https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip")
gold_raw = load_cftc_bundle("https://www.cftc.gov/files/dea/history/fut_disagg_txt_2026.zip")

# Filterung (Fehler aus Bildschirmfoto_13-5-2026_0236... behoben)
n_data = nasdaq_raw[nasdaq_raw['Market_and_Exchange_Names'].str.contains("MICRO E-MINI NASDAQ-100", na=False)].copy()
g_data = gold_raw[gold_raw['Market_and_Exchange_Names'].str.contains("GOLD - COMMODITY EXCHANGE", na=False)].copy()

if n_data.empty or g_data.empty:
    st.error("⚠️ SYSTEM_FEHLER: Verbindung zum Datenstrom verloren.")
else:
    # Datum säubern
    d = str(n_data.iloc[0]['As_of_Date_In_Form_YYMMDD'])
    clean_date = f"{d[4:6]}.{d[2:4]}.20{d[0:2]}"

    # Netto-Werte
    n_net = int(n_data.iloc[0]['Lev_Money_Positions_Long_All']) - int(n_data.iloc[0]['Lev_Money_Positions_Short_All'])
    g_net = int(g_data.iloc[0]['M_Money_Positions_Long_All']) - int(g_data.iloc[0]['M_Money_Positions_Short_All'])

    st.title("🚢 MAKRO_BASE // DEEP_BLUE_MONITOR")
    st.write(f"PROZESS-STEUERUNG | DATEN-STAND: {clean_date}")
    st.write("---")

    # --- STRATEGISCHE BEURTEILUNG ---
    st.subheader("STRATEGISCHE LAGEBEURTEILUNG")
    
    if n_net < -150000 and g_net > 50000:
        st.markdown(f"""<div class='status-card' style='border-left: 5px solid #ff4136;'>
            <h3 style='color: #ff4136;'>Lagebericht: Warnstufe Rot</h3>
            <p style='color: #ffffff;'>Die Daten zeigen eine deutliche Fluchtbewegung. Große Marktteilnehmer ziehen Kapital aus risikoreichen Aktien ab 
            und sichern sich mit Gold ab. Dies deutet auf eine gezielte Vorbereitung auf sinkende Kurse hin.</p>
        </div>""", unsafe_allow_html=True)
    elif n_net > 0:
        st.markdown(f"""<div class='status-card' style='border-left: 5px solid #2ecc40;'>
            <h3 style='color: #2ecc40;'>Lagebericht: Markt-Vertrauen</h3>
            <p style='color: #ffffff;'>Das Marktumfeld ist stabil. Die führenden Handelsgruppen investieren verstärkt in Technik-Werte. 
            Es herrscht eine positive Grundstimmung ohne Anzeichen von Absicherungs-Panik.</p>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class='status-card' style='border-left: 5px solid #0074D9;'>
            <h3 style='color: #0074D9;'>Lagebericht: Neutrale Phase</h3>
            <p style='color: #ffffff;'>Die Akteure halten sich derzeit zurück. Es gibt keine klaren Anzeichen für massive Käufe oder Verkäufe. 
            In dieser Phase beobachten die Marktteilnehmer die weitere Entwicklung, ohne sich festzulegen.</p>
        </div>""", unsafe_allow_html=True)

    # --- METRIKEN ---
    col1, col2 = st.columns(2)
    with col1:
        st.metric("NASDAQ KRAFT-INDEX", f"{n_net:,}", help="Ein negativer Wert bedeutet, dass Profis auf fallende Kurse wetten.")
    with col2:
        st.metric("GOLD ABSICHERUNGS-WERT", f"{g_net:,}", help="Ein positiver Wert zeigt den Kauf von Sicherheit an.")

    # --- DATEN-HISTORIE ---
    st.write("---")
    st.subheader("HISTORISCHES PROTOKOLL")
    
    hist = n_data[['As_of_Date_In_Form_YYMMDD', 'Lev_Money_Positions_Long_All', 'Lev_Money_Positions_Short_All']].head(8).copy()
    hist.columns = ['DATUM', 'KAUF', 'VERKAUF']
    st.table(hist)
