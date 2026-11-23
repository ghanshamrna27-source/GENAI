"""
app/main.py
FastAPI Web API service for GitGuru — Git & GitHub Learning Assistant.
Provides endpoints for health checks, records retrieval, keyword/TF-IDF search,
persistent Chroma semantic search over document chunks, learner question answering,
and LLM-powered chat.
"""

from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, status, Response
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    RecordSchema,
    QuestionRequest,
    QuestionResponse,
    HealthResponse,
    ChatRequest,
    ChatResponse,
    SemanticSearchResult,
    AskRequest,
    AskResponse,
    Citation,
    AgentRequest,
    AgentResponse,
)
from app.records import load_records, get_by_id
from app.smart_search import rank_records
from app.llm import generate_chat_response
from app.vectorstore import query_semantic
from app.rag import answer_question
from app.graph import run_langgraph_agent
from app.agent_loop import run_handwritten_agent
from app.cache import GLOBAL_CACHE
from app.security import is_prompt_injection, PROMPT_INJECTION_REFUSAL
from app.observability import (
    GLOBAL_TELEMETRY,
    ObservabilityMiddleware,
    estimate_tokens,
)

app = FastAPI(
    title="GitGuru API",
    description="Interactive Web API for learning Git and GitHub commands, workflows, and concepts.",
    version="1.0.0",
)

# Observability middleware (measures latency, logs request events, sets X-Process-Time-Ms)
app.add_middleware(ObservabilityMiddleware)

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
            "semantic_search": "GET /search/semantic?q=",
            "ask_question": "POST /questions",
            "chat": "POST /chat",
            "rag_ask": "POST /ask",
            "agent": "POST /agent",
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


@app.get("/search/semantic", response_model=List[SemanticSearchResult], tags=["Search"])
def search_semantic(
    q: str = Query(..., min_length=1, description="Semantic search query"),
    limit: Optional[int] = Query(default=5, ge=1, le=20, description="Max results to return"),
):
    """
    Semantic search over document chunks in persistent Chroma collection.
    Ranks chunks using dense vector embeddings and returns source, page, and title metadata.
    """
    limit_val = limit if isinstance(limit, int) else 5
    return query_semantic(query=q, limit=limit_val)


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


@app.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK, tags=["LLM Chat"])
def chat(payload: ChatRequest, response: Response = None):
    """
    Chat with GitGuru LLM Assistant (Groq / Gemini / Grounded Fallback).
    Protected by Prompt Injection Defense and Response Caching.
    Returns structured JSON with fields:
      - answer: The solution or explanation
      - confidence: Assessment rating ('high', 'medium', 'low')
      - follow_up: Proactive next command or logical follow-up step
    """
    # 1. Security Guardrail: Prompt Injection Check
    is_injection, _ = is_prompt_injection(payload.message)
    if is_injection:
        if response is not None:
            response.headers["X-Cache-Status"] = "BYPASS"
            response.headers["X-Security-Flag"] = "INJECTION_ATTEMPT"
        return ChatResponse(
            answer=PROMPT_INJECTION_REFUSAL,
            confidence="low",
            follow_up="Please ask a question related to Git commands, workflows, or GitHub collaboration.",
            provider="security-guardrail",
            model="prompt-shield-v1",
        )

    # 2. Performance & Cost Optimization: In-Memory Cache Lookup
    cache_key = f"chat:{payload.version or 'v2'}:{payload.provider or 'default'}:{payload.message}"
    cached_data = GLOBAL_CACHE.get(cache_key)
    if cached_data is not None:
        if response is not None:
            response.headers["X-Cache-Status"] = "HIT"
            response.headers["X-Prompt-Tokens"] = "0"
            response.headers["X-Completion-Tokens"] = "0"
        return ChatResponse(**cached_data)

    # 3. Cache Miss: Generate Chat Response
    response_data = generate_chat_response(
        query=payload.message,
        version=payload.version or "v2",
        provider=payload.provider,
    )
    p_tokens = estimate_tokens(payload.message)
    c_tokens = estimate_tokens(response_data.get("answer", ""))

    if response is not None:
        response.headers["X-Cache-Status"] = "MISS"
        response.headers["X-Prompt-Tokens"] = str(p_tokens)
        response.headers["X-Completion-Tokens"] = str(c_tokens)

    GLOBAL_CACHE.set(cache_key, response_data, estimated_tokens=p_tokens + c_tokens)
    return ChatResponse(**response_data)


