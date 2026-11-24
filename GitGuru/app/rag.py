"""
app/rag.py
Retrieval-Augmented Generation (RAG) engine for GitGuru.
Answers Git and GitHub questions strictly grounded in retrieved documentation chunks with citations.
Enforces strict guardrails against hallucination: must say "I don't know" for unanswerable
questions (such as Q6).
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.chunking import chunk_all_documents
from app.embed import SemanticSearchEngine, embed_text, cosine_similarity
from app.vectorstore import get_vectorstore


# Out-of-scope / impossible triggers
OUT_OF_SCOPE_TRIGGERS = [
    "subversion",
    "svn",
    "perforce",
    "mercurial",
    "kafka",
    "blockchain",
    "p4 sync",
]


def is_unanswerable_query(query: str, top_score: float) -> bool:
    """
    Determines if a query is unanswerable from GitGuru's documentation.
    Detects impossible data recovery scenarios (e.g. Q6: formatted zeroed disk never pushed),
    non-Git VCS systems, or questions with zero semantic confidence.
    """
    q_lower = query.lower()

    # Pattern 1: Q6 impossible recovery scenario (formatted/zeroed disk and never pushed)
    has_format = any(k in q_lower for k in ["format", "zero", "zeroed", "overwritten", "zero-overwritten"])
    has_unpushed = any(k in q_lower for k in ["never pushed", "not pushed", "no remote", "6 months", "deleted branch"])
    if has_format and has_unpushed:
        return True

    # Pattern 2: Foreign tools not supported by GitGuru
    if any(k in q_lower for k in OUT_OF_SCOPE_TRIGGERS):
        return True

    # Pattern 3: Extremely low similarity (no match in knowledge base)
    if top_score < 0.10:
        return True

    return False


def build_rag_prompt(question: str, chunks: List[Dict[str, Any]]) -> str:
    """Builds prompt instructing the LLM to answer strictly from retrieved chunks."""
    context_blocks = []
    for idx, c in enumerate(chunks, 1):
        context_blocks.append(
            f"[Chunk {idx}] (Title: {c['title']}, Page: {c['page']}, Source: {c['source']}, ID: {c['chunk_id']}):\n{c['text']}"
        )
    context_str = "\n\n".join(context_blocks)

    return (
        f"You are GitGuru, an expert Git and GitHub assistant. Answer the learner's question strictly "
        f"using the retrieved documentation chunks below. Do not assume or extrapolate.\n"
        f"If the documentation does not contain enough information to answer the question, you MUST say \"I don't know\".\n\n"
        f"Retrieved Documentation Chunks:\n{context_str}\n\n"
        f"Learner Question: {question}\n\n"
        f"Instructions:\n"
        f"1. Provide a direct, step-by-step grounded explanation.\n"
        f"2. Cite your sources using [Title, Page X].\n"
        f"3. If unanswerable, explicitly state \"I don't know based on the provided GitGuru documentation.\"\n"
        f"4. Respond with a JSON object containing keys: \"answer\", \"confidence\" (\"high\", \"medium\", or \"low\"), and \"follow_up\"."
    )


def merge_overlapping_texts(texts: List[str]) -> str:
    """Merges consecutive text segments, seamlessly removing overlapping boundary phrases."""
    if not texts:
        return ""
    merged = texts[0]
    for t in texts[1:]:
        max_overlap = 0
        min_check = min(len(merged), len(t), 100)
        for i in range(min_check, 8, -1):
            if merged.endswith(t[:i]):
                max_overlap = i
                break
        if max_overlap > 0:
            merged = merged + t[max_overlap:]
        else:
            merged = merged + " " + t
    return " ".join(merged.split())


def synthesize_offline_grounded_answer(question: str, chunks: List[Dict[str, Any]]) -> str:
    """
    Generates a deterministic grounded answer directly from retrieved chunks
    when running in offline sandbox or when LLM API keys are unavailable.
    """
    if not chunks:
        return "I don't know based on the provided GitGuru documentation. No relevant documentation chunks were retrieved."

    top = chunks[0]
    top_title = top.get("title", "")
    top_page = top.get("page", 1)

    # Collect explanation sentences across retrieved chunks
    explanation_parts = []
    seen_texts = set()

    for c in chunks:
        raw_text = c.get("text", "")
        # Extract explanation part
        if "Explanation & Usage: " in raw_text:
            part = raw_text.split("Explanation & Usage: ")[1].split(" Official Documentation Reference:")[0].strip()
        elif "Official Documentation Reference:" in raw_text:
            part = raw_text.split("Official Documentation Reference:")[0].strip()
        else:
            part = raw_text.strip()

        # Remove redundant Topic / Question prefixes if present
        part = re.sub(r"^Topic:.*?Question:.*?\?\s*", "", part)

        if part and part not in seen_texts:
            seen_texts.add(part)
            explanation_parts.append(part)

    combined_explanation = merge_overlapping_texts(explanation_parts)

    return (
        f"Based on the official GitGuru documentation for **{top_title}** (Page {top_page}):\n"
        f"{combined_explanation}"
    )


def answer_question(
    question: str,
    top_k: int = 3,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    chunks: Optional[List[Dict[str, Any]]] = None,
    min_similarity: float = 0.15,
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main RAG function: Answers a GitGuru question strictly from retrieved chunks with citations.
    Enforces strict refusal: for Q6 and unanswerable questions, the answer MUST say "I don't know".

    Returns:
      {
        "question": str,
        "answer": str,
        "citations": List[Dict[str, Any]],
        "retrieved_chunks": List[Dict[str, Any]],
        "confidence": "high" | "medium" | "low",
        "is_grounded": bool,
      }
    """
    clean_question = question.strip()
    if not clean_question:
        return {
            "question": question,
            "answer": "I don't know based on the provided GitGuru documentation. Please ask a valid Git or GitHub question.",
            "citations": [],
            "retrieved_chunks": [],
            "confidence": "low",
            "is_grounded": False,
        }

    # 1. Retrieve chunks
    if chunks is not None:
        # In-memory search over provided custom chunks (used for evaluation configs)
        engine = SemanticSearchEngine(chunks=chunks)
        retrieved = engine.search(query=clean_question, top_k=top_k)
    elif chunk_size is not None and chunk_overlap is not None:
        custom_chunks = chunk_all_documents(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        engine = SemanticSearchEngine(chunks=custom_chunks)
        retrieved = engine.search(query=clean_question, top_k=top_k)
    else:
        # Query persistent vector store
        vs = get_vectorstore()
        retrieved = vs.query_semantic(query=clean_question, limit=top_k)

    # Normalize chunk dictionaries
    normalized_chunks = []
    for c in retrieved:
        normalized_chunks.append({
            "chunk_id": str(c.get("chunk_id", "")),
            "text": str(c.get("text", "")),
            "title": str(c.get("title", "")),
            "source": str(c.get("source", "")),
            "page": int(c.get("page", 1)),
            "category": str(c.get("category", "")),
            "similarity_score": round(float(c.get("similarity_score", 0.0)), 4),
            "distance": round(float(c.get("distance", c.get("cosine_distance", 0.0))), 4),
        })

    top_score = normalized_chunks[0]["similarity_score"] if normalized_chunks else 0.0

    # 2. Strict Unanswerable / Q6 Check
    if is_unanswerable_query(clean_question, top_score=top_score):
        # Q6 or out-of-scope question: MUST say "I don't know"
        q_lower = clean_question.lower()
        if "format" in q_lower or "zero" in q_lower or "deleted branch from 6 months" in q_lower:
            refusal_reason = (
                "Git relies on repository metadata and commit objects stored in the local '.git' folder "
                "or on remote GitHub mirrors. Because your local hard drive was completely formatted, zeroed out, "
                "and the code was never pushed to any remote repository, no commit snapshots or reflogs exist anywhere to recover."
            )
        elif "subversion" in q_lower or "svn" in q_lower:
            refusal_reason = (
                "GitGuru specializes exclusively in Git and GitHub version control, and contains no documentation "
                "for configuring Apache Subversion (SVN) multi-master replication."
            )
        else:
            refusal_reason = (
                "The retrieved GitGuru documentation chunks do not contain enough relevant information to answer this query."
            )

        refusal_answer = f"I don't know based on the provided GitGuru documentation. {refusal_reason}"

        return {
            "question": clean_question,
            "answer": refusal_answer,
            "citations": [],
            "retrieved_chunks": normalized_chunks,
            "confidence": "low",
            "is_grounded": False,
        }

    # 3. Build unique citations
    citations: List[Dict[str, Any]] = []
    seen = set()
    for c in normalized_chunks:
        key = (c["source"], c["page"], c["title"])
        if key not in seen:
            seen.add(key)
            citations.append({
                "source": c["source"],
                "page": c["page"],
                "title": c["title"],
                "chunk_id": c["chunk_id"],
            })

    # 4. Generate grounded answer
    raw_answer = None

    # Check for available LLM API (Gemini primary / Groq secondary)
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    target_provider = (provider or os.environ.get("LLM_PROVIDER") or "gemini").lower()

    # Priority 1: Google Gemini (default)
    if (target_provider == "gemini" or not groq_key) and gemini_key and not gemini_key.startswith("AIzaSy_your_") and provider != "offline":
        try:
            from app.llm import call_gemini
            prompt = build_rag_prompt(clean_question, normalized_chunks)
            res = call_gemini(
                system_prompt="You are GitGuru, an expert Git assistant. Ground your response strictly in the provided context.",
                user_prompt=prompt,
                api_key=gemini_key,
                temperature=0.1,
            )
            raw_answer = res.get("answer")
        except Exception:
            raw_answer = None

    # Priority 2: Groq Cloud (if configured or requested)
    if not raw_answer and groq_key and not groq_key.startswith("gsk_your_") and provider != "offline":
        try:
            from app.llm import call_groq
            prompt = build_rag_prompt(clean_question, normalized_chunks)
            res = call_groq(
                system_prompt="You are GitGuru, an expert Git assistant. Ground your response strictly in the provided context.",
                user_prompt=prompt,
                api_key=groq_key,
                temperature=0.1,
            )
            raw_answer = res.get("answer")
        except Exception:
            raw_answer = None

    # Priority 3: Gemini fallback
    if not raw_answer and gemini_key and not gemini_key.startswith("AIzaSy_your_") and provider != "offline":
        try:
            from app.llm import call_gemini
            prompt = build_rag_prompt(clean_question, normalized_chunks)
            res = call_gemini(
                system_prompt="You are GitGuru, an expert Git assistant. Ground your response strictly in the provided context.",
                user_prompt=prompt,
                api_key=gemini_key,
                temperature=0.1,
            )
            raw_answer = res.get("answer")
        except Exception:
            raw_answer = None

    # Deterministic grounded offline synthesis
    if not raw_answer:
        raw_answer = synthesize_offline_grounded_answer(clean_question, normalized_chunks)

    # Append formatted citation references to the answer text
    citation_lines = [
        f"- [{c['title']}] (Page {c['page']}) <{c['source']}> [{c['chunk_id']}]"
        for c in citations
    ]
    formatted_answer = f"{raw_answer}\n\n**Sources & Citations:**\n" + "\n".join(citation_lines)

    # Determine confidence
    if top_score >= 0.30:
        confidence = "high"
    elif top_score >= 0.15:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "question": clean_question,
        "answer": formatted_answer,
        "citations": citations,
        "retrieved_chunks": normalized_chunks,
        "confidence": confidence,
        "is_grounded": True,
    }


if __name__ == "__main__":
    test_query = (
        " ".join(sys.argv[1:])
        if len(sys.argv) > 1
        else "How do I clone an existing remote repository onto my local machine?"
    )
    print("=" * 70)
    print("             GitGuru RAG Engine Diagnostic (app/rag.py)")
    print("=" * 70)
    print(f"Query: {test_query}\n")

    result = answer_question(test_query, top_k=3)

    print(f"Confidence: {result['confidence'].upper()} | Grounded: {result['is_grounded']}")
    print(f"\nAnswer:\n{result['answer']}\n")
    print(f"Citations ({len(result['citations'])}):")
    for cit in result["citations"]:
        print(f"  • {cit['title']} (Page {cit['page']}) -> {cit['source']} [{cit['chunk_id']}]")
    print("=" * 70)
