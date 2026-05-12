import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# --- TERMINAL KONFIGURATION ---
st.set_page_config(page_title="MakroBase_INTELLIGENCE", layout="wide")
st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500&display=swap');
    * { background-color: #000 !important; color: #00ff41 !important; font-family: 'JetBrains Mono', monospace !important; }
    .stTable, table { border: 1px solid #00ff41 !important; }
    .stSelectbox div[data-baseweb="select"] { border: 1px solid #00ff41 !important; }
</style>""", unsafe_allow_html=True)

# --- CORE ENGINE (Lädt Nasdaq und Gold) ---
@st.cache_data(ttl=600)
def get_market_data():
    url = "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip"
    r = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
    df.columns = df.columns.str.strip()
    return df

raw_df = get_market_data()

def process_market(market_name, search_term):
    data = raw_df[raw_df['Market_and_Exchange_Names'].str.contains(search_term, na=False)].copy()
    data['Date'] = pd.to_datetime(data['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
    data = data.sort_values('Date', ascending=False)
    return data

# Daten-Extraktion
nasdaq_data = process_market("Nasdaq", "MICRO E-MINI NASDAQ-100")
gold_data = process_market("Gold", "GOLD - COMMODITY EXCHANGE") # Klassisches Gold (COMEX)

# --- SEITENMENÜ FÜR NAVIGATION ---
st.sidebar.title("MakroBase // NAVIGATION")
auswahl = st.sidebar.radio("MARKT_AUSWAHL", ["KORRELATION_CHECK", "NASDAQ_DETAILS", "GOLD_DETAILS"])

if auswahl == "KORRELATION_CHECK":
    st.header("STRATEGISCHER_KORRELATIONS_ABGLEICH")
    
    # Aktuelle Netto-Werte holen
    n_long = int(nasdaq_data.iloc[0]['Lev_Money_Positions_Long_All'])
    n_short = int(nasdaq_data.iloc[0]['Lev_Money_Positions_Short_All'])
    n_netto = n_long - n_short
    
    # Bei Gold (Legacy-Report) nutzen wir Non-Commercials
    g_long = int(gold_data.iloc[0]['NonComm_Positions_Long_All'])
    g_short = int(gold_data.iloc[0]['NonComm_Positions_Short_All'])
    g_netto = g_long - g_short
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("NASDAQ_BIAS")
        st.write(f"Netto: {n_netto:,}")
        n_status = "BÄRISCH" if n_netto < 0 else "BULLISCH"
        st.write(f"Status: {n_status}")
        
    with col2:
        st.subheader("GOLD_BIAS")
        st.write(f"Netto: {g_netto:,}")
        g_status = "BÄRISCH" if g_netto < 0 else "BULLISCH"
        st.write(f"Status: {g_status}")

    st.write("---")
    st.header("INTELLIGENZ_AUSWERTUNG:")
    
    if n_netto < -100000 and g_netto > 100000:
        st.error("!!! FLUCHT IN SICHERHEIT (RISK-OFF) !!!")
        st.write("LOGIK: Hedgefonds wetten gegen Tech-Aktien und kaufen Gold. Dies deutet auf eine bevorstehende Markt-Korrektur oder globale Unsicherheit hin.")
    elif n_netto > 50000 and g_netto < 0:
        st.success("!!! RISIKO-MODUS AKTIV (RISK-ON) !!!")
        st.write("LOGIK: Aktien werden gekauft, Gold wird verkauft. Volles Vertrauen in die Wirtschaft.")
    else:
        st.warning("MARKT-NEUTRALITÄT")
        st.write("LOGIK: Keine eindeutige Fluchtbewegung erkennbar.")

elif auswahl == "NASDAQ_DETAILS":
    st.header("NASDAQ_NODE_DATA")
    # (Hier kommt dein bekannter Nasdaq-Code rein...)
    st.write("Aktuelle Netto-Power:", n_netto)

elif auswahl == "GOLD_DETAILS":
    st.header("GOLD_NODE_DATA")
    st.write(f"Gold Netto-Position: {g_netto:,}")
    st.table(gold_data[['Date', 'NonComm_Positions_Long_All', 'NonComm_Positions_Short_All']].head(10))
