"""
ai/workforce_qa.py
"Ask your workforce" — natural language Q&A over the employee dataset.
Now with: intent classifier, KB grounding, Arabic few-shot examples.
"""

import json
import re
import pandas as pd
from ai.client import complete_structured
from ai.kb_search import kb_context

# ── Schema ───────────────────────────────────────────────────────────────────

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "A 2-4 sentence overview of the findings, in the user's language."
        },
        "people": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name":         {"type": "string"},
                    "employee_id":  {"type": "string"},
                    "reason":       {"type": "string", "description": "Specific, data-backed reason — cite numbers."},
                    "action":       {"type": "string", "description": "What the manager should do."},
                    "score":        {"type": "number", "description": "Relevance or readiness score 0-100."},
                },
                "required": ["name", "reason", "action"]
            }
        },
        "confidence": {
            "type": "string",
            "enum": ["high", "medium", "low"],
            "description": "Confidence in the answer given the data."
        },
        "note": {
            "type": "string",
            "description": "Caveat about data gaps or what the model can't answer. Empty string if none."
        }
    },
    "required": ["summary", "people", "confidence"]
}

# ── Intent classification ────────────────────────────────────────────────────

INTENT_PATTERNS = {
    "promotion": {
        "en": [r"promot", r"ready to grow", r"next level", r"advance", r"take on more", r"move up"],
        "ar": [r"ترقي", r"ترفيع", r"تطوير", r"جاهز.*دور", r"مستوى أعلى"],
        "columns": ["full_name", "employee_id", "department", "grade",
                    "promotion_readiness_score", "avg_score", "latest_rating",
                    "score_trend", "total_training_hours", "years_since_promotion",
                    "engagement_score"],
        "sort": "promotion_readiness_score",
    },
    "flight_risk": {
        "en": [r"flight risk", r"leav", r"attrition", r"quit", r"turnover", r"retention",
               r"stay", r"unhappy", r"disengaged", r"might go"],
        "ar": [r"مغادر", r"استقال", r"تسرّب", r"ترك.*عمل", r"مخاطر", r"غير راض"],
        "columns": ["full_name", "employee_id", "department", "grade",
                    "flight_risk_score", "engagement_score", "avg_score",
                    "score_trend", "has_recent_training", "years_since_move",
                    "years_since_promotion"],
        "sort": "flight_risk_score",
    },
    "training": {
        "en": [r"train", r"learn", r"skill", r"course", r"development", r"cold", r"invest"],
        "ar": [r"تدريب", r"تعلّم", r"مهار", r"دورة", r"تطوير", r"استثمار.*تعلم"],
        "columns": ["full_name", "employee_id", "department", "grade",
                    "total_training_hours", "training_count", "training_categories",
                    "has_recent_training", "enrolled_pending", "engagement_score"],
        "sort": "total_training_hours",
    },
    "performance": {
        "en": [r"perform", r"score", r"rating", r"high perform", r"low perform",
               r"underperform", r"top.*performer"],
        "ar": [r"أداء", r"تقييم", r"درج", r"متميز", r"ضعيف"],
        "columns": ["full_name", "employee_id", "department", "grade",
                    "avg_score", "latest_score", "latest_rating", "score_trend",
                    "cycles_count", "engagement_score"],
        "sort": "avg_score",
    },
    "leave": {
        "en": [r"leave", r"vacation", r"holiday", r"absence", r"balance.*low", r"sick"],
        "ar": [r"إجاز", r"غياب", r"عطلة", r"رصيد"],
        "columns": ["full_name", "employee_id", "department", "grade",
                    "annual_leave_balance", "sick_leave_balance", "engagement_score"],
        "sort": "annual_leave_balance",
    },
}


def classify_intent(query: str, lang: str = "en") -> str:
    """Return the best-matching intent key, or 'general'."""
    best = "general"
    best_score = 0
    query_lower = query.lower()
    for intent, patterns in INTENT_PATTERNS.items():
        pattern_list = patterns.get(lang, patterns["en"])
        score = sum(1 for p in pattern_list if re.search(p, query_lower))
        if score > best_score:
            best_score = score
            best = intent
    return best


