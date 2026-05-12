import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go

st.set_page_config(page_title="Nasdaq Alpha Gauge", layout="centered")

# --- ULTRA DARK DESIGN ---
st.markdown("""
    <style>
    .main { background-color: #050505; color: #e2e8f0; }
    .info-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        padding: 20px;
        border-radius: 4px;
        margin-top: 10px;
    }
    .label { color: #64748b; font-size: 12px; font-weight: bold; letter-spacing: 1px; }
    .explanation { color: #94a3b8; font-size: 14px; line-height: 1.5; margin-bottom: 15px; }
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
    min_val, max_val = data['Netto'].min(), data['Netto'].max()

    st.markdown("<h2 style='text-align: center; color: white;'>NASDAQ SENTIMENT INDEX</h2>", unsafe_allow_html=True)

    # --- DER OPTIMIERTE TACHO (OHNE BLAUEN BALKEN) ---
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = val,
        number = {'font': {'color': 'white', 'size': 50}, 'valueformat': ','},
        gauge = {
            'axis': {'range': [min_val, max_val], 'tickwidth': 1, 'tickcolor': "#475569"},
            'bar': {'color': "rgba(0,0,0,0)"}, # HIER: Den blauen Balken unsichtbar gemacht!
            'bgcolor': "#0f172a",
            'borderwidth': 0,
            'steps': [
                {'range': [min_val, min_val*0.5], 'color': '#ef4444'}, # Rot
                {'range': [min_val*0.5, 0], 'color': '#f59e0b'},       # Orange
                {'range': [0, max_val], 'color': '#10b981'}           # Grün
            ],
            'threshold': {
                'line': {'color': "white", 'width': 5}, # Die weiße Nadel
                'thickness': 0.8,
                'value': val
            }
        }
    ))

    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=380, margin=dict(t=20, b=0, l=40, r=40))
    st.plotly_chart(fig, use_container_width=True)

    # --- DIE ÜBERSICHTLICHE BESCHREIBUNG ---
    st.markdown("### 🔍 Was bedeuten diese Werte?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        st.markdown("<p class='label'>NETTO-EXPOSURE</p>", unsafe_allow_html=True)
        st.markdown(f"**{val:,} Kontrakte**")
        st.markdown("""<p class='explanation'>
            Das ist das 'Gewicht' der Wetten. <br>
            <b>Negativ:</b> Profis verdienen Geld, wenn der Markt fällt. <br>
            <b>Positiv:</b> Profis verdienen Geld, wenn der Markt steigt.
            </p>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        st.markdown("<p class='label'>KONTEXT-ANALYSE</p>", unsafe_allow_html=True)
        if val < -150000:
            st.markdown("<b style='color:#ef4444;'>EXTREM-BEREICH</b>")
        else:
            st.markdown("<b style='color:#f59e0b;'>ERHÖHTES RISIKO</b>")
        st.markdown("""<p class='explanation'>
            Wenn die Nadel im <b>roten Bereich</b> steht, ist der Markt 'überverkauft'. Oft folgt eine plötzliche Erholung (Short Squeeze).
            </p>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Fehler: {e}")
