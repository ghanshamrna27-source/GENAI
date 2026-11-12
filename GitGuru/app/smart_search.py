"""
app/smart_search.py
Smart Search using TF-IDF (Term Frequency-Inverse Document Frequency)
and Cosine Similarity to rank Git and GitHub knowledge records.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.records import load_records


def build_record_corpus(records: List[Dict[str, Any]]) -> List[str]:
    """
    Constructs a textual document representation for each record by combining
    informative fields (title, keyword, question, category, answer).
    """
    corpus = []
    for r in records:
        title = str(r.get("title", ""))
        keyword = str(r.get("keyword", ""))
        category = str(r.get("category", ""))
        question = str(r.get("question", ""))
        answer = str(r.get("answer", ""))
        # Give title and keyword extra weight by repeating them
        combined_text = f"{title} {title} {keyword} {keyword} {category} {question} {answer}"
        corpus.append(combined_text)
    return corpus


class SmartSearcher:
    """
    TF-IDF + Cosine Similarity search engine for GitGuru records.
    """

    def __init__(self, records: Optional[List[Dict[str, Any]]] = None):
        self.records = records if records is not None else load_records()
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            lowercase=True
        )
        self.corpus = build_record_corpus(self.records)
        if self.corpus:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus)
        else:
            self.tfidf_matrix = None

    def search(
        self,
        query: str,
        limit: Optional[int] = None,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Rank records against query using cosine similarity between TF-IDF vectors.
        """
        if not query or not query.strip() or self.tfidf_matrix is None or not self.records:
            return []

        clean_query = query.strip()
        query_vec = self.vectorizer.transform([clean_query])
        scores = cosine_similarity(query_vec, self.tfidf_matrix)[0]

        ranked_indices = np.argsort(scores)[::-1]

        results = []
        for idx in ranked_indices:
            score = float(scores[idx])
            if score < min_score:
                continue
            if score == 0.0 and len(results) > 0:
                # Once we hit zero score after positive matches, stop
                break
            record_copy = dict(self.records[idx])
            record_copy["similarity_score"] = round(score, 4)
            results.append(record_copy)
            if limit is not None and len(results) >= limit:
                break

        return results


def rank_records(
    query: str,
    records: Optional[List[Dict[str, Any]]] = None,
    limit: Optional[int] = None,
    min_score: float = 0.01
) -> List[Dict[str, Any]]:
    """
    Convenience function to rank records using TF-IDF and Cosine Similarity.
    Used by /search endpoint in app/main.py.
    """
    searcher = SmartSearcher(records=records)
    return searcher.search(query=query, limit=limit, min_score=min_score)


if __name__ == "__main__":
    import sys

    search_query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "how do I resolve merge conflict"
    print(f"=== GitGuru Smart Search (TF-IDF + Cosine Similarity) ===")
    print(f"Query: '{search_query}'\n")

    matches = rank_records(search_query, limit=5, min_score=0.0)
    if not matches:
        print("No matching records found.")
    else:
        for rank, match in enumerate(matches, 1):
            print(f"#{rank} [Score: {match['similarity_score']:.4f}] - ID {match['id']}: {match['title']} ({match['category']})")
            print(f"   Question: {match['question']}")
            print(f"   Answer:   {match['answer'][:100]}...")
            print(f"   URL:      {match['source_url']}\n")

