import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# =================================================================
# 1. HARDCORE TERMINAL CONFIG (v71 - PROFESSIONAL FOREX MATRIX)
# =================================================================
st.set_page_config(page_title="HEDGE FUND TERMINAL v71", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;700&display=swap');
    :root { --bg: #000; --card: #050505; --brd: #111; --green: #00ff41; --red: #ff4136; --blue: #0077ff; }
    .stApp { background-color: var(--bg); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    
    /* Forex Matrix Styling */
    .fx-card { background: var(--card); border: 1px solid var(--brd); padding: 15px; border-radius: 2px; margin-bottom: 10px; }
    .label-row { display: flex; justify-content: space-between; font-family: 'JetBrains Mono'; font-size: 11px; color: #444; text-transform: uppercase; margin-bottom: 5px; }
    .main-row { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px; }
    .ticker { font-family: 'JetBrains Mono'; font-size: 18px; font-weight: 700; color: #fff; }
    .net-val { font-family: 'JetBrains Mono'; font-size: 18px; font-weight: 700; }
    
    /* Progress Bar for Long/Short Ratio */
    .ratio-bar-bg { background: var(--red); height: 4px; width: 100%; border-radius: 2px; display: flex; overflow: hidden; margin: 10px 0; }
    .ratio-bar-fill { background: var(--green); height: 100%; transition: width 0.5s; }
    
    .status-tag { font-family: 'JetBrains Mono'; font-size: 9px; padding: 2px 6px; border-radius: 2px; }
    .dept-header { font-family: 'JetBrains Mono'; font-size: 13px; color: #333; letter-spacing: 5px; border-bottom: 1px solid #111; margin-bottom: 20px; padding-bottom: 10px; }
    
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# =================================================================
# 2. DATA ENGINE
# =================================================================
@st.cache_data(ttl=3600)
def get_cftc_master(year):
    data = {}
    for k, suffix in [("fin", "fin"), ("dis", "disagg")]:
        try:
            url = f"https://www.cftc.gov/files/dea/history/fut_{suffix}_txt_{year}.zip"
            r = requests.get(url, timeout=25)
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
            df.columns = df.columns.str.strip()
            data[k] = df
        except: data[k] = pd.DataFrame()
    return data

def extract_data(df, search, mode="fin"):
    match = df[df['Market_and_Exchange_Names'].str.contains(search, na=False, case=False)]
    if match.empty: return None
    r = match.iloc[0]
    l_c = 'Lev_Money_Positions_Long_All' if mode == "fin" else 'M_Money_Positions_Long_All'
    s_c = 'Lev_Money_Positions_Short_All' if mode == "fin" else 'M_Money_Positions_Short_All'
    cl_c = 'Change_in_Lev_Money_Long_All' if mode == "fin" else 'Change_in_M_Money_Long_All'
    cs_c = 'Change_in_Lev_Money_Short_All' if mode == "fin" else 'Change_in_M_Money_Short_All'
    return {"l": int(r[l_c]), "s": int(r[s_c]), "cl": int(r[cl_c]), "cs": int(r[cs_c]), "net": int(r[l_c]) - int(r[s_c])}

# =================================================================
# 3. INTERFACE
# =================================================================
master = get_cftc_master(2026)

with st.sidebar:
    st.markdown("### 🖥️ CORE SELECT")
    selection = st.radio("Abteilung:", ["🛡️ FOREX MATRIX", "📊 NASDAQ (NQ)", "🟡 GOLD (GC)", "🛢️ CRUDE OIL (CL)"])

if not master["fin"].empty:
    
    if selection == "🛡️ FOREX MATRIX":
        st.markdown('<div class="dept-header">INSTITUTIONAL CURRENCY FLOWS</div>', unsafe_allow_html=True)
        
        # USD Score Berechnung
        basket = {"EUR": "EURO FX", "GBP": "BRITISH POUND", "JPY": "JAPANESE YEN", "AUD": "AUSTRALIAN DOLLAR", "CAD": "CANADIAN DOLLAR", "CHF": "SWISS FRANC"}
        total_net = 0
        fx_data = {}
        for ticker, search in basket.items():
            res = extract_data(master["fin"], search, "fin")
            if res:
                fx_data[ticker] = res
                total_net += res['net']
        
        usd_score = -(total_net) / 25000
        score_color = "var(--green)" if usd_score > 0 else "var(--red)"
        
        # Hero Stat
        st.markdown(f"""
            <div style="background:#080808; padding:30px; border:1px solid #111; margin-bottom:20px;">
                <div style="font-family:'JetBrains Mono'; font-size:10px; color:#444;">AGGREGATED USD POWER INDEX</div>
                <div style="font-size:54px; font-weight:700; color:{score_color};">{usd_score:.2f}</div>
            </div>
        """, unsafe_allow_html=True)

        # Die Matrix
        for ticker, data in fx_data.items():
            total_pos = data['l'] + data['s']
            long_pct = (data['l'] / total_pos * 100) if total_pos > 0 else 50
            net_color = "var(--green)" if data['net'] > 0 else "var(--red)"
            flow = data['cl'] - data['cs']
            flow_color = "var(--green)" if flow > 0 else "var(--red)"
            
            # Status Logik
            if long_pct > 70: status, s_bg = "EXTREME LONG", "rgba(0, 255, 65, 0.1)"
            elif long_pct < 30: status, s_bg = "EXTREME SHORT", "rgba(255, 65, 54, 0.1)"
            else: status, s_bg = "NEUTRAL / BALANCED", "#111"

            st.markdown(f"""
            <div class="fx-card">
                <div class="label-row">
                    <span>Ticker: {ticker}/USD</span>
                    <span style="background:{s_bg}; color:{net_color}; padding: 0 5px;">{status}</span>
                </div>
                <div class="main-row">
                    <span class="ticker">{ticker}</span>
                    <span class="net-val" style="color:{net_color};">{data['net']:,}</span>
                </div>
                <div class="ratio-bar-bg"><div class="ratio-bar-fill" style="width:{long_pct}%;"></div></div>
                <div class="label-row">
                    <span>LONG: {long_pct:.1f}%</span>
                    <span style="color:{flow_color};">WEEKLY FLOW: {flow:+,}</span>
                    <span>SHORT: {100-long_pct:.1f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # --- ANDERE ASSETS (NQ, GOLD, CL) ---
    elif selection in ["📊 NASDAQ (NQ)", "🟡 GOLD (GC)", "🛢️ CRUDE OIL (CL)"]:
        mapping = {"📊 NASDAQ (NQ)": ("NASDAQ-100", "fin"), "🟡 GOLD (GC)": ("GOLD", "dis"), "🛢️ CRUDE OIL (CL)": ("CRUDE OIL", "dis")}
        search_term, m_type = mapping[selection]
        asset = extract_data(master[m_type], search_term, m_type)
        if asset:
            a_col = "var(--green)" if asset['net'] > 0 else "var(--red)"
            st.markdown(f'<div class="dept-header">{selection}</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="fx-card">
                <div class="metrics-grid" style="display:flex; justify-content:space-between;">
                    <div><div class="label-row">NET POSITION</div><div class="ticker" style="color:{a_col};">{asset['net']:,}</div></div>
                    <div><div class="label-row">LONGS</div><div class="ticker" style="color:var(--blue);">{asset['l']:,}</div></div>
                    <div><div class="label-row">SHORTS</div><div class="ticker" style="color:var(--red);">{asset['s']:,}</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.error("CFTC DATA STREAM OFFLINE")