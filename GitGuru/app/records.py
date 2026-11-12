import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from data.sample_records import records as SAMPLE_RECORDS

ROOT = Path(__file__).resolve().parents[1]
RECORDS_FILE = ROOT / "data" / "records.json"

def load_records() -> List[Dict[str, Any]]:
    if RECORDS_FILE.exists():
        try:
            data = json.loads(RECORDS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                return data
        except (OSError, json.JSONDecodeError):
            pass
    return [dict(r) for r in SAMPLE_RECORDS]

def save_records(records: List[Dict[str, Any]]) -> bool:
    try:
        RECORDS_FILE.parent.mkdir(parents=True, exist_ok=True)
        RECORDS_FILE.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except OSError:
        return False

def search(keyword: str) -> List[Dict[str, Any]]:
    term = keyword.strip().lower()
    if not term:
        return []
    return [
        r for r in load_records()
        if term in " ".join(str(r.get(k, "")) for k in ("category", "title", "keyword", "question", "answer")).lower()
    ]

def count_by(category: str) -> int:
    return sum(
        1 for r in load_records()
        if r.get("category", "").lower() == category.strip().lower()
    )

def get_by_id(record_id: int) -> Optional[Dict[str, Any]]:
    return next((r for r in load_records() if int(r.get("id", -1)) == int(record_id)), None)

def add_record(record_dict: Dict[str, Any]) -> Dict[str, Any]:
    records = load_records()
    max_id = max((int(r.get("id", 0)) for r in records), default=0)
    record_dict["id"] = max_id + 1
    records.append(record_dict)
    save_records(records)
    return record_dict
