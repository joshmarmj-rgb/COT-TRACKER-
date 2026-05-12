import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.express as px

# Seite einrichten
st.set_page_config(page_title="Nasdaq Sentiment", layout="centered")

# Styling
st.markdown("""
    <style>
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
    
    # Richtiges Datumsobjekt erstellen für die Sortierung
    nasdaq['Date_Obj'] = pd.to_datetime(nasdaq['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
    nasdaq['Netto'] = nasdaq['Lev_Money_Positions_Long_All'] - nasdaq['Lev_Money_Positions_Short_All']
    
    # Chronologisch sortieren (alt nach neu)
    return nasdaq.sort_values('Date_Obj', ascending=True)

try:
    data = get_cot_data()
    latest = data.iloc[-1] # Letzter Eintrag nach Sortierung
    val = int(latest['Netto'])
    
    st.title("Nasdaq 100 Sentiment")
    
    # 1. Status Karte
    status_text = "EXTREM BÄRISCH" if val < -50000 else "NEUTRAL"
    st.markdown(f"""
        <div class="sentiment-card">
            <p style="margin:0; color:#9ca3af; font-size:14px;">AKTUELLER STATUS ({latest['Date_Obj'].strftime('%d.%m.%Y')})</p>
            <h2 style="margin:0; color:white;">{status_text} ({val:,})</h2>
            <p style="margin:0; color:#ef4444; font-size:14px;">Hedgefonds wetten massiv gegen den Markt.</p>
        </div>
    """, unsafe_allow_html=True)

    # 2. Profi-Chart mit Plotly
    st.subheader("Wochen-Trend (Netto-Positionen)")
    
    # Wir nehmen die letzten 15 Datenpunkte
    chart_df = data.tail(15)
    
    fig = px.bar(chart_df, x='Date_Obj', y='Netto',
                 labels={'Date_Obj': 'Datum', 'Netto': 'Netto-Position'},
                 color_discrete_sequence=['#3b82f6'])
    
    fig.update_layout(
        xaxis_tickformat='%d.%m.',
        xaxis_title=None,
        yaxis_title=None,
        margin=dict(l=0, r=0, t=0, b=0),
        height=350,
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # 3. Historischer Vergleich
    st.subheader("Historischer Vergleich")
    max_short = data['Netto'].min()
    avg_short = data['Netto'].mean()
    
    col1, col2 = st.columns(2)
    col1.metric("Rekord Short", f"{int(max_short):,}")
    col2.metric("Durchschnitt", f"{int(avg_short):,}")

except Exception as e:
    st.error(f"Fehler: {e}")