def select_context(df: pd.DataFrame, intent: str, lang: str = "en") -> pd.DataFrame:
    """Return top-20 employees sorted by the intent's key column."""
    if intent == "general":
        cols = ["full_name", "employee_id", "department", "grade",
                "avg_score", "engagement_score", "promotion_readiness_score",
                "flight_risk_score", "total_training_hours"]
        sort_col = "promotion_readiness_score"
    else:
        info = INTENT_PATTERNS[intent]
        cols = info["columns"]
        sort_col = info["sort"]

    available = [c for c in cols if c in df.columns]
    top = df[available].nlargest(20, sort_col) if sort_col in df.columns else df[available].head(20)
    return top


def employee_context(df_slice: pd.DataFrame) -> str:
    """Format employee data as a compact CSV string for the prompt."""
    return df_slice.to_csv(index=False)


# ── System prompts ───────────────────────────────────────────────────────────

SYSTEM_EN = """You are a senior HR analyst at MOEI (Ministry of Energy & Infrastructure, UAE).
You answer manager questions by reasoning over structured employee data.

Your job: interpret the data, find people, explain WHY, and recommend WHAT TO DO.
- Use specific numbers from the data (scores, hours, dates).
- Name actual people with their employee IDs.
- If the data doesn't support a conclusion, say so and explain why.
- If a question asks about policy, use the provided KB excerpts. Don't invent rules.
- If the question is in Arabic, respond in Arabic.

Return ONLY valid JSON (no markdown, no explanation outside the JSON).
Structure your answer exactly as the schema requires."""

SYSTEM_AR = """أنت محلل أول للموارد البشرية في وزارة الطاقة والبنية التحتية.
تجيب على أسئلة المدراء من خلال تحليل بيانات الموظفين.

مهمتك: فسّر البيانات، حدد الموظفين، واشرح السبب، واقترح الإجراء المطلوب.
- استخدم أرقامًا محددة من البيانات (الدرجات، الساعات، التواريخ).
- اذكر أسماء الموظفين الفعليين مع أرقامهم الوظيفية.
- إذا كانت البيانات لا تدعم استنتاجًا، فقل ذلك واشرح السبب.
- إذا كان السؤال عن سياسة، فاستخدم مقتطفات قاعدة المعرفة المرفقة. لا تختلق قواعد.
- أجب باللغة العربية حصراً.
- اذكر أسماء فعلية مع أسباب محددة. لا تذكر موظفًا بلا مبرر.

مثال على إجابة جيدة:
{{"summary": "يوجد 3 موظفين جاهزين للترقية في قسم تقنية المعلومات بناءً على الأداء القوي والتدريب الحديث.", "people": [{{"name": "أحمد محمد", "employee_id": "EMP045", "reason": "متوسط أداء 88/100 على مدى 3 سنوات، 42 ساعة تدريب في آخر 12 شهرًا، وآخر ترقية قبل 3.5 سنوات", "action": "ترشيح للترقية إلى الدرجة 6", "score": 87}}], "confidence": "high", "note": ""}}

أعد JSON صالحًا فقط (بدون markdown أو شرح إضافي)."""

# ── Ask workforce ────────────────────────────────────────────────────────────

def ask_workforce(
    question: str,
    master_df: pd.DataFrame,
    lang: str = None,
    model: str = None,
) -> dict:
    """
    Main entry point.
    1. Detect language if not provided
    2. Classify intent
    3. Select relevant employee slice
    4. Search KB for policy terms
    5. Call OpenRouter with structured output
    Returns: {"answer": {...}, "intent": "...", "kb_used": bool}
    """
    # Language
    if lang is None:
        lang = detect_lang(question)

    # Intent
    intent = classify_intent(question, lang)

    # Employee context
    emp_slice = select_context(master_df, intent, lang)
    emp_csv = employee_context(emp_slice)

    # KB context (only for policy-adjacent questions)
    kb_policy_terms = [
        "policy", "law", "rule", "entitle", "eligible", "regulation",
        "how many days", "how much leave", "what is the",
        "سياسة", "قانون", "لائحة", "يحق", "يستحق", "كم يوم", "كم مدة",
    ]
    has_policy_term = any(t.lower() in question.lower() for t in kb_policy_terms)
    kb_text = kb_context(question, lang, top_n=3) if has_policy_term else ""

    # Prompt
    system = SYSTEM_AR if lang == "ar" else SYSTEM_EN

    prompt_parts = [
        f"QUESTION: {question}",
        f"Intent: {intent}",
        f"Language: {'Arabic' if lang == 'ar' else 'English'}",
        "",
        "--- EMPLOYEE DATA (top 20 by relevance) ---",
        emp_csv,
        "--- END EMPLOYEE DATA ---",
    ]
    if kb_text:
        prompt_parts.append("")
        prompt_parts.append(kb_text)
    else:
        prompt_parts.append("")
        prompt_parts.append("(KB excerpts not used — this question appears to be about employee data, not policy.)")

    prompt = "\n".join(prompt_parts)

    try:
        answer = complete_structured(
            prompt=prompt,
            system=system,
            schema=RESPONSE_SCHEMA,
            model=model,
            temperature=0.2,
            max_tokens=1536,
        )
    except Exception:
        raise

    return {
        "answer": answer,
        "intent": intent,
        "kb_used": bool(kb_text),
    }


