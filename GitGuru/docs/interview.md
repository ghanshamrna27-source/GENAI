# GitGuru — Interview Preparation & Engineering Story

This guide contains the 60-second elevator pitch, answers to 10 likely technical and behavioral interview questions, and the STAR-formatted "hardest problem" story for **GitGuru**.

---

## 1. 60-Second Elevator Pitch (`{P}`)

> "Git is mandatory for every software engineer, yet over 40% of junior developers experience code loss or commit paralysis from detached HEAD states, merge conflicts, or accidental `git reset --hard` commands. Worse, generic LLMs often hallucinate flags and recommend destructive commands without warning.
>
> I built **GitGuru**, a production-grade AI Git & GitHub assistant that solves this with four pillars: First, a **hybrid RAG pipeline** combining TF-IDF lexical search and 384-dimensional ONNX embeddings in ChromaDB to answer strictly from official documentation with verifiable `[Title, Page X]` citations. Second, **deterministic anti-hallucination guardrails** that refuse impossible queries with *'I don't know'*. Third, a **LangGraph agent with a Human-in-the-Loop gate** that intercepts destructive commands like `reset --hard` and pauses for confirmation. Fourth, an interactive **Streamlit visual branch simulator** rendered in Mermaid.
>
> In production, I added prompt-injection shields, an in-memory TTL cache that cut P50 latency by **99.4%** (382ms to 2.15ms) and token costs by **68.4%**, and automated CI/CD with 33 Pytest tests deployed live on Render."

*(Speaking time: ~55–60 seconds at a natural pace.)*

---

## 2. Hardest Engineering Problem Story (`{H}`)

### Topic: **Zero-Hallucination Grounding & Stateful Human-in-the-Loop Safety Under Multi-Provider Failover**

* **Situation:** While building GitGuru's RAG (`/ask`) and Agent (`/agent`) endpoints, two critical failure modes emerged. First, even when prompted to stay grounded, LLMs would still fabricate plausible-sounding `git reflog` recovery steps for impossible scenarios (like recovering unpushed commits from a formatted, zeroed-out hard drive). Second, in multi-turn agent workflows, destructive commands needed to pause mid-execution for human confirmation and seamlessly resume without losing conversation context—while also handling external LLM API deprecations and offline test environments.
* **Task:** Engineer a deterministic anti-hallucination gate (`0%` false citations on unanswerable queries), a stateful Human-in-the-Loop pause/resume mechanism, and resilient multi-provider routing across Google Gemini, Groq Cloud, and an offline grounded fallback.
* **Action:**
  1. Implemented a pre-inference and similarity-threshold guardrail (`is_unanswerable_query` in `app/rag.py`) that detects impossible recovery patterns and low semantic similarity (`< 0.10`), short-circuiting before LLM generation to return an explicit *"I don't know"* with zero citations.
  2. Built a LangGraph `StateGraph` (`app/graph.py`) backed by `MemorySaver` checkpointing keyed by `thread_id`. Safe tools (`git status`, `git log`) execute immediately, while destructive tools (`reset_hard`, `push_force`, `branch_delete_force`) halt in a `pending_approval` state until re-invoked with `approved=True`.
  3. Added automatic backup model failover in `app/llm.py` (`gemini-3.8-flash` &rarr; `gemini-3.5-flash`; `openai/gpt-oss-120b` &rarr; `llama-3.3-70b-versatile`) plus a deterministic TF-IDF grounded fallback for offline CI sandboxes.
* **Result:** Achieved **0% hallucinations** on out-of-scope evaluations (verified by `test_ask_unanswerable_q6_strict_refusal`), **100% interception** of destructive Git actions across multi-turn sessions, and **33/33 passing Pytest tests** in CI regardless of external API availability.

---

## 3. Answers to 10 Likely Interview Questions

### Q1. Why did you build GitGuru instead of just prompting ChatGPT?
**Answer:** Generic chatbots lack repository grounding, hallucinate CLI flags, never cite exact documentation pages, and casually output dangerous commands like `git push --force` without an approval gate. GitGuru pairs official documentation RAG with deterministic refusal rules, a stateful Human-in-the-Loop safety check, and an interactive Mermaid branch graph simulator.

