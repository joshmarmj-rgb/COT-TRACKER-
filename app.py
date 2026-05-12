import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# Design & Header
st.set_page_config(page_title="Nasdaq COT Insider", layout="wide")

st.markdown("""
    <style>
    .sentiment-box {
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        font-weight: bold;
        font-size: 24px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Nasdaq 100 Sentiment-Check")

@st.cache_data(ttl=3600)
def get_cot_data():
    url = "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip"
    response = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        fname = z.namelist()[0]
        with z.open(fname) as f:
            df = pd.read_csv(f, low_memory=False)
    
    df.columns = df.columns.str.strip()
    nasdaq = df[df['Market_and_Exchange_Names'].str.contains("NASDAQ-100", na=False)].copy()
    
    def format_date(d_str):
        d_str = str(d_str)
        return f"{d_str[4:6]}.{d_str[2:4]}." # Kürzeres Format für den Chart

    nasdaq['Datum'] = nasdaq['As_of_Date_In_Form_YYMMDD'].apply(format_date)
    nasdaq['Netto'] = nasdaq['Lev_Money_Positions_Long_All'] - nasdaq['Lev_Money_Positions_Short_All']
    
    # Nur die letzten 20 Wochen für bessere Übersicht
    return nasdaq.head(20).iloc[::-1]

try:
    data = get_cot_data()
    latest_netto = data.iloc[-1]['Netto']
    
    # 1. KLARE STATUS ANZEIGE
    if latest_netto < -50000:
        st.markdown('<div class="sentiment-box" style="background-color: #7f1d1d; color: white;">⚠️ EXTREMES SHORT-SENTIMENT (Hedgefonds wetten stark gegen Nasdaq)</div>', unsafe_allow_html=True)
    elif latest_netto < 0:
        st.markdown('<div class="sentiment-box" style="background-color: #374151; color: white;">📉 LEICHT BÄRISCH (Mehr Shorts als Longs)</div>', unsafe_allow_html=True)
    elif latest_netto > 50000:
        st.markdown('<div class="sentiment-box" style="background-color: #064e3b; color: white;">🚀 EXTREME GIER (Hedgefonds sind massiv Long)</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="sentiment-box" style="background-color: #1e3a8a; color: white;">⚖️ NEUTRALER BEREICH</div>', unsafe_allow_html=True)

    # 2. ÜBERSICHTLICHER CHART
    st.subheader("Werden die Wetten mehr oder weniger?")
    # Balkendiagramm zeigt die Richtung viel klarer als eine dünne Linie
    st.bar_chart(data.set_index('Datum')['Netto'])

    # 3. EINFACHE ERKLÄRUNG
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Aktueller Wert: {int(latest_netto):,}**\n\nDas bedeutet, Hedgefonds halten aktuell {abs(int(latest_netto)):,} mehr Short- als Long-Verträge.")
    with col2:
        st.help("Wenn der Balken nach unten geht, bauen Profis ihre Absicherungen (Shorts) aus. Geht er nach oben, setzen sie auf eine Rallye.")

except Exception as e:
    st.error(f"Fehler: {e}")