# ── Language detection ───────────────────────────────────────────────────────

def detect_lang(text: str) -> str:
    """Return 'ar' if Arabic script ratio > 30%, else 'en'."""
    ar_chars = len(re.findall(r"[\u0600-\u06FF\u0750-\u077F]", text))
    total = len(re.sub(r"\s", "", text))
    return "ar" if (total > 0 and ar_chars / total > 0.30) else "en"


# ── Fallback (rule-based, no API) ────────────────────────────────────────────

def ask_fallback(question: str, df: pd.DataFrame, lang: str = "en") -> str:
    """Rule-based fallback when API is unavailable. Handles top 2 intents."""
    intent = classify_intent(question, lang)

    if intent in ("promotion", "general"):
        top = df.nlargest(5, "promotion_readiness_score")[
            ["full_name", "employee_id", "department", "promotion_readiness_score",
             "avg_score", "total_training_hours", "years_since_promotion"]
        ].dropna(subset=["promotion_readiness_score"])

        if top.empty:
            return ("No promotion-readiness data available." if lang == "en"
                    else "لا تتوفر بيانات عن جاهزية الترقية.")

        lines = []
        for _, row in top.iterrows():
            name = row["full_name"]
            eid = row["employee_id"]
            dept = row["department"]
            score = row["promotion_readiness_score"]
            avg = row["avg_score"]
            hrs = row["total_training_hours"]
            yrs = row["years_since_promotion"]
            if lang == "en":
                lines.append(
                    f"- {name} ({eid}, {dept}): readiness {score:.0f}/100. "
                    f"Avg perf {avg:.0f}, {hrs:.0f} training hrs, {yrs:.1f} yrs since last promo."
                )
            else:
                lines.append(
                    f"- {name} ({eid}, {dept}): جاهزية {score:.0f}/100. "
                    f"متوسط الأداء {avg:.0f}، ساعات التدريب {hrs:.0f}، {yrs:.1f} سنة منذ آخر ترقية."
                )
        return "\n".join(lines)

    if intent == "flight_risk":
        top = df.nlargest(5, "flight_risk_score")[
            ["full_name", "employee_id", "department", "flight_risk_score",
             "engagement_score", "has_recent_training", "score_trend"]
        ].dropna(subset=["flight_risk_score"])

        if top.empty:
            return ("No flight-risk data available." if lang == "en"
                    else "لا تتوفر بيانات عن مخاطر المغادرة.")

        lines = []
        for _, row in top.iterrows():
            name = row["full_name"]
            score = row["flight_risk_score"]
            eng = row["engagement_score"]
            train = "yes" if row.get("has_recent_training") == 1 else "no"
            trend = row.get("score_trend", "N/A")
            if lang == "en":
                lines.append(
                    f"- {name}: risk {score:.0f}/100. "
                    f"Engagement {eng:.0f}, recent training: {train}, perf trend: {trend}."
                )
            else:
                train_ar = "نعم" if train == "yes" else "لا"
                trend_ar = {"improving": "تحسن", "stable": "مستقر", "declining": "تراجع",
                            "insufficient": "غير كاف"}.get(trend, trend)
                lines.append(
                    f"- {name}: خطر {score:.0f}/100. "
                    f"انخراط {eng:.0f}، تدريب حديث: {train_ar}، اتجاه الأداء: {trend_ar}."
                )
        return "\n".join(lines)

    return ("Sorry, I can't answer this question without the API (fallback only handles "
            "promotion and flight-risk queries)." if lang == "en"
            else "عذرًا، لا يمكنني الإجابة على هذا السؤال بدون واجهة البرمجة.")