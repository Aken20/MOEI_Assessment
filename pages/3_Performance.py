"""
pages/3_Performance.py
Performance & Promotion Readiness page.
Charts + tables showing score trends, promotion-readiness scores, and flight risk.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.session import get_master
from components.bilingual import t
from components.navbar import render as navbar
import components.charts as charts
from ai.workforce_qa import ask_workforce, ask_fallback

master = get_master()
lang = st.session_state.lang

# ── Top navbar ───────────────────────────────────────────────────────────────
navbar()

st.markdown(f"# 📈 {t('perf_title', lang)}")

# Dept filter
all_depts = ["All"] + sorted(master["department"].dropna().unique().tolist())
sel_dept = st.selectbox(t("dept_filter", lang), options=all_depts)

df = master if sel_dept == "All" else master[master["department"] == sel_dept]

# ── KPI row ───────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Avg Performance Score", f"{df['avg_score'].mean():.1f}")
col2.metric("Avg Promotion Readiness", f"{df['promotion_readiness_score'].mean():.1f}")
col3.metric("High Flight Risk (>60)", int((df["flight_risk_score"] > 60).sum()))

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    t("promotion_readiness", lang),
    t("score_trend", lang),
    t("perf_by_dept", lang),
])

with tab1:
    st.plotly_chart(charts.promotion_readiness_table(df, top_n=20, lang=lang), use_container_width=True)
    st.divider()
    # Flight risk
    st.markdown(f"### 🚨 {t('risk', lang)} — Flight Risk")
    st.plotly_chart(charts.flight_risk_table(df, top_n=20, lang=lang), use_container_width=True)

with tab2:
    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(charts.score_trend_pie(df, lang=lang), use_container_width=True)
    with col_b:
        # Score trend vs engagement scatter
        import plotly.express as px
        scatter_df = df.dropna(subset=["avg_score", "engagement_score"])
        fig = px.scatter(
            scatter_df, x="avg_score", y="engagement_score",
            color="score_trend", hover_name="full_name",
            title="Performance vs Engagement by Trend",
            labels={"avg_score": "Avg Score", "engagement_score": "Engagement Score"},
            color_discrete_map={"improving": "#417505", "stable": "#0066B3",
                                "declining": "#D0021B", "insufficient": "#F5A623"},
        )
        fig.update_layout(template="plotly_white", height=350)
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.plotly_chart(charts.perf_by_dept(master, lang=lang), use_container_width=True)

st.divider()

# ── AI Interpretation ────────────────────────────────────────────────────────
st.markdown(f"## 🤖 {t('ai_interpret', lang)}")

ai_col1, ai_col2, ai_col3 = st.columns(3)

interpret_questions_en = [
    ("Explain the promotion-readiness patterns", "Look at the top promotion-ready employees. What patterns do you see? Which departments are over/under represented? What should the manager do?"),
    ("What's driving flight risk?", "Analyze the flight-risk-flagged employees. What common factors do they share — low engagement? no training? performance decline? What actions should the manager take?"),
    ("What about the declining performers?", "Look at employees with declining score trends. Who are they, which departments, and what should their managers do — training? coaching? role change?"),
]
interpret_questions_ar = [
    ("اشرح أنماط جاهزية الترقية", "انظر إلى أكثر الموظفين جاهزية للترقية. ما الأنماط التي تراها؟ أي الإدارات ممثلة أكثر/أقل؟ ما الذي يجب على المدير فعله؟"),
    ("ما أسباب مخاطر المغادرة؟", "حلل الموظفين المعرضين لخطر المغادرة. ما العوامل المشتركة بينهم — انخراط منخفض؟ لا تدريب؟ تراجع الأداء؟ ما الإجراءات المطلوبة؟"),
    ("ماذا عن المتراجعين في الأداء؟", "انظر إلى الموظفين ذوي اتجاه الأداء المتراجع. من هم، في أي إدارات، وماذا يجب على مديريهم فعله — تدريب؟ توجيه؟ تغيير دور؟"),
]
interpret_questions = interpret_questions_ar if lang == "ar" else interpret_questions_en

# Store selection
if "perf_ai_question" not in st.session_state:
    st.session_state["perf_ai_question"] = None
if "perf_ai_result" not in st.session_state:
    st.session_state["perf_ai_result"] = None

for col, (label, prompt) in zip([ai_col1, ai_col2, ai_col3], interpret_questions):
    with col:
        if st.button(f"💡 {label}", key=f"perf_ai_{label[:20]}", use_container_width=True):
            st.session_state["perf_ai_question"] = prompt
            st.session_state["perf_ai_result"] = None
            st.rerun()

# Custom question
with st.expander(t("ai_custom", lang) if lang == "en" else "سؤال مخصص"):
    custom_q = st.text_area(
        "Ask about the data on this page",
        placeholder="Why does department X have lower average scores?" if lang == "en" else "لماذا درجة القسم X أقل من المتوسط؟",
        height=70,
        label_visibility="collapsed",
        key="perf_custom_q",
    )
    if st.button(f"🔍 {t('ask_button', lang)}", key="perf_custom_btn"):
        if custom_q:
            st.session_state["perf_ai_question"] = custom_q
            st.session_state["perf_ai_result"] = None
            st.rerun()

# Process question
if st.session_state.get("perf_ai_question") and st.session_state.get("perf_ai_result") is None:
    question = st.session_state["perf_ai_question"]
    with st.spinner(t("thinking", lang)):
        try:
            result = ask_workforce(question, df, lang=lang)
            st.session_state["perf_ai_result"] = result
        except Exception as e:
            err = str(e)
            if "OPENROUTER_API_KEY" in err or "not set" in err.lower():
                fallback = ask_fallback(question, df, lang)
                st.session_state["perf_ai_result"] = {"fallback": fallback}
            else:
                st.session_state["perf_ai_result"] = {"error": err}
    st.rerun()

# Display result
ai_result = st.session_state.get("perf_ai_result")
if ai_result:
    if "error" in ai_result:
        st.error(f"{t('api_error', lang)}: {ai_result['error']}")
    elif "fallback" in ai_result:
        st.info(t("fallback_header", lang) if lang == "en" else "وضع احتياطي (بدون API)")
        st.markdown(ai_result["fallback"])
    elif "answer" in ai_result:
        answer = ai_result["answer"]
        if ai_result.get("kb_used"):
            st.caption("📚 Grounded in HR Knowledge Base")
        st.info(answer.get("summary", ""))
        st.caption(f"🟡 Confidence: {answer.get('confidence', 'medium')}")
        if answer.get("note"):
            st.warning(answer["note"])
        for p in answer.get("people", []):
            st.markdown(f"**{p.get('name', '')}** — {p.get('reason', '')}")
            act = p.get("action", "")
            if act:
                st.markdown(f"→ *{act}*")
            st.divider()
    if st.button(t("clear", lang) if lang == "en" else "مسح", key="perf_ai_clear"):
        st.session_state["perf_ai_question"] = None
        st.session_state["perf_ai_result"] = None
        st.rerun()

st.divider()

# ── Detailed table ────────────────────────────────────────────────────────────
st.markdown(f"### {t('top_ready', lang)}")
display_cols = [
    "employee_id", "full_name", "department", "grade",
    "promotion_readiness_score", "avg_score", "score_trend",
    "total_training_hours", "years_since_promotion", "engagement_score",
]
available = [c for c in display_cols if c in df.columns]
table_df = df[available].sort_values("promotion_readiness_score", ascending=False).head(30)
table_df = table_df.rename(columns={
    "promotion_readiness_score": t("promotion_readiness", lang),
    "total_training_hours": t("training_hrs", lang),
})
st.dataframe(table_df, use_container_width=True, hide_index=True)

# CSV export
csv = table_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label=t("export_csv", lang),
    data=csv,
    file_name="promotion_readiness.csv",
    mime="text/csv",
)