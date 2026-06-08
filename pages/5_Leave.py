"""
pages/5_Leave.py
Leave Balances page.
Charts showing annual and sick leave distribution, low-balance warnings.
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

st.markdown(f"# 🏖️ {t('leave_title', lang)}")

# Dept filter
all_depts = ["All"] + sorted(master["department"].dropna().unique().tolist())
sel_dept = st.selectbox(t("dept_filter", lang), options=all_depts)

df = master if sel_dept == "All" else master[master["department"] == sel_dept]

# ── KPI row ───────────────────────────────────────────────────────────────────
annual_avg = df["annual_leave_balance"].mean()
sick_avg = df["sick_leave_balance"].mean()
low_annual = int((df["annual_leave_balance"] < 5).sum())
low_sick = int((df["sick_leave_balance"] < 5).sum())

kpi_row([
    ("Avg Annual Leave Balance", f"{annual_avg:.1f} days", None),
    ("Avg Sick Leave Balance", f"{sick_avg:.1f} days", None),
    ("Low Annual (< 5 days)", str(low_annual), None),
    ("Low Sick (< 5 days)", str(low_sick), None),
], lang)

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs([t("annual_balance", lang), t("sick_balance", lang)])

with tab1:
    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(charts.leave_balance_hist(df, "annual", lang), use_container_width=True)
    with col_b:
        st.plotly_chart(charts.leave_by_dept(df, lang), use_container_width=True)

with tab2:
    st.plotly_chart(charts.leave_balance_hist(df, "sick", lang), use_container_width=True)

st.divider()

# ── Low balance warnings ───────────────────────────────────────────────────────
st.markdown(f"### ⚠️ {t('low_leave', lang)}")
warn_df = df[df["annual_leave_balance"] < 5][
    ["employee_id", "full_name", "department", "grade",
     "annual_leave_balance", "sick_leave_balance"]
].sort_values("annual_leave_balance")
st.dataframe(warn_df.head(30), use_container_width=True, hide_index=True)

csv = warn_df.to_csv(index=False).encode("utf-8")
st.download_button(label=t("export_csv", lang), data=csv, file_name="low_leave_balance.csv", mime="text/csv")