"""
components/charts.py
Plotly chart helpers for the dashboard.
All charts return plotly.graph_objects.Figure objects.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# MOEI brand palette
MOEI_COLORS = {
    "primary": "#003366",      # Deep navy
    "secondary": "#0066B3",    # MOEI blue
    "accent": "#00A9E0",      # Light blue
    "warning": "#F5A623",      # Amber
    "danger": "#D0021B",       # Red
    "success": "#417505",     # Green
    "text": "#2C3E50",
    "bg": "#F8F9FA",
}

DEPT_COLORS = [
    "#003366", "#0066B3", "#00A9E0", "#417505",
    "#F5A623", "#D0021B", "#7B2D8B", "#E64C3C",
    "#1ABC9C", "#9B59B6",
]


def headcount_bar(df: pd.DataFrame, lang: str = "en") -> go.Figure:
    """Bar chart: employee count per department."""
    dept_counts = df.groupby("department").size().reset_index(name="count")
    dept_counts = dept_counts.sort_values("count", ascending=True)

    label = "department" if lang == "en" else "department"
    title = "Headcount by Department" if lang == "en" else "عدد الموظفين بالإدارة"

    fig = px.bar(
        dept_counts,
        x="count",
        y="department",
        orientation="h",
        color="count",
        color_continuous_scale="Blues",
        title=title,
    )
    fig.update_layout(
        yaxis_title="",
        xaxis_title="Number of Employees",
        showlegend=False,
        template="plotly_white",
        height=max(400, len(dept_counts) * 45),
    )
    fig.update_traces(texttemplate="%{x}", textposition="outside")
    return fig


def engagement_hist(df: pd.DataFrame, lang: str = "en") -> go.Figure:
    """Histogram of engagement scores."""
    title = "Engagement Score Distribution" if lang == "en" else "توزيع درجات الانخراط"
    fig = px.histogram(
        df,
        x="engagement_score",
        nbins=20,
        title=title,
        color_discrete_sequence=[MOEI_COLORS["secondary"]],
        labels={"engagement_score": "Engagement Score", "count": "Employees"},
    )
    fig.update_layout(template="plotly_white", showlegend=False, height=300)
    # Add vertical lines for zones
    for score, color, label in [
        (70, MOEI_COLORS["success"], "High"),
        (55, MOEI_COLORS["warning"], "Medium"),
        (40, MOEI_COLORS["danger"], "Low"),
    ]:
        fig.add_vline(x=score, line_color=color, line_dash="dash", annotation_text=label)
    return fig


def engagement_by_dept(df: pd.DataFrame, lang: str = "en") -> go.Figure:
    """Box plot: engagement score distribution per department."""
    title = "Engagement by Department" if lang == "en" else "الانخراط حسب الإدارة"
    fig = px.box(
        df,
        x="department",
        y="engagement_score",
        color="department",
        title=title,
        color_discrete_sequence=DEPT_COLORS,
        labels={"engagement_score": "Engagement Score", "department": ""},
    )
    fig.update_layout(showlegend=False, template="plotly_white", height=350)
    fig.update_xaxes(tickangle=30)
    return fig


def perf_by_dept(df: pd.DataFrame, lang: str = "en") -> go.Figure:
    """Bar chart: average performance score by department."""
    perf = df.groupby("department")["avg_score"].mean().reset_index()
    perf = perf.sort_values("avg_score", ascending=True)
    title = "Average Performance Score by Department" if lang == "en" else "متوسط درجة الأداء بالإدارة"
    fig = px.bar(
        perf,
        x="avg_score",
        y="department",
        orientation="h",
        color="avg_score",
        color_continuous_scale="RdYlGn",
        title=title,
        range_color=[50, 85],
        labels={"avg_score": "Avg Score", "department": ""},
    )
    fig.update_layout(showlegend=False, template="plotly_white", height=max(350, len(perf) * 45))
    fig.update_traces(texttemplate="%{x:.1f}", textposition="outside")
    return fig


def score_trend_pie(df: pd.DataFrame, lang: str = "en") -> go.Figure:
    """Pie chart: distribution of score trends."""
    title = "Score Trend Distribution" if lang == "en" else "توزيع اتجاه الدرجات"
    trend_labels = {
        "improving": "Improving" if lang == "en" else "تحسين",
        "stable": "Stable" if lang == "en" else "مستقر",
        "declining": "Declining" if lang == "en" else "تراجع",
        "insufficient": "Limited Data" if lang == "en" else "بيانات محدودة",
    }
    colors = [MOEI_COLORS["success"], MOEI_COLORS["secondary"], MOEI_COLORS["danger"], MOEI_COLORS["warning"]]
    ct = df["score_trend"].value_counts()
    fig = go.Figure(data=[go.Pie(
        labels=[trend_labels.get(k, k) for k in ct.index],
        values=ct.values,
        marker_colors=colors[:len(ct)],
        hole=0.4,
    )])
    fig.update_layout(title=title, template="plotly_white", height=300, showlegend=True)
    return fig


def training_heatmap(df: pd.DataFrame, top_n: int = 30, lang: str = "en") -> go.Figure:
    """Heatmap: training hours by department and category."""
    title = "Training Hours by Department & Category" if lang == "en" else "ساعات التدريب بالإدارة والفئة"
    agg = (
        df.groupby(["department", "category"])["hours"]
        .sum()
        .reset_index()
    )
    fig = px.density_heatmap(
        agg,
        x="category",
        y="department",
        z="hours",
        title=title,
        color_continuous_scale="Blues",
        labels={"hours": "Hours", "category": "Category"},
    )
    fig.update_layout(template="plotly_white", height=max(400, len(agg["department"].unique()) * 40))
    fig.update_xaxes(tickangle=30)
    return fig


def training_bar(df: pd.DataFrame, top_n: int = 30, lang: str = "en") -> go.Figure:
    """Bar chart: top N employees by training hours. Resilient to missing columns."""
    col = "total_training_hours"
    if col not in df.columns or df[col].dropna().empty:
        fig = go.Figure()
        fig.update_layout(
            title="Training hours data not available" if lang == "en" else "بيانات ساعات التدريب غير متوفرة",
            height=250,
        )
        return fig

    top = df.nlargest(min(top_n, len(df)), col)
    name_col = "full_name" if "full_name" in df.columns else "employee_id"
    dept_col = "department" if "department" in df.columns else None

    title = f"Top {min(top_n, len(top))} Employees by Training Hours" if lang == "en" else f"أعلى {min(top_n, len(top))} موظفًا بساعات التدريب"
    if dept_col and dept_col in top.columns:
        fig = px.bar(
            top,
            x=col,
            y=name_col,
            color=dept_col,
            orientation="h",
            title=title,
            color_discrete_sequence=DEPT_COLORS,
            labels={col: "Hours", name_col: ""},
        )
        fig.update_layout(showlegend=True, template="plotly_white", height=max(400, min(top_n, len(top)) * 28))
    else:
        fig = px.bar(
            top,
            x=col,
            y=name_col,
            orientation="h",
            title=title,
            labels={col: "Hours", name_col: ""},
        )
        fig.update_layout(showlegend=False, template="plotly_white", height=max(400, min(top_n, len(top)) * 28))
    return fig


def leave_balance_hist(df: pd.DataFrame, leave_type: str = "annual", lang: str = "en") -> go.Figure:
    """Histogram of leave balances."""
    col = "annual_leave_balance" if leave_type == "annual" else "sick_leave_balance"
    title = "Annual Leave Balance Distribution" if lang == "en" else "توزيع رصيد الإجازة السنوية"
    color = MOEI_COLORS["secondary"]
    fig = px.histogram(
        df,
        x=col,
        nbins=15,
        title=title,
        color_discrete_sequence=[color],
        labels={col: "Balance (days)", "count": "Employees"},
    )
    fig.update_layout(template="plotly_white", showlegend=False, height=280)
    # Warn zone
    fig.add_vline(x=5, line_color=MOEI_COLORS["danger"], line_dash="dash",
                  annotation_text="Low (<5)" if lang == "en" else "منخفض (<5)")
    return fig


def promotion_readiness_table(df: pd.DataFrame, top_n: int = 20, lang: str = "en") -> go.Figure:
    """Horizontal bar chart: top N promotion-ready employees."""
    top = df.nlargest(top_n, "promotion_readiness_score")[
        ["full_name", "department", "grade", "promotion_readiness_score",
         "avg_score", "total_training_hours", "years_since_promotion"]
    ].dropna(subset=["promotion_readiness_score"])

    fig = px.bar(
        top,
        x="promotion_readiness_score",
        y="full_name",
        orientation="h",
        color="promotion_readiness_score",
        color_continuous_scale="RdYlGn",
        title=f"Top {top_n} Promotion-Ready Employees" if lang == "en" else f"أعلى {top_n} جاهزين للترقية",
        range_color=[0, 100],
        labels={
            "promotion_readiness_score": "Readiness Score",
            "full_name": "",
            "avg_score": "Avg Perf",
            "total_training_hours": "Training Hrs",
            "years_since_promotion": "Yrs Since Promo",
        },
    )
    fig.update_layout(
        showlegend=False,
        template="plotly_white",
        height=max(450, top_n * 28),
    )
    # Add score labels
    fig.update_traces(texttemplate="%{x:.0f}", textposition="outside")
    return fig


def flight_risk_table(df: pd.DataFrame, top_n: int = 20, lang: str = "en") -> go.Figure:
    """Horizontal bar chart: top N flight-risk employees."""
    top = df.nlargest(top_n, "flight_risk_score")[
        ["full_name", "department", "grade", "flight_risk_score",
         "engagement_score", "has_recent_training", "score_trend"]
    ].dropna(subset=["flight_risk_score"])

    fig = px.bar(
        top,
        x="flight_risk_score",
        y="full_name",
        orientation="h",
        color="flight_risk_score",
        color_continuous_scale="RdYlGn_r",   # reversed: high = red
        title=f"Top {top_n} Flight Risk Flagged" if lang == "en" else f"أعلى {top_n} مخاطر المغادرة",
        range_color=[0, 100],
        labels={
            "flight_risk_score": "Risk Score",
            "full_name": "",
            "engagement_score": "Engagement",
            "has_recent_training": "Recent Training",
            "score_trend": "Perf Trend",
        },
    )
    fig.update_layout(
        showlegend=False,
        template="plotly_white",
        height=max(450, top_n * 28),
    )
    fig.update_traces(texttemplate="%{x:.0f}", textposition="outside")
    return fig


def grade_pyramid(df: pd.DataFrame, lang: str = "en") -> go.Figure:
    """Horizontal bar chart: employee count per grade."""
    grp = df.groupby("grade").size().reset_index(name="count")
    grp.columns = ["grade", "count"]
    grp = grp.sort_values("grade")

    title = "Employee Distribution by Grade" if lang == "en" else "توزيع الموظفين حسب الدرجة"
    fig = px.bar(
        grp,
        x="count",
        y="grade",
        orientation="h",
        color="count",
        color_continuous_scale="Blues",
        title=title,
        labels={"grade": "Grade (1=Junior, 9=Leadership)", "count": "Employees"},
    )
    fig.update_layout(
        showlegend=False,
        template="plotly_white",
        height=350,
        yaxis=dict(tickmode="array", tickvals=sorted(df["grade"].dropna().unique())),
    )
    return fig


def leave_by_dept(df: pd.DataFrame, lang: str = "en") -> go.Figure:
    """Grouped bar: avg annual and sick leave balance by department."""
    dept_leave = df.groupby("department")[["annual_leave_balance", "sick_leave_balance"]].mean().reset_index()
    dept_leave = dept_leave.sort_values("annual_leave_balance")
    title = "Avg Leave Balances by Department" if lang == "en" else "متوسط أرصدة الإجازات بالإدارة"

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=dept_leave["department"],
        y=dept_leave["annual_leave_balance"],
        name="Annual" if lang == "en" else "سنوية",
        marker_color=MOEI_COLORS["secondary"],
    ))
    fig.add_trace(go.Bar(
        x=dept_leave["department"],
        y=dept_leave["sick_leave_balance"],
        name="Sick" if lang == "en" else "مرضية",
        marker_color=MOEI_COLORS["accent"],
    ))
    fig.update_layout(
        title=title,
        barmode="group",
        xaxis_title="",
        yaxis_title="Avg Balance (days)",
        template="plotly_white",
        height=350,
    )
    fig.update_xaxes(tickangle=30)
    return fig