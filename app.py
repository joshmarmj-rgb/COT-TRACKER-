import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# --- DESIGN: ABSOLUTE MIDNIGHT ---
st.set_page_config(page_title="MakroBase_Final", layout="wide")
st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Nahezu 100% Schwarz für maximale Konzentration */
    .stApp { background-color: #000205; color: #00ff41; font-family: 'JetBrains Mono', monospace; }
    
    .status-card { 
        padding: 25px; 
        border-radius: 12px; 
        border: 1px solid #001d3d; 
        margin-bottom: 25px;
        background-color: #00050a;
    }
    
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
    n_oi = int(n_data.iloc[0]['Open_Interest_All'])
    
    g_long, g_short = int(g_data.iloc[0]['M_Money_Positions_Long_All']), int(g_data.iloc[0]['M_Money_Positions_Short_All'])
    g_net = g_long - g_short

    st.title("🚢 MAKRO_BASE // OPERATIVES_TERMINAL")
    st.write(f"STEUERUNG AKTIV | PROTOKOLL VOM: {clean_date}")
    st.write("---")

    # --- LAGEBEURTEILUNG ---
    st.subheader("STRATEGISCHE LAGEBEURTEILUNG")
    if n_net < -150000 and g_net > 50000:
        st.markdown(f"""<div class='status-card' style='border-left: 5px solid #ff4136;'>
            <h3 style='color: #ff4136;'>Lagebericht: Kritische Fluchtbewegung</h3>
            <p>Kapitalabfluss aus Nasdaq: <span class='neg-red'>{n_net:,}</span> | Sicherheitsaufbau Gold: <span class='pos-green'>{g_net:,}</span>. 
            Ein seltener Zustand massiver Risiko-Vermeidung.</p>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class='status-card' style='border-left: 5px solid #0074D9;'>
            <h3 style='color: #0074D9;'>Lagebericht: Operation Normalzustand</h3>
            <p>Keine außergewöhnlichen Fluchtbewegungen in den sicheren Hafen (Gold) erkennbar.</p>
        </div>""", unsafe_allow_html=True)

    # --- KRAFT-INDIZES ---
    col1, col2 = st.columns(2)
    with col1:
        color = "neg-red" if n_net < 0 else "pos-green"
        st.markdown(f"NASDAQ KRAFT-INDEX<br><span class='{color}' style='font-size:35px;'>{n_net:,}</span>", unsafe_allow_html=True)

    with col2:
        color = "pos-green" if g_net > 0 else "neg-red"
        st.markdown(f"GOLD ABSICHERUNGS-WERT<br><span class='{color}' style='font-size:35px;'>{g_net:,}</span>", unsafe_allow_html=True)

    # --- NEU: INSTITUTIONELLE LIQUIDITÄTS-MATRIX (Anstelle Trend-Radar) ---
    st.write("---")
    st.subheader("🌐 INSTITUTIONELLE LIQUIDITÄTS-MATRIX")
    
    m1, m2, m3 = st.columns(3)
    
    with m1:
        st.write("**Dichte der Wetten (Nasdaq)**")
        n_density = ( (n_long + n_short) / n_oi ) * 100
        st.write(f"Auslastung: {n_density:.1f}%")
        st.write("Erklärung: Zeigt, wie viel Prozent des Marktes allein durch Hedgefonds kontrolliert werden.")

    with m2:
        st.write("**Gleichgewichts-Check**")
        bias = "EXTREME SHORT-SEITE" if n_short > (n_long * 3) else "NEUTRAL"
        st.write(f"Status: <span class='neg-red'>{bias}</span>" if "SHORT" in bias else f"Status: {bias}", unsafe_allow_html=True)
        st.write("Erklärung: Bei einem Verhältnis von 3:1 steigt das Risiko für einen plötzlichen Preissprung (Squeeze).")

    with m3:
        st.write("**Kapital-Engagement**")
        g_total = g_long + g_short
        st.write(f"Aktive Kontrakte: {g_total:,}")
        st.write("Erklärung: Die Gesamtmenge der Gold-Wetten der Profis. Höhere Werte bedeuten stärkere Überzeugung.")
