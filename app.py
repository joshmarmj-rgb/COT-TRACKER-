import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# --- DESIGN: ABSOLUTE MIDNIGHT SUBMARINE ---
st.set_page_config(page_title="MakroBase_Master", layout="wide")
st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #000103; color: #00ff41; font-family: 'JetBrains Mono', monospace; }
    .pos-green { color: #00ff41 !important; font-weight: bold; font-size: 28px; }
    .neg-red { color: #ff4136 !important; font-weight: bold; font-size: 28px; }
    .info-box { padding: 20px; border-radius: 10px; border: 1px solid #001d3d; background-color: #00040a; margin-bottom: 20px; }
    h3 { color: #8ecae6 !important; border-bottom: 1px solid #001d3d; padding-bottom: 10px; }
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_data_source(url):
    try:
        r = requests.get(url, timeout=20)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# Daten laden
nasdaq_raw = load_data_source("https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip")
gold_raw = load_data_source("https://www.cftc.gov/files/dea/history/fut_disagg_txt_2026.zip")

# Filterung
n_data = nasdaq_raw[nasdaq_raw['Market_and_Exchange_Names'].str.contains("MICRO E-MINI NASDAQ-100", na=False)].copy()
g_data = gold_raw[gold_raw['Market_and_Exchange_Names'].str.contains("GOLD - COMMODITY EXCHANGE", na=False)].copy()

if n_data.empty or g_data.empty:
    st.error("⚠️ SYSTEM_FEHLER: Verbindung zum Datenkern unterbrochen.")
else:
    # Datum säubern
    d = str(n_data.iloc[0]['As_of_Date_In_Form_YYMMDD'])
    clean_date = f"{d[4:6]}.{d[2:4]}.20{d[0:2]}"

    # Werte extrahieren
    n_long, n_short = int(n_data.iloc[0]['Lev_Money_Positions_Long_All']), int(n_data.iloc[0]['Lev_Money_Positions_Short_All'])
    n_net = n_long - n_short
    
    g_long, g_short = int(g_data.iloc[0]['M_Money_Positions_Long_All']), int(g_data.iloc[0]['M_Money_Positions_Short_All'])
    g_net = g_long - g_short

    # --- NAVIGATION ---
    st.sidebar.title("⚓ NAVIGATOR")
    page = st.sidebar.radio("ZENTRALE", ["LIVE-DASHBOARD", "TRADE-IDEEN"])

    if page == "LIVE-DASHBOARD":
        st.title("📊 ECHTZEIT-ANALYSE")
        st.write(f"Stand der Protokolle: {clean_date}")
        st.write("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("<div class='info-box'>", unsafe_allow_html=True)
            st.subheader("🖥️ NASDAQ (Technik-Aktien)")
            n_color = "pos-green" if n_net > 0 else "neg-red"
            st.markdown(f"NETTO-POWER: <span class='{n_color}'>{n_net:,}</span>", unsafe_allow_html=True)
            st.write(f"**Bedeutung:** {'Optimismus. Profis kaufen.' if n_net > 0 else 'Skepsis. Profis wetten auf fallende Kurse.'}")
            st.write(f"Käufer: {n_long:,} | Verkäufer: {n_short:,}")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='info-box'>", unsafe_allow_html=True)
            st.subheader("💰 GOLD (Sicherer Hafen)")
            g_color = "pos-green" if g_net > 0 else "neg-red"
            st.markdown(f"NETTO-POWER: <span class='{g_color}'>{g_net:,}</span>", unsafe_allow_html=True)
            st.write(f"**Bedeutung:** {'Angst-Schutz. Gold wird als Sicherheit gekauft.' if g_net > 0 else 'Desinteresse. Gold wird verkauft.'}")
            st.write(f"Käufer: {g_long:,} | Verkäufer: {g_short:,}")
            st.markdown("</div>", unsafe_allow_html=True)

        st.write("---")
        st.subheader("🌐 DIE LOGIK DER ZAHLEN")
        st.info(f"Wenn Nasdaq im Minus (<0) steht und Gold im Plus (>0), bereiten sich die großen Banken auf einen Sturm vor. Aktuell ist das Verhältnis Nasdaq ({n_net:,}) zu Gold ({g_net:,}).")

    elif page == "TRADE-IDEEN":
        st.title("💡 STRATEGISCHE TRADE-IDEEN")
        st.write("Basierend auf der aktuellen Verteilung der Hedgefonds:")
        st.write("---")

        # Logik für Trade-Ideen
        if n_net < -180000 and g_net > 50000:
            st.markdown("<div class='info-box' style='border-color: #ff4136;'>", unsafe_allow_html=True)
            st.write("### 🚨 IDEE: SHORT-SQUEEZE GEFAHR")
            st.write("Die Nasdaq-Verkäufe sind extrem hoch. Wenn der Markt nicht weiter fällt, müssen alle Verkäufer gleichzeitig zurückkaufen. Das könnte eine explosionsartige Rallye nach oben auslösen.")
            st.write("**Empfehlung:** Vorsicht bei neuen Verkäufen. Auf Trendwende achten.")
            st.markdown("</div>", unsafe_allow_html=True)
        
        elif n_net > 50000 and g_net < 0:
            st.markdown("<div class='info-box' style='border-color: #00ff41;'>", unsafe_allow_html=True)
            st.write("### 🚀 IDEE: TREND-FORTSETZUNG")
            st.write("Die Profis kaufen Aktien und verkaufen Gold. Das Schiff hat volle Fahrt aufgenommen.")
            st.write("**Empfehlung:** Aktien-Käufe im Nasdaq bevorzugen, solange Gold schwach bleibt.")
            st.markdown("</div>", unsafe_allow_html=True)
        
        else:
            st.write("### ⚖️ IDEE: SEITWÄRTS-PHASE")
            st.write("Die Daten liefern aktuell kein extremes Signal. Es ist klüger, an der Seitenlinie zu warten, bis eine Seite (Nasdaq oder Gold) massiv ausschlägt.")
