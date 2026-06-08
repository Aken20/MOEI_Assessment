# REFLECTION — MOEI HR Companion

> Five short questions. A few sentences each is plenty — we want your thinking, not an essay.
> (Which model you used, your structured/agentic pattern, and how you grounded answers go in the README, not here.)

**Name:** Ahmed Ibrahim
**Door I built:** management side (Door B — The Management View)
**In one line, what it does:** A manager-facing workforce intelligence dashboard where you can ask questions about employees in plain language and get named people with specific reasons and recommended actions.

---

**1. Why this product?**

I picked Door B because the differentiation is real. A FAQ bot or a leave request submitter is the floor — every candidate will build something like that. A management view that reasons over 260 employees and explains *why* someone looks like a flight risk, or *what* makes someone promotion-ready, requires actual analytical design. The dataset has enough texture (3 years of performance cycles, training records, movement history, engagement scores) for the AI to give named, specific answers — not generic platitudes. I also wanted to show something visual that a manager could actually use in a walkthrough, and the charts + "Ask your workforce" combination felt like the strongest demo.

---

**2. The door you didn't build.**

Door A — the employee assistant — is the other side of the same door. It would serve the employee, not the manager. The employee asks a question or requests an action, and the assistant:
- Answers policy questions grounded in the HR KB (RAG over the EN/AR policy PDFs — HR Law, Executive Regulations, Training System, Performance Management, Code of Ethics)
- Checks personal eligibility against the employee's own record — "Am I eligible for this training?" cross-referenced against grade, tenure, prior training, and leave balance
- Submits requests on the employee's behalf (leave, training nomination) after running eligibility checks — no manager intervention needed for routine requests
- Walks through processes step-by-step ("how do I apply for study leave?")

It needs: a vector store for the KB (ChromaDB or pgvector), read access to the employee's own row in the dataset, and a tool-calling layer to submit pre-approved request types. The employee would care because they get an immediate, personalized answer grounded in their own record — not a generic policy description. And it completes the task, it doesn't just answer it.

---

**3. AI: help vs. override.**

AI helped most with designing the structured output schema and the intent classifier. DeepSeek V4 Pro via OpenRouter with a strict JSON schema forces named people, specific reasons, and recommended actions — without that constraint, the model would return vague paragraphs. I also used AI for the bilingual prompt engineering (separate EN/AR system prompts with concrete Arabic few-shot examples to anchor output quality) and for the CSS variables and component patterns in the navbar and theme files.

Where I overrode: the scoring formulas. The model suggested some initial weightings for the promotion-readiness and flight-risk scores, but I overrode them with manually tuned weights after noticing the model's suggestions produced unintuitive results (e.g. someone with zero training hours getting a high readiness score because their tenure penalty was too small). I also built the rule-based fallback explicitly because I didn't trust the API to always be available during the demo — the fallback handles the most common queries directly from the dataframe without any API call. The KB search (`kb_search.py`) is a deliberately simple keyword matcher rather than a full embedding-based RAG pipeline — sometimes "good enough" is the right engineering call for a 2-hour build. I also overrode the default Streamlit sidebar in favor of a top navbar with localStorage-backed language persistence — the manager's eye should be on the data, not on a thin left strip.

On the model choice: DeepSeek was a deliberate pick, not the default. For an HR system dealing with 260 employees' personal data, the open-weight deployment path matters — a production version of this could run DeepSeek on a self-hosted Ollama instance, keeping all workforce queries on MOEI's own network. That's a real privacy advantage over Claude or GPT-4o.

---

**4. Cut for time.**

I left out the org chart visualization (manager → direct reports tree). The data has `manager_id` so it was technically possible, but building an interactive hierarchy in Streamlit was taking too long and I cut it to focus on the "Ask your workforce" page which is the actual differentiator.

I also kept the KB search deliberately lightweight — keyword matching over extracted PDF text rather than a full embedding-based RAG pipeline. For a 2-hour build this was the right call: it grounds policy-adjacent questions in real document text without the setup overhead of a vector store. With more time, I'd upgrade to proper embeddings (multilingual model for Arabic) and add citation extraction so the model can reference specific policy sections by name.

---

**5. One thing you'd redo.**

I would have started with the intent classifier from the beginning rather than retrofitting it. The original design injected all 260 employees into every prompt — it worked but wasted context tokens on irrelevant columns and employees. Adding the classifier later meant refactoring the prompt construction logic after the structured output schema was already working. If I'd thought through "what data does this *specific* question actually need?" first, the whole pipeline would have been cleaner from the start.

With more time, I'd also upgrade the KB search from keyword matching to proper multilingual embeddings. The Arabic policy documents are rich sources of Emirati legal terminology that keyword search can miss. A cross-lingual retrieval setup (search in Arabic, retrieve in both languages) would make the bilingual grounding genuinely deep rather than just functional.