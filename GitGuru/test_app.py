"""
test_app.py
Comprehensive automated test suite for GitGuru FastAPI endpoints, smart search,
data analysis, LLM chat service, chunking, and Chroma semantic search.
"""

import sys
from pathlib import Path
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import (
    root,
    health,
    get_records,
    get_record,
    search_records,
    search_semantic,
    ask_question,
    chat,
)
from app.models import (
    QuestionRequest,
    HealthResponse,
    RecordSchema,
    QuestionResponse,
    ChatRequest,
    ChatResponse,
    SemanticSearchResult,
)
from analysis.explore import explore_records
from app.smart_search import rank_records, SmartSearcher
from app.llm import generate_chat_response, parse_llm_json
from app.chunking import chunk_all_documents, split_text_into_chunks
from app.embed import embed_text, semantic_search
from app.vectorstore import get_vectorstore, query_semantic


def test_root():
    res = root()
    assert "message" in res
    assert res["version"] == "1.0.0"
    assert "semantic_search" in res["endpoints"]
    assert "chat" in res["endpoints"]
    print("✓ root() endpoint passed (includes /search/semantic and /chat)")


def test_health():
    res = health()
    assert isinstance(res, HealthResponse)
    assert res.status == "ok"
    assert res.project == "GitGuru"
    assert res.records_count >= 5
    print(f"✓ health() passed: project={res.project}, records={res.records_count}")


def test_get_records():
    all_records = get_records()
    assert len(all_records) >= 5
    print(f"✓ get_records() returned {len(all_records)} records")

    limited_records = get_records(limit=3)
    assert len(limited_records) == 3
    print("✓ get_records(limit=3) returned exactly 3 records")


def test_get_record_by_id():
    rec = get_record(id=1)
    assert rec["id"] == 1
    assert "Git" in rec["category"]
    print(f"✓ get_record(1) returned: {rec['title']}")

    try:
        get_record(id=9999)
        assert False, "Expected HTTPException for missing ID"
    except HTTPException as e:
        assert e.status_code == 404
        assert "not found" in e.detail.lower()
        print(f"✓ get_record(9999) correctly raised 404: {e.detail}")


def test_search():
    results = search_records(q="how to resolve merge conflict", limit=5)
    assert len(results) > 0
    top = results[0]
    assert "similarity_score" in top
    assert top["similarity_score"] > 0.0
    assert "conflict" in top["title"].lower() or "conflict" in top["question"].lower() or "conflict" in top["keyword"].lower()
    print(f"✓ search_records('conflict') passed: top match='{top['title']}' (score: {top['similarity_score']})")


def test_ask_questions():
    payload = QuestionRequest(
        question="How do I push changes to remote repository?",
        category="GitHub",
        asker="Alex"
    )
    res = ask_question(payload)
    assert isinstance(res, QuestionResponse)
    assert res.status == "success"
    assert res.matched_record is not None
    assert "push" in res.matched_record.title.lower() or "push" in res.matched_record.answer.lower()
    print(f"✓ ask_question() passed: matched='{res.matched_record.title}', asker={res.asker}")


def test_chat_endpoint():
    payload = ChatRequest(
        message="How do I create and switch to a new Git branch?",
        version="v2"
    )
    res = chat(payload)
    assert isinstance(res, ChatResponse)
    assert len(res.answer) > 10
    assert res.confidence in ("high", "medium", "low")
    assert len(res.follow_up) > 5
    print(f"✓ POST /chat passed (confidence: {res.confidence})")


def test_chat_unanswerable_q6():
    payload = ChatRequest(
        message="How do I recover a deleted branch from 6 months ago if my local hard drive was completely formatted, zeroed out, and the code was never pushed to any remote repository?",
        version="v2"
    )
    res = chat(payload)
    assert isinstance(res, ChatResponse)
    assert res.confidence == "low"
    assert "cannot" in res.answer.lower() or "unrecoverable" in res.answer.lower()
    print("✓ POST /chat Q6 boundary test passed: properly recognized unrecoverable data")


def test_chunking_metadata():
    chunks = chunk_all_documents()
    assert len(chunks) >= 40
    for c in chunks:
        assert "chunk_id" in c
        assert "source" in c and c["source"].startswith("http")
        assert "page" in c and isinstance(c["page"], int)
        assert "title" in c and len(c["title"]) > 0
        assert "text" in c and len(c["text"]) > 10
    print(f"✓ chunk_all_documents() generated {len(chunks)} chunks with verified source, page, and title metadata")


def test_embedding_and_semantic_search():
    v = embed_text("Git clone repository")
    assert len(v) > 0
    hits = semantic_search(query="how to clone repository", top_k=3)
    assert len(hits) == 3
    top_hit = hits[0]
    assert "clone" in top_hit["title"].lower() or "clone" in top_hit["text"].lower()
    assert top_hit["similarity_score"] > 0.50
    assert "source" in top_hit and "page" in top_hit and "title" in top_hit
    print(f"✓ semantic_search() passed: top hit='{top_hit['title']}', score={top_hit['similarity_score']}")


def test_vectorstore_and_endpoint():
    vs = get_vectorstore()
    count = vs.index_chunks()
    assert count >= 40

    endpoint_hits = search_semantic(q="resolve merge conflict", limit=3)
    assert len(endpoint_hits) == 3
    top = endpoint_hits[0]
    assert "conflict" in top["title"].lower() or "conflict" in top["text"].lower()
    assert top["page"] == 11
    assert "source" in top and len(top["source"]) > 0
    assert "title" in top and len(top["title"]) > 0
    print(f"✓ GET /search/semantic passed: top hit='{top['title']}' (Page: {top['page']}), score={top['similarity_score']}")


def test_smart_search_class():
    searcher = SmartSearcher()
    ranked = searcher.search("clone repository", limit=3)
    assert len(ranked) > 0
    assert "clone" in ranked[0]["title"].lower() or "clone" in ranked[0]["keyword"].lower()
    print(f"✓ SmartSearcher.search('clone repository') passed: top='{ranked[0]['title']}'")


def test_analysis_explore():
    insights = explore_records()
    assert insights["total_records"] >= 5
    assert "fact_1" in insights and "Git" in insights["fact_1"]
    assert "fact_2" in insights and "words" in insights["fact_2"]
    assert "fact_3" in insights and "keywords" in insights["fact_3"]
    print("✓ explore_records() passed 3 facts with pandas")


def run_all():
    print("=" * 68)
    print("       GitGuru Comprehensive Test Suite (S1 + S2 Complete)")
    print("=" * 68)
    test_root()
    test_health()
    test_get_records()
    test_get_record_by_id()
    test_search()
    test_ask_questions()
    test_chat_endpoint()
    test_chat_unanswerable_q6()
    test_chunking_metadata()
    test_embedding_and_semantic_search()
    test_vectorstore_and_endpoint()
    test_smart_search_class()
    test_analysis_explore()
    print("=" * 68)
    print("       ALL 13 TEST SUITES PASSED SUCCESSFULLY! (100%)       ")
    print("=" * 68)


if __name__ == "__main__":
    run_all()
