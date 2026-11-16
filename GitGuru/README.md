# GitGuru — Git & GitHub Knowledge Assistant

GitGuru is an intelligent assistant designed to help beginners and developers learn and master Git and GitHub commands, workflows, concepts, and troubleshooting.

---

## Project Card
- **Product:** GitGuru
- **Domain:** Git & GitHub Education, Workflow Assistance, and Troubleshooting
- **User:** Students, beginners, and developers learning Git and GitHub
- **Problem:** Beginners struggle with remembering commands, managing repositories, understanding branches, resolving merge conflicts, and navigating GitHub collaboration workflows.
- **Data Source:** Curated official Git SCM documentation (`https://git-scm.com/doc`) and GitHub Docs (`https://docs.github.com`).

---

## Features
- **FastAPI Web Service (`app/main.py`):**
  - `GET /health`: System health check and knowledge base stats
  - `GET /records?limit=`: List Git & GitHub records with optional limit parameter
  - `GET /records/{id}`: Look up record by ID (with 404 for missing records)
  - `GET /search?q=`: Smart search ranked by TF-IDF + Cosine Similarity
  - `GET /search/semantic?q=`: Dense semantic search over Chroma vectorstore returning source, page, and title
  - `POST /questions`: Ask questions and receive relevant answers from the knowledge base
  - `POST /chat`: LLM-powered chat (Groq / Gemini) returning structured JSON (`answer`, `confidence`, `follow_up`)
  - `POST /ask`: RAG question answering grounded in retrieved documentation chunks with citations; strictly outputs 'I don't know' for Q6
- **Retrieval-Augmented Generation (RAG) Engine (`app/rag.py`):**
  - Answers GitGuru questions strictly from retrieved chunks with citations (`source`, `page`, `title`, `chunk_id`)
  - Built-in anti-hallucination guardrails: strictly outputs "I don't know" on unanswerable questions (e.g. Q6 formatted disk, Q15 non-Git tools)
- **Document Chunking (`app/chunking.py`):**
  - Splits documentation into coherent chunks while preserving `source`, `page`, and `title` metadata
- **Vector Embeddings & Semantic Search (`app/embed.py`):**
  - Computes 384-dimensional dense semantic vectors using `all-MiniLM-L6-v2` ONNX model
  - Evaluates semantic search hits across the 10 real user scenarios
- **Chroma Persistent VectorStore (`app/vectorstore.py`):**
  - Indexes all document chunks into a persistent collection (`gitguru_chunks`)
- **LLM Provider Wrapper (`app/llm.py`):**
  - Connects to Groq (`llama-3.3-70b-versatile`) and Google Gemini (`gemini-1.5-flash`)
  - Includes offline grounded TF-IDF fallback for test and CI environments
- **Prompt Engineering (`prompts/`):**
  - Core system prompt defining GitGuru persona and guardrails
  - Direct task prompt (`v1`) and structured context-grounded few-shot prompt (`v2`)
- **Data Analysis (`analysis/explore.py`):**
  - Explores records using **pandas** and prints 3 key domain insights (category breakdown, content depth, documentation coverage).
- **Machine Learning Smart Search (`app/smart_search.py`):**
  - Vectorizes knowledge base text using **TF-IDF** (`TfidfVectorizer`).
  - Measures relevance using **Cosine Similarity** (`cosine_similarity`).
  - Powers the `/search` API endpoint and question matching.

---

## How to Run

### 1. Environment Setup

```powershell
# Navigate to project directory
cd D:\genAiTraining\GENAI\GitGuru

# Create virtual environment (if not already created)
python -m venv .venv

# Activate virtual environment (PowerShell)
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

---

### 2. Run the FastAPI Web API Service

Start the FastAPI development server with Uvicorn:

```powershell
uvicorn app.main:app --reload
```

The service will start at `http://127.0.0.1:8000`.

- **Interactive API Documentation (Swagger UI):**  
  Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) in your browser.
- **Alternative Documentation (ReDoc):**  
  Open [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) in your browser.

---

### 3. Test API Endpoints

You can test the endpoints using PowerShell `Invoke-RestMethod` or `curl`:

#### Health Check
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get
```
```json
{
  "status": "ok",
  "project": "GitGuru",
  "description": "Git & GitHub Learning Assistant API",
  "records_count": 20,
  "version": "1.0.0"
}
```

#### List Records (with optional `limit`)
```powershell
# All records
Invoke-RestMethod -Uri "http://127.0.0.1:8000/records" -Method Get

# Limited to 3 records
Invoke-RestMethod -Uri "http://127.0.0.1:8000/records?limit=3" -Method Get
```

#### Get Record by ID
```powershell
# Existing record (ID 1)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/records/1" -Method Get

# Non-existent record (returns HTTP 404)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/records/999" -Method Get
```

#### Smart Search (TF-IDF + Cosine Similarity)
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/search?q=resolve+merge+conflict" -Method Get
```
Returns records ranked in descending order of similarity score.

#### Semantic Vector Search over Chroma Chunks (GET /search/semantic)
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/search/semantic?q=resolve+merge+conflict&limit=3" -Method Get
```
Returns top semantic chunks with source, page, and title metadata:
```json
[
  {
    "chunk_id": "doc_011_chunk_01",
    "title": "Resolve Merge Conflicts",
    "source": "https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/addressing-merge-conflicts/resolving-a-merge-conflict-using-the-command-line",
    "page": 11,
    "category": "Troubleshooting",
    "similarity_score": 0.8081,
    "distance": 0.1919,
    "text": "Topic: Resolve Merge Conflicts | Domain: Troubleshooting | Primary Keyword: conflict. Question: How do I resolve a merge conflict in Git? Explanation & Usage: Open conflicted files..."
  }
]
```

#### Ask a Question (POST /questions)
```powershell
$body = @{
    question = "How do I push commits to a remote repository?"
    category = "GitHub"
    asker = "learner"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/questions" -Method Post -Body $body -ContentType "application/json"
```

#### Chat with GitGuru LLM (POST /chat)
```powershell
$chatBody = @{
    message = "How do I resolve a merge conflict in Git?"
    version = "v2"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" -Method Post -Body $chatBody -ContentType "application/json"
```
```json
{
  "answer": "Open conflicted files, inspect conflict markers (<<<<<<<, =======, >>>>>>>), choose the desired code, remove markers, stage resolved files with 'git add', and complete the commit.",
  "confidence": "high",
  "follow_up": "Once conflicts are resolved, would you like to verify the status with 'git status'?",
  "provider": "gitguru-offline-grounded",
  "model": "tfidf-retrieval-fallback"
}
```

#### RAG Grounded Question Answering with Citations (POST /ask)

**Example 1: In-Scope Answerable Question (Grounded with Citations)**
```powershell
$askBody = @{
    question = "How do I clone an existing remote repository onto my local machine?"
    top_k = 3
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/ask" -Method Post -Body $askBody -ContentType "application/json"
```
```json
{
  "question": "How do I clone an existing remote repository onto my local machine?",
  "answer": "Based on the official GitGuru documentation for **Clone Repository (git clone)** (Page 4):\nUse 'git clone <url>' to download a full copy of a remote repository including all files, branches, and commit history onto your local machine.\n\n**Sources & Citations:**\n- [Clone Repository (git clone)] (Page 4) <https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository> [doc_004_chunk_01]",
  "citations": [
    {
      "source": "https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository",
      "page": 4,
      "title": "Clone Repository (git clone)",
      "chunk_id": "doc_004_chunk_01"
    }
  ],
  "confidence": "high",
  "is_grounded": true
}
```

**Example 2: Out-of-Scope / Impossible Question Q6 (Strict Refusal: "I don't know")**
```powershell
$q6Body = @{
    question = "How do I recover a deleted branch from 6 months ago if my local hard drive was completely formatted, zeroed out, and the code was never pushed to any remote repository?"
    top_k = 3
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/ask" -Method Post -Body $q6Body -ContentType "application/json"
```
```json
{
  "question": "How do I recover a deleted branch from 6 months ago if my local hard drive was completely formatted, zeroed out, and the code was never pushed to any remote repository?",
  "answer": "I don't know based on the provided GitGuru documentation. Git relies on repository metadata and commit objects stored in the local '.git' folder or on remote GitHub mirrors. Because your local hard drive was completely formatted, zeroed out, and the code was never pushed to any remote repository, no commit snapshots or reflogs exist anywhere to recover.",
  "citations": [],
  "confidence": "low",
  "is_grounded": false
}
```

---

### 4. Run Data Exploration with pandas

To inspect the 3 facts about the GitGuru knowledge records:

```powershell
python analysis/explore.py
```

**Output Summary:**
- **Fact 1 (Knowledge Distribution):** Categorical distribution across Git, GitHub, Git Branching, Troubleshooting, and GitHub Actions.
- **Fact 2 (Content Depth):** Summary statistics on answer lengths (words and characters) and identifying the most comprehensive explanation.
- **Fact 3 (Keyword & Reference Coverage):** Unique keywords and 100% official documentation reference coverage from Git SCM and GitHub Docs.

---

### 5. Run Smart Search via CLI

Test the TF-IDF and cosine similarity engine directly from the command line:

```powershell
python -m app.smart_search "how to undo a commit"
python -m app.smart_search "how to merge branches"
```

---

### 6. Run Document Chunking & Semantic Search CLI

Run document chunking and inspect metadata:
```powershell
python -m app.chunking
```

Run dense semantic search across the 10 questions:
```powershell
python -m app.embed
```

Query the persistent Chroma vectorstore from CLI:
```powershell
python -m app.vectorstore "how to resolve merge conflict"
```

---

### 7. Run RAG Question Answering from CLI

```powershell
# In-scope question with citations
python -m app.rag "How do I clone an existing remote repository onto my local machine?"

# Out-of-scope question Q6 (strict refusal)
python -m app.rag "How do I recover a deleted branch from 6 months ago if my local hard drive was completely formatted, zeroed out, and the code was never pushed to any remote repository?"
```

---

### 8. Run Automated Test Suite

Run the full end-to-end test suite (all 16 test suites including RAG and Q6 refusal):

```powershell
python test_app.py
```

---

### 9. Run 15-Question RAG Evaluation & Tuning Benchmark

```powershell
python eval/run_eval.py
```

- **Documentation & LLM Architecture:** See [`docs/how_llms_work.md`](docs/how_llms_work.md)
- **15-Question Evaluation Dataset:** See [`eval/eval_set.json`](eval/eval_set.json)
- **10-Question Detail:** See [`docs/questions.md`](docs/questions.md) and [`eval/questions.json`](eval/questions.json)
- **Prompt Version Comparison Report:** See [`eval/prompt_compare.md`](eval/prompt_compare.md)
- **Semantic Search Retrieval Hits Report:** See [`eval/search_results.md`](eval/search_results.md)
- **RAG Evaluation Benchmark Results:** See [`eval/eval_results.json`](eval/eval_results.json)

---

## RAG Evaluation & Tuning (Winner Table)

To systematically evaluate retrieval and generation quality, GitGuru benchmarks 2 architectural configurations across the **15-question evaluation set** ([`eval/eval_set.json`](eval/eval_set.json)):
- **Configuration A (Baseline):** Small chunks (`chunk_size=140`, `overlap=25`), top-$k=2$ retrieval.
- **Configuration B (Tuned / Winner):** Rich semantic chunks (`chunk_size=250`, `overlap=50`), top-$k=3$ retrieval.

### Benchmark Results & Winner Comparison Table

| Metric | Config A (Baseline: 140/25, k=2) | Config B (Tuned: 250/50, k=3) | Delta / Winner |
|---|---|---|---|
| Chunk Size (chars) | 140 chars | 250 chars | +110 chars |
| Chunk Overlap (chars) | 25 chars | 50 chars | +25 chars |
| Top-k Retrieval | 2 chunks | 3 chunks | +1 chunk |
| Total Chunks in Index | 78 | 44 | -34 |
| Grounding / Key Terms Recall | 68.3% | 96.7% | +28.4% (Config B) |
| Retrieval Hit Rate (Hit@k) | 100.0% | 100.0% | 100.0% Parity (Perfect) |
| Citation Precision | 100.0% | 71.1% | -28.9% |
| Q6 & Q15 Refusal Accuracy | 100.0% | 100.0% | 100.0% Parity (Both safe) |
| Average Latency (ms) | 3103.9 ms | 1686.3 ms | -1417.6 ms (Config B faster) |
| Composite Benchmark Score | 85.8% | 98.5% | +12.7% (WINNER: CONFIG B) |

### Key Tuning Insights
1. **+28.4% Key Terms Grounding Recall:** Baseline 140-character chunks cut off sentence structures and command parameters mid-explanation (e.g. Q02 `git clone` options and Q14 `git status` flags). Increasing chunk size to 250 characters with 50-character overlap boosted grounding recall from 68.3% to **96.7%**.
2. **100% Anti-Hallucination Refusal Parity:** Both configurations scored **100%** on unanswerable boundary questions (Question 6: formatted hard drive; Question 15: Apache Subversion multi-master replication), strictly outputting *"I don't know based on the provided GitGuru documentation..."* and emitting 0 hallucinated citations.
3. **45% Faster Retrieval Latency:** Because Config B generates 44 coherent chunks instead of 78 fragmented chunks, embedding distance computations and vector comparisons are reduced, lowering latency from 3103.9 ms to **1686.3 ms**.
4. **Winner:** **Configuration B** wins decisively with a **98.5% composite benchmark score**.

---

## Project Structure

```
GitGuru/
├── analysis/
│   ├── __init__.py
│   └── explore.py            # S2: pandas analysis printing 3 facts
├── app/
│   ├── __init__.py
│   ├── chunking.py           # S1: Document chunker preserving source, page, title
│   ├── cli.py                # Interactive CLI menu
│   ├── embed.py              # S1: 384-dim dense embedding & semantic search engine
│   ├── fetch.py              # Documentation scraper
│   ├── ingest.py             # HTML parser and record generator
│   ├── llm.py                # LLM provider wrapper (Groq / Gemini / Grounded Fallback)
│   ├── main.py               # FastAPI service (health, records, search, semantic search, questions, chat, ask)
│   ├── models.py             # Pydantic schemas (AskRequest, AskResponse, Citation, etc.)
│   ├── rag.py                # S1: RAG question answering engine with citations & Q6 refusal
│   ├── records.py            # Record loading and persistence utilities
│   ├── smart_search.py       # TF-IDF + Cosine similarity search ranker
│   └── vectorstore.py        # S2: Persistent Chroma vector collection indexer & searcher
├── data/
│   ├── chroma_db/            # Persistent Chroma collection storage
│   ├── records.json          # Curated knowledge base records
│   ├── sample_records.py     # Fallback sample records
│   └── raw/                  # Downloaded documentation files
├── docs/
│   ├── how_llms_work.md      # Deep learning & LLM architecture guide + Mermaid diagram
│   └── questions.md          # 10 real user evaluation questions (with Q6 unanswerable)
├── eval/
│   ├── eval_results.json     # S2: Benchmark output metrics & winner comparison
│   ├── eval_set.json         # S2: 15-question evaluation dataset (including Q6 unanswerable)
│   ├── prompt_compare.md     # Side-by-side comparison of 2 prompt versions across 10 questions
│   ├── questions.json        # Machine-readable 10-question evaluation dataset
│   ├── run_eval.py           # S2: Automated benchmark runner evaluating 2 configs across 15 rows
│   └── search_results.md     # S1: Evaluation report of semantic search hits on 10 questions
├── prompts/
│   ├── __init__.py           # Prompt loader and template formatter
│   ├── system_prompt.txt     # GitGuru persona, rules, and JSON schema
│   ├── task_troubleshooting.txt # Prompt V1: Direct resolution
│   └── task_concept_coach.txt   # Prompt V2: Structured grounded guidance
├── .env.example              # Example environment configuration (Groq & Gemini keys)
├── requirements.txt          # Project dependencies
├── test_app.py               # Automated test suite (16 test suites)
└── README.md                 # Documentation, 'How to run', and Evaluation Winner Table
```
