"""
components/navbar.py
Top navigation bar — renders on every page.
Includes brand, page links, and language toggle.
Persists language to localStorage/query params.
"""

import streamlit as st
from components.bilingual import t

NAV_PAGES = [
    ("📊", "overview_title", "pages/1_Overview.py"),
    ("💬", "ask_title", "pages/2_Ask_Your_Workforce.py"),
    ("📈", "perf_title", "pages/3_Performance.py"),
    ("🎓", "training_title", "pages/4_Training.py"),
    ("🏖️", "leave_title", "pages/5_Leave.py"),
]


def _inject_localstorage():
    """JS to read/write language preference from localStorage."""
    st.components.v1.html("""
    <script>
    (function() {
        // On load: read lang from localStorage and send to Streamlit
        const saved = localStorage.getItem('moei_lang');
        if (saved && (saved === 'en' || saved === 'ar')) {
            // Send via URL query param
            const url = new URL(window.location);
            if (url.searchParams.get('lang') !== saved) {
                url.searchParams.set('lang', saved);
                window.location.search = url.searchParams.toString();
            }
        }
        // Listen for lang changes from Streamlit
        window.addEventListener('message', function(e) {
            if (e.data && e.data.type === 'set_lang') {
                localStorage.setItem('moei_lang', e.data.lang);
            }
        });
    })();
    </script>
    """, height=0)

    st.session_state["_ls_inited"] = 1


def _save_lang_to_storage(lang: str):
    """Send lang to localStorage via postMessage."""
    st.components.v1.html(f"""
    <script>
    localStorage.setItem('moei_lang', '{lang}');
    </script>
    """, height=0)


def init_lang():
    """Initialize language from query params or localStorage."""
    # Check query params first (set by localStorage JS injection)
    query_lang = st.query_params.get("lang")
    if query_lang in ("en", "ar"):
        st.session_state.lang = query_lang
    elif "lang" not in st.session_state:
        st.session_state.lang = "en"

    # Inject localStorage bridge (only once)
    if "_ls_inited" not in st.session_state:
        _inject_localstorage()


def lang_switch():
    """Render language toggle as compact pill buttons."""
    lang = st.session_state.lang
    c1, c2 = st.columns([0.5, 0.5], gap="small")

    with c1:
        en_active = lang == "en"
        if st.button(
            "🇬🇧 EN",
            key="nav_lang_en",
            type="primary" if en_active else "secondary",
            use_container_width=True,
        ):
            if lang != "en":
                st.session_state.lang = "en"
                _save_lang_to_storage("en")
                st.query_params["lang"] = "en"
                st.rerun()

    with c2:
        ar_active = lang == "ar"
        if st.button(
            "🇦🇪 عربي",
            key="nav_lang_ar",
            type="primary" if ar_active else "secondary",
            use_container_width=True,
        ):
            if lang != "ar":
                st.session_state.lang = "ar"
                _save_lang_to_storage("ar")
                st.query_params["lang"] = "ar"
                st.rerun()


def render():
    """Render the full top navbar. Call at the top of every page."""
    lang = st.session_state.lang

    # Lang switch on the far right
    nav_cols = st.columns([0.6, 1.5, 1.5, 1.5, 1.5, 1.5, 2.0])

    with nav_cols[0]:
        st.markdown(
            '<div style="font-size:1.5rem; padding-top:2px;">🏛️</div>',
            unsafe_allow_html=True,
        )

    for i, (icon, label_key, target) in enumerate(NAV_PAGES):
        with nav_cols[i + 1]:
            label = t(label_key, lang)
            st.page_link(target, label=f"{icon}  {label}", use_container_width=True)

    with nav_cols[6]:
        lang_switch()

    st.divider()