@app.post("/ask", response_model=AskResponse, status_code=status.HTTP_200_OK, tags=["RAG"])
def ask(payload: AskRequest, response: Response = None):
    """
    RAG Question Answering Endpoint:
    Answers Git and GitHub questions strictly grounded in retrieved documentation chunks with citations.
    Enforces strict hallucination guardrails: outputs 'I don't know' for unanswerable questions (Q6).
    Protected by Prompt Injection Defense and Response Caching.
    """
    # 1. Security Guardrail: Prompt Injection Check
    is_injection, _ = is_prompt_injection(payload.question)
    if is_injection:
        if response is not None:
            response.headers["X-Cache-Status"] = "BYPASS"
            response.headers["X-Security-Flag"] = "INJECTION_ATTEMPT"
        return AskResponse(
            question=payload.question,
            answer=PROMPT_INJECTION_REFUSAL,
            citations=[],
            retrieved_chunks=[],
            confidence="low",
            is_grounded=False,
        )

    # 2. Performance & Cost Optimization: In-Memory Cache Lookup
    cache_key = f"ask:{payload.top_k or 3}:{payload.question}"
    cached_data = GLOBAL_CACHE.get(cache_key)
    if cached_data is not None:
        if response is not None:
            response.headers["X-Cache-Status"] = "HIT"
            response.headers["X-Prompt-Tokens"] = "0"
            response.headers["X-Completion-Tokens"] = "0"
        return AskResponse(**cached_data)

    # 3. Cache Miss: Execute Grounded RAG Pipeline
    response_data = answer_question(question=payload.question, top_k=payload.top_k or 3)
    p_tokens = estimate_tokens(payload.question)
    c_tokens = estimate_tokens(response_data.get("answer", ""))

    if response is not None:
        response.headers["X-Cache-Status"] = "MISS"
        response.headers["X-Prompt-Tokens"] = str(p_tokens)
        response.headers["X-Completion-Tokens"] = str(c_tokens)

    GLOBAL_CACHE.set(cache_key, response_data, estimated_tokens=p_tokens + c_tokens)
    return AskResponse(**response_data)


@app.post("/agent", response_model=AgentResponse, status_code=status.HTTP_200_OK, tags=["Agent"])
def agent_endpoint(payload: AgentRequest):
    """
    Autonomous GitGuru Agent Endpoint:
    Executes developer tasks using LangGraph (with Memory & Human Approval Step) or Handwritten ReAct loop.
    Coordinates RAG semantic search and Git action tool {T}.
    Destructive actions pause with pending_approval until confirmed with approved=True.
    """
    if payload.query:
        is_injection, _ = is_prompt_injection(payload.query)
        if is_injection:
            return AgentResponse(
                query=payload.query,
                answer=PROMPT_INJECTION_REFUSAL,
                thread_id=payload.thread_id or "security_session",
                agent_type="security-guardrail",
                pending_approval=None,
                tools_called=[],
                is_approved=False,
                steps=[{"node": "security_check", "status": "BLOCKED", "reason": "PROMPT_INJECTION"}],
                messages_count=1,
            )

    mode = (payload.agent_type or "langgraph").lower()

    if mode == "handwritten":
        result = run_handwritten_agent(
            query=payload.query,
            approved=payload.approved is True,
        )
        return AgentResponse(
            query=result["query"],
            answer=result["final_answer"],
            thread_id=payload.thread_id or "handwritten_session",
            agent_type="handwritten",
            pending_approval=result.get("pending_approval"),
            tools_called=result.get("tools_called", []),
            is_approved=payload.approved,
            steps=result.get("steps", []),
            messages_count=len(result.get("steps", [])),
        )

    # Default: LangGraph with memory and approval step
    result = run_langgraph_agent(
        query=payload.query,
        thread_id=payload.thread_id,
        approved=payload.approved,
    )
    return AgentResponse(
        query=result["query"],
        answer=result["answer"],
        thread_id=result["thread_id"],
        agent_type="langgraph",
        pending_approval=result.get("pending_approval"),
        tools_called=result.get("tools_called", []),
        is_approved=result.get("is_approved"),
        steps=result.get("steps", []),
        messages_count=result.get("messages_count", 0),
    )


@app.get("/metrics", tags=["Observability"])
def get_metrics():
    """
    Exposes production observability telemetry:
    - Traffic volume and endpoint distribution
    - Request processing latency (average and P95)
    - Token consumption (prompt, completion, and cache savings)
    - Response cache performance and hit rates
    - Estimated cost calculations
    """
    return GLOBAL_TELEMETRY.get_metrics()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
