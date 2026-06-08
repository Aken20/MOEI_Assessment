"""
data/metrics.py
Derived metrics computed from the raw sheets.
Nothing is pre-computed in the dataset — we derive it here.
"""

from datetime import date
import pandas as pd
import numpy as np

AS_OF_DATE = date(2026, 6, 1)


# ---------------------------------------------------------------------------
# Per-employee summaries
# ---------------------------------------------------------------------------

def perf_summary(perf_df: pd.DataFrame) -> pd.DataFrame:
    """
    For each employee compute:
    - cycles_count       : how many performance cycles they have
    - avg_score           : mean score across all cycles
    - latest_score        : most recent cycle score
    - latest_year         : most recent cycle year
    - latest_rating       : rating_band of most recent cycle
    - score_trend         : 'improving', 'stable', 'declining', 'insufficient'
    - score_change        : latest - earliest (signed)
    """
    latest = perf_df.sort_values("cycle_year").groupby("employee_id").last().reset_index()
    latest = latest.rename(columns={"score": "latest_score", "rating_band": "latest_rating",
                                     "cycle_year": "latest_year"})

    avg = perf_df.groupby("employee_id")["score"].mean().reset_index()
    avg.columns = ["employee_id", "avg_score"]

    count = perf_df.groupby("employee_id")["cycle_year"].count().reset_index()
    count.columns = ["employee_id", "cycles_count"]

    def compute_trend(grp):
        years = grp.sort_values("cycle_year")["score"].tolist()
        if len(years) < 2:
            return "insufficient"
        if years[-1] > years[0] + 5:
            return "improving"
        elif years[-1] < years[0] - 5:
            return "declining"
        else:
            return "stable"

    trend = perf_df.groupby("employee_id").apply(compute_trend).reset_index()
    trend.columns = ["employee_id", "score_trend"]

    score_change = (
        perf_df.sort_values(["employee_id", "cycle_year"])
        .groupby("employee_id")["score"]
        .agg(lambda x: x.iloc[-1] - x.iloc[0])
        .reset_index()
    )
    score_change.columns = ["employee_id", "score_change"]

    result = latest[["employee_id", "latest_score", "latest_year", "latest_rating"]].copy()
    result = result.merge(avg, on="employee_id", how="left")
    result = result.merge(count, on="employee_id", how="left")
    result = result.merge(trend, on="employee_id", how="left")
    result = result.merge(score_change, on="employee_id", how="left")
    return result


def training_summary(train_df: pd.DataFrame, as_of: date = AS_OF_DATE) -> pd.DataFrame:
    """
    For each employee compute:
    - total_training_hours     : sum hours of Completed + In Progress (no Enrolled)
    - training_count           : number of such records
    - last_training_date       : most recent completion date
    - training_categories_set  : distinct categories completed
    - has_recent_training      : 1 if last training within 12 months, else 0
    - enrolled_pending         : count of Enrolled courses (planned but not started)
    """
    active = train_df[train_df["status"].isin(["Completed", "In Progress"])].copy()
    enrolled = train_df[train_df["status"] == "Enrolled"].copy()

    hours_sum = active.groupby("employee_id")["hours"].sum().reset_index()
    hours_sum.columns = ["employee_id", "total_training_hours"]

    count = active.groupby("employee_id")["record_id"].count().reset_index()
    count.columns = ["employee_id", "training_count"]

    last_date = (
        active.sort_values("completion_date", na_position="last")
        .groupby("employee_id")["completion_date"]
        .last()
        .reset_index()
    )
    last_date.columns = ["employee_id", "last_training_date"]

    def recent_flag(dates):
        if dates is None or dates.dropna().empty:
            return 0
        d = dates.dropna().max()
        if d is None:
            return 0
        return 1 if (as_of - d).days <= 365 else 0

    recent = active.groupby("employee_id")["completion_date"].apply(recent_flag).reset_index()
    recent.columns = ["employee_id", "has_recent_training"]

    pending = enrolled.groupby("employee_id")["record_id"].count().reset_index()
    pending.columns = ["employee_id", "enrolled_pending"]

    cats = (
        active.dropna(subset=["category"])
        .groupby("employee_id")["category"]
        .apply(lambda x: ", ".join(sorted(set(x))))
        .reset_index()
    )
    cats.columns = ["employee_id", "training_categories"]

    result = hours_sum.merge(count, on="employee_id", how="left")
    result = result.merge(last_date, on="employee_id", how="left")
    result = result.merge(recent, on="employee_id", how="left")
    result = result.merge(pending, on="employee_id", how="left")
    result = result.merge(cats, on="employee_id", how="left")
    return result


