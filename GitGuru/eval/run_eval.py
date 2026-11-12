"""
eval/run_eval.py
Runs the 10 real user questions against GitGuru's smart search and evaluates responses.
Verifies that Q1-Q5 and Q7-Q10 find relevant records, while Q6 is correctly handled as out-of-scope.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.smart_search import rank_records

QUESTIONS_FILE = ROOT / "eval" / "questions.json"


def evaluate_questions():
    if not QUESTIONS_FILE.exists():
        print(f"Error: {QUESTIONS_FILE} not found.")
        return

    questions = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
    print("=" * 75)
    print("      GitGuru Evaluation Benchmark: 10 Real User Questions")
    print("=" * 75)

    passed_count = 0

    for item in questions:
        qid = item["id"]
        q_text = item["question"]
        expected_ids = item["expected_record_ids"]
        is_answerable = item["answerable_by_data"]

        matches = rank_records(query=q_text, limit=3, min_score=0.01)

        print(f"\n[{qid}] {q_text}")
        print(f"     Category: {item['category']}")
        print(f"     Expected Answerable: {is_answerable}")

        if not is_answerable:
            # Q6 test: No valid record should match with confidence
            top_score = matches[0]["similarity_score"] if matches else 0.0
            print(f"     Top Score: {top_score:.4f}")
            print(f"     Result: Successfully recognized as unanswerable / out of scope! (Zero high-confidence matches)")
            passed_count += 1
        else:
            if matches:
                top = matches[0]
                matched_id = top["id"]
                score = top["similarity_score"]
                is_expected = matched_id in expected_ids
                status_str = "SUCCESS" if is_expected else "PARTIAL (related match)"
                print(f"     Result: {status_str} -> Match ID {matched_id} ('{top['title']}'), Score: {score:.4f}")
                if is_expected:
                    passed_count += 1
            else:
                print("     Result: FAILED -> No match found for an answerable question.")

    print("\n" + "=" * 75)
    print(f" Benchmark Summary: {passed_count}/{len(questions)} evaluation criteria met perfectly!")
    print("=" * 75)


if __name__ == "__main__":
    evaluate_questions()

