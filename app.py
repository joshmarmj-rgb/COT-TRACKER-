import streamlit as st
import pandas as pd
import requests
import io
import zipfile
from datetime import datetime

# Design-Einstellungen
st.set_page_config(page_title="Nasdaq COT Pro-Tracker", layout="wide")

# CSS für ein besseres Design
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Nasdaq 100 COT Dashboard (TFF Report)")

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
    
    # Datum formatieren (aus 260505 wird 05.05.2026)
    def format_date(d_str):
        d_str = str(d_str)
        return f"{d_str[4:6]}.{d_str[2:4]}.20{d_str[0:2]}"

    nasdaq['Datum_Clean'] = nasdaq['As_of_Date_In_Form_YYMMDD'].apply(format_date)
    
    # Mapping
    cols = {
        'Lev_Money_Positions_Long_All': 'Hedgefonds_Long',
        'Lev_Money_Positions_Short_All': 'Hedgefonds_Short',
        'Asset_Mgr_Positions_Long_All': 'Insti_Long',
        'Asset_Mgr_Positions_Short_All': 'Insti_Short'
    }
    nasdaq = nasdaq.rename(columns=cols)
    nasdaq['Netto_Hedgefonds'] = nasdaq['Hedgefonds_Long'] - nasdaq['Hedgefonds_Short']
    
    return nasdaq

try:
    data = get_cot_data()
    latest = data.iloc[0]
    
    # Obere Metriken
    c1, c2, c3 = st.columns(3)
    c1.metric("Letzter Bericht vom", latest['Datum_Clean'])
    c2.metric("Netto-Position Hedgefonds", f"{int(latest['Netto_Hedgefonds']):,}")
    
    # Veränderung berechnen
    if len(data) > 1:
        change = latest['Netto_Hedgefonds'] - data.iloc[1]['Netto_Hedgefonds']
        c3.metric("Wöchentliche Änderung", f"{int(change):,}", delta=int(change))

    # Chart Bereich
    st.subheader("📈 Sentiment-Verlauf (Leveraged Money)")
    st.line_chart(data.set_index('Datum_Clean')['Netto_Hedgefonds'])

    # --- BESCHREIBUNGS SEKTION ---
    with st.expander("📖 Was bedeuten diese Zahlen? (Erklärung)"):
        st.write("""
        ### Wer sind die Akteure?
        1. **Leveraged Money (Hedgefonds):** Das ist das 'schnelle Geld'. Diese Akteure spekulieren auf Trends. Wenn sie stark Long sind, ist die Stimmung bullisch. Sind sie extrem Short (wie aktuell), kann das auf einen Wendepunkt hindeuten.
        2. **Asset Manager (Instis):** Pensionskassen und Versicherungen. Sie halten meist langfristige Long-Positionen zur Absicherung.
        
        ### Was bedeutet 'Netto-Position'?
        Die Zahl ergibt sich aus **Long-Kontrakten minus Short-Kontrakten**. 
        *   **Positive Zahl:** Die Gruppe wettet mehrheitlich auf steigende Kurse.
        *   **Negative Zahl:** Die Gruppe wettet mehrheitlich auf fallende Kurse.
        
        ### Warum ist das wichtig?
        Der COT-Bericht hilft dir zu sehen, ob die 'Profis' gerade aussteigen oder massiv gegen den aktuellen Trend wetten. Oft dreht der Markt, wenn eine Gruppe eine extrem hohe Position (ein 'Extrem-Sentiment') erreicht hat.
        """)

    st.write("### 📋 Alle Daten (Tabellenansicht)")
    st.dataframe(data[['Datum_Clean', 'Hedgefonds_Long', 'Hedgefonds_Short', 'Netto_Hedgefonds']])

except Exception as e:
    st.error(f"Fehler: {e}")