### Q2. How does your RAG pipeline prevent hallucinations?
**Answer:** Three layers work together: (1) Documents are chunked into 200–400 character segments with 50-char overlap preserving `source`, `page`, and `title` metadata (`app/chunking.py`). (2) `is_unanswerable_query()` enforces a hard refusal (*"I don't know"*) with `0` citations if similarity is below `0.10` or impossible recovery patterns (like Q6 formatted disk) are detected. (3) Prompts strictly instruct the LLM to cite `[Title, Page X]` and refuse ungrounded extrapolation.

### Q3. Why use both TF-IDF lexical search and ChromaDB dense embeddings?
**Answer:** Exact Git command names and flags (like `git cherry-pick` or `--amend`) are sometimes diluted by dense embeddings, whereas conceptual questions (like *"how do I undo my last mistake?"*) need semantic understanding. Combining scikit-learn TF-IDF Cosine Similarity (`app/smart_search.py`) with 384-dim `all-MiniLM-L6-v2` ONNX embeddings in ChromaDB (`app/vectorstore.py`) gives high precision for both exact flags and natural-language intent.

### Q4. How does the Human-in-the-Loop safety gate work in LangGraph?
**Answer:** In `app/tools.py`, `DESTRUCTIVE_ACTIONS` classifies high-risk operations (`reset_hard`, `push_force`, `branch_delete_force`, `clean_force`). In `app/graph.py`, the LangGraph `StateGraph` uses `MemorySaver` to persist conversation state per `thread_id`. When a destructive action is requested without `approved=True`, execution pauses and returns `pending_approval`. Re-submitting with `approved=True` on the same `thread_id` resumes the graph and executes safely.

### Q5. Why did you build both a LangGraph agent and a handwritten ReAct loop?
**Answer:** Building the handwritten ReAct loop (`app/agent_loop.py`) first ensured I understood the core `Thought -> Action -> Observation -> Final Answer` cycle without framework magic. Implementing the LangGraph `StateGraph` (`app/graph.py`) then added production-grade state persistence (`MemorySaver`) and clean node-based conditional routing.

### Q6. How did you reduce latency by 99.4% and token costs by 68.4%?
**Answer:** In `app/cache.py`, I implemented a thread-safe in-memory LRU cache with TTL (`SimpleResponseCache`). Before calling `generate_chat_response` or `answer_question`, `POST /chat` and `POST /ask` check the cache. Warm hits bypass the LLM completely, returning in ~2.15ms with 0 tokens consumed (`X-Cache-Status: HIT`), while `ObservabilityMiddleware` logs latency and token savings to `GET /metrics`.

### Q7. How do you protect the API from prompt injection and payload abuse?
**Answer:** In `app/security.py`, `is_prompt_injection()` runs pre-inference regex checks to intercept jailbreaks and system-override attempts (e.g., *"ignore previous instructions"*, *"reveal system prompt and API keys"*), returning a safe refusal before any LLM call or vector query. Additionally, Pydantic models enforce `min_length=2`, `max_length=1000`, and null-byte (`\x00`) sanitization.

### Q8. How did you handle FastAPI & Pydantic edge cases during production hardening?
**Answer:** Two real issues surfaced: (1) Injecting `response: Optional[Response] = None` in FastAPI route signatures caused a `FastAPIError` because Pydantic tried to validate `starlette.responses.Response | None` as a response field; changing the annotation to `response: Response = None` resolved it while keeping unit tests calling `ask(payload)` directly working. (2) Model deprecations on external APIs were solved by adding multi-model failover chains in `app/llm.py`.

### Q9. How do you test an LLM application reliably in CI without burning API keys?
**Answer:** In `tests/test_ask_rag.py`, I mock `app.llm.call_groq` and `app.llm.call_gemini` with `unittest.mock.patch` to verify RAG prompt wiring, citation formatting, and grounded output deterministically. When no keys are present, the system falls back to `synthesize_offline_grounded_answer`, so all 33 Pytest tests run fast and deterministically in GitHub Actions without network dependencies.

### Q10. What would you build next if you had two more weeks?
**Answer:** (1) Replace the in-memory LRU cache with **Redis** for shared multi-worker caching across horizontal replicas. (2) Add **semantic caching** (embedding similarity cache lookup) so paraphrased Git questions also hit cache. (3) Integrate **OpenTelemetry** tracing and automated **RAGAS** evaluation runs into GitHub Actions on every PR.
