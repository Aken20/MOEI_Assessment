"""
components/bilingual.py
Bilingual (EN/AR) text helper.
All user-facing strings go through this module.
Streamlit session_state['lang'] drives which language is active.
"""

# ---------------------------------------------------------------------------
# All UI strings — English and Arabic pairs
# ---------------------------------------------------------------------------

STRINGS = {
    # App shell
    "app_title": {"en": "MOEI HR Companion", "ar": "الرفيق الوظيفي - وزارة الطاقة والبنية التحتية"},
    "app_subtitle": {"en": "Management View — Workforce Intelligence", "ar": "عرض الإدارة — ذكاء القوى العاملة"},
    "lang_toggle_label": {"en": "Language", "ar": "اللغة"},
    "sidebar_title": {"en": "Navigation", "ar": "التنقل"},
    "data_note": {"en": "Data as of 1 June 2026 · ~260 employees", "ar": "البيانات كما في 1 يونيو 2026 · حوالي 260 موظفًا"},

    # Overview page
    "overview_title": {"en": "Workforce Overview", "ar": "نظرة عامة على القوى العاملة"},
    "total_employees": {"en": "Total Employees", "ar": "إجمالي الموظفين"},
    "avg_engagement": {"en": "Avg Engagement Score", "ar": "متوسط نقاط الانخراط"},
    "avg_performance": {"en": "Avg Performance Score", "ar": "متوسط تقييم الأداء"},
    "nationals": {"en": "UAE Nationals", "ar": "المواطنون"},
    "dept_headcount": {"en": "Headcount by Department", "ar": "عدد الموظفين بالإدارة"},
    "engagement_dist": {"en": "Engagement Distribution", "ar": "توزيع الانخراط"},
    "grade_dist": {"en": "Distribution by Grade", "ar": "التوزيع حسب الدرجة"},

    # Ask workforce page
    "ask_title": {"en": "Ask Your Workforce", "ar": "اسأل القوى العاملة"},
    "ask_subtitle": {"en": "Ask anything about your people in plain language. I reason over the data.", "ar": "اسأل أي شيء عن موظفيك بلغة بسيطة. أستدل على البيانات."},
    "ask_placeholder_en": {"en": 'e.g. "Who looks ready for promotion and why?"', "ar": 'e.g. "Who looks ready for promotion and why?"'},
    "ask_placeholder_ar": {"en": 'e.g. "Who looks ready for promotion and why?"', "ar": 'مثال: "من يبدو جاهزًا للترقية ولماذا؟"'},
    "ask_button": {"en": "Ask", "ar": "اسأل"},
    "ask_examples": {"en": "Try:", "ar": "جرّب:"},
    "ask_example_1": {"en": '"Who looks ready for promotion?"', "ar": '"من يبدو جاهزًا للترقية؟"'},
    "ask_example_2": {"en": '"Who might be a flight risk?"', "ar": '"من قد يكون عرضة للمغادرة؟"'},
    "ask_example_3": {"en": '"Where do we have a skills gap?"', "ar": '"أين لدينا فجوة في المهارات؟"'},
    "ask_example_4": {"en": '"Who has stopped investing in learning?"', "ar": '"من توقف عن الاستثمار في التعلم؟"'},
    "answer_summary": {"en": "Summary", "ar": "ملخص"},
    "answer_people": {"en": "People", "ar": "الأشخاص"},
    "answer_confidence": {"en": "Confidence", "ar": "الثقة"},
    "answer_note": {"en": "Note", "ar": "ملاحظة"},
    "recommended_action": {"en": "Recommended Action", "ar": "الإجراء المقترح"},
    "no_answer": {"en": "No answer available. Check your OpenRouter API key.", "ar": "لا تتوفر إجابة. تحقق من مفتاح OpenRouter API."},
    "thinking": {"en": "Thinking...", "ar": "جارٍ التحليل..."},
    "api_error": {"en": "API Error", "ar": "خطأ في واجهة برمجة التطبيقات"},
    "fallback_header": {"en": "Fallback Result (API unavailable)", "ar": "النتيجة الاحتياطية (الواجهة غير متوفرة)"},

    # Performance page
    "perf_title": {"en": "Performance & Promotion Readiness", "ar": "الأداء وجاهزية الترقية"},
    "promotion_readiness": {"en": "Promotion Readiness Score", "ar": "درجة جاهزية الترقية"},
    "perf_by_dept": {"en": "Average Score by Department", "ar": "متوسط الدرجة بالإدارة"},
    "score_trend": {"en": "Score Trend Distribution", "ar": "توزيع اتجاه الدرجات"},
    "top_ready": {"en": "Top Ready for Promotion", "ar": "الأعلى جاهزية للترقية"},
    "dept_filter": {"en": "Filter by Department", "ar": "تصفية حسب الإدارة"},
    "export_csv": {"en": "Export CSV", "ar": "تصدير CSV"},

    # Training page
    "training_title": {"en": "Learning & Development", "ar": "التعلم والتطوير"},
    "learning_investment": {"en": "Learning Investment by Employee", "ar": "استثمار التعلم لكل موظف"},
    "training_by_category": {"en": "Hours by Category", "ar": "الساعات حسب الفئة"},
    "recent_training": {"en": "Recent Training (< 12 months)", "ar": "التدريب recent (< 12 شهرًا)"},
    "training_cold": {"en": "Employees with No Recent Training", "ar": "الموظفون بدون تدريب حديث"},
    "training_enrolled": {"en": "Enrolled — Not Yet Started", "ar": "مسجّل — لم يبدأ بعد"},
    "training_hrs": {"en": "Training Hours", "ar": "ساعات التدريب"},

    # Leave page
    "leave_title": {"en": "Leave Balances", "ar": "رصيد الإجازات"},
    "annual_balance": {"en": "Annual Leave Balance", "ar": "رصيد الإجازة السنوية"},
    "sick_balance": {"en": "Sick Leave Balance", "ar": "رصيد إجازة المرض"},
    "low_leave": {"en": "Low Leave Warning (< 5 days)", "ar": "تحذير انخفاض الإجازة (< 5 أيام)"},
    "leave_by_dept": {"en": "Average Leave Balance by Department", "ar": "متوسط رصيد الإجازة بالإدارة"},

    # General
    "loading": {"en": "Loading...", "ar": "جارٍ التحميل..."},
    "no_data": {"en": "No data available", "ar": "لا تتوفر بيانات"},
    "employee_id": {"en": "Employee ID", "ar": "الرقم الوظيفي"},
    "department": {"en": "Department", "ar": "الإدارة"},
    "score": {"en": "Score", "ar": "الدرجة"},
    "grade": {"en": "Grade", "ar": "الدرجة الوظيفية"},
    "risk": {"en": "Risk", "ar": "المخاطر"},

    # AI Interpretation (Performance page)
    "ai_interpret": {"en": "AI Interpretation", "ar": "تحليل الذكاء الاصطناعي"},
    "ai_custom": {"en": "Ask a custom question", "ar": "اطرح سؤالاً مخصصاً"},
    "clear": {"en": "Clear answer", "ar": "مسح الإجابة"},
}


def t(key: str, lang: str = "en") -> str:
    """Return the string for the given key and language."""
    lang = lang if lang in ("en", "ar") else "en"
    return STRINGS.get(key, {}).get(lang, STRINGS.get(key, {}).get("en", key))


def detect_lang(text: str) -> str:
    """Detect whether text is Arabic or English."""
    import re
    if not text:
        return "en"
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    return "ar" if arabic_chars / max(len(text), 1) > 0.3 else "en"


def set_lang(st):
    """Initialize language radio in sidebar. Call at start of app.py."""
    import streamlit as st
    st.session_state.setdefault("lang", "en")


def lang_toggle(st):
    """Render language toggle. Call in sidebar."""
    import streamlit as st
    st.session_state.lang = st.radio(
        t("lang_toggle_label"),
        options=["en", "ar"],
        format_func=lambda x: "English" if x == "en" else "العربية",
        horizontal=True,
        key="lang_toggle",
    )