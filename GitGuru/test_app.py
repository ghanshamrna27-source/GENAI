"""
test_app.py
Unit and integration tests for GitGuru FastAPI endpoints, smart search, and data analysis.
"""

import sys
from pathlib import Path
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import root, health, get_records, get_record, search_records, ask_question
from app.models import QuestionRequest, HealthResponse, RecordSchema, QuestionResponse
from analysis.explore import explore_records
from app.smart_search import rank_records, SmartSearcher


def test_root():
    res = root()
    assert "message" in res
    assert res["version"] == "1.0.0"
    assert "health" in res["endpoints"]
    print("✓ root() endpoint passed")


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
    print("✓ explore_records() passed:")
    print("   Fact 1:", insights["fact_1"])
    print("   Fact 2:", insights["fact_2"])
    print("   Fact 3:", insights["fact_3"])


def run_all():
    print("=" * 65)
    print("       GitGuru Comprehensive Test Suite       ")
    print("=" * 65)
    test_root()
    test_health()
    test_get_records()
    test_get_record_by_id()
    test_search()
    test_ask_questions()
    test_smart_search_class()
    test_analysis_explore()
    print("=" * 65)
    print("       ALL TESTS PASSED SUCCESSFULLY! (100%)       ")
    print("=" * 65)


if __name__ == "__main__":
    run_all()
