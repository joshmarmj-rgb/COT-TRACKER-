import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# --- DESIGN: ULTRA DARK SUBMARINE ---
st.set_page_config(page_title="MakroBase_Final", layout="wide")
st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Extrem dunkles Midnight (nahezu Schwarz) */
    .stApp { background-color: #00040a; color: #00ff41; font-family: 'JetBrains Mono', monospace; }
    
    /* Karten-Design */
    .status-card { 
        padding: 25px; 
        border-radius: 12px; 
        border: 1px solid #001d3d; 
        margin-bottom: 25px;
        background-color: #000814;
    }
    
    /* Farben für Kauf/Verkauf */
    .pos-green { color: #00ff41 !important; font-weight: bold; }
    .neg-red { color: #ff4136 !important; font-weight: bold; }
    
    [data-testid="stMetricValue"] { font-size: 35px; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #8ecae6 !important; }
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_data_pack(url):
    try:
        r = requests.get(url, timeout=20)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# Daten-Streams
nasdaq_raw = load_data_pack("https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip")
gold_raw = load_data_pack("https://www.cftc.gov/files/dea/history/fut_disagg_txt_2026.zip")

# Filter
n_data = nasdaq_raw[nasdaq_raw['Market_and_Exchange_Names'].str.contains("MICRO E-MINI NASDAQ-100", na=False)].copy()
g_data = gold_raw[gold_raw['Market_and_Exchange_Names'].str.contains("GOLD - COMMODITY EXCHANGE", na=False)].copy()

if n_data.empty or g_data.empty:
    st.error("⚠️ SYSTEM_FEHLER: Datenstrom unterbrochen.")
else:
    # Datum
    d = str(n_data.iloc[0]['As_of_Date_In_Form_YYMMDD'])
    clean_date = f"{d[4:6]}.{d[2:4]}.20{d[0:2]}"

    # Aktuelle Werte
    n_long, n_short = int(n_data.iloc[0]['Lev_Money_Positions_Long_All']), int(n_data.iloc[0]['Lev_Money_Positions_Short_All'])
    n_net = n_long - n_short
    
    g_long, g_short = int(g_data.iloc[0]['M_Money_Positions_Long_All']), int(g_data.iloc[0]['M_Money_Positions_Short_All'])
    g_net = g_long - g_short

    # Trend-Berechnung (Vergleich zur Vorwoche)
    n_net_prev = int(n_data.iloc[1]['Lev_Money_Positions_Long_All']) - int(n_data.iloc[1]['Lev_Money_Positions_Short_All'])
    n_trend = n_net - n_net_prev

    st.title("🚢 MAKRO_BASE // OPERATIVES_TERMINAL")
    st.write(f"STEUERUNG AKTIV | PROTOKOLL VOM: {clean_date}")
    st.write("---")

    # --- LAGEBEURTEILUNG ---
    if n_net < -150000 and g_net > 50000:
        st.markdown(f"""<div class='status-card' style='border-left: 5px solid #ff4136;'>
            <h3 style='color: #ff4136;'>Lagebericht: Kritische Fluchtbewegung</h3>
            <p>Die Akteure ziehen massiv Kapital aus dem Nasdaq ab (<span class='neg-red'>{n_net:,}</span>) 
            und verstärken ihre Positionen im Gold (<span class='pos-green'>{g_net:,}</span>). 
            Das System erkennt eine strategische Absicherung gegen fallende Aktienkurse.</p>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class='status-card' style='border-left: 5px solid #0074D9;'>
            <h3 style='color: #0074D9;'>Lagebericht: Standard-Operation</h3>
            <p>Der Markt zeigt aktuell ein ausgeglichenes Verhalten. Keine extremen Fluchtbewegungen in Gold erkennbar.</p>
        </div>""", unsafe_allow_html=True)

    # --- METRIKEN MIT FARB-LOGIK ---
    col1, col2 = st.columns(2)
    with col1:
        color = "neg-red" if n_net < 0 else "pos-green"
        st.markdown(f"NASDAQ KRAFT-INDEX<br><span class='{color}' style='font-size:35px;'>{n_net:,}</span>", unsafe_allow_html=True)
        st.write(f"Trend zur Vorwoche: {'📈' if n_trend > 0 else '📉'} {n_trend:,}")

    with col2:
        color = "pos-green" if g_net > 0 else "neg-red"
        st.markdown(f"GOLD ABSICHERUNGS-WERT<br><span class='{color}' style='font-size:35px;'>{g_net:,}</span>", unsafe_allow_html=True)
        st.write("Wird als Schutzschild gegen Marktschwankungen genutzt.")

    # --- NEU: TREND-RADAR (Informativer als nur Historie) ---
    st.write("---")
    st.subheader("📡 STRATEGISCHER TREND-RADAR")
    
    c1, c2, c3 = st.columns(3)
    c1.write("**MARKT-STÄRKE**")
    c1.write(f"Käufer: <span class='pos-green'>{n_long:,}</span>", unsafe_allow_html=True)
    c1.write(f"Verkäufer: <span class='neg-red'>{n_short:,}</span>", unsafe_allow_html=True)
    
    c2.write("**DOMINANZ**")
    dom = (n_short / (n_long + n_short)) * 100
    c2.write(f"Short-Anteil: {dom:.1f}%")
    c2.write("Über 60% = Aggressiv")

    c3.write("**GOLD-STATUS**")
    c3.write(f"Long-Power: <span class='pos-green'>{g_long:,}</span>", unsafe_allow_html=True)
    c3.write(f"Short-Power: <span class='neg-red'>{g_short:,}</span>", unsafe_allow_html=True)
