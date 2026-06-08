"""
pages/2_Ask_Your_Workforce.py
The killer feature: natural language Q&A over the employee dataset.
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.session import get_master
from ai.workforce_qa import ask_workforce, ask_fallback
from components.bilingual import t, detect_lang
from components.navbar import render as navbar
from components.theme import apply_theme

master = get_master()
lang = st.session_state.lang
apply_theme()
navbar()

st.markdown(f"# 💬 {t('ask_title', lang)}")
st.markdown(t("ask_subtitle", lang))
st.divider()

# ── Example questions ────────────────────────────────────────────────────────
st.caption(t("ask_examples", lang))
examples_en = [
    "Who looks ready for promotion and why?",
    "Who might be a flight risk?",
    "Where do we have a skills gap?",
    "Who has stopped investing in learning?",
    "Which department has the lowest engagement?",
]
examples_ar = [
    "من يبدو جاهزًا للترقية ولماذا؟",
    "من قد يكون عرضة للمغادرة؟",
    "أين لدينا فجوة في المهارات؟",
    "من توقف عن الاستثمار في التعلم؟",
    "أي إدارة لديها أقل انخراط؟",
]
examples = examples_ar if lang == "ar" else examples_en

cols = st.columns(len(examples))
for col, ex in zip(cols, examples):
    with col:
        if st.button(f"💡 {ex[:45]}{'...' if len(ex)>45 else ''}", key=f"ex_{hash(ex)%100000}", use_container_width=True):
            # Sync the trigger and the pending question
            st.session_state["trigger_question"] = ex
            st.session_state["pending_question"] = ex
            st.rerun()

st.divider()

# ── Question input ───────────────────────────────────────────────────────────
# Pop pending suggestion (set by example button) and use as default value
if "pending_question" in st.session_state:
    pending = st.session_state.pop("pending_question")
else:
    pending = ""

question = st.text_area(
    label="Your question",
    value=pending,
    placeholder=t("ask_placeholder_en", lang) if lang == "en" else t("ask_placeholder_ar", lang),
    height=80,
    label_visibility="collapsed",
    key="qa_input",
)
col_btn, col_clear = st.columns([1, 4])
with col_btn:
    ask_clicked = st.button(f"🔍 {t('ask_button', lang)}", type="primary", use_container_width=True)
with col_clear:
    if st.button("🗑 Clear", use_container_width=True):
        for k in ("qa_input", "question", "trigger_question", "last_answer"):
            st.session_state.pop(k, None)
        st.rerun()

st.divider()

# ── Render answer ────────────────────────────────────────────────────────────
def render_answer(answer: dict, lang: str):
    st.markdown("---")
    st.markdown(f"### 📋 {t('answer_summary', lang)}")
    st.info(answer.get("summary", ""))

    conf = answer.get("confidence", "medium")
    conf_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}[conf]
    st.caption(f"{conf_emoji} {t('answer_confidence', lang)}: **{conf}**")

    if answer.get("note"):
        st.warning(f"⚠️ {answer['note']}")

    people = answer.get("people", [])
    if people:
        st.markdown(f"### 👥 {t('answer_people', lang)} ({len(people)} found)")
        for p in people:
            name = p.get('name', 'Unknown')
            eid = p.get('employee_id', '')
            reason = p.get('reason', '')
            action = p.get('action', '')
            score = p.get('score')

            with st.container():
                cols = st.columns([3, 1])
                with cols[0]:
                    st.markdown(f"**{name}** · `{eid}`")
                    st.markdown(f"_{reason}_")
                    if action:
                        st.markdown(f"🎯 **{t('recommended_action', lang)}:** {action}")
                with cols[1]:
                    if score is not None:
                        st.metric("Score", f"{score:.0f}")
                st.divider()
    else:
        st.info("No people matched your question. Try a different query.")


# ── Process question (button click OR suggestion click) ──────────────────────
trigger = st.session_state.pop("trigger_question", None)
to_ask = trigger or (question if ask_clicked else None)

if to_ask:
    lang = detect_lang(to_ask)
    st.session_state.lang = lang
    st.session_state["question"] = to_ask

    with st.spinner(t("thinking", lang)):
        try:
            result = ask_workforce(to_ask, master, lang=lang)
        except Exception as e:
            result = {"error": str(e)}

    st.session_state["last_answer"] = result
    st.rerun()  # rerun so the answer renders fresh

elif ask_clicked and not question:
    st.warning("Please enter a question first." if lang == "en" else "الرجاء إدخال سؤال أولاً")

# ── Display last answer ──────────────────────────────────────────────────────
last = st.session_state.get("last_answer")
if last:
    if "error" in last:
        err = str(last["error"])
        if "OPENROUTER_API_KEY" in err or "not set" in err.lower() or "not found" in err.lower():
            st.warning(t("api_error", lang) + ": " + err)
            fallback = ask_fallback(st.session_state.get("question", ""), master, lang)
            st.markdown(f"**{t('fallback_header', lang)}**")
            st.markdown(fallback)
        else:
            st.error(f"{t('api_error', lang)}: {err}")
    else:
        # Show the question that was answered
        q_answered = st.session_state.get("question", "")
        if q_answered:
            st.caption(f"**Q:** {q_answered}")
        render_answer(last.get("answer", {}), lang)