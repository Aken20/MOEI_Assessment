"""
app.py — MOEI HR Companion (Door B: Management View)
Ministry of Energy & Infrastructure, UAE
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from components.bilingual import t, set_lang
from components.theme import apply_theme
from components.navbar import init_lang, render as navbar

# ── Config ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MOEI HR Companion",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

set_lang(st)
init_lang()
apply_theme()
navbar()

lang = st.session_state.lang

# ── Welcome shell ───────────────────────────────────────────────────────────
st.markdown(f"# 🏛  MOEI HR Companion")
st.markdown(f"### {t('app_subtitle', lang)}")

col_a, col_b = st.columns(2)
with col_a:
    st.info(
        "**Welcome to the Management View.**\n\n"
        "Use the navigation bar above to explore:\n\n"
        "📊 **Overview** — workforce KPIs at a glance\n"
        "💬 **Ask Your Workforce** — ask questions in plain language\n"
        "📈 **Performance** — promotion readiness & flight risk\n"
        "🎓 **Training** — learning investment & gaps\n"
        "🏖️ **Leave** — balance monitoring & warnings"
    )
with col_b:
    st.success(
        "**Built with:**\n\n"
        "🧠 DeepSeek V4 Pro via OpenRouter\n"
        "🎯 Intent classifier + structured JSON output\n"
        "📚 KB-grounded policy search (24 PDFs, EN+AR)\n"
        "🔁 Graceful fallback when API is down\n"
        "🌐 Fully bilingual — English & Arabic"
    )