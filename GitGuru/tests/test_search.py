"""
tests/test_search.py
Tests for TF-IDF Smart Search and Chroma dense semantic search.
"""

import pytest
from app.smart_search import rank_records, SmartSearcher
from app.main import search_records, search_semantic
from app.embed import semantic_search


def test_smart_search_keyword_matching():
    """Verify TF-IDF search returns relevant records for Git concepts."""
    results = rank_records("resolve merge conflict", limit=3)
    assert len(results) > 0
    top = results[0]
    assert "conflict" in top["title"].lower() or "conflict" in top["answer"].lower()
    assert top["similarity_score"] > 0.0


def test_smart_searcher_class_instance():
    """Verify the SmartSearcher class correctly indexes and searches documents."""
    searcher = SmartSearcher()
    hits = searcher.search("clone remote repository", limit=2)
    assert len(hits) == 2
    assert any("clone" in h["title"].lower() for h in hits)


def test_search_api_empty_query():
    """Verify that searching with an empty string returns an empty list."""
    res = search_records(q="")
    assert res == []

    res_whitespace = search_records(q="   ")
    assert res_whitespace == []


def test_semantic_dense_search():
    """Verify dense embedding semantic search matches conceptual queries."""
    hits = semantic_search("how do I clone an existing remote repository onto my local machine", top_k=3)
    assert len(hits) == 3
    top = hits[0]
    assert "clone" in top["title"].lower() or "clone" in top["text"].lower()
    assert top["similarity_score"] > 0.40
    assert "source" in top and "page" in top and "title" in top


def test_api_semantic_search_endpoint():
    """Verify the GET /search/semantic endpoint returns expected schema metadata."""
    results = search_semantic(q="create and switch branch", limit=2)
    assert len(results) == 2
    top = results[0]
    assert "branch" in top["title"].lower() or "branch" in top["text"].lower()
    assert top["page"] in (9, 10, 4)
