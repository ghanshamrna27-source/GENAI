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
    ask,
    agent_endpoint,
)
from app.models import (
    QuestionRequest,
    HealthResponse,
    RecordSchema,
    QuestionResponse,
    ChatRequest,
    ChatResponse,
    SemanticSearchResult,
    AskRequest,
    AskResponse,
    Citation,
    AgentRequest,
    AgentResponse,
)
from analysis.explore import explore_records
from app.smart_search import rank_records, SmartSearcher
from app.llm import generate_chat_response, parse_llm_json
from app.chunking import chunk_all_documents, split_text_into_chunks
from app.embed import embed_text, semantic_search
from app.vectorstore import get_vectorstore, query_semantic
from app.rag import answer_question
from app.tools import rag_search, execute_git_action, generate_git_workflow
from app.agent_loop import run_handwritten_agent
from app.graph import run_langgraph_agent


def test_root():
    res = root()
    assert "message" in res
    assert res["version"] == "1.0.0"
    assert "semantic_search" in res["endpoints"]
    assert "chat" in res["endpoints"]
    assert "rag_ask" in res["endpoints"]
    assert "agent" in res["endpoints"]
    print("✓ root() endpoint passed (includes /search/semantic, /chat, /ask, and /agent)")


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


def test_rag_ask_endpoint():
    payload = AskRequest(
        question="How do I clone an existing remote repository onto my local machine?",
        top_k=3
    )
    res = ask(payload)
    assert isinstance(res, AskResponse)
    assert res.is_grounded is True
    assert res.confidence in ("high", "medium")
    assert len(res.citations) >= 1
    top_cit = res.citations[0]
    assert isinstance(top_cit, Citation)
    assert "clone" in top_cit.title.lower()
    assert top_cit.page == 4
    assert top_cit.source.startswith("http")
    assert "Sources & Citations" in res.answer
    print(f"✓ POST /ask passed: answered with {len(res.citations)} citations (Top: '{top_cit.title}', Page {top_cit.page})")


def test_rag_ask_q6_refusal():
    payload = AskRequest(
        question="How do I recover a deleted branch from 6 months ago if my local hard drive was completely formatted, zeroed out, and the code was never pushed to any remote repository?",
        top_k=3
    )
    res = ask(payload)
    assert isinstance(res, AskResponse)
    # Strict Day 8 requirement: Must say "I don't know" for Q6!
    assert "i don't know" in res.answer.lower()
    assert res.is_grounded is False
    assert res.confidence == "low"
    assert len(res.citations) == 0
    print("✓ POST /ask Q6 strict refusal passed: answered with 'I don't know' and 0 hallucinated citations")


def test_rag_module_direct():
    res = answer_question("What is git rebase and when should I use it instead of merge?", top_k=2)
    assert res["is_grounded"] is True
    assert "rebase" in res["answer"].lower()
    assert len(res["citations"]) >= 1
    assert any("rebase" in c["title"].lower() for c in res["citations"])
    print(f"✓ app.rag.answer_question() passed: retrieved {len(res['citations'])} citations for git rebase")


def test_tools_module():
    # 1. RAG Search Tool
    rag_res = rag_search("How do I clone an existing repository?", top_k=2)
    assert rag_res["tool"] == "rag_search"
    assert rag_res["chunks_retrieved"] >= 1
    assert len(rag_res["citations"]) >= 1

    # 2. Safe Git Action Tool
    safe_act = execute_git_action("branch_create", target="feature/test-branch")
    assert safe_act["status"] == "SUCCESS"
    assert safe_act["requires_approval"] is False

    # 3. Destructive Action without approval
    dest_no_appr = execute_git_action("reset_hard", target="HEAD~1", approved=False)
    assert dest_no_appr["status"] == "APPROVAL_REQUIRED"
    assert dest_no_appr["requires_approval"] is True

    # 4. Destructive Action with approval
    dest_appr = execute_git_action("reset_hard", target="HEAD~1", approved=True)
    assert dest_appr["status"] == "SUCCESS"
    assert dest_appr["approved"] is True
    print("✓ app/tools.py passed: rag_search, safe action, and approval-guarded destructive action")


def test_handwritten_agent_loop():
    # 1. Safe multi-step workflow
    res = run_handwritten_agent("How do I clone a repository and check status?")
    assert len(res["steps"]) >= 2
    assert "rag_search" in res["tools_called"]
    assert len(res["final_answer"]) > 20
    assert res["is_grounded"] is True

    # 2. Destructive query requiring approval
    dest_res = run_handwritten_agent("Run git reset --hard to discard all uncommitted changes")
    assert dest_res["pending_approval"] is not None
    assert dest_res["pending_approval"]["requires_approval"] is True
    print(f"✓ app/agent_loop.py passed: executed ReAct loop with {res['iterations']} iterations and detected approval requirement")


