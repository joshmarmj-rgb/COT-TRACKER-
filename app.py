import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# --- DESIGN: PRESTIGE BLACK ---
st.set_page_config(page_title="MakroBase", layout="wide")
st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&display=swap');

    .stApp { background-color: #000000; color: #ffffff; font-family: 'JetBrains Mono', monospace; }
    
    /* Terminal Header Style */
    .terminal-header {
        font-family: 'Orbitron', sans-serif;
        color: #ffffff;
        font-size: 45px;
        font-weight: 900;
        letter-spacing: 5px;
        border-left: 8px solid #ff4136;
        padding-left: 20px;
        margin-bottom: 40px;
    }

    .data-card { 
        padding: 20px; 
        border: 1px solid #1a1a1a; 
        background-color: #050505;
        text-align: center;
        border-radius: 4px;
    }
    
    /* Markt-Überschriften */
    .nasdaq-title { color: #00f2ff; font-family: 'Orbitron', sans-serif; font-size: 24px; letter-spacing: 2px; }
    .gold-title { color: #ffcc00; font-family: 'Orbitron', sans-serif; font-size: 24px; letter-spacing: 2px; }

    /* Werte-Farben */
    .net-green { color: #00ff41 !important; font-weight: bold; font-size: 32px; }
    .net-red { color: #ff4136 !important; font-weight: bold; font-size: 32px; }
    .buy-blue { color: #0077ff !important; font-weight: bold; font-size: 26px; }
    .sell-red { color: #ff4136 !important; font-weight: bold; font-size: 26px; }
    
    .label { color: #444444; font-size: 11px; font-weight: bold; margin-bottom: 10px; }
    hr { border: 0; border-top: 1px solid #1a1a1a; margin: 30px 0; }
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def fetch_data(url):
    try:
        r = requests.get(url, timeout=15)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# Daten-Kern
n_raw = fetch_data("https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip")
g_raw = fetch_data("https://www.cftc.gov/files/dea/history/fut_disagg_txt_2026.zip")

if not n_raw.empty and not g_raw.empty:
    ndq = n_raw[n_raw['Market_and_Exchange_Names'].str.contains("MICRO E-MINI NASDAQ-100", na=False)].iloc[0]
    gld = g_raw[g_raw['Market_and_Exchange_Names'].str.contains("GOLD - COMMODITY EXCHANGE", na=False)].iloc[0]

    n_l, n_s = int(ndq['Lev_Money_Positions_Long_All']), int(ndq['Lev_Money_Positions_Short_All'])
    g_l, g_s = int(gld['M_Money_Positions_Long_All']), int(gld['M_Money_Positions_Short_All'])
    n_net, g_net = n_l - n_s, g_l - g_s

    # --- UI RENDER ---
    st.markdown("<div class='terminal-header'>SYSTEM_CORE // 2026</div>", unsafe_allow_html=True)
    
    # NASDAQ SEKTION
    st.markdown("<p class='nasdaq-title'>NETWORK_ASSET: NASDAQ-100</p>", unsafe_allow_html=True)
    cn1, cn2, cn3 = st.columns(3)
    with cn1:
        st.markdown(f"<div class='data-card'><p class='label'>KÄUFER</p><p class='buy-blue'>{n_l:,}</p></div>", unsafe_allow_html=True)
    with cn2:
        st.markdown(f"<div class='data-card'><p class='label'>VERKÄUFER</p><p class='sell-red'>{n_s:,}</p></div>", unsafe_allow_html=True)
    with cn3:
        n_c = "net-green" if n_net > 0 else "net-red"
        st.markdown(f"<div class='data-card'><p class='label'>NETTO_POWER</p><p class='{n_c}'>{n_net:,}</p></div>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    
    # GOLD SEKTION
    st.markdown("<p class='gold-title'>RESERVE_ASSET: GOLD_BULLION</p>", unsafe_allow_html=True)
    cg1, cg2, cg3 = st.columns(3)
    with cg1:
        st.markdown(f"<div class='data-card'><p class='label'>KÄUFER</p><p class='buy-blue'>{g_l:,}</p></div>", unsafe_allow_html=True)
    with cg2:
        st.markdown(f"<div class='data-card'><p class='label'>VERKÄUFER</p><p class='sell-red'>{g_s:,}</p></div>", unsafe_allow_html=True)
    with cg3:
        g_c = "net-green" if g_net > 0 else "net-red"
        st.markdown(f"<div class='data-card'><p class='label'>NETTO_POWER</p><p class='{g_c}'>{g_net:,}</p></div>", unsafe_allow_html=True)

    # Sidebar für Logik-Wechsel
    st.sidebar.title("ACCESS_LEVEL")
    mode = st.sidebar.selectbox("SELECT_VIEW", ["DASHBOARD", "STRATEGY_LOG"])
    
    if mode == "STRATEGY_LOG":
        st.sidebar.write("---")
        if n_net < 0 and g_net > 0:
            st.sidebar.error("BIAS: RISK-OFF (Flight to Safety)")
        elif n_net > 0 and g_net < 0:
            st.sidebar.success("BIAS: RISK-ON (Asset Expansion)")
        else:
            st.sidebar.warning("BIAS: NEUTRAL (Market Compression)")
