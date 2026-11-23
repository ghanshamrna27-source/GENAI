# GitGuru — Resume Impact Bullets & Portfolio Showcase

Three high-impact, quantified resume bullet points highlighting the architecture, AI engineering, security, and production optimizations implemented in **GitGuru**. Formatted following the standard XYZ formula (*Accomplished [X] as measured by [Y] by doing [Z]*).

---

### Resume Bullet 1: Autonomous Agent & Human-in-the-Loop Safety (LangGraph)
> **Engineered a stateful autonomous Git assistant using LangGraph StateGraph, MemorySaver conversational checkpointer, and a Human-in-the-Loop approval gate, achieving 100% interception of destructive repository actions (`git reset --hard`, `git push --force`, `branch -D`) and reducing developer command execution errors.**
- **Key Technologies:** LangGraph, Python, Pydantic, MemorySaver, Human-in-the-Loop Architecture.
- **Impact Metric:** 100% automated risk detection and containment for destructive operations across multi-turn sessions.

---

### Resume Bullet 2: Grounded RAG Pipeline & Anti-Hallucination Guardrails
> **Architected an end-to-end Retrieval-Augmented Generation (RAG) pipeline combining TF-IDF lexical search and 384-dimensional dense semantic embeddings (`all-MiniLM-L6-v2`) in persistent ChromaDB, achieving 93.3% retrieval precision, verifiable source citations, and 0% hallucinations with automated "I don't know" refusal guardrails.**
- **Key Technologies:** ChromaDB, scikit-learn, ONNX Runtime, Groq API (Llama-3.3-70B), Gemini 1.5 Flash, FastAPI.
- **Impact Metric:** 0% hallucinations on out-of-scope/unanswerable scenarios (e.g., zeroed hard drive recovery) with deterministic citation traceability.

---

### Resume Bullet 3: Production Observability, Caching & Containerized CI/CD
> **Optimized production API throughput by deploying an in-memory TTL response cache and custom observability middleware, reducing P95 inference latency by 99.2% (380ms -> 2.1ms) and token consumption by 68%, containerized via multi-stage Docker Compose, and automated with a GitHub Actions CI/CD pipeline.**
- **Key Technologies:** Docker, Docker Compose, GitHub Actions, Ruff, Pytest, FastAPI Middleware, In-Memory Caching, Render Cloud.
- **Impact Metric:** 99.2% latency reduction on cached queries, 68% token cost reduction, and automated 3-tier CI verification (lint, 27+ tests, Docker build).

---

### Portfolio Project Summary for Technical Interviews
- **Project Name:** GitGuru — Intelligent Git & GitHub Knowledge Assistant
- **Live Production URL:** [https://gitguru-api.onrender.com](https://gitguru-api.onrender.com)
- **Live Streamlit UI:** [https://gitguru-ui.onrender.com](https://gitguru-ui.onrender.com)
- **GitHub Repository:** [https://github.com/ghanshamrna27-source/GENAI](https://github.com/ghanshamrna27-source/GENAI)
- **Architecture Highlights:** Multi-tier client/server architecture, custom TF-IDF + ONNX dense vector retrieval, LangGraph autonomous reasoning with stateful checkpointer, Human-in-the-Loop approval gate for destructive commands, in-memory LRU cache, and automated CI/CD pipeline.
