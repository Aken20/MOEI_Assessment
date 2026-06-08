"""
ai/kb_search.py
Lightweight keyword search over the HR Knowledge Base PDFs.
Extracts text from EN and AR PDFs, indexes by paragraph,
and returns top-N chunks for a given query.

Uses pymupdf for extraction — no heavy embedding model needed.
"""

import os
import re
from pathlib import Path
from collections import OrderedDict

KB_DIR = Path(__file__).parent.parent / "resources" / "HR_Knowledge_Base"

# Cache: loaded paragraphs indexed once per session
_index: list[dict] = []
_loaded: bool = False


def _extract_text_from_pdf(path: Path) -> str:
    """Extract raw text from a single PDF via pymupdf."""
    try:
        import pymupdf
    except ImportError:
        return ""

    try:
        doc = pymupdf.open(str(path))
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text
    except Exception:
        return ""


def _paragraphs(text: str, min_len: int = 40) -> list[str]:
    """Split text into paragraphs, filtering short/empty ones."""
    chunks = re.split(r"\n{2,}", text)
    return [c.strip() for c in chunks if len(c.strip()) >= min_len]


def load_kb() -> list[dict]:
    """Load and index all PDFs in the KB directory. Returns list of
    {'source': filename, 'lang': 'en'|'ar', 'text': paragraph}."""
    global _index, _loaded
    if _loaded:
        return _index

    records = []
    for fpath in sorted(KB_DIR.glob("*.pdf")):
        lang = "ar" if fpath.stem.startswith("AR-") or fpath.stem.endswith("AR") else "en"
        text = _extract_text_from_pdf(fpath)
        for para in _paragraphs(text):
            records.append({
                "source": fpath.stem,
                "lang": lang,
                "text": para,
            })

    _index = records
    _loaded = True
    return _index


def search_kb(query: str, top_n: int = 3, lang: str = "en") -> list[dict]:
    """Keyword search: return top-N paragraphs containing any query term."""
    records = load_kb()

    # Filter by language
    lang_records = [r for r in records if r["lang"] == lang]
    if len(lang_records) < top_n:
        lang_records = [r for r in records if r["lang"] == ("ar" if lang == "en" else "en")]
        if len(lang_records) < top_n:
            lang_records = records  # fallback to all

    # Simple TF scoring
    terms = [t.lower() for t in re.split(r"\s+", query) if len(t) > 2]
    if not terms:
        return lang_records[:top_n]

    scored = []
    for r in lang_records:
        text_lower = r["text"].lower()
        score = sum(text_lower.count(t) for t in terms)
        if score > 0:
            scored.append((score, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored[:top_n]]


def kb_context(query: str, lang: str = "en", top_n: int = 3) -> str:
    """Return a formatted KB context string for injection into a prompt."""
    results = search_kb(query, top_n, lang)
    if not results:
        return ""

    lines = ["--- HR Knowledge Base excerpts ---"]
    for i, r in enumerate(results, 1):
        lines.append(f"  [{i}] ({r['source']}) {r['text'][:600]}")
    lines.append("--- end KB excerpts ---")
    return "\n".join(lines)