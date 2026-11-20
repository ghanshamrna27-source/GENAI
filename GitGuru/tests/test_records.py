"""
tests/test_records.py
Tests for GitGuru knowledge base records retrieval and schema validation.
"""

import pytest
from fastapi import HTTPException
from app.records import load_records, get_by_id
from app.main import get_records, get_record
from app.models import RecordSchema, Record


def test_load_records_non_empty():
    """Verify that records are loaded correctly and contain at least 20 items."""
    records = load_records()
    assert isinstance(records, list)
    assert len(records) >= 20
    first = records[0]
    assert "id" in first
    assert "title" in first
    assert "answer" in first
    assert "source_url" in first


def test_get_record_by_valid_id():
    """Verify retrieving a specific record by its ID."""
    rec = get_by_id(1)
    assert rec is not None
    assert rec["id"] == 1
    assert "About Git" in rec["title"]
    assert "git-scm.com" in rec["source_url"]


def test_get_record_by_missing_id():
    """Verify that missing record IDs return None."""
    rec = get_by_id(99999)
    assert rec is None


def test_api_get_records_with_limit():
    """Verify that GET /records endpoint supports the limit parameter."""
    res_all = get_records()
    assert len(res_all) >= 20

    res_limited = get_records(limit=5)
    assert len(res_limited) == 5


def test_api_get_record_404_handling():
    """Verify that requesting an invalid ID via the API raises HTTPException 404."""
    with pytest.raises(HTTPException) as excinfo:
        get_record(id=88888)
    assert excinfo.value.status_code == 404
    assert "not found" in excinfo.value.detail.lower()


def test_record_dataclass_and_schema():
    """Verify conversion between Record dataclass and Pydantic schema."""
    raw = {
        "id": 99,
        "category": "Git Test",
        "title": "Test Title",
        "keyword": "test",
        "question": "How to test?",
        "answer": "Run pytest.",
        "source_url": "https://example.com/test",
    }
    obj = Record.from_dict(raw)
    assert obj.id == 99
    schema = RecordSchema(**obj.to_dict())
    assert schema.title == "Test Title"
