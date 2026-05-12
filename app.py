import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go

st.set_page_config(page_title="Nasdaq Intelligence", layout="centered")

# --- STYLING ---
st.markdown("""
    <style>
    .main { background-color: #050505; color: #e2e8f0; }
    .metric-box {
        background: #0f172a;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #1e293b;
        text-align: center;
    }
    .delta-positive { color: #10b981; font-weight: bold; }
    .delta-negative { color: #ef4444; font-weight: bold; }
    .label { color: #64748b; font-size: 11px; text-transform: uppercase; margin-bottom: 5px; }
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
    nasdaq['Date_Obj'] = pd.to_datetime(nasdaq['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
    return nasdaq.sort_values('Date_Obj', ascending=False)

try:
    data = get_cot_data()
    latest = data.iloc[0]
    prev = data.iloc[1] # Die Vorwoche
    
    val = int(latest['Netto'])
    delta = val - int(prev['Netto'])
    
    st.markdown("<h2 style='text-align: center; color: white;'>NASDAQ SENTIMENT TERMINAL</h2>", unsafe_allow_html=True)

    # --- 1. DER TACHO (Kompakter) ---
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = val,
        number = {'font': {'color': 'white', 'size': 40}, 'valueformat': ','},
        gauge = {
            'axis': {'range': [data['Netto'].min(), data['Netto'].max()], 'tickcolor': "#475569"},
            'bar': {'color': "rgba(0,0,0,0)"},
            'bgcolor': "#0f172a",
            'steps': [
                {'range': [data['Netto'].min(), -100000], 'color': '#ef4444'},
                {'range': [-100000, 0], 'color': '#f59e0b'},
                {'range': [0, data['Netto'].max()], 'color': '#10b981'}
            ],
            'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.8, 'value': val}
        }
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=280, margin=dict(t=0, b=0, l=50, r=50))
    st.plotly_chart(fig, use_container_width=True)

    # --- 2. DIE NEUE ANALYSE-SEKTION (Das Fehlende "Wissen") ---
    st.markdown("### 📊 Live-Analyse")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("<div class='metric-box'><div class='label'>Trend vs. Vorwoche</div>", unsafe_allow_html=True)
        color_class = "delta-positive" if delta > 0 else "delta-negative"
        arrow = "↑" if delta > 0 else "↓"
        st.markdown(f"<span class='{color_class}'>{arrow} {abs(delta):,}</span>", unsafe_allow_html=True)
        st.markdown("<small style='color:#64748b;'>Kontrakte</small></div>", unsafe_allow_html=True)
        
    with c2:
        st.markdown("<div class='metric-box'><div class='label'>Long Positionen</div>", unsafe_allow_html=True)
        st.markdown(f"<span style='color:white;'>{int(latest['Lev_Money_Positions_Long_All']):,}</span>", unsafe_allow_html=True)
        st.markdown("<small style='color:#10b981;'>Käufer</small></div>", unsafe_allow_html=True)

    with c3:
        st.markdown("<div class='metric-box'><div class='label'>Short Positionen</div>", unsafe_allow_html=True)
        st.markdown(f"<span style='color:white;'>{int(latest['Lev_Money_Positions_Short_All']):,}</span>", unsafe_allow_html=True)
        st.markdown("<small style='color:#ef4444;'>Verkäufer</small></div>", unsafe_allow_html=True)

    # --- 3. DAS "INSIDER-URTEIL" ---
    st.markdown("---")
    st.markdown("### 🏛️ Das Insider-Urteil")
    
    if delta < 0:
        trend_desc = "Die Hedgefonds **erhöhen ihren Druck**. Sie haben ihre Short-Wetten im Vergleich zur Vorwoche weiter ausgebaut."
    else:
        trend_desc = "Es gibt eine **leichte Entspannung**. Die Profis haben begonnen, ihre Short-Wetten leicht zu reduzieren."

    st.info(f"""
    **Aktueller Status:** {trend_desc}
    
    **Was das für dich heißt:** 
    Obwohl wir im roten Bereich sind (Netto-Short), ist die *Richtung* der Veränderung ({delta:,}) entscheidend. 
    Solange die Zahl negativer wird, ist der Abwärtstrend intakt. Dreht die Zahl ins Positive, bereiten sich die Profis auf eine Rallye vor.
    """)

except Exception as e:
    st.error(f"Fehler: {e}")
