import json
from pathlib import Path
from data.sample_records import records as SAMPLE_RECORDS

ROOT = Path(__file__).resolve().parents[1]
RECORDS_FILE = ROOT / "data" / "records.json"

def load_records():
    if RECORDS_FILE.exists():
        try:
            data = json.loads(RECORDS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                return data
        except (OSError, json.JSONDecodeError):
            pass
    return SAMPLE_RECORDS.copy()

def search(keyword):
    term = keyword.strip().lower()
    return [r for r in load_records()
            if term and term in " ".join(str(r.get(k, "")) for k in
            ("category", "title", "keyword", "question", "answer")).lower()]

def count_by(category):
    return sum(1 for r in load_records()
               if r.get("category", "").lower() == category.strip().lower())

def get_by_id(record_id):
    return next((r for r in load_records() if r.get("id") == record_id), None)
