"""
app/vectorstore.py
Persistent Chroma VectorStore indexing all GitGuru documentation chunks.
Preserves chunk metadata (source, page, title) and provides semantic similarity queries.
Includes a fail-safe persistent fallback for restricted sandbox environments.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from app.chunking import chunk_all_documents
from app.embed import get_embedding_function, embed_text, cosine_similarity

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_DIR = ROOT / "data" / "chroma_db"
COLLECTION_NAME = "gitguru_chunks"


class LocalPersistentVectorStore:
    """
    Persistent fallback vectorstore used if the host OS blocks Chroma's Rust IPC handles.
    Stores chunks and embeddings in persistent JSON format with identical query semantics.
    """

    def __init__(self, persist_dir: Path):
        self.persist_dir = persist_dir
        try:
            self.persist_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        self.index_file = self.persist_dir / "fallback_index.json"
        self.records: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if self.index_file.exists():
            try:
                self.records = json.loads(self.index_file.read_text(encoding="utf-8"))
            except Exception:
                self.records = []

    def _save(self):
        try:
            self.index_file.write_text(json.dumps(self.records, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    def count(self) -> int:
        return len(self.records)

    def add(self, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]]):
        ef = get_embedding_function()
        vectors = ef(documents)
        existing_ids = {r["id"] for r in self.records}

        for chunk_id, doc, meta, vec in zip(ids, documents, metadatas, vectors):
            if chunk_id in existing_ids:
                continue
            self.records.append({
                "id": chunk_id,
                "document": doc,
                "metadata": meta,
                "embedding": [float(x) for x in vec],
            })
            existing_ids.add(chunk_id)
        self._save()

    def query(self, query_texts: List[str], n_results: int = 5) -> Dict[str, Any]:
        if not query_texts or not self.records:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        query_text = query_texts[0]
        q_vec = embed_text(query_text)

        scored = []
        for r in self.records:
            sim = cosine_similarity(q_vec, r["embedding"])
            dist = max(0.0, 1.0 - sim)
            scored.append((dist, sim, r))

        scored.sort(key=lambda x: x[0])  # Sort by distance ascending
        top = scored[:n_results]

        return {
            "ids": [[item[2]["id"] for item in top]],
            "documents": [[item[2]["document"] for item in top]],
            "metadatas": [[item[2]["metadata"] for item in top]],
            "distances": [[round(item[0], 4) for item in top]],
            "similarities": [[round(item[1], 4) for item in top]],
        }


class VectorStoreManager:
    """
    Manages persistent Chroma collection lifecycle, chunk indexing, and semantic search.
    """

    def __init__(self, persist_dir: Optional[Path] = None):
        self.persist_dir = Path(persist_dir) if persist_dir else DEFAULT_DB_DIR
        try:
            self.persist_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        self.collection_name = COLLECTION_NAME
        self.client = None
        self.collection = None
        self.fallback_store = None
        self._initialize_store()

    def _initialize_store(self):
        """Attempts Chroma persistent client initialization; falls back if restricted."""
        try:
            import chromadb
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

            ef = DefaultEmbeddingFunction()
            self.client = chromadb.PersistentClient(path=str(self.persist_dir))
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=ef,
            )
        except Exception:
            # Fall back gracefully to local persistent vectorstore
            self.fallback_store = LocalPersistentVectorStore(self.persist_dir)

    def count(self) -> int:
        if self.collection is not None:
            return self.collection.count()
        if self.fallback_store is not None:
            return self.fallback_store.count()
        return 0

    def index_chunks(self, force: bool = False) -> int:
        """
        Indexes all documentation chunks from app/chunking.py into the persistent collection.
        Skips if already indexed unless force=True.
        """
        chunks = chunk_all_documents()
        current_count = self.count()

        if current_count >= len(chunks) and not force:
            return current_count

        ids = [c["chunk_id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [
            {
                "source": c["source"],
                "page": int(c["page"]),
                "title": c["title"],
                "category": c["category"],
                "chunk_index": int(c["chunk_index"]),
            }
            for c in chunks
        ]

        if self.collection is not None:
            # Upsert in batches of 40 to stay well within limits
            batch_size = 40
            for i in range(0, len(ids), batch_size):
                end = min(len(ids), i + batch_size)
                self.collection.upsert(
                    ids=ids[i:end],
                    documents=documents[i:end],
                    metadatas=metadatas[i:end],
                )
            return self.collection.count()

        if self.fallback_store is not None:
            self.fallback_store.add(ids=ids, documents=documents, metadatas=metadatas)
            return self.fallback_store.count()

        return 0

    def query_semantic(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Queries persistent collection and formats hits preserving source, page, and title.
        """
        if not query or not query.strip():
            return []

        # Ensure index has chunks
        if self.count() == 0:
            self.index_chunks()

        clean_query = query.strip()

        if self.collection is not None:
            res = self.collection.query(
                query_texts=[clean_query],
                n_results=limit,
                include=["documents", "metadatas", "distances"],
            )
            raw_ids = res.get("ids", [[]])[0]
            raw_docs = res.get("documents", [[]])[0]
            raw_metas = res.get("metadatas", [[]])[0]
            raw_dists = res.get("distances", [[]])[0]

            results = []
            for chunk_id, doc, meta, dist in zip(raw_ids, raw_docs, raw_metas, raw_dists):
                score = round(max(0.0, 1.0 - float(dist)), 4)
                results.append({
                    "chunk_id": str(chunk_id),
                    "text": str(doc),
                    "title": str(meta.get("title", "")),
                    "source": str(meta.get("source", "")),
                    "page": int(meta.get("page", 1)),
                    "category": str(meta.get("category", "")),
                    "similarity_score": score,
                    "distance": round(float(dist), 4),
                })
            return results

        if self.fallback_store is not None:
            res = self.fallback_store.query(query_texts=[clean_query], n_results=limit)
            raw_ids = res.get("ids", [[]])[0]
            raw_docs = res.get("documents", [[]])[0]
            raw_metas = res.get("metadatas", [[]])[0]
            raw_dists = res.get("distances", [[]])[0]
            raw_sims = res.get("similarities", [[]])[0]

            results = []
            for chunk_id, doc, meta, dist, sim in zip(raw_ids, raw_docs, raw_metas, raw_dists, raw_sims):
                results.append({
                    "chunk_id": str(chunk_id),
                    "text": str(doc),
                    "title": str(meta.get("title", "")),
                    "source": str(meta.get("source", "")),
                    "page": int(meta.get("page", 1)),
                    "category": str(meta.get("category", "")),
                    "similarity_score": round(float(sim), 4),
                    "distance": round(float(dist), 4),
                })
            return results

        return []


