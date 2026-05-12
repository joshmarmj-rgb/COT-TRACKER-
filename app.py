import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# --- DESIGN: HIGH CONTRAST MINIMALISM ---
st.set_page_config(page_title="Makro Terminal", layout="wide")
st.markdown("""<style>
    /* Klare, hochlesbare Schriftart */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');

    .stApp { background-color: #000000; color: #ffffff; font-family: 'Inter', sans-serif; }
    
    .main-title {
        font-size: 32px;
        font-weight: 900;
        letter-spacing: -1px;
        margin-bottom: 40px;
        color: #ffffff;
    }

    .asset-label {
        font-size: 14px;
        color: #666666;
        text-transform: uppercase;
        margin-bottom: 5px;
    }

    .instrument-name {
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 20px;
    }

    /* Nasdaq-Farbe */
    .color-nasdaq { color: #00d4ff; }
    /* Gold-Farbe */
    .color-gold { color: #ffcc00; }

    .data-box { 
        padding: 25px; 
        border: 1px solid #222222; 
        background-color: #080808;
        text-align: center;
        border-radius: 8px;
    }
    
    .val-net-pos { color: #00ff41 !important; font-weight: 700; font-size: 34px; }
    .val-net-neg { color: #ff4136 !important; font-weight: 700; font-size: 34px; }
    .val-buy { color: #0077ff !important; font-weight: 700; font-size: 28px; }
    .val-sell { color: #ff4136 !important; font-weight: 700; font-size: 28px; }
    
    .box-label { color: #555555; font-size: 12px; font-weight: bold; margin-bottom: 8px; text-transform: uppercase; }
    hr { border: 0; border-top: 1px solid #222222; margin: 40px 0; }
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

# Daten
n_raw = fetch_data("https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip")
g_raw = fetch_data("https://www.cftc.gov/files/dea/history/fut_disagg_txt_2026.zip")

if not n_raw.empty and not g_raw.empty:
    ndq = n_raw[n_raw['Market_and_Exchange_Names'].str.contains("MICRO E-MINI NASDAQ-100", na=False)].iloc[0]
    gld = g_raw[g_raw['Market_and_Exchange_Names'].str.contains("GOLD - COMMODITY EXCHANGE", na=False)].iloc[0]

    n_l, n_s = int(ndq['Lev_Money_Positions_Long_All']), int(ndq['Lev_Money_Positions_Short_All'])
    g_l, g_s = int(gld['M_Money_Positions_Long_All']), int(gld['M_Money_Positions_Short_All'])
    n_net, g_net = n_l - n_s, g_l - g_s

    # --- UI ---
    st.markdown("<div class='main-title'>Makro Terminal Numbers</div>", unsafe_allow_html=True)
    
    # ASSET: NASDAQ
    st.markdown("<div class='asset-label'>Asset</div>", unsafe_allow_html=True)
    st.markdown("<div class='instrument-name color-nasdaq'>Nasdaq 100</div>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='data-box'><p class='box-label'>Käufer</p><p class='val-buy'>{n_l:,}</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='data-box'><p class='box-label'>Verkäufer</p><p class='val-sell'>{n_s:,}</p></div>", unsafe_allow_html=True)
    with c3:
        n_style = "val-net-pos" if n_net > 0 else "val-net-neg"
        st.markdown(f"<div class='data-box'><p class='box-label'>Netto</p><p class='{n_style}'>{n_net:,}</p></div>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    
    # ASSET: GOLD
    st.markdown("<div class='asset-label'>Asset</div>", unsafe_allow_html=True)
    st.markdown("<div class='instrument-name color-gold'>Gold</div>", unsafe_allow_html=True)
    
    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown(f"<div class='data-box'><p class='box-label'>Käufer</p><p class='val-buy'>{g_l:,}</p></div>", unsafe_allow_html=True)
    with g2:
        st.markdown(f"<div class='data-box'><p class='box-label'>Verkäufer</p><p class='val-sell'>{g_s:,}</p></div>", unsafe_allow_html=True)
    with g3:
        g_style = "val-net-pos" if g_net > 0 else "val-net-neg"
        st.markdown(f"<div class='data-box'><p class='box-label'>Netto</p><p class='{g_style}'>{g_net:,}</p></div>", unsafe_allow_html=True)
