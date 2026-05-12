import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go

st.set_page_config(page_title="Nasdaq Alpha Speedometer", layout="centered")

# --- CLEAN TRADING DESIGN ---
st.markdown("""
    <style>
    .main { background-color: #000000; color: #ffffff; }
    .decision-box {
        background-color: #111827;
        padding: 25px;
        border-radius: 12px;
        border: 2px solid #374151;
        margin-top: 20px;
    }
    .metric-label { color: #9ca3af; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 36px; font-weight: bold; color: #ffffff; }
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
    return nasdaq

try:
    data = get_cot_data()
    latest = data.iloc[0]
    val = int(latest['Netto'])
    
    # Historische Extremwerte für den Tacho
    min_val = data['Netto'].min()
    max_val = data['Netto'].max()

    st.title("Nasdaq Insider Tacho")
    st.write(f"Marktzustand basierend auf CFTC-Daten vom {latest['As_of_Date_In_Form_YYMMDD']}")

    # --- DER TACHO (STATT DIAGRAMM) ---
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = val,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Hedgefonds Sentiment", 'font': {'size': 24, 'color': '#ffffff'}},
        gauge = {
            'axis': {'range': [min_val, max_val], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "#3b82f6"},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "#374151",
            'steps': [
                {'range': [min_val, min_val*0.6], 'color': '#7f1d1d'}, # Extrem Short
                {'range': [min_val*0.6, 0], 'color': '#450a0a'},     # Short
                {'range': [0, max_val], 'color': '#064e3b'}          # Long
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': val
            }
        }
    ))

    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white", 'family': "Arial"}, height=350, margin=dict(t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

    # --- DIE ENTSCHEIDUNGS-MATRIX ---
    st.markdown("<div class='decision-box'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<p class='metric-label'>Positionierung</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='metric-value'>{val:,}</p>", unsafe_allow_html=True)
        st.write("Hedgefonds wetten aktuell massiv gegen den Markt.")
        
    with col2:
        st.markdown("<p class='metric-label'>Markt-Phase</p>", unsafe_allow_html=True)
        phase = "⚠️ SHORT SQUEEZE GEFAHR" if val < -150000 else "📉 ABWÄRTSTREND"
        st.markdown(f"<p class='metric-value' style='color:#ef4444;'>{phase}</p>", unsafe_allow_html=True)
        st.write("Das Smart Money zieht sich zurück oder sichert ab.")

    st.write("---")
    st.markdown("### 🛠️ Handlungs-Empfehlung")
    if val < -100000:
        st.warning("**KONTRA-CHANCE:** Die Stimmung ist so schlecht, dass ein Boden nahe sein könnte. Achte auf Umkehrsignale im Chart (z.B. RSI-Divergenz).")
    else:
        st.info("**TREND-FOLGE:** Die Profis sind pessimistisch. Vorsicht bei Long-Einstiegen, solange der Tacho tief im roten Bereich steht.")
    
    st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Fehler: {e}")
