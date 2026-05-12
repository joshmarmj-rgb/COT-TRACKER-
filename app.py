import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# --- DESIGN: ABSOLUTE BLACK ---
st.set_page_config(page_title="MakroBase", layout="wide")
st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #000000; color: #ffffff; font-family: 'JetBrains Mono', monospace; }
    
    .data-card { 
        padding: 20px; 
        border: 1px solid #111111; 
        background-color: #050505;
        text-align: center;
        border-radius: 5px;
    }
    
    .net-green { color: #00ff41 !important; font-weight: bold; font-size: 38px; }
    .net-red { color: #ff4136 !important; font-weight: bold; font-size: 38px; }
    .buy-blue { color: #0077ff !important; font-weight: bold; font-size: 28px; }
    .sell-red { color: #ff4136 !important; font-weight: bold; font-size: 28px; }
    .label { color: #555555; font-size: 12px; letter-spacing: 1px; }
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

# Daten laden
n_raw = fetch_data("https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip")
g_raw = fetch_data("https://www.cftc.gov/files/dea/history/fut_disagg_txt_2026.zip")

# Filter
ndq = n_raw[n_raw['Market_and_Exchange_Names'].str.contains("MICRO E-MINI NASDAQ-100", na=False)].iloc[0]
gld = g_raw[g_raw['Market_and_Exchange_Names'].str.contains("GOLD - COMMODITY EXCHANGE", na=False)].iloc[0]

# Werte extrahieren
n_l, n_s = int(ndq['Lev_Money_Positions_Long_All']), int(ndq['Lev_Money_Positions_Short_All'])
g_l, g_s = int(gld['M_Money_Positions_Long_All']), int(gld['M_Money_Positions_Short_All'])
n_net, g_net = n_l - n_s, g_l - g_s

# --- UI ---
page = st.sidebar.radio("NAV", ["DASHBOARD", "LOGIK"])

if page == "DASHBOARD":
    st.title("TERMINAL // 2026")
    
    # NASDAQ SEKTION
    st.markdown("### NASDAQ-100")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='data-card'><p class='label'>KÄUFER</p><p class='buy-blue'>{n_l:,}</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='data-card'><p class='label'>VERKÄUFER</p><p class='sell-red'>{n_s:,}</p></div>", unsafe_allow_html=True)
    with c3:
        n_c = "net-green" if n_net > 0 else "net-red"
        st.markdown(f<div class='data-card'><p class='label'>NETTO</p><p class='{n_c}'>{n_net:,}</p></div>", unsafe_allow_html=True)

    st.write("---")
    
    # GOLD SEKTION
    st.markdown("### GOLD")
    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown(f"<div class='data-card'><p class='label'>KÄUFER</p><p class='buy-blue'>{g_l:,}</p></div>", unsafe_allow_html=True)
    with g2:
        st.markdown(f"<div class='data-card'><p class='label'>VERKÄUFER</p><p class='sell-red'>{g_s:,}</p></div>", unsafe_allow_html=True)
    with g3:
        g_c = "net-green" if g_net > 0 else "net-red"
        st.markdown(f"<div class='data-card'><p class='label'>NETTO</p><p class='{g_c}'>{g_net:,}</p></div>", unsafe_allow_html=True)

elif page == "LOGIK":
    st.title("IDEEN")
    if n_net < -150000:
        st.error(f"NASDAQ OVERSELL: {n_net:,} | FOKUS: SHORT-SQUEEZE")
    if g_net > 50000:
        st.warning(f"GOLD HEDGE: {g_net:,} | FOKUS: RISK-OFF")
    if n_net > 0 and g_net < 0:
        st.success("BULLISH BIAS: NASDAQ LONG / GOLD SHORT")
