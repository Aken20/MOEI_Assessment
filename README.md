# MOEI HR Companion — Door B: Management View

> An HR intelligence dashboard for managers. Ask questions about your workforce in plain language — the AI reasons over employee data and returns named people with specific reasons and recommended actions.

---

## What It Does

**Door B — The Management View**

The dashboard turns raw employee data (~260 employees, 5 data sheets) into insight a manager can act on.

**Five pages:**

1. **Overview** — KPIs (headcount, avg engagement, avg performance, UAE nationals %), department headcount bar chart, engagement distribution histogram, engagement by department box plots, grade pyramid.
2. **Ask Your Workforce** *(the killer feature)* — Type a question in plain language. The AI reasons over the employee dataset and returns named people with:
   - Specific reasons (numbers, trends, patterns)
   - A recommended action for the manager
   - A confidence level and data caveats
3. **Performance & Promotion Readiness** — Promotion-readiness score table (top 20), flight-risk table (top 20), score trend distribution, performance vs engagement scatter, performance by department.
4. **Training** — Learning investment bar chart (top 25), hours by category, training heatmap (dept × category), employees with no recent training (cold list).
5. **Leave** — Annual and sick leave balance histograms, avg leave by department, low-balance warning table.

---

## How to Run

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd moei_assessment

# 2. Copy the data file from the assessment package
#    (not committed — resources/ is in .gitignore)
cp /path/to/assessment/package/resources/ .

# 3. Set up environment
cp .env.example .env
# Edit .env and replace with your real OpenRouter key

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run
streamlit run app.py
```

The app runs at `http://localhost:8501`.

**Environment variables:**
- `OPENROUTER_API_KEY` — your OpenRouter API key (required for AI Q&A)
- `OPENROUTER_MODEL` — optional, defaults to `deepseek/deepseek-v4-pro`

---

## Model Choice

**`deepseek/deepseek-v4-pro`** via OpenRouter.

Why: DeepSeek V4 Pro excels at structured reasoning over tabular data — it reliably follows JSON schemas, maintains consistent formatting, and produces nuanced natural-language analysis from numeric inputs. It's a strong model at a competitive price point on OpenRouter for this multi-step interpretation task.

**Local-deployment option:** DeepSeek models are open-weight and can be self-hosted with Ollama, vLLM, or llama.cpp, which is a real advantage for production HR systems dealing with sensitive employee data. A local DeepSeek deployment would let MOEI keep all workforce queries on its own infrastructure — no employee data leaves the network. That's something proprietary closed models (Claude, GPT-4o) can't offer.

Alternative considered: `anthropic/claude-sonnet-4` — equally capable for structured output, slightly more consistent instruction-following in some benchmarks, but DeepSeek V4 Pro provides comparable quality for HR-analytics reasoning at lower latency and cost, plus the open-weight local-deployment path.

---

## AI Pattern: Intent Classifier + Structured Output + KB Grounding

**"Ask Your Workforce"** uses a deliberate multi-step pattern:

1. **Intent classification** — The question is parsed to detect the category (promotion, flight risk, training, performance, leave, or general). Each category maps to a specific set of employee columns and a sort key. Only the top-20 employees by that key are injected — reducing context bloat by ~60%.

2. **KB grounding (when relevant)** — If the question contains policy terms ("eligible", "law", "regulation", "سياسة", "قانون"), the app searches the 24 HR policy PDFs (EN + AR) via keyword matching and injects the top-3 matching paragraphs into the prompt. The model is instructed to cite policy when it answers.

3. **Structured JSON output** — The model returns valid JSON matching a strict schema (`RESPONSE_SCHEMA`). The schema enforces: `summary`, `people[]` (name, employee_id, reason, action, score), `confidence`, `note`. This forces named people, specific reasons, and recommended actions — not vague paragraphs.