def test_langgraph_agent_memory_and_approval():
    test_session = "test_memory_thread_001"

    # Turn 1: Destructive request without approval -> enters Approval Step & pauses with pending_approval
    turn1 = run_langgraph_agent("Force push my commits with git push --force", thread_id=test_session)
    assert turn1["pending_approval"] is not None
    assert turn1["pending_approval"]["requires_approval"] is True
    assert "force" in turn1["pending_approval"]["action"]

    # Turn 2: User approves with approved=True on the same thread_id -> resumes from memory and executes!
    turn2 = run_langgraph_agent("", thread_id=test_session, approved=True)
    assert turn2["pending_approval"] is None
    assert turn2["is_approved"] is True
    assert "Force pushed" in turn2["answer"]
    assert turn2["messages_count"] > turn1["messages_count"]
    print("✓ app/graph.py passed: LangGraph state graph with MemorySaver checkpointer & Human Approval Step")


def test_post_agent_endpoint():
    # 1. LangGraph endpoint safe query
    req1 = AgentRequest(query="How do I create and switch to a new branch?", agent_type="langgraph")
    res1 = agent_endpoint(req1)
    assert isinstance(res1, AgentResponse)
    assert res1.agent_type == "langgraph"
    assert len(res1.tools_called) >= 1

    # 2. Handwritten mode
    req2 = AgentRequest(query="How do I stash uncommitted work?", agent_type="handwritten")
    res2 = agent_endpoint(req2)
    assert isinstance(res2, AgentResponse)
    assert res2.agent_type == "handwritten"
    assert "stash" in res2.answer.lower()

    # 3. LangGraph destructive query with approval cycle
    thread_key = "api_test_approval_002"
    req3_turn1 = AgentRequest(query="Run git reset --hard", thread_id=thread_key, agent_type="langgraph")
    res3_turn1 = agent_endpoint(req3_turn1)
    assert res3_turn1.pending_approval is not None

    req3_turn2 = AgentRequest(query="", thread_id=thread_key, approved=True, agent_type="langgraph")
    res3_turn2 = agent_endpoint(req3_turn2)
    assert res3_turn2.pending_approval is None
    assert res3_turn2.is_approved is True
    print("✓ POST /agent endpoint passed: verified LangGraph, Handwritten, and Approval multi-turn cycle")


def test_streamlit_ui_and_feedback():
    from ui.app import save_user_feedback, FEEDBACK_FILE
    import json

    ui_file = ROOT / "ui" / "app.py"
    assert ui_file.exists(), "ui/app.py must exist"

    # Test saving feedback
    ok = save_user_feedback(
        query="How do I clone a repository?",
        answer="Use git clone <url>.",
        rating="thumbs_up",
        mode="RAG Search (/ask)",
        citations_count=1,
        thread_id="test_suite_thread",
    )
    assert ok is True
    assert FEEDBACK_FILE.exists()
    content = json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
    assert len(content) >= 1
    assert any(c.get("rating") == "thumbs_up" for c in content)

    # Test screenshot file exists
    screenshot = ROOT / "docs" / "screenshots" / "ui_demo.png"
    assert screenshot.exists(), "Screenshot must exist at docs/screenshots/ui_demo.png"
    assert screenshot.stat().st_size > 1000

    print("✓ ui/app.py passed: verified Streamlit UI module, feedback persistence, and UI screenshot")


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
    print("       GitGuru Comprehensive Test Suite (Checkpoint 2)")
    print("=" * 68)
    test_root()
    test_health()
    test_get_records()
    test_get_record_by_id()
    test_search()
    test_ask_questions()
    test_chat_endpoint()
    test_chat_unanswerable_q6()
    test_rag_ask_endpoint()
    test_rag_ask_q6_refusal()
    test_rag_module_direct()
    test_tools_module()
    test_handwritten_agent_loop()
    test_langgraph_agent_memory_and_approval()
    test_post_agent_endpoint()
    test_streamlit_ui_and_feedback()
    test_chunking_metadata()
    test_embedding_and_semantic_search()
    test_vectorstore_and_endpoint()
    test_smart_search_class()
    test_analysis_explore()
    print("=" * 68)
    print("       ALL 21 TEST SUITES PASSED SUCCESSFULLY! (100%)       ")
    print("=" * 68)


if __name__ == "__main__":
    run_all()
