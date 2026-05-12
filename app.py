import streamlit as st
import pandas as pd
import requests
import io
import zipfile

# Seite einrichten
st.set_page_config(page_title="Nasdaq Sentiment", layout="centered")

# Styling
st.markdown("""
    <style>
    .reportview-container { background: #0e1117; }
    .sentiment-card {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 10px;
        border-left: 10px solid #ef4444;
        margin-bottom: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

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
    nasdaq['Netto'] = nasdaq['Lev_Money_Positions_Long_All'] - nasdaq['Lev_Money_Positions_Short_All']
    nasdaq['Datum'] = nasdaq['As_of_Date_In_Form_YYMMDD'].astype(str).apply(lambda x: f"{x[4:6]}.{x[2:4]}.")
    return nasdaq

try:
    data = get_cot_data()
    latest = data.iloc[0]
    val = int(latest['Netto'])
    
    # 1. Headline & Status
    st.title("Nasdaq 100 Sentiment")
    
    status_text = "EXTREM BÄRISCH" if val < -50000 else "NEUTRAL"
    st.markdown(f"""
        <div class="sentiment-card">
            <p style="margin:0; color:#9ca3af; font-size:14px;">AKTUELLER STATUS</p>
            <h2 style="margin:0; color:white;">{status_text} ({val:,})</h2>
            <p style="margin:0; color:#ef4444; font-size:14px;">Hedgefonds wetten massiv gegen den Markt.</p>
        </div>
    """, unsafe_allow_html=True)

    # 2. Kompakter Chart (Nur die letzten 12 Wochen für Fokus)
    st.subheader("Wochen-Trend (Netto-Positionen)")
    chart_df = data.head(12).iloc[::-1]
    st.bar_chart(chart_df.set_index('Datum')['Netto'], height=250)

    # 3. Historische Einordnung
    st.subheader("Historischer Vergleich")
    max_short = data['Netto'].min()
    avg_short = data['Netto'].mean()
    
    col1, col2 = st.columns(2)
    col1.metric("All-Time Low (Short)", f"{int(max_short):,}")
    col2.metric("Durchschnitt", f"{int(avg_short):,}")
    
    percent_of_extreme = (val / max_short) * 100
    st.write(f"👉 Wir sind aktuell bei **{percent_of_extreme:.1f}%** des historischen Short-Extrems.")

except Exception as e:
    st.error(f"Fehler: {e}")
