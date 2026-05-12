import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# --- TERMINAL OPTIK ---
st.set_page_config(page_title="MakroBase_CORE", layout="wide")
st.markdown("""<style>
    * { background-color: #000 !important; color: #00ff41 !important; font-family: 'JetBrains Mono', monospace !important; }
    .stTable, table { border: 1px solid #00ff41 !important; }
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_cftc_data(url):
    try:
        r = requests.get(url, timeout=10)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# 1. Finanz-Daten (Nasdaq)
fin_df = load_cftc_data("https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip")
# 2. Rohstoff-Daten (Gold)
com_df = load_cftc_data("https://www.cftc.gov/files/dea/history/fut_disagg_txt_2026.zip")

# --- FILTERUNG ---
nasdaq = fin_df[fin_df['Market_and_Exchange_Names'].str.contains("MICRO E-MINI NASDAQ-100", na=False)].copy()
gold = com_df[com_df['Market_and_Exchange_Names'].str.contains("GOLD - COMMODITY EXCHANGE", na=False)].copy()

st.sidebar.title("MakroBase // NAV")
auswahl = st.sidebar.radio("MODUS", ["KORRELATION", "NASDAQ", "GOLD"])

# SICHERHEITS-CHECK gegen Fehler aus Bildschirmfoto_12-5-2026_235721...
if nasdaq.empty or gold.empty:
    st.error("DATEN_LADE_FEHLER: Verbindung zur CFTC unterbrochen oder Filter ungültig.")
else:
    # NASDAQ DATEN (TFF Report Spalten)
    n_l = int(nasdaq.iloc[0]['Lev_Money_Positions_Long_All'])
    n_s = int(nasdaq.iloc[0]['Lev_Money_Positions_Short_All'])
    n_net = n_l - n_s
    
    # GOLD DATEN (Disaggregated Report Spalten - Korrektur für KeyError)
    # Die Spalten heißen hier 'M_Money_Positions_Long_All' (abgekürzt)
    g_l = int(gold.iloc[0]['M_Money_Positions_Long_All'])
    g_s = int(gold.iloc[0]['M_Money_Positions_Short_All'])
    g_net = g_l - g_s

    if auswahl == "KORRELATION":
        st.header("STRATEGISCHE_ANALYSE")
        st.write(f"STICHTAG: {nasdaq.iloc[0]['As_of_Date_In_Form_YYMMDD']}")
        st.write("---")
        c1, c2 = st.columns(2)
        c1.metric("NASDAQ_NETTO", f"{n_net:,}")
        c2.metric("GOLD_NETTO", f"{g_net:,}")
        
        st.write("---")
        if n_net < -150000 and g_net > 50000:
            st.error("!!! SIGNAL: RISK-OFF (FLUCHT IN GOLD / TECH-ABVERKAUF) !!!")
        elif n_net > 0 and g_net < 0:
            st.success("!!! SIGNAL: RISK-ON (TECH-RALLYE / GOLD-ABVERKAUF) !!!")
        else:
            st.warning("STATUS: MARKT-NEUTRAL (KEINE EXTREME KORRELATION)")

    elif auswahl == "NASDAQ":
        st.header("NASDAQ_NODE_DETAIL")
        st.metric("NETTO_POWER", f"{n_net:,}")
        st.table(nasdaq[['As_of_Date_In_Form_YYMMDD', 'Lev_Money_Positions_Long_All', 'Lev_Money_Positions_Short_All']].head(10))

    elif auswahl == "GOLD":
        st.header("GOLD_NODE_DETAIL")
        st.metric("NETTO_POWER", f"{g_net:,}")
        # Tabellenspalten für Gold angepasst
        st.table(gold[['As_of_Date_In_Form_YYMMDD', 'M_Money_Positions_Long_All', 'M_Money_Positions_Short_All']].head(10))
