import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# --- TERMINAL OPTIK ---
st.set_page_config(page_title="MakroBase_PRO", layout="wide")
st.markdown("""<style>
    * { background-color: #000 !important; color: #00ff41 !important; font-family: 'JetBrains Mono', monospace !important; }
    .stTable, table { border: 1px solid #00ff41 !important; }
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_cftc(url):
    try:
        r = requests.get(url)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# Lade beide Quellen
fin_df = load_cftc("https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip") # Nasdaq
com_df = load_cftc("https://www.cftc.gov/files/dea/history/fut_disagg_txt_2026.zip") # Gold

# --- DATEN-EXTRAKTION ---
nasdaq = fin_df[fin_df['Market_and_Exchange_Names'].str.contains("MICRO E-MINI NASDAQ-100", na=False)].copy()
gold = com_df[com_df['Market_and_Exchange_Names'].str.contains("GOLD - COMMODITY EXCHANGE", na=False)].copy()

st.sidebar.title("MakroBase // NAV")
auswahl = st.sidebar.radio("MODUS", ["KORRELATION", "NASDAQ", "GOLD"])

if nasdaq.empty or gold.empty:
    st.error("FEHLER: DATENQUELLE NICHT ERREICHBAR.")
else:
    # Nasdaq Werte (Leveraged Funds)
    n_l, n_s = int(nasdaq.iloc[0]['Lev_Money_Positions_Long_All']), int(nasdaq.iloc[0]['Lev_Money_Positions_Short_All'])
    n_net = n_l - n_s
    
    # Gold Werte (Managed Money)
    g_l, g_s = int(gold.iloc[0]['Managed_Money_Positions_Long_All']), int(gold.iloc[0]['Managed_Money_Positions_Short_All'])
    g_net = g_l - g_s

    if auswahl == "KORRELATION":
        st.header("STRATEGISCHE_ANALYSE")
        st.write(f"NASDAQ_NETTO: {n_net:,} | GOLD_NETTO: {g_net:,}")
        if n_net < -150000 and g_net > 50000:
            st.error("!!! SIGNAL: RISK-OFF (KRISENMODUS) !!!")
        else:
            st.success("STATUS: NORMALBETRIEB")
            
    elif auswahl == "GOLD":
        st.header("GOLD_ROHDATEN")
        st.metric("NETTO_GOLD", f"{g_net:,}")
        st.table(gold[['As_of_Date_In_Form_YYMMDD', 'Managed_Money_Positions_Long_All', 'Managed_Money_Positions_Short_All']].head(10))
