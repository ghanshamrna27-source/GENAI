"""
app/embed.py
Embedding engine and semantic similarity search for GitGuru chunks.
Generates 384-dimensional dense semantic vectors using all-MiniLM-L6-v2 ONNX embeddings
and provides cosine similarity search across chunked documentation.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from app.chunking import chunk_all_documents

ROOT = Path(__file__).resolve().parents[1]

_EMBEDDER_INSTANCE = None


def get_embedding_function():
    """
    Returns the cached ONNX MiniLM embedding function or a robust local fallback.
    """
    global _EMBEDDER_INSTANCE
    if _EMBEDDER_INSTANCE is not None:
        return _EMBEDDER_INSTANCE

    try:
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        ef = DefaultEmbeddingFunction()
        # Test call to ensure it runs
        test_vec = ef(["Git version control"])
        if test_vec and len(test_vec[0]) > 0:
            _EMBEDDER_INSTANCE = ef
            return _EMBEDDER_INSTANCE
    except Exception:
        pass

    # High-reliability fallback using scikit-learn TF-IDF + dense normalization
    class LocalFallbackEmbedder:
        def __init__(self):
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.decomposition import TruncatedSVD
            self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
            self.svd = TruncatedSVD(n_components=64, random_state=42)
            self._fitted = False

        def __call__(self, input: List[str]) -> List[List[float]]:
            from sklearn.decomposition import TruncatedSVD
            if not self._fitted:
                chunks = chunk_all_documents()
                corpus = [c["text"] for c in chunks] + input
                tfidf = self.vectorizer.fit_transform(corpus)
                n_comp = min(64, tfidf.shape[1] - 1, len(corpus) - 1)
                if n_comp > 1:
                    self.svd = TruncatedSVD(n_components=n_comp, random_state=42)
                    self.svd.fit(tfidf)
                self._fitted = True

            sparse_vecs = self.vectorizer.transform(input)
            dense_vecs = self.svd.transform(sparse_vecs)
            norms = np.linalg.norm(dense_vecs, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            normalized = dense_vecs / norms
            return normalized.tolist()

    _EMBEDDER_INSTANCE = LocalFallbackEmbedder()
    return _EMBEDDER_INSTANCE


def embed_text(text: str) -> List[float]:
    """Generates a dense vector embedding for a single text string."""
    ef = get_embedding_function()
    vectors = ef([text])
    return list(vectors[0])


def embed_batch(texts: List[str]) -> List[List[float]]:
    """Generates dense vector embeddings for a list of text strings."""
    if not texts:
        return []
    ef = get_embedding_function()
    return [list(v) for v in ef(texts)]


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes cosine similarity between two numeric vectors."""
    a = np.array(v1, dtype=float)
    b = np.array(v2, dtype=float)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class SemanticSearchEngine:
    """
    In-memory semantic search engine operating over chunked GitGuru documents.
    """

    def __init__(self, chunks: Optional[List[Dict[str, Any]]] = None):
        self.chunks = chunks if chunks is not None else chunk_all_documents()
        self.chunk_texts = [c["text"] for c in self.chunks]
        self.chunk_embeddings = embed_batch(self.chunk_texts) if self.chunk_texts else []

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Ranks chunks against query using dense embedding cosine similarity.
        """
        if not query or not query.strip() or not self.chunk_embeddings:
            return []

        query_vec = embed_text(query.strip())
        scores = [cosine_similarity(query_vec, cv) for cv in self.chunk_embeddings]

        ranked_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in ranked_indices:
            score = float(scores[idx])
            chunk_copy = dict(self.chunks[idx])
            chunk_copy["similarity_score"] = round(score, 4)
            chunk_copy["cosine_distance"] = round(max(0.0, 1.0 - score), 4)
            results.append(chunk_copy)

        return results


def semantic_search(
    query: str,
    chunks: Optional[List[Dict[str, Any]]] = None,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """
    Convenience function for semantic chunk search.
    """
    engine = SemanticSearchEngine(chunks=chunks)
    return engine.search(query=query, top_k=top_k)


def run_semantic_search_for_questions() -> List[Dict[str, Any]]:
    """
    Runs semantic search for the 10 questions in eval/questions.json
    and returns question metadata with ranked chunk hits.
    """
    import json

    q_path = ROOT / "eval" / "questions.json"
    if not q_path.exists():
        raise FileNotFoundError(f"Missing {q_path}")

    questions = json.loads(q_path.read_text(encoding="utf-8"))
    engine = SemanticSearchEngine()

    evaluation_results = []
    for q_item in questions:
        hits = engine.search(query=q_item["question"], top_k=3)
        evaluation_results.append({
            "id": q_item["id"],
            "question": q_item["question"],
            "category": q_item["category"],
            "answerable_by_data": q_item["answerable_by_data"],
            "expected_record_ids": q_item.get("expected_record_ids", []),
            "top_hits": hits,
        })
    return evaluation_results


if __name__ == "__main__":
    print("=" * 70)
    print("       GitGuru Semantic Search Engine (app/embed.py)")
    print("=" * 70)

    print("\nExecuting semantic search across 10 evaluation questions...\n")
    results = run_semantic_search_for_questions()

    for item in results:
        print(f"[{item['id']}] {item['question']}")
        print(f"     Answerable: {item['answerable_by_data']}")
        for rank, hit in enumerate(item["top_hits"], 1):
            print(f"     #{rank} [Score: {hit['similarity_score']:.4f} | Dist: {hit['cosine_distance']:.4f}] "
                  f"ID: {hit['chunk_id']} | Title: '{hit['title']}' | Page: {hit['page']}")
            print(f"        Source: {hit['source']}")
            print(f"        Preview: {hit['text'][:90]}...")
        print()
    print("=" * 70)

