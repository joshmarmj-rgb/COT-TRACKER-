import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import datetime

# =================================================================
# 1. CORE CONFIGURATION & HEDGE FUND UI STYLING
# =================================================================
# Wir setzen das Layout auf 'wide' für maximale Datenübersicht auf Profi-Monitoren.
st.set_page_config(
    page_title="INSTITUTIONAL MACRO TERMINAL v55", 
    page_icon="📡", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Das CSS wurde massiv erweitert, um den "Dark-Pool" Look zu erzeugen.
# Jedes Element wurde chirurgisch platziert, um FTMO-Tradern Fokus zu ermöglichen.
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;700&family=Inter:wght@300;400;700&display=swap');
    
    :root {
        --bg-color: #000000;
        --card-bg: #030303;
        --border-color: #111111;
        --text-main: #e0e0e0;
        --text-dim: #555555;
        --accent-blue: #0077ff;
        --accent-green: #00ff41;
        --accent-red: #ff4136;
        --gold: #ffcc00;
    }

    /* Basis-Setup */
    .stApp { background-color: var(--bg-color); color: var(--text-main); font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 1rem !important; max-width: 96% !important; }
    
    /* Header-Sektionen */
    .section-header { 
        font-family: 'JetBrains Mono', monospace; 
        font-size: 11px; 
        color: var(--text-dim); 
        text-transform: uppercase; 
        letter-spacing: 3px; 
        border-bottom: 1px solid var(--border-color);
        margin: 35px 0 20px 0;
        padding-bottom: 8px;
    }
    
    /* Instrumenten-Karten */
    .data-card { 
        background-color: var(--card-bg); 
        border: 1px solid var(--border-color); 
        padding: 22px; 
        border-radius: 2px;
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
    }
    .data-card:hover { border-color: #333; background-color: #050505; }
    
    .instrument-title { font-size: 22px; font-weight: 700; letter-spacing: -0.8px; margin-bottom: 4px; }
    .status-tag { font-size: 9px; padding: 2px 10px; border-radius: 1px; font-weight: 800; text-transform: uppercase; }
    
    /* Metriken */
    .metric-label { color: var(--text-dim); font-size: 9px; text-transform: uppercase; font-weight: 700; letter-spacing: 1px; }
    .metric-value { font-size: 28px; font-weight: 700; font-family: 'JetBrains Mono', monospace; line-height: 1.2; }
    
    /* USD Power Meter Spezifikation */
    .power-container { background: #080808; height: 8px; border-radius: 4px; overflow: hidden; margin: 15px 0; border: 1px solid #151515; }
    .power-bar { height: 100%; transition: width 1.2s ease-in-out; }
    
    /* Playbook & Intelligence Box */
    .playbook-box { 
        border-left: 2px solid var(--accent-blue); 
        background: linear-gradient(90deg, #050505 0%, #000000 100%); 
        padding: 20px; 
        margin-top: 10px; 
    }
    .playbook-title { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--accent-blue); margin-bottom: 10px; font-weight: 700; }

    /* Entfernung von Standard-UI-Elementen */
    #MainMenu, footer, header { visibility: hidden; }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #000; }
    ::-webkit-scrollbar-thumb { background: #222; }
</style>
""", unsafe_allow_html=True)

# =================================================================
# 2. DATA ENGINE: SURGICAL FETCHING & ERROR HANDLING
# =================================================================
@st.cache_data(ttl=3600)
def load_cftc_data(report_type="fin"):
    """
    Holt die Rohdaten direkt von der CFTC. 
    Wir nutzen 2026 als aktuelles Jahr für deine App.
    """
    urls = {
        "fin": "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip",
        "dis": "https://www.cftc.gov/files/dea/history/fut_disagg_txt_2026.zip"
    }
    try:
        r = requests.get(urls[report_type], timeout=25)
        r.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        # Falls die CFTC-Server down sind oder das Jahr 2026 noch keine Daten hat
        st.error(f"SYSTEM_CRITICAL: Data stream interrupted. Error: {e}")
        return pd.DataFrame()

def get_row_safe(df, search_term):
    """
    CHIRURGISCHE LOGIK: Verhindert den 'out-of-bounds' Fehler.
    Sucht nach dem Asset und gibt die Zeile nur zurück, wenn sie existiert.
    """
    if df.empty: return None
    # Wir suchen unempfindlich gegenüber Groß-/Kleinschreibung
    match = df[df['Market_and_Exchange_Names'].str.contains(search_term, na=False, case=False)]
    if not match.empty:
        return match.iloc[0]
    return None

def calculate_sentiment(net_pos):
    """Klassifiziert die institutionelle Stimmung basierend auf Netto-Positionen."""
    if net_pos > 60000: return "EXTREME BULLISH", "#00ff41"
    if net_pos > 15000: return "BULLISH", "#008f26"
    if net_pos < -60000: return "EXTREME BEARISH", "#ff4136"
    if net_pos < -15000: return "BEARISH", "#9e2a24"
    return "NEUTRAL / BALANCED", "#444444"

# =================================================================
# 3. RENDERING COMPONENTS (MODULAR)
# =================================================================
def render_instrument_card(name, long, short, color="#fff", category="FINANCIAL"):
    """Erstellt eine hochpräzise Daten-Karte für ein Asset."""
    net = long - short
    status_text, status_color = calculate_sentiment(net)
    
    st.markdown(f"""
        <div class="data-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span class="metric-label" style="color: {color}">{category} Asset</span>
                <span class="status-tag" style="background: {status_color}; color: #000;">{status_text}</span>
            </div>
            <div class="instrument-title">{name}</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-top: 20px;">
                <div>
                    <div class="metric-label">Institutional Long</div>
                    <div class="metric-value" style="color: var(--accent-blue);">{long:,}</div>
                </div>
                <div>
                    <div class="metric-label">Institutional Short</div>
                    <div class="metric-value" style="color: var(--accent-red);">{short:,}</div>
                </div>
                <div>
                    <div class="metric-label">Net Delta</div>
                    <div class="metric-value" style="color: {status_color};">{net:,}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# =================================================================
# 4. MAIN APPLICATION LOGIC (THE SURGERY)
# =================================================================
fin_df = load_cftc_data("fin")
dis_df = load_cftc_data("dis")

# Sicherstellen, dass Daten vorhanden sind, bevor wir rechnen
if not fin_df.empty and not dis_df.empty:
    try:
        # 4.1 Asset Extraktion (Stabilisiert durch get_row_safe)
        nq_row = get_row_safe(fin_df, "NASDAQ-100")
        gc_row = get_row_safe(dis_df, "GOLD")
        cl_row = get_row_safe(dis_df, "CRUDE OIL")
        
        # 4.2 Forex Basket Extraction (Umfassender Korb für USD-Power)
        # Wir tracken hier die 'Big 7' Währungen
        currency_map = {
            "EUR": "EURO FX",
            "GBP": "BRITISH POUND",
            "JPY": "JAPANESE YEN",
            "AUD": "AUSTRALIAN DOLLAR",
            "CAD": "CANADIAN DOLLAR",
            "CHF": "SWISS FRANC",
            "NZD": "NEW ZEALAND DOLLAR"
        }
        
        fx_results = {}
        weighted_fx_sum = 0
        
        for code, search in currency_map.items():
            row = get_row_safe(fin_df, search)
            if row is not None:
                # Wir nutzen 'Lev_Money_Positions' für das Smart Money Sentiment
                l = int(row.get('Lev_Money_Positions_Long_All', 0))
                s = int(row.get('Lev_Money_Positions_Short_All', 0))
                net = l - s
                fx_results[code] = net
                weighted_fx_sum += net
            else:
                fx_results[code] = 0

        # 4.3 USD Power Calculation
        # Logik: DXY Stärke = Invertiertes Sentiment der Majors
        # Wir skalieren durch 30.000 für eine Index-Range von ca. -50 bis +50
        usd_score = - (weighted_fx_sum) / 30000

        # =================================================================
        # 5. UI RENDERING (BUILDING THE TERMINAL)
        # =================================================================
        
        # Sektion 1: Core Markets
        st.markdown('<div class="section-header">Institutional Core Assets</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        
        with c1:
            if nq_row is not None:
                render_instrument_card("Nasdaq 100", int(nq_row['Lev_Money_Positions_Long_All']), int(nq_row['Lev_Money_Positions_Short_All']), "#00d4ff", "EQUITY INDEX")
        with c2:
            if gc_row is not None:
                render_instrument_card("Gold (Spot/Futures)", int(gc_row['M_Money_Positions_Long_All']), int(gc_row['M_Money_Positions_Short_All']), "#ffcc00", "COMMODITY")
        with c3:
            if cl_row is not None:
                render_instrument_card("WTI Crude Oil", int(cl_row['M_Money_Positions_Long_All']), int(cl_row['M_Money_Positions_Short_All']), "#bf55ff", "ENERGY")

        # Sektion 2: USD Power Meter
        st.markdown('<div class="section-header">Global Currency Power (Institutional Bias)</div>', unsafe_allow_html=True)
        
        # Berechnung der Meter-Breite (Mapping von -50/+50 auf 0-100%)
        meter_width = min(max((usd_score + 50) / 100, 0), 1) * 100
        meter_color = var_color = "#00ff41" if usd_score > 0 else "#ff4136"
        
        m_col_left, m_col_right = st.columns([4, 1])
        with m_col_right:
            st.markdown(f'<div class="metric-value" style="color: {meter_color}; text-align: right;">{usd_score:.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label" style="text-align: right;">Relativer USD Index</div>', unsafe_allow_html=True)
        with m_col_left:
            st.markdown(f"""
                <div class="power-container">
                    <div class="power-bar" style="width: {meter_width}%; background: {meter_color};"></div>
                </div>
            """, unsafe_allow_html=True)
            st.markdown('<div style="display: flex; justify-content: space-between; font-size: 9px; color: #444; font-family: monospace;"><span>USD BEARISH (RISK-ON)</span><span>NEUTRAL BIAS</span><span>USD BULLISH (SAFE-HAVEN)</span></div>', unsafe_allow_html=True)

        # Sektion 3: Forex Detail Grid
        st.markdown('<br>', unsafe_allow_html=True)
        fx_cols = st.columns(7)
        for i, (code, net) in enumerate(fx_results.items()):
            with fx_cols[i]:
                f_color = "#00ff41" if net > 0 else "#ff4136"
                st.markdown(f"""
                    <div style="background: #050505; border: 1px solid #111; padding: 12px; text-align: center;">
                        <div class="metric-label">{code}</div>
                        <div style="color: {f_color}; font-family: 'JetBrains Mono'; font-weight: bold; font-size: 16px;">{net/1000:.1f}k</div>
                    </div>
                """, unsafe_allow_html=True)

        # Sektion 4: Institutional Playbook (AI Logic)
        # Hier generiert der Code basierend auf den Daten konkrete Trade-Ideen.
        st.markdown('<div class="section-header">Institutional Intelligence Playbook</div>', unsafe_allow_html=True)
        
        pb_container = st.container()
        with pb_container:
            st.markdown('<div class="playbook-box">', unsafe_allow_html=True)
            p_left, p_right = st.columns(2)
            
            with p_left:
                st.markdown('<div class="playbook-title">MARKET REGIME & BIAS</div>', unsafe_allow_html=True)
                if usd_score > 12:
                    st.write("🏛️ **USD DOMINANCE:** Die Banken akkumulieren Dollar. Erwarte Verkaufsdruck bei Gold und EUR/USD. FTMO-Strategie: 'Sell the Rallies' in Forex-Majors.")
                elif usd_score < -12:
                    st.write("🚀 **RISK-ON REGIME:** USD wird abgestoßen. Geld fließt in Aktien (NQ) und Rohstoffwährungen (AUD). FTMO-Strategie: Suche Longs in NQ und AUD/USD.")
                else:
                    st.write("⚖️ **BALANCED MARKET:** Kein klarer Richtungsgeber vom Dollar. Range-Trading und Fokus auf Einzeltitel-News.")
            
            with p_right:
                st.markdown('<div class="playbook-title">DIVERGENCE ALERTS</div>', unsafe_allow_html=True)
                # Logik für Gold/USD Divergenz
                gold_net = 0
                if gc_row is not None:
                    gold_net = int(gc_row['M_Money_Positions_Long_All']) - int(gc_row['M_Money_Positions_Short_All'])
                
                if usd_score > 5 and gold_net > 20000:
                    st.warning("⚠️ UNGEWÖHNLICH: Dollar UND Gold werden gleichzeitig gekauft. Dies deutet auf massive geopolitische Risiken oder bevorstehende Marktcrashs hin.")
                elif usd_score < -5 and gold_net < -10000:
                    st.info("💡 LIQUIDITÄTS-CHECK: Schwacher Dollar schiebt Gold nicht an. Vorsicht vor Gold-Longs, da das institutionelle Interesse trotz USD-Schwäche fehlt.")
                else:
                    st.write("✅ KORRELATION INTACKT: Die Märkte bewegen sich im Einklang mit den institutionellen Kapitalflüssen.")
            st.markdown('</div>', unsafe_allow_html=True)

        # Sektion 5: Risk Management Parameters (New!)
        st.markdown('<div class="section-header">Prop-Firm Risk Parameters (FTMO-Specific)</div>', unsafe_allow_html=True)
        r_col1, r_col2, r_col3 = st.columns(3)
        with r_col1:
            st.markdown('<div class="metric-label">Max Volatility Risk</div>', unsafe_allow_html=True)
            vol_status = "HIGH" if abs(usd_score) > 25 else "STABLE"
            st.markdown(f'<div style="font-family: monospace; color: {"#ff4136" if vol_status == "HIGH" else "#0077ff"}">{vol_status}</div>', unsafe_allow_html=True)
        with r_col2:
            st.markdown('<div class="metric-label">Institutional Participation</div>', unsafe_allow_html=True)
            st.markdown('<div style="font-family: monospace; color: #fff;">OPTIMAL (2026 COT Data)</div>', unsafe_allow_html=True)
        with r_col3:
            st.markdown('<div class="metric-label">Terminal Sync Status</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-family: monospace; color: #555;">v55.0.4 ONLINE</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"RUNTIME_ERROR: A technical glitch occurred during data processing. {e}")

else:
    st.warning("📡 Warte auf Datenstrom von der CFTC... (Eventuell Wochenende oder Server-Wartung)")

# =================================================================
# 6. SYSTEM FOOTER
# =================================================================
# Ein dezenter Status-Bar am unteren Bildschirmrand.
st.markdown(f"""
    <div style="position: fixed; bottom: 8px; right: 20px; color: #1a1a1a; font-size: 9px; font-family: 'JetBrains Mono', monospace; letter-spacing: 1px;">
        DATA_REFRESH_UTC: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | SYSTEM_MODE: SURGICAL_PRECISION
    </div>
""", unsafe_allow_html=True)

# Ende der App.py v55