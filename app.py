import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.express as px

st.set_page_config(page_title="Nasdaq Sentiment", layout="centered")

# --- DESIGN UPGRADE ---
st.markdown("""
    <style>
    .sentiment-card {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 10px;
        border-left: 10px solid #ef4444;
        margin-bottom: 25px;
    }
    .info-box {
        background-color: #111827;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #374151;
        font-size: 14px;
        color: #d1d5db;
        line-height: 1.6;
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
    nasdaq['Date_Obj'] = pd.to_datetime(nasdaq['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
    nasdaq['Netto'] = nasdaq['Lev_Money_Positions_Long_All'] - nasdaq['Lev_Money_Positions_Short_All']
    return nasdaq.sort_values('Date_Obj', ascending=True)

try:
    data = get_cot_data()
    latest = data.iloc[-1]
    val = int(latest['Netto'])
    
    st.title("Nasdaq 100 Sentiment")
    
    # 1. Status Karte (Datum schön formatiert)
    st.markdown(f"""
        <div class="sentiment-card">
            <p style="margin:0; color:#9ca3af; font-size:14px;">HANDELSSCHLUSS VOM {latest['Date_Obj'].strftime('%d.%m.%Y')}</p>
            <h2 style="margin:0; color:white;">EXTREM BÄRISCH ({val:,})</h2>
            <p style="margin:0; color:#ef4444; font-size:14px;">⚠️ Warnung: Hedgefonds halten massive Short-Wetten.</p>
        </div>
    """, unsafe_allow_html=True)

    # 2. Verbesserter Chart (Farben nach Wert)
    st.subheader("Wochen-Trend (Netto-Positionen)")
    chart_df = data.tail(15).copy()
    
    # Farbe festlegen: Rot für Short, Grün für Long
    chart_df['Farbe'] = ['#ef4444' if x < 0 else '#10b981' for x in chart_df['Netto']]
    
    fig = px.bar(chart_df, x='Date_Obj', y='Netto',
                 hover_data={'Date_Obj': '|%d.%m.%Y', 'Netto': ':,'})
    
    fig.update_traces(marker_color=chart_df['Farbe'], marker_line_width=0)
    
    fig.update_layout(
        xaxis_tickformat='%d.%m.',
        xaxis_title=None,
        yaxis_title=None,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color="#9ca3af",
        height=350,
        margin=dict(l=0, r=0, t=20, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # --- DIE INTERPRETATIONS-ANLEITUNG ---
    st.markdown("""
    <div class="info-box">
    <strong>💡 Wie du diese Daten liest:</strong><br>
    Die Balken zeigen die <strong>Netto-Positionen</strong> von Hedgefonds (Leveraged Money). 
    <br><br>
    1. <strong>Balken nach unten (ROT):</strong> Hedgefonds wetten auf fallende Kurse. Je tiefer der Balken, desto größer die Angst oder die Spekulation auf einen Crash.<br>
    2. <strong>Balken nach oben (GRÜN):</strong> Hedgefonds setzen auf steigende Kurse.<br>
    3. <strong>Was bedeutet 'Netto'?</strong> Es ist einfach <i>(Alle Long-Wetten) minus (Alle Short-Wetten)</i>. Aktuell überwiegen die Shorts massiv.<br>
    <br>
    <strong>Trading-Hinweis:</strong> Wenn die Balken ein historisches Tief erreichen (wie aktuell), kommt es oft zu einem <i>Short Squeeze</i> – die Kurse steigen plötzlich stark an, weil die Hedgefonds ihre Wetten schnell schließen müssen.
    </div>
    """, unsafe_allow_html=True)

    # 3. Historie
    st.write("---")
    c1, c2 = st.columns(2)
    c1.metric("Historischer Rekord-Short", f"{int(data['Netto'].min()):,}")
    c2.metric("Durchschnitt (2026)", f"{int(data['Netto'].mean()):,}")

except Exception as e:
    st.error(f"Fehler: {e}")
