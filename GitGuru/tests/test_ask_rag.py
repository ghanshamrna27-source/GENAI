"""
tests/test_ask_rag.py
Tests for RAG Question Answering (POST /ask) with a Fake/Mocked LLM,
grounding verification, and strict anti-hallucination guardrails (Q6).
"""

from unittest.mock import patch
import pytest
from app.main import ask
from app.models import AskRequest, AskResponse, Citation
from app.rag import answer_question


def test_ask_endpoint_with_fake_llm():
    """
    Test POST /ask with a fake LLM: mocks the LLM provider to ensure
    the RAG pipeline passes retrieved context and synthesizes grounded answers with citations.
    """
    fake_llm_response = {
        "answer": (
            "To clone an existing repository onto your local machine, run 'git clone <url>'. "
            "This downloads a full copy of all branches and history [Clone Repository (git clone), Page 4]."
        ),
        "confidence": "high",
        "follow_up": "Check the remote URL with git remote -v.",
        "provider": "fake-llm-mock",
        "model": "fake-llama-test",
    }

    with patch("app.llm.call_groq", return_value=fake_llm_response):
        with patch.dict("os.environ", {"GROQ_API_KEY": "gsk_fake_test_key_12345"}):
            payload = AskRequest(
                question="How do I clone an existing remote repository onto my local machine?",
                top_k=2,
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


def test_ask_endpoint_offline_grounded_synthesis():
    """Verify that when no LLM API key is present, offline synthesis provides grounded answers with citations."""
    with patch.dict("os.environ", {"GROQ_API_KEY": "", "GEMINI_API_KEY": ""}):
        payload = AskRequest(
            question="How do I create and switch to a new Git branch?",
            top_k=2,
        )
        res = ask(payload)
        assert isinstance(res, AskResponse)
        assert res.is_grounded is True
        assert "branch" in res.answer.lower()
        assert len(res.citations) >= 1
        assert any("branch" in c.title.lower() for c in res.citations)


def test_ask_unanswerable_q6_strict_refusal():
    """
    Strict Day 8 & Day 11 requirement:
    Question 6 (recovering from a formatted, zeroed-out hard drive with no remote push)
    MUST say 'I don't know' and emit 0 false citations.
    """
    payload = AskRequest(
        question="How do I recover a deleted branch from 6 months ago if my local hard drive was completely formatted, zeroed out, and the code was never pushed to any remote repository?",
        top_k=3,
    )
    res = ask(payload)
    assert isinstance(res, AskResponse)
    assert "i don't know" in res.answer.lower()
    assert res.is_grounded is False
    assert res.confidence == "low"
    assert len(res.citations) == 0


def test_ask_empty_question_handling():
    """Verify that empty or whitespace-only questions are handled gracefully."""
    res = answer_question("")
    assert "i don't know" in res["answer"].lower()
    assert res["is_grounded"] is False
    assert len(res["citations"]) == 0
