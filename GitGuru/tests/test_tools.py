"""
tests/test_tools.py
Tests for GitGuru Agent Tools ({T}): rag_search, execute_git_action, and generate_git_workflow.
Verifies safe actions and human approval guardrails for destructive actions.
"""

import pytest
from app.tools import (
    rag_search,
    execute_git_action,
    generate_git_workflow,
    is_destructive_action,
    execute_tool,
    DESTRUCTIVE_ACTIONS,
)


def test_rag_search_tool():
    """Verify that the rag_search agent tool retrieves relevant chunks and citations."""
    res = rag_search("How do I resolve a merge conflict?", top_k=2)
    assert res["tool"] == "rag_search"
    assert res["chunks_retrieved"] >= 1
    assert len(res["citations"]) >= 1
    assert res["is_grounded"] is True


def test_safe_git_action_tool():
    """Verify executing safe Git actions (e.g. status, branch_create, clone) succeeds without approval."""
    res_status = execute_git_action("status")
    assert res_status["status"] == "SUCCESS"
    assert res_status["requires_approval"] is False
    assert "working tree clean" in res_status["output"]

    res_branch = execute_git_action("branch_create", target="feature/pytest-suite")
    assert res_branch["status"] == "SUCCESS"
    assert "feature/pytest-suite" in res_branch["output"]


def test_destructive_git_action_requires_approval():
    """
    Verify that destructive operations (reset --hard, push --force, branch -D, clean -fd)
    strictly require human approval and return status APPROVAL_REQUIRED when unapproved.
    """
    res_hard = execute_git_action("reset_hard", target="HEAD~1", approved=False)
    assert res_hard["status"] == "APPROVAL_REQUIRED"
    assert res_hard["requires_approval"] is True
    assert "permanent data loss" in res_hard["warning"].lower()

    res_force = execute_git_action("push_force", target="main", approved=False)
    assert res_force["status"] == "APPROVAL_REQUIRED"
    assert res_force["requires_approval"] is True


def test_destructive_git_action_executes_when_approved():
    """Verify that destructive operations execute successfully when approved=True."""
    res_approved = execute_git_action("reset_hard", target="HEAD~1", approved=True)
    assert res_approved["status"] == "SUCCESS"
    assert res_approved["approved"] is True
    assert "Hard reset executed" in res_approved["output"]


def test_generate_git_workflow_planner():
    """Verify the workflow generator generates structured commands for tasks."""
    wf = generate_git_workflow("create a new feature branch and push to github")
    assert wf["tool"] == "generate_git_workflow"
    assert wf["steps_count"] >= 3
    assert any("switch -c" in cmd for cmd in wf["commands"])


def test_unified_execute_tool_dispatcher():
    """Verify the unified execute_tool dispatcher handles valid and unknown tools."""
    valid_res = execute_tool("execute_git_action", {"action": "status"})
    assert valid_res["status"] == "SUCCESS"

    unknown_res = execute_tool("non_existent_tool", {})
    assert "error" in unknown_res
    assert "not found" in unknown_res["error"]
