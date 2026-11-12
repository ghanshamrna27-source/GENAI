"""
app/main.py
FastAPI Web API service for GitGuru — Git & GitHub Learning Assistant.
Provides endpoints for health checks, records retrieval, smart TF-IDF search,
and learner question answering.
"""

from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    RecordSchema,
    QuestionRequest,
    QuestionResponse,
    HealthResponse,
)
from app.records import load_records, get_by_id
from app.smart_search import rank_records

app = FastAPI(
    title="GitGuru API",
    description="Interactive Web API for learning Git and GitHub commands, workflows, and concepts.",
    version="1.0.0",
)

# Enable CORS for browser-based clients and local frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["General"])
def root():
    """Welcome endpoint with an index of available API routes."""
    return {
        "message": "Welcome to GitGuru API — Your guide to mastering Git and GitHub!",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "health": "GET /health",
            "list_records": "GET /records?limit=",
            "get_record_by_id": "GET /records/{id}",
            "smart_search": "GET /search?q=",
            "ask_question": "POST /questions",
        },
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
def health():
    """Health check endpoint reporting API status and knowledge base size."""
    records = load_records()
    return HealthResponse(
        status="ok",
        project="GitGuru",
        description="Git & GitHub Learning Assistant API",
        records_count=len(records),
        version="1.0.0",
    )


@app.get("/records", response_model=List[RecordSchema], tags=["Records"])
def get_records(limit: Optional[int] = None):
    """
    Retrieve Git and GitHub records from the knowledge base.
    Optionally restrict the number of results using the `limit` query parameter.
    """
    records = load_records()
    if limit is not None and isinstance(limit, int):
        return records[:limit]
    return records


@app.get("/records/{id}", response_model=RecordSchema, tags=["Records"])
def get_record(id: int):
    """
    Retrieve a specific Git or GitHub record by its integer ID.
    Returns 404 if the record is missing.
    """
    record = get_by_id(id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record with ID {id} not found",
        )
    return record


@app.get("/search", response_model=List[RecordSchema], tags=["Search"])
def search_records(q: str = "", limit: Optional[int] = 10):
    """
    Search GitGuru records using TF-IDF vectorization and Cosine Similarity ranking.
    Powered by app/smart_search.py.
    """
    if not q or not q.strip():
        return []
    limit_val = limit if isinstance(limit, int) else None
    ranked = rank_records(query=q, limit=limit_val, min_score=0.0)
    return ranked


@app.post("/questions", response_model=QuestionResponse, status_code=status.HTTP_200_OK, tags=["Q&A"])
def ask_question(payload: QuestionRequest):
    """
    Ask a Git or GitHub question.
    Ranks the knowledge base using smart TF-IDF search to find the most relevant
    answer and guidance.
    """
    matches = rank_records(query=payload.question, limit=3, min_score=0.01)

    if matches:
        top_match = matches[0]
        matched_category = top_match.get("category", payload.category or "General")
        return QuestionResponse(
            status="success",
            question=payload.question,
            category=payload.category or matched_category,
            asker=payload.asker,
            answer=top_match.get("answer"),
            matched_record=RecordSchema(**top_match),
            relevant_records=[RecordSchema(**m) for m in matches],
            message=f"Found relevant answer from GitGuru knowledge base (similarity score: {top_match.get('similarity_score', 0):.4f}).",
        )

    # Fallback if no close match is found
    return QuestionResponse(
        status="success",
        question=payload.question,
        category=payload.category,
        asker=payload.asker,
        answer="I don't have an exact answer for that topic in the current GitGuru knowledge base yet. Try checking the official Git docs at https://git-scm.com/doc or GitHub Docs at https://docs.github.com.",
        matched_record=None,
        relevant_records=[],
        message="No high-confidence match found for your query. Consider checking official documentation.",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