def movement_summary(move_df: pd.DataFrame, as_of: date = AS_OF_DATE) -> pd.DataFrame:
    """
    For each employee compute:
    - promotion_count  : number of Promotion events
    - transfer_count    : number of Transfer events
    - last_movement_date: most recent movement effective_date
    - years_since_move  : years since last movement
    """
    promos = move_df[move_df["event_type"] == "Promotion"].groupby("employee_id")["record_id"].count().reset_index()
    promos.columns = ["employee_id", "promotion_count"]

    transfers = move_df[move_df["event_type"] == "Transfer"].groupby("employee_id")["record_id"].count().reset_index()
    transfers.columns = ["employee_id", "transfer_count"]

    last_move = (
        move_df.sort_values("effective_date", na_position="last")
        .groupby("employee_id")["effective_date"]
        .last()
        .reset_index()
    )
    last_move.columns = ["employee_id", "last_movement_date"]

    result = promos.merge(transfers, on="employee_id", how="outer")
    result = result.merge(last_move, on="employee_id", how="outer")
    result["promotion_count"] = result["promotion_count"].fillna(0).astype(int)
    result["transfer_count"] = result["transfer_count"].fillna(0).astype(int)
    return result


def leave_summary(leave_df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot leave so each employee has Annual and Sick balance_days side by side.
    """
    piv = leave_df.pivot_table(index="employee_id", columns="leave_type", values="balance_days", aggfunc="sum").reset_index()
    piv.columns.name = None
    # Rename to avoid spaces
    piv = piv.rename(columns={"Annual": "annual_leave_balance", "Sick": "sick_leave_balance"})
    return piv


# ---------------------------------------------------------------------------
# Core derived scores
# ---------------------------------------------------------------------------

def promotion_readiness_score(
    emp: pd.Series,
    perf: pd.DataFrame,
    train: pd.DataFrame,
    move: pd.DataFrame,
) -> pd.Series:
    """
    Returns a DataFrame with employee_id and promotion_readiness_score (0–100).
    Components:
      - avg_score (35%): higher is better, normalized to 0–100
      - learning_investment (25%): percentile rank of total_training_hours, 0–100
      - stagnation_penalty (25%): years since last move; 0 if recent, penalty if stale
      - engagement (15%): directly from engagement_score, 0–100
    """
    # Merge performance summary
    ps = perf_summary(perf)
    ts = training_summary(train)
    ms = movement_summary(move)

    df = emp[["employee_id", "engagement_score", "grade"]].copy()
    df = df.merge(ps[["employee_id", "avg_score"]], on="employee_id", how="left")
    df = df.merge(ts[["employee_id", "total_training_hours"]], on="employee_id", how="left")
    df = df.merge(ms[["employee_id", "last_movement_date"]], on="employee_id", how="left")

    # Normalize avg_score to 0–100 (score is already 0–100)
    df["avg_score_norm"] = df["avg_score"].fillna(50)

    # Percentile rank of training hours (0–100)
    df["training_hours_rank"] = df["total_training_hours"].rank(pct=True, na_option="keep") * 100

    # Years since last movement
    df["years_since_move"] = df["last_movement_date"].apply(
        lambda d: (AS_OF_DATE - d).days / 365.25 if d else 999
    )
    # stagnation: 0 if <1yr, grows after; cap at ~5yr+ = max penalty
    df["stagnation_score"] = df["years_since_move"].apply(
        lambda y: max(0, 100 - (y * 20)) if y < 999 else 20
    )

    # Grade factor: grade 8–9 (leadership) already senior → lower readiness score
    df["grade_factor"] = df["grade"].apply(lambda g: 60 if g >= 8 else 100)

    df["promotion_readiness_score"] = (
        df["avg_score_norm"] * 0.35
        + df["training_hours_rank"] * 0.25
        + df["stagnation_score"] * 0.25
        + df["engagement_score"].fillna(50) * 0.15
    ).clip(0, 100)

    return df[["employee_id", "promotion_readiness_score", "avg_score_norm",
               "training_hours_rank", "stagnation_score", "years_since_move",
               "total_training_hours"]]


def flight_risk_score(
    emp: pd.DataFrame,
    perf: pd.DataFrame,
    train: pd.DataFrame,
    move: pd.DataFrame,
) -> pd.Series:
    """
    Returns a DataFrame with employee_id and flight_risk_score (0–100).
    Components:
      - engagement_risk (30%): engagement < 60 = flag, < 45 = high flag
      - performance_decline (30%): declining trend or low avg score
      - learning_cold (40%): no training in 12 months
    """
    ps = perf_summary(perf)
    ts = training_summary(train)
    ms = movement_summary(move)

    df = emp[["employee_id", "engagement_score"]].copy()
    df = df.merge(ps[["employee_id", "avg_score", "score_trend"]], on="employee_id", how="left")
    df = df.merge(ts[["employee_id", "has_recent_training", "total_training_hours"]], on="employee_id", how="left")

    # Engagement risk: 0–100, high engagement = low risk
    df["engagement_risk"] = df["engagement_score"].apply(
        lambda s: 100 if s < 40 else (70 if s < 55 else (30 if s < 70 else 0))
    )

    # Performance risk
    def perf_risk(row):
        if row["score_trend"] == "insufficient":
            return 50  # uncertain — mid
        if row["score_trend"] == "declining":
            return 80
        if pd.isna(row["avg_score"]) or row["avg_score"] < 55:
            return 70
        if row["avg_score"] < 65:
            return 30
        return 10

    df["performance_risk"] = df.apply(perf_risk, axis=1)

    # Learning cold risk
    df["learning_risk"] = df["has_recent_training"].apply(
        lambda r: 90 if r == 0 else 10
    )

    df["flight_risk_score"] = (
        df["engagement_risk"] * 0.30
        + df["performance_risk"] * 0.30
        + df["learning_risk"] * 0.40
    ).clip(0, 100)

    return df[["employee_id", "flight_risk_score", "engagement_risk",
               "performance_risk", "learning_risk"]]


# ---------------------------------------------------------------------------
# Master employee view
# ---------------------------------------------------------------------------

def build_employee_master(emp_df, perf_df, train_df, move_df, leave_df):
    """Merge all summaries into one wide employee dataframe."""

    ps = perf_summary(perf_df)
    ts = training_summary(train_df)
    ms = movement_summary(move_df)
    lv = leave_summary(leave_df)
    pr = promotion_readiness_score(emp_df, perf_df, train_df, move_df)
    fr = flight_risk_score(emp_df, perf_df, train_df, move_df)

    df = emp_df.copy()
    df["tenure_years"] = df["hire_date"].apply(
        lambda d: round((AS_OF_DATE - d).days / 365.25, 1) if d else None
    )
    df["years_since_promotion"] = df["last_promotion_date"].apply(
        lambda d: round((AS_OF_DATE - d).days / 365.25, 1) if d else None
    )

    df = df.merge(ps, on="employee_id", how="left")
    df = df.merge(ts, on="employee_id", how="left")
    df = df.merge(ms, on="employee_id", how="left")
    df = df.merge(lv, on="employee_id", how="left")
    df = df.merge(pr, on="employee_id", how="left", suffixes=("", "_pr"))
    df = df.merge(fr, on="employee_id", how="left", suffixes=("", "_fr"))

    # Clean up column collisions from multiple merges of the same source
    for dup_col in ["total_training_hours", "has_recent_training", "enrolled_pending",
                    "training_count", "last_training_date", "training_categories",
                    "avg_score", "latest_score", "latest_rating", "score_trend",
                    "engagement_score", "flight_risk_score"]:
        suffix_col = dup_col + "_pr"
        if suffix_col in df.columns:
            df.drop(columns=[suffix_col], inplace=True)
        suffix_col = dup_col + "_fr"
        if suffix_col in df.columns:
            df.drop(columns=[suffix_col], inplace=True)

    return df