4. **Graceful failure** — If the API errors (missing key, timeout, rate limit), the app falls back to a rule-based engine that handles the top queries (promotion readiness, flight risk) directly from the dataframe. The fallback returns named people with scores and reasons, so the demo never breaks.

5. **Bilingual (structural)** — Separate EN and AR system prompts, with Arabic few-shot examples to anchor output quality. Language detected via Arabic character ratio. The KB is searched in both languages. Replies in the detected language.

---

## Design of Door A (The Unbuilt Door)

Door A — The Employee Assistant — is the other side of the same door. It serves the employee, not the manager. Where Door B interprets patterns across the workforce, Door A helps one person get things done.

### What it would do

An assistant grounded in the HR Knowledge Base AND the employee's own record. The employee asks a question or requests an action, and the assistant both answers *and* acts.

### Concrete workflow: "Submit a study leave request"

Here's how one feature-end-to-end workflow would work:

```
Employee: "I want to apply for study leave this semester"

Step 1 — CLAIM: The app authenticates via employee_id (session/login).
         Loads this employee's row + their Leave, Performance,
         and Training records into context.

Step 2 — ELIGIBILITY: The AI calls the eligibility-check tool, which:
         (a) searches the KB for "study leave" policy rules
         (b) cross-references against the employee's actual record:
             - tenure ≥ 2 years? (from hire_date)
             - performance ≥ meets expectations? (from latest rating)
             - no prior study leave this year? (from Leave sheet)
             - annual leave balance > 5 days? (from Leave sheet)
         (c) returns: {eligible: true/false, reasons: [...], rule_ref: "Policy §4.3"}

Step 3 — EXPLAIN: If ineligible, the AI explains why, citing the specific
         rule and the employee's own numbers. "You need 2 years of service —
         you've been here 14 months. You'll be eligible in October 2026."

Step 4 — ACT: If eligible, the AI submits the request via the submit tool:
         POST /requests {type: "study_leave", employee_id, semester, justification}
         Returns: {status: "submitted", request_id: "REQ-042"}

Step 5 — CONFIRM: "Done. Your study leave request (REQ-042) has been
         submitted. HR will review it within 5 working days. You'll get
         a notification at your registered email."
```

### AI architecture for Door A

**Tool-calling / function-calling pattern** — the model receives a system prompt with available tools:

| Tool | Purpose | Data source |
|------|---------|-------------|
| `search_policy(query, lang)` | Retrieve relevant policy paragraphs | Vector store over KB PDFs (EN + AR) |
| `check_eligibility(employee_id, request_type)` | Cross-reference employee record against policy rules | Employee dataset + KB |
| `submit_request(employee_id, request_type, details)` | Submit a leave or training request | Internal requests queue (or webhook) |
| `get_employee_record(employee_id)` | Read the employee's full data profile | All 5 data sheets, filtered by ID |

**RAG pipeline:**
- EN policy PDFs → chunked by paragraph → embedded (all-MiniLM-L6-v2 or OpenAI ada) → ChromaDB
- AR policy PDFs → same pipeline, separate index, Arabic embeddings (paraphrase-multilingual)
- At query time: detect language → search both indexes → rank by relevance → inject top-5 chunks into prompt
- Citations: every policy answer includes the document name and section reference

**Bilingual grounding strategy:**
- EN questions → search EN index first, fall back to AR translated chunks
- AR questions → search AR index first, fall back to EN translated chunks
- The model replies in the same language as the question, citing Arabic or English policy as available
- Arabic policy documents (13 PDFs) are NOT just translated labels — they contain the actual Emirati legal terminology the employee expects

**Model:** Claude or GPT-4o with native tool/function calling. The agent loops: call tools → get results → decide if it needs more info → respond or act. Max 3 tool calls per turn to keep latency reasonable.

### Why the employee would care

