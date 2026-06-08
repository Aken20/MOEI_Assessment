"""
pages/1_Overview.py — Workforce Overview
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.session import get_master
from components.bilingual import t
from components.theme import kpi_row
from components.navbar import render as navbar
import components.charts as charts

master = get_master()
lang = st.session_state.get("lang", "en")

# ── Top navbar ───────────────────────────────────────────────────────────────
navbar()

st.markdown(f"# 📊 {t('overview_title', lang)}")

# ── KPI Row ──────────────────────────────────────────────────────────────────
kpi_row([
    (t("total_employees", lang), f"{len(master):,}", None),
    (t("avg_engagement", lang), f"{master['engagement_score'].mean():.1f}", None),
    (t("avg_performance", lang), f"{master['avg_score'].mean():.1f}", None),
    (t("nationals", lang), f"{(master['uae_national'] == 'Yes').mean() * 100:.0f}%", None),
], lang)

st.divider()

# ── Charts ───────────────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)
with col_a:
    st.plotly_chart(charts.headcount_bar(master, lang), use_container_width=True)
with col_b:
    st.plotly_chart(charts.engagement_hist(master, lang), use_container_width=True)

col_c, col_d = st.columns(2)
with col_c:
    st.plotly_chart(charts.engagement_by_dept(master, lang), use_container_width=True)
with col_d:
    st.plotly_chart(charts.grade_pyramid(master, lang), use_container_width=True)