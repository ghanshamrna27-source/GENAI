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
  - `POST /questions`: Ask questions and receive relevant answers from the knowledge base
  - `POST /chat`: LLM-powered chat (Groq / Gemini) returning structured JSON (`answer`, `confidence`, `follow_up`)
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

### 6. Run Automated Test Suite

Run the full end-to-end test suite:

```powershell
python test_app.py
```

---

### 7. Run 10-Question Evaluation Benchmark
```powershell
python eval/run_eval.py
```

- **Documentation & LLM Architecture:** See [`docs/how_llms_work.md`](docs/how_llms_work.md)
- **Evaluation Questions Detail:** See [`docs/questions.md`](docs/questions.md) and [`eval/questions.json`](eval/questions.json)
- **Prompt Version Comparison Report:** See [`eval/prompt_compare.md`](eval/prompt_compare.md)

---

## Project Structure

```
GitGuru/
├── analysis/
│   ├── __init__.py
│   └── explore.py            # S2: pandas analysis printing 3 facts
├── app/
│   ├── __init__.py
│   ├── cli.py                # Interactive CLI menu
│   ├── fetch.py              # Documentation scraper
│   ├── ingest.py             # HTML parser and record generator
│   ├── llm.py                # LLM provider wrapper (Groq / Gemini / Grounded Fallback)
│   ├── main.py               # FastAPI service (health, records, search, questions, chat)
│   ├── models.py             # Pydantic schemas and dataclasses
│   ├── records.py            # Record loading and persistence utilities
│   └── smart_search.py       # TF-IDF + Cosine similarity search ranker
├── data/
│   ├── records.json          # Curated knowledge base records
│   ├── sample_records.py     # Fallback sample records
│   └── raw/                  # Downloaded documentation files
├── docs/
│   ├── how_llms_work.md      # Deep learning & LLM architecture guide + Mermaid diagram
│   └── questions.md          # 10 real user evaluation questions (with Q6 unanswerable)
├── eval/
│   ├── prompt_compare.md     # Side-by-side comparison of 2 prompt versions across 10 questions
│   ├── questions.json        # Machine-readable evaluation dataset
│   └── run_eval.py           # Automated benchmark runner for the 10 questions
├── prompts/
│   ├── __init__.py           # Prompt loader and template formatter
│   ├── system_prompt.txt     # GitGuru persona, rules, and JSON schema
│   ├── task_troubleshooting.txt # Prompt V1: Direct resolution
│   └── task_concept_coach.txt   # Prompt V2: Structured grounded guidance
├── .env.example              # Example environment configuration (Groq & Gemini keys)
├── requirements.txt          # Project dependencies
├── test_app.py               # Automated test suite
└── README.md                 # Documentation and 'How to run' guide
```
