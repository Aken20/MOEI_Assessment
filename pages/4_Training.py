"""
pages/4_Training.py
Learning & Development page.
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.session import get_master, get_raw_sheets
from components.bilingual import t
from components.navbar import render as navbar
import components.charts as charts

master = get_master()
raw = get_raw_sheets()
train_raw = raw["training"]
lang = st.session_state.lang

# ── Top navbar ───────────────────────────────────────────────────────────────
navbar()

st.markdown(f"# 🎓 {t('training_title', lang)}")

# Dept filter
all_depts = ["All"] + sorted(master["department"].dropna().unique().tolist())
sel_dept = st.selectbox(t("dept_filter", lang), options=all_depts)
df = master if sel_dept == "All" else master[master["department"] == sel_dept]

# ── KPI row ───────────────────────────────────────────────────────────────────
# Use raw training for KPI (not the per-employee summary)
active_train = train_raw[train_raw["status"].isin(["Completed", "In Progress"])] if "status" in train_raw.columns else train_raw
total_hrs = active_train["hours"].sum() if "hours" in active_train.columns else 0
avg_hrs = active_train.groupby("employee_id")["hours"].sum().mean() if "hours" in active_train.columns else 0

# From master
no_recent = int(df["has_recent_training"].sum() == 0) if "has_recent_training" in df.columns else 0
enrolled_pending = int(df["enrolled_pending"].sum()) if "enrolled_pending" in df.columns else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Training Hours", f"{total_hrs:.0f}")
col2.metric("Avg Hours/Employee", f"{avg_hrs:.1f}")
col3.metric("No Recent Training", no_recent)
col4.metric("Enrolled — Not Started", enrolled_pending)
st.divider()

# ── Charts (with safety fallbacks) ──────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    t("learning_investment", lang),
    t("training_by_category", lang),
    t("training_cold", lang),
])

with tab1:
    if "total_training_hours" in df.columns and not df["total_training_hours"].dropna().empty:
        st.plotly_chart(charts.training_bar(df, top_n=25, lang=lang), use_container_width=True)
    else:
        st.info("Training hours data not yet derived. Run data/metrics.py first or check the training sheet.")

with tab2:
    if "category" in train_raw.columns and "hours" in train_raw.columns:
        import plotly.express as px
        cat_agg = (
            active_train.groupby("category")["hours"].sum().reset_index()
            .sort_values("hours", ascending=False)
        )
        fig = px.bar(
            cat_agg, x="category", y="hours",
            title="Training Hours by Category" if lang == "en" else "ساعات التدريب حسب الفئة",
            color="hours", color_continuous_scale="Blues",
            labels={"category": "Category", "hours": "Hours"},
        )
        fig.update_layout(template="plotly_white", height=350, showlegend=False)
        fig.update_xaxes(tickangle=30)
        st.plotly_chart(fig, use_container_width=True)
        st.divider()
        try:
            st.plotly_chart(charts.training_heatmap(train_raw, lang=lang), use_container_width=True)
        except Exception as e:
            st.warning(f"Heatmap unavailable: {e}")
    else:
        st.info("Category/hours columns not found in training data.")

with tab3:
    cold_cols = ["employee_id", "full_name", "department", "grade", "has_recent_training"]
    if "flight_risk_score" in df.columns:
        cold_cols.append("flight_risk_score")
    available_cold = [c for c in cold_cols if c in df.columns]
    if "has_recent_training" in df.columns:
        cold_df = df[df["has_recent_training"] == 0][available_cold].sort_values(
            "flight_risk_score" if "flight_risk_score" in df.columns else "employee_id", ascending=False
        )
        st.dataframe(cold_df.head(30), use_container_width=True, hide_index=True)
        st.caption(
            "Employees with no completed or in-progress training in the last 12 months."
            if lang == "en"
            else "الموظفون الذين لم يكملوا أو يبدأوا تدريبًا في آخر 12 شهرًا."
        )
    else:
        st.info("has_recent_training column not available.")

st.divider()

# ── Training detail table ────────────────────────────────────────────────────
st.markdown(f"### {t('training_hrs', lang)}")
disp_cols = ["employee_id", "full_name", "department", "grade"]
if "total_training_hours" in df.columns:
    disp_cols += ["total_training_hours", "training_count", "last_training_date", "training_categories"]
disp = df[disp_cols].sort_values(
    "total_training_hours" if "total_training_hours" in df.columns else "employee_id", ascending=False
).head(30)
st.dataframe(disp, use_container_width=True, hide_index=True)

csv = disp.to_csv(index=False).encode("utf-8")
st.download_button(label=t("export_csv", lang), data=csv, file_name="training_report.csv", mime="text/csv")