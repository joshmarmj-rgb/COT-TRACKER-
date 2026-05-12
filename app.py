import streamlit as st
import pandas as pd
import requests
import io
import zipfile
from PIL import Image

# --- DESIGN: ABSOLUTE MIDNIGHT ---
st.set_page_config(page_title="MakroBase_Journal", layout="wide")
st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #000103; color: #00ff41; font-family: 'JetBrains Mono', monospace; }
    .pos-green { color: #00ff41 !important; font-weight: bold; }
    .neg-red { color: #ff4136 !important; font-weight: bold; }
    .info-box { padding: 20px; border-radius: 10px; border: 1px solid #001d3d; background-color: #00040a; margin-bottom: 20px; }
    .stTextArea textarea { background-color: #000814 !important; color: #00ff41 !important; border: 1px solid #001d3d !important; }
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_data_source(url):
    try:
        r = requests.get(url, timeout=20)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# Daten-Download (2026 Daten laut Systemzeit)
nasdaq_raw = load_data_source("https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip")
gold_raw = load_data_source("https://www.cftc.gov/files/dea/history/fut_disagg_txt_2026.zip")

# Filterung
n_data = nasdaq_raw[nasdaq_raw['Market_and_Exchange_Names'].str.contains("MICRO E-MINI NASDAQ-100", na=False)].copy()
g_data = gold_raw[gold_raw['Market_and_Exchange_Names'].str.contains("GOLD - COMMODITY EXCHANGE", na=False)].copy()

if not n_data.empty and not g_data.empty:
    d = str(n_data.iloc[0]['As_of_Date_In_Form_YYMMDD'])
    clean_date = f"{d[4:6]}.{d[2:4]}.20{d[0:2]}"
    n_net = int(n_data.iloc[0]['Lev_Money_Positions_Long_All']) - int(n_data.iloc[0]['Lev_Money_Positions_Short_All'])
    g_net = int(g_data.iloc[0]['M_Money_Positions_Long_All']) - int(g_data.iloc[0]['M_Money_Positions_Short_All'])

    # --- NAVIGATION ---
    st.sidebar.title("⚓ NAVIGATOR")
    page = st.sidebar.radio("ZENTRALE", ["LIVE-DASHBOARD", "TRADE-IDEEN & JOURNAL"])

    if page == "LIVE-DASHBOARD":
        st.title("📊 ECHTZEIT-ANALYSE")
        st.write(f"Stand: {clean_date}")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<div class='info-box'><h3>NASDAQ</h3><p class='{'pos-green' if n_net > 0 else 'neg-red'}'>{n_net:,}</p></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='info-box'><h3>GOLD</h3><p class='{'pos-green' if g_net > 0 else 'neg-red'}'>{g_net:,}</p></div>", unsafe_allow_html=True)

    elif page == "TRADE-IDEEN & JOURNAL":
        st.title("💡 STRATEGIE-ZENTRALE")
        
        # 1. Automatischer Vorschlag
        st.subheader("KI-ANALYSE")
        if n_net < -150000:
            st.warning("⚠️ Starker Verkaufsdruck im Nasdaq – Squeeze-Potential prüfen.")
        else:
            st.success("✅ Marktstimmung stabil.")

        st.write("---")

        # 2. Journal-Funktion
        st.subheader("📝 DEIN TRADING-JOURNAL")
        
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            uploaded_file = st.file_uploader("Screenshot hochladen (Chart-Analyse)", type=["jpg", "png", "jpeg"])
            if uploaded_file is not None:
                image = Image.open(uploaded_file)
                st.image(image, caption="Hochgeladener Chart-Ausschnitt", use_container_width=True)
        
        with col_right:
            st.write("**Notizen zum Trade:**")
            trade_notes = st.text_area("Hier Gedanken, Einstiegspunkte und Strategie eintragen...", height=300)
            
            if st.button("Journal-Eintrag lokal bestätigen"):
                st.success("Notiz für aktuelle Sitzung gespeichert!")
                # Hier könnte man später eine Datenbank-Anbindung machen

        st.write("---")
        st.subheader("📌 CHECKLISTE FÜR KINDER ERKLÄRT")
        st.markdown("""
        *   **Schritt 1:** Ist der Nasdaq-Wert rot? (Wenn ja: Profis sind vorsichtig)
        *   **Schritt 2:** Ist der Gold-Wert grün? (Wenn ja: Profis suchen Sicherheit)
        *   **Schritt 3:** Hast du deinen Screenshot gemacht?
        *   **Schritt 4:** Schreib auf, warum du diesen Trade machst!
        """)
