import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# --- DESIGN: ULTRA MINIMALIST ---
st.set_page_config(page_title="Terminal", page_icon="📈", layout="wide")

st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700&display=swap');
    
    .stApp { background-color: #000000; color: #ffffff; font-family: 'Inter', sans-serif; }
    
    /* Dezenter, minimalistischer Header */
    .terminal-branding {
        font-size: 11px;
        letter-spacing: 3px;
        color: #333333; /* Sehr dunkles Grau, damit es nicht stört */
        text-transform: uppercase;
        border-bottom: 1px solid #111111;
        padding-bottom: 10px;
        margin-bottom: 50px;
        display: flex;
        justify-content:间;
    }

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
        transition: border 0.3s;
    }
    .data-box:hover { border: 1px solid #222222; }
    
    .val-net-pos { color: #00ff41 !important; font-weight: 700; font-size: 28px; }
    .val-net-neg { color: #ff4136 !important; font-weight: 700; font-size: 28px; }
    .val-buy { color: #0077ff !important; font-weight: 400; font-size: 24px; }
    .val-sell { color: #ff4136 !important; font-weight: 400; font-size: 24px; }
    
    .box-label { color: #333333; font-size: 10px; font-weight: bold; margin-bottom: 5px; text-transform: uppercase; }
    hr { border: 0; border-top: 1px solid #111111; margin: 40px 0; }
    
    /* Verstecke Streamlit Standard-Elemente für den Pro-Look */
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

# Daten
n_raw = fetch_data("https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip")
dis_raw = fetch_data("https://www.cftc.gov/files/dea/history/fut_disagg_txt_2026.zip")

def render_asset(title, color_class, long, short):
    net = long - short
    st.markdown(f"<div class='asset-label'>Market Source: CFTC</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='instrument-name {color_class}'>{title}</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"<div class='data-box'><p class='box-label'>Long</p><p class='val-buy'>{long:,}</p></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='data-box'><p class='box-label'>Short</p><p class='val-sell'>{short:,}</p></div>", unsafe_allow_html=True)
    with c3:
        style = "val-net-pos" if net > 0 else "val-net-neg"
        st.markdown(f"<div class='data-box'><p class='box-label'>Net</p><p class='{style}'>{net:,}</p></div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

# --- UI RENDER ---
# Der Header ist jetzt nur noch eine feine Linie mit dezentem Text
st.markdown("<div class='terminal-branding'><span>MT // Numbers 2026</span><span>v42.0</span></div>", unsafe_allow_html=True)

if not n_raw.empty and not dis_raw.empty:
    try:
        ndq = n_raw[n_raw['Market_and_Exchange_Names'].str.contains("NASDAQ-100", na=False)].iloc[0]
        gld = dis_raw[dis_raw['Market_and_Exchange_Names'].str.contains("GOLD", na=False)].iloc[0]
        oil = dis_raw[dis_raw['Market_and_Exchange_Names'].str.contains("CRUDE OIL, LIGHT SWEET", na=False)].iloc[0]

        render_asset("NASDAQ 100", "color-nasdaq", int(ndq['Lev_Money_Positions_Long_All']), int(ndq['Lev_Money_Positions_Short_All']))
        render_asset("GOLD BULLION", "color-gold", int(gld['M_Money_Positions_Long_All']), int(gld['M_Money_Positions_Short_All']))
        render_asset("CRUDE OIL WTI", "color-oil", int(oil['M_Money_Positions_Long_All']), int(oil['M_Money_Positions_Short_All']))
    except:
        st.error("Sync Error.")
