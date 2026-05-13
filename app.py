import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import datetime

# =================================================================
# 1. CORE CONFIGURATION & HANDY-GRID STYLING
# =================================================================
st.set_page_config(
    page_title="INSTITUTIONAL MACRO v56", 
    page_icon="📡", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;700&display=swap');
    
    :root {
        --bg-color: #000000;
        --card-bg: #050505;
        --border-color: #1a1a1a;
        --text-main: #e0e0e0;
    }

    .stApp { background-color: var(--bg-color); color: var(--text-main); font-family: 'Inter', sans-serif; }
    
    .data-card { 
        background-color: var(--card-bg); 
        border: 1px solid var(--border-color); 
        padding: 15px; 
        border-radius: 4px;
        margin-bottom: 10px;
    }

    .instrument-title { 
        font-size: 18px; 
        font-weight: 700; 
        margin-bottom: 12px; 
        color: #fff;
    }

    .metrics-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 8px;
    }

    .metric-box { display: flex; flex-direction: column; }
    .label { color: #555; font-size: 9px; text-transform: uppercase; font-weight: 700; }
    
    .number { 
        font-size: clamp(14px, 4.5vw, 20px); 
        font-family: 'JetBrains Mono', monospace; 
        font-weight: 700;
        white-space: nowrap;
    }

    .power-container { background: #111; height: 10px; border-radius: 5px; margin: 10px 0; border: 1px solid #222; }
    .power-bar { height: 100%; transition: width 1s ease; }

    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# =================================================================
# 2. DATA ENGINE
# =================================================================
@st.cache_data(ttl=3600)
def load_cftc_data(report_type="fin"):
    urls = {
        "fin": "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip",
        "dis": "https://www.cftc.gov/files/dea/history/fut_disagg_txt_2026.zip"
    }
    try:
        r = requests.get(urls[report_type], timeout=25)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

def get_row_safe(df, search_term):
    if df.empty: return None
    match = df[df['Market_and_Exchange_Names'].str.contains(search_term, na=False, case=False)]
    return match.iloc[0] if not match.empty else None

def render_instrument_card(name, long, short, color="#fff"):
    net = long - short
    n_color = "#00ff41" if net > 0 else "#ff4136"
    st.markdown(f"""
    <div class="data-card">
        <div class="instrument-title" style="border-left: 3px solid {color}; padding-left: 10px;">{name}</div>
        <div class="metrics-grid">
            <div class="metric-box"><span class="label">Long</span><span class="number" style="color: #0077ff;">{long:,}</span></div>
            <div class="metric-box"><span class="label">Short</span><span class="number" style="color: #ff4136;">{short:,}</span></div>
            <div class="metric-box"><span class="label">Net</span><span class="number" style="color: {n_color};">{net:,}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =================================================================
# 3. MAIN EXECUTION (FIXED INDENTATION)
# =================================================================
fin_df = load_cftc_data("fin")
dis_df = load_cftc_data("dis")

if not fin_df.empty and not dis_df.empty:
    nq_row = get_row_safe(fin_df, "NASDAQ-100")
    gc_row = get_row_safe(dis_df, "GOLD")
    cl_row = get_row_safe(dis_df, "CRUDE OIL")

    st.markdown('<p style="color: #444; font-size: 10px; letter-spacing: 2px;">MARKET_ASSETS</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if nq_row is not None:
            render_instrument_card("Nasdaq 100", int(nq_row['Lev_Money_Positions_Long_All']), int(nq_row['Lev_Money_Positions_Short_All']), "#00d4ff")
    with col2:
        if gc_row is not None:
            render_instrument_card("Gold", int(gc_row['M_Money_Positions_Long_All']), int(gc_row['M_Money_Positions_Short_All']), "#ffcc00")
    with col3:
        if cl_row is not None:
            render_instrument_card("WTI Oil", int(cl_row['M_Money_Positions_Long_All']), int(cl_row['M_Money_Positions_Short_All']), "#bf55ff")

    # Forex & USD Power
    pairs = {"EUR": "EURO FX", "GBP": "BRITISH POUND", "JPY": "JAPANESE YEN", "AUD": "AUSTRALIAN DOLLAR", "CAD": "CANADIAN DOLLAR"}
    total_net = 0
    fx_results = {}
    for code, search in pairs.items():
        row = get_row_safe(fin_df, search)
        if row is not None:
            net = int(row['Lev_Money_Positions_Long_All']) - int(row['Lev_Money_Positions_Short_All'])
            fx_results[code] = net
            total_net += net
    
    usd_score = -(total_net) / 25000
    p_color = "#00ff41" if usd_score > 0 else "#ff4136"
    p_width = min(max((usd_score + 50) / 100, 0), 1) * 100

    st.markdown('<br><p style="color: #444; font-size: 10px; letter-spacing: 2px;">USD_POWER_INDEX</p>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background: #050505; border: 1px solid #111; padding: 20px; border-radius: 4px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 14px; font-weight: bold;">Institutional Bias</span>
            <span style="color: {p_color}; font-family: monospace; font-size: 20px; font-weight: bold;">{usd_score:.2f}</span>
        </div>
        <div class="power-container"><div class="power-bar" style="width: {p_width}%; background: {p_color};"></div></div>
    </div>
    """, unsafe_allow_html=True)

    # Forex Grid
    f_cols = st.columns(5)
    for i, (code, val) in enumerate(fx_results.items()):
        with f_cols[i]:
            v_color = "#00ff41" if val > 0 else "#ff4136"
            st.markdown(f"""
            <div style="background: #050505; border: 1px solid #111; padding: 10px; text-align: center;">
                <div class="label">{code}</div>
                <div style="color: {v_color}; font-weight: bold; font-family: monospace;">{val//1000}k</div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.error("Warte auf Datenstream...")
