import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# --- DESIGN: ABSOLUTE DATA FOCUS ---
st.set_page_config(page_title="Terminal", page_icon="📈", layout="wide")

st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700&display=swap');
    
    .stApp { background-color: #000000; color: #ffffff; font-family: 'Inter', sans-serif; }
    
    /* Padding oben reduzieren, da der Titel weg ist */
    .block-container { padding-top: 2rem !important; }

    .asset-label { font-size: 10px; color: #444444; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 2px; }
    .instrument-name { font-size: 20px; font-weight: 400; margin-bottom: 25px; letter-spacing: -0.5px; }
    
    .color-nasdaq { color: #00d4ff; }
    .color-gold { color: #ffcc00; }
    .color-oil { color: #bf55ff; }
    
    .data-box { 
        padding: 20px; 
        border: 1px solid #111111; 
        background-color: #030303; 
        border-radius: 4px;
    }
    
    .val-net-pos { color: #00ff41 !important; font-weight: 700; font-size: 28px; }
    .val-net-neg { color: #ff4136 !important; font-weight: 700; font-size: 28px; }
    .val-buy { color: #0077ff !important; font-weight: 400; font-size: 24px; }
    .val-sell { color: #ff4136 !important; font-weight: 400; font-size: 24px; }
    
    .box-label { color: #333333; font-size: 10px; font-weight: bold; margin-bottom: 5px; text-transform: uppercase; }
    hr { border: 0; border-top: 1px solid #111111; margin: 40px 0; }
    
    /* UI-Elemente verstecken */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
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

# Daten-Import
n_raw = fetch_data("https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip")
dis_raw = fetch_data("https://www.cftc.gov/files/dea/history/fut_disagg_txt_2026.zip")

def render_asset(title, color_class, long, short):
    net = long - short
    st.markdown(f"<div class='asset-label'>Asset</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='instrument-name {color_class}'>{title}</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"<div class='data-box'><p class='box-label'>Käufer</p><p class='val-buy'>{long:,}</p></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='data-box'><p class='box-label'>Verkäufer</p><p class='val-sell'>{short:,}</p></div>", unsafe_allow_html=True)
    with c3:
        style = "val-net-pos" if net > 0 else "val-net-neg"
        st.markdown(f"<div class='data-box'><p class='box-label'>Netto</p><p class='{style}'>{net:,}</p></div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

# --- UI RENDER ---
if not n_raw.empty and not dis_raw.empty:
    try:
        # Suche Assets
        ndq = n_raw[n_raw['Market_and_Exchange_Names'].str.contains("NASDAQ-100", na=False)].iloc[0]
        gld = dis_raw[dis_raw['Market_and_Exchange_Names'].str.contains("GOLD", na=False)].iloc[0]
        oil = dis_raw[dis_raw['Market_and_Exchange_Names'].str.contains("CRUDE OIL, LIGHT SWEET", na=False)].iloc[0]

        # Anzeige (Reihenfolge unverändert)
        render_asset("Nasdaq 100", "color-nasdaq", int(ndq['Lev_Money_Positions_Long_All']), int(ndq['Lev_Money_Positions_Short_All']))
        render_asset("Gold", "color-gold", int(gld['M_Money_Positions_Long_All']), int(gld['M_Money_Positions_Short_All']))
        render_asset("Crude Oil WTI", "color-oil", int(oil['M_Money_Positions_Long_All']), int(oil['M_Money_Positions_Short_All']))
    except:
        st.error("Datenfehler.")
