"""
tests/test_agent.py
Tests for Hand-Written ReAct Agent and LangGraph Agent with Memory & Approval Step.
"""

import pytest
from app.agent_loop import run_handwritten_agent
from app.graph import run_langgraph_agent
from app.main import agent_endpoint
from app.models import AgentRequest, AgentResponse


def test_handwritten_react_agent_safe_query():
    """Verify the hand-written ReAct loop coordinates RAG search and tool {T}."""
    res = run_handwritten_agent("How do I clone a repository and check working tree status?")
    assert res["iterations"] >= 2
    assert "rag_search" in res["tools_called"]
    assert "execute_git_action" in res["tools_called"]
    assert len(res["steps"]) >= 2
    assert res["is_grounded"] is True
    assert len(res["final_answer"]) > 30


def test_handwritten_react_agent_detects_destructive_action():
    """Verify the hand-written agent identifies destructive commands requiring confirmation."""
    res = run_handwritten_agent("Run git reset --hard to discard all modifications")
    assert res["pending_approval"] is not None
    assert res["pending_approval"]["requires_approval"] is True
    assert "reset_hard" in res["pending_approval"]["action"]


def test_langgraph_agent_multi_turn_memory_and_approval():
    """
    Verify the LangGraph StateGraph agent:
    Turn 1: Destructive request pauses at the Approval Step.
    Turn 2: Supplying approved=True with the same thread_id resumes from MemorySaver and completes execution.
    """
    session_id = "pytest_session_approval_test"

    # Turn 1: Request destructive operation without approval
    turn1 = run_langgraph_agent("Run git reset --hard to discard local changes", thread_id=session_id)
    assert turn1["pending_approval"] is not None
    assert turn1["pending_approval"]["requires_approval"] is True
    assert "reset_hard" in turn1["pending_approval"]["action"]

    # Turn 2: Confirm with approved=True on the same session
    turn2 = run_langgraph_agent("", thread_id=session_id, approved=True)
    assert turn2["pending_approval"] is None
    assert turn2["is_approved"] is True
    assert "reset" in turn2["answer"].lower()
    assert turn2["messages_count"] > turn1["messages_count"]


def test_api_agent_endpoint():
    """Verify the POST /agent FastAPI endpoint handles both LangGraph and handwritten modes."""
    # LangGraph mode
    req_lg = AgentRequest(query="How do I create a new branch?", agent_type="langgraph")
    res_lg = agent_endpoint(req_lg)
    assert isinstance(res_lg, AgentResponse)
    assert res_lg.agent_type == "langgraph"
    assert len(res_lg.tools_called) >= 1

    # Handwritten mode
    req_hw = AgentRequest(query="How do I stash working changes?", agent_type="handwritten")
    res_hw = agent_endpoint(req_hw)
    assert isinstance(res_hw, AgentResponse)
    assert res_hw.agent_type == "handwritten"
    assert "stash" in res_hw.answer.lower()