- **Less digging** — instead of searching through PDFs or asking an HR officer, the employee gets an immediate, personalized answer grounded in their own record
- **Completes the task** — doesn't just answer, it acts. Submits the request. Doesn't make the employee fill a form after the conversation ends
- **Not generic** — every answer references the employee's own numbers. "You have 12 days of leave remaining" is different from "employees are entitled to 30 days"
- **Bilingual** — works in Arabic or English, grounded in the original Arabic policy documents (not translated approximations), replies in the language the employee used
- **Trustworthy** — answers cite specific policy sections. If the assistant doesn't have enough data, it says so. Never invents rules or entitlements
- **Catches mistakes** — an employee asking for training they've already completed gets told: "You completed this course in March 2025 (certificate on file)"

---

## Features Completed

| Feature | Status |
|---------|--------|
| Overview page (KPIs + 4 charts) | ✅ |
| Ask Your Workforce (AI Q&A) | ✅ |
| AI interpretation on Performance page | ✅ |
| KB grounding (policy search injected into Q&A) | ✅ |
| Intent classifier (focused context per question type) | ✅ |
| Top navbar (page links + lang switch) | ✅ |
| Lang persistence (localStorage + query params) | ✅ |
| MOEI brand theme (navy/gold, glass cards) | ✅ |
| Hidden sidebar + Streamlit toolbar | ✅ |
| Performance & Promotion Readiness page | ✅ |
| Training & Development page | ✅ |
| Leave Balances page | ✅ |
| Bilingual EN/AR (UI + AI responses) | ✅ |
| Promotion-readiness score (derived metric) | ✅ |
| Flight-risk score (derived metric) | ✅ |
| Score trend analysis (3-cycle) | ✅ |
| CSV export on all table pages | ✅ |
| Graceful API failure with fallback | ✅ |
| API key from environment (not hardcoded) | ✅ |
| README with Door A design | ✅ |
| REFLECTION.md | ✅ |

---

## Project Structure

```
moei_assessment/
├── app.py                    # Streamlit entry point (top navbar, no sidebar)
├── requirements.txt
├── README.md
├── REFLECTION.md
├── .streamlit/
│   └── config.toml           # MOEI brand theme (navy + light bg)
├── resources/
│   ├── MOEI_HR_Employee_Dataset.xlsx   # (copied from assessment package, not committed)
│   ├── MOEI_HR_Employee_Dataset_CSV/   # raw CSVs (not committed)
│   └── HR_Knowledge_Base/              # 24 policy PDFs EN+AR (not committed)
├── data/
│   ├── loader.py             # Load all 5 sheets from xlsx
│   ├── metrics.py            # Derived: tenure, readiness, risk scores
│   └── session.py            # Shared @st.cache_data loader (one load per session)
├── ai/
│   ├── client.py             # OpenRouter API client (loads key from env or .env)
│   ├── workforce_qa.py       # "Ask your workforce" — structured Q&A + intent classifier + KB grounding
│   └── kb_search.py          # Lightweight keyword search over HR policy PDFs
├── components/
│   ├── bilingual.py          # EN/AR strings, language detection
│   ├── theme.py              # MOEI-themed CSS injection + KPI cards, badges
│   ├── navbar.py             # Top navbar with page links + EN/AR switch (persisted to localStorage)
│   └── charts.py             # Plotly chart functions
└── pages/
    ├── 1_Overview.py         # KPIs + overview charts
    ├── 2_Ask_Your_Workforce.py  # AI Q&A (killer feature)
    ├── 3_Performance.py      # Promotion readiness + flight risk + AI interpretation
    ├── 4_Training.py         # Learning investment
    └── 5_Leave.py            # Leave balances
```

---

## UI / UX

- **Top navbar** with brand, 5 page links, and EN/AR language toggle (visible on every page)
- **No sidebar** — Streamlit's default sidebar + header toolbar hidden via CSS
- **MOEI brand theme** — navy (#003366) + gold accents, glass-morphism KPI cards, navy table headers, hover effects
- **Language persists** to browser localStorage + URL query params — reloading the page keeps the chosen language
- **Shared data cache** via `data/session.py` — pages don't re-load on navigation