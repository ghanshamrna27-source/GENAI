"""
tests/test_health.py
Tests for FastAPI service health check and general metadata endpoints.
"""

import pytest
from app.main import health, root
from app.models import HealthResponse


def test_health_endpoint():
    """Verify GET /health returns valid status, project name, and record counts."""
    res = health()
    assert isinstance(res, HealthResponse)
    assert res.status == "ok"
    assert res.project == "GitGuru"
    assert res.records_count >= 20
    assert res.version == "1.0.0"


def test_root_endpoint_metadata():
    """Verify GET / root endpoint exposes documentation and API routes."""
    res = root()
    assert "message" in res
    assert "GitGuru" in res["message"]
    assert res["version"] == "1.0.0"
    assert res["documentation"] == "/docs"

    endpoints = res["endpoints"]
    assert "health" in endpoints
    assert "smart_search" in endpoints
    assert "semantic_search" in endpoints
    assert "rag_ask" in endpoints
    assert "agent" in endpoints