_VECTORSTORE_INSTANCE = None


def get_vectorstore(persist_dir: Optional[Path] = None) -> VectorStoreManager:
    """Returns singleton VectorStoreManager instance."""
    global _VECTORSTORE_INSTANCE
    if _VECTORSTORE_INSTANCE is None:
        _VECTORSTORE_INSTANCE = VectorStoreManager(persist_dir=persist_dir)
    return _VECTORSTORE_INSTANCE


def query_semantic(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Convenience function for semantic search using the persistent vectorstore."""
    vs = get_vectorstore()
    return vs.query_semantic(query=query, limit=limit)


if __name__ == "__main__":
    import sys

    search_query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "How do I clone a repository?"
    print("=" * 65)
    print("       GitGuru Persistent Chroma VectorStore Diagnostic")
    print("=" * 65)

    vs = get_vectorstore()
    total_indexed = vs.index_chunks()
    print(f"Total chunks in vectorstore: {total_indexed}")

    print(f"\nQuerying: '{search_query}' (limit=3)\n")
    hits = vs.query_semantic(query=search_query, limit=3)

    for rank, hit in enumerate(hits, 1):
        print(f"#{rank} [Score: {hit['similarity_score']:.4f} | Dist: {hit['distance']:.4f}]")
        print(f"   Chunk ID: {hit['chunk_id']}")
        print(f"   Title:    {hit['title']} (Page: {hit['page']})")
        print(f"   Source:   {hit['source']}")
        print(f"   Text:     {hit['text'][:90]}...\n")
    print("=" * 65)
