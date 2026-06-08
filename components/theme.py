"""
components/theme.py
Inject professional dashboard CSS across all pages.
Call apply_theme() at the top of every page after set_page_config.
Design: MOEI Government Dashboard — dark sidebar, glass cards, gold accents.
"""

import streamlit as st

THEME_CSS = """
<style>
/* ===== ROOT VARIABLES ===== */
:root {
    --navy: #003366;
    --navy-dark: #0A1628;
    --navy-light: #0D2137;
    --blue: #0066B3;
    --blue-light: #E8F0FE;
    --gold: #C8961E;
    --gold-light: #FFF8E7;
    --white: #FFFFFF;
    --bg: #F4F6F9;
    --text: #1A202C;
    --text-secondary: #64748B;
    --border: #E2E8F0;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
    --shadow-lg: 0 8px 24px rgba(0,0,0,0.10);
    --radius: 12px;
    --radius-sm: 8px;
}

/* ===== GLOBAL ===== */
.stApp {
    background: var(--bg);
}
/* Hide Streamlit's default toolbar (deploy button, etc.) */
.stApp > header:first-child,
[data-testid="stAppToolbar"],
.st-emotion-cache-14vh5up,
[data-testid="stHeader"] {
    display: none !important;
}
/* Tighten top padding slightly */
.main .block-container {
    padding-top: 0.5rem !important;
}

/* ===== SIDEBAR — hidden entirely ===== */
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
button[kind="header"] {
    display: none !important;
}
/* Push main content to full width when sidebar is hidden */
[data-testid="stAppViewContainer"] > .main {
    padding-left: 2rem !important;
}
[data-testid="stAppViewContainer"] > .main .block-container {
    padding-left: 2rem !important;
    max-width: 100% !important;
}

/* ===== KPI CARDS ===== */
[data-testid="stMetric"] {
    background: var(--white);
    border-radius: var(--radius);
    padding: 20px 24px;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border);
    transition: box-shadow 0.2s;
}
[data-testid="stMetric"]:hover {
    box-shadow: var(--shadow-md);
}
[data-testid="stMetricValue"] {
    font-size: 2rem !important;
    font-weight: 700 !important;
    color: var(--navy) !important;
}
[data-testid="stMetricLabel"] {
    color: var(--text-secondary) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ===== CHARTS ===== */
.js-plotly-plot, .plot-container {
    border-radius: var(--radius) !important;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border);
}

/* ===== DATA TABLES ===== */
[data-testid="stDataFrame"] {
    border-radius: var(--radius) !important;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border);
}
[data-testid="stDataFrame"] th {
    background: var(--navy) !important;
    color: var(--white) !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    padding: 10px 14px !important;
}
[data-testid="stDataFrame"] td {
    padding: 8px 14px !important;
    font-size: 0.82rem !important;
}
[data-testid="stDataFrame"] tr:nth-child(even) {
    background: #F8FAFC;
}
[data-testid="stDataFrame"] tr:hover {
    background: var(--blue-light) !important;
}

/* ===== BUTTONS ===== */
.stButton > button {
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 8px 20px !important;
    transition: all 0.2s;
}
.stButton > button[kind="primary"] {
    background: var(--navy) !important;
    border-color: var(--navy) !important;
    color: var(--white) !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--blue) !important;
    border-color: var(--blue) !important;
    box-shadow: 0 2px 8px rgba(0,51,102,0.25);
}
.stButton > button[kind="secondary"] {
    background: var(--white) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: var(--blue) !important;
    color: var(--navy) !important;
}

/* ===== SELECT BOX ===== */
.stSelectbox > div > div {
    border-radius: var(--radius-sm) !important;
    border-color: var(--border) !important;
}

/* ===== TABS ===== */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    background: var(--white);
    border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
    padding: 10px 20px !important;
    border: 1px solid var(--border);
    border-bottom: none;
    color: var(--text-secondary);
    font-weight: 500;
    font-size: 0.85rem;
    transition: all 0.15s;
}
.stTabs [aria-selected="true"] {
    background: var(--navy) !important;
    color: var(--white) !important;
    border-color: var(--navy) !important;
}

/* ===== EXPANDER ===== */
.streamlit-expanderHeader {
    border-radius: var(--radius-sm) !important;
    background: var(--white) !important;
    border: 1px solid var(--border) !important;
    font-weight: 600;
}

/* ===== INFO / WARNING / ERROR BOXES ===== */
.stAlert {
    border-radius: var(--radius-sm) !important;
    border: none !important;
}
div[data-testid="stInfo"] {
    background: var(--blue-light) !important;
}
div[data-testid="stWarning"] {
    background: var(--gold-light) !important;
}

/* ===== HEADINGS ===== */
h1 {
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    color: var(--navy) !important;
    letter-spacing: -0.5px;
}
h2 {
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    color: var(--text) !important;
}
h3 {
    font-size: 1.0rem !important;
    font-weight: 600 !important;
    color: var(--text) !important;
}

/* ===== DIVIDER ===== */
hr {
    border-color: var(--border) !important;
    margin: 24px 0 !important;
}

/* ===== TOP NAVBAR ===== */
a[href*="pages/"] {
    text-decoration: none !important;
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--text-secondary) !important;
    transition: all 0.15s;
    display: inline-block;
}
a[href*="pages/"]:hover {
    background: var(--blue-light);
    color: var(--navy) !important;
}

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(0,0,0,0.12);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(0,0,0,0.20); }
</style>
"""


def apply_theme():
    """Inject theme CSS. Call once at the top of app.py."""
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def card(content_func):
    """Wrap content in a glass card container."""
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    content_func()
    st.markdown('</div>', unsafe_allow_html=True)


def kpi_row(items: list[tuple[str, str, str]], lang: str = "en"):
    """Render a row of KPI metric cards. items = [(label, value, delta), ...]"""
    cols = st.columns(len(items))
    for col, (label, value, delta) in zip(cols, items):
        with col:
            st.metric(label=label, value=value, delta=delta)


def badge(text: str, style: str = "blue"):
    """Render a colored badge."""
    st.markdown(f'<span class="badge badge-{style}">{text}</span>', unsafe_allow_html=True)


def section_header(title: str, icon: str = ""):
    """Render a styled section header."""
    icon_str = f"{icon} " if icon else ""
    st.markdown(
        f'<div style="margin: 24px 0 12px; font-size:1.1rem; font-weight:600; '
        f'color:var(--navy); border-left:4px solid var(--blue); padding-left:12px;">'
        f'{icon_str}{title}</div>',
        unsafe_allow_html=True,
    )