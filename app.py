import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# --- DESIGN: SUBMARINE BLUE & CLEAN UI ---
st.set_page_config(page_title="MakroBase_Submarine", layout="wide")
st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Submarine Blau Hintergrund */
    .stApp { background-color: #001f3f; color: #00ff41; font-family: 'JetBrains Mono', monospace; }
    
    /* Boxen und Metriken */
    [data-testid="stMetricValue"] { color: #00ff41 !important; font-size: 32px; }
    [data-testid="stMetricLabel"] { color: #ffffff !important; }
    .stTable { border: 1px solid #0074D9 !important; background-color: #001f3f; }
    
    /* Status Boxen */
    .status-card { 
        padding: 20px; 
        border-radius: 10px; 
        border: 2px solid #0074D9; 
        margin-bottom: 20px;
        background-color: rgba(0, 116, 217, 0.1);
    }
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_all_data(url):
    try:
        r = requests.get(url, timeout=15)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# Daten-Download
nasdaq_df = load_all_data("https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip")
gold_df = load_all_data("https://www.cftc.gov/files/dea/history/fut_disagg_txt_2026.zip")

# Marktspezifische Filterung
n_data = nasdaq_df[nasdaq_df['Market_and_Exchange_Names'].str.contains("MICRO E-MINI NASDAQ-100", na=False)].copy()
g_data = gold_df[gold_raw['Market_and_Exchange_Names'].str.contains("GOLD - COMMODITY EXCHANGE", na=False)].copy() if 'gold_raw' not in locals() else gold_df[gold_df['Market_and_Exchange_Names'].str.contains("GOLD - COMMODITY EXCHANGE", na=False)].copy()

if n_data.empty or g_data.empty:
    st.error("SYSTEM_MELDUNG: Datenübertragung unterbrochen.")
else:
    # Sauberes Datum-Format (Tag.Monat.Jahr)
    raw_date = str(n_data.iloc[0]['As_of_Date_In_Form_YYMMDD'])
    clean_date = f"{raw_date[4:6]}.{raw_date[2:4]}.20{raw_date[0:2]}"

    # Werte
    n_net = int(n_data.iloc[0]['Lev_Money_Positions_Long_All']) - int(n_data.iloc[0]['Lev_Money_Positions_Short_All'])
    g_net = int(g_data.iloc[0]['M_Money_Positions_Long_All']) - int(g_data.iloc[0]['M_Money_Positions_Short_All'])

    st.title("🚢 MAKRO_BASE // TIEFEN-MONITOR")
    st.write(f"**PROTOKOLL-DATUM:** {clean_date} | **STATUS:** GETAUCHT")
    st.write("---")

    # --- SERIÖSE ANALYSE-TEXTE ---
    st.subheader("STRATEGISCHE LAGEBEURTEILUNG")
    
    if n_net < -150000 and g_net > 50000:
        st.markdown(f"""<div class='status-card' style='border-color: #ff4136;'>
            <h3 style='color: #ff4136;'>Achtung: Vorsicht geboten</h3>
            <p style='color: #ffffff;'>Die großen Händler ziehen ihr Geld aus modernen Firmen ab und tauschen es gegen Gold. 
            Das bedeutet: Die Profis bereiten sich auf schwierigere Zeiten vor und suchen einen sicheren Hafen.</p>
        </div>""", unsafe_allow_html=True)
    elif n_net > 0:
        st.markdown(f"""<div class='status-card' style='border-color: #2ecc40;'>
            <h3 style='color: #2ecc40;'>Lagebericht: Zuversicht</h3>
            <p style='color: #ffffff;'>Aktuell herrscht großes Vertrauen in die Wirtschaft. Die Händler investieren mutig 
            in moderne Firmen. Es gibt derzeit keine Anzeichen für eine Fluchtbewegung.</p>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class='status-card'>
            <h3 style='color: #0074D9;'>Lagebericht: Beobachtung</h3>
            <p style='color: #ffffff;'>Der Markt hält im Moment inne. Es gibt weder übermäßigen Mut noch große Angst. 
            Es ist eine Zeit des Abwartens, bis neue Signale erscheinen.</p>
        </div>""", unsafe_allow_html=True)

    # --- METRIKEN ---
    c1, c2 = st.columns(2)
    with c1:
        st.metric("NASDAQ-KRAFT (AKTIEN)", f"{n_net:,}", help="Ein Minuswert zeigt an, dass Profis eher vorsichtig sind.")
    with c2:
        st.metric("GOLD-KRAFT (SICHERHEIT)", f"{g_net:,}", help="Ein Pluswert zeigt an, dass Sicherheit gesucht wird.")

    st.write("---")
    st.subheader("HISTORISCHE AUFZEICHNUNGEN")
    
    # Historie mit sauberem Datum
    history_tab = n_data[['As_of_Date_In_Form_YYMMDD', 'Lev_Money_Positions_Long_All', 'Lev_Money_Positions_Short_All']].head(8).copy()
    history_tab.columns = ['DATUM', 'KÄUFE', 'VERKÄUFE']
    st.table(history_tab)
