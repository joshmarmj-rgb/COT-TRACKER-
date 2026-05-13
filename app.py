import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# =================================================================
# v72.1 - MOBILE FIRST (KEIN MENÜ NOTWENDIG)
# =================================================================
st.set_page_config(page_title="TERMINAL v72.1", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    :root { --bg: #000; --card: #080808; --brd: #111; --green: #00ff41; --red: #ff4136; --blue: #0077ff; }
    .stApp { background-color: var(--bg); color: #e0e0e0; }
    
    /* Karten für Handy optimiert */
    .data-box { 
        background: var(--card); 
        border: 1px solid var(--brd); 
        padding: 15px; 
        border-radius: 4px; 
        margin-bottom: 10px;
    }
    .header-style { 
        font-family: 'JetBrains Mono'; 
        font-size: 14px; 
        color: #555; 
        border-bottom: 1px solid #222; 
        margin-top: 20px; 
        padding-bottom: 5px;
        text-transform: uppercase;
    }
    .val-large { font-family: 'JetBrains Mono'; font-size: 24px; font-weight: 700; }
    .label-small { font-size: 10px; color: #444; text-transform: uppercase; }
    
    /* Verstecke Streamlit Standard-Elemente */
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_data(year):
    data = {}
    for k, s in [("fin", "fin"), ("dis", "disagg")]:
        try:
            url = f"https://www.cftc.gov/files/dea/history/fut_{s}_txt_{year}.zip"
            r = requests.get(url, timeout=20)
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
            df.columns = df.columns.str.strip()
            data[k] = df
        except: data[k] = pd.DataFrame()
    return data

def quick_extract(df, name, mode="fin"):
    m = df[df['Market_and_Exchange_Names'].str.contains(name, na=False, case=False)]
    if m.empty: return None
    r = m.iloc[0]
    l = int(r['Lev_Money_Positions_Long_All' if mode=="fin" else 'M_Money_Positions_Long_All'])
    s = int(r['Lev_Money_Positions_Short_All' if mode=="fin" else 'M_Money_Positions_Short_All'])
    return {"l": l, "s": s, "net": l - s}

# --- ENGINE ---
master = get_data(2026)

if not master["fin"].empty:
    # 1. USD SCORE
    st.markdown('<div class="header-style">🛡️ USD Power Index</div>', unsafe_allow_html=True)
    fx = {"EUR": "EURO FX", "GBP": "BRITISH POUND", "JPY": "JAPANESE YEN", "AUD": "AUSTRALIAN DOLLAR", "CAD": "CANADIAN DOLLAR", "CHF": "SWISS FRANC"}
    nets = []
    for t, n in fx.items():
        res = quick_extract(master["fin"], n, "fin")
        if res: nets.append(res['net'])
    
    score = -(sum(nets)) / 25000
    c = "var(--green)" if score > 0 else "var(--red)"
    st.markdown(f'<div class="data-box" style="text-align:center;"><div class="label-small">Aggregate Score</div><div class="val-large" style="color:{c}; font-size:40px;">{score:.2f}</div></div>', unsafe_allow_html=True)

    # 2. MARKETS
    st.markdown('<div class="header-style">📊 Market Net Positions</div>', unsafe_allow_html=True)
    m_list = [("NASDAQ-100", "fin", "NASDAQ"), ("GOLD", "dis", "GOLD"), ("CRUDE OIL", "dis", "CRUDE OIL")]
    
    for search, mode, label in m_list:
        d = quick_extract(master[mode], search, mode)
        if d:
            color = "var(--green)" if d['net'] > 0 else "var(--red)"
            st.markdown(f"""
            <div class="data-box">
                <div class="label-small">{label}</div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span class="val-large" style="color:{color};">{d['net']:,}</span>
                    <span style="font-size:10px; color:#333;">L: {d['l']:,} | S: {d['s']:,}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.error("DATA OFFLINE")
