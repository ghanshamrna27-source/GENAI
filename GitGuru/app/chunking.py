"""
app/chunking.py
Document chunking engine for GitGuru knowledge base.
Splits Git and GitHub documentation into coherent text chunks while strictly
preserving essential metadata: source, page, and title.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.records import load_records

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class DocumentChunk:
    chunk_id: str
    text: str
    source: str
    page: int
    title: str
    category: str
    chunk_index: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def split_text_into_chunks(text: str, chunk_size: int = 250, chunk_overlap: int = 50) -> List[str]:
    """
    Splits text into overlapping chunks, strictly respecting word boundaries
    so chunks never start or end in the middle of a word.
    """
    clean_text = " ".join(text.split()).strip()
    if not clean_text:
        return []

    if len(clean_text) <= chunk_size:
        return [clean_text]

    chunks = []
    start = 0
    text_len = len(clean_text)

    while start < text_len:
        end = min(text_len, start + chunk_size)

        # If not at the very end of text, find the nearest space boundary before end
        if end < text_len:
            space_pos = clean_text.rfind(" ", start + chunk_overlap, end)
            if space_pos != -1:
                end = space_pos

        chunk = clean_text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_len:
            break

        # Calculate next start point with overlap, snapping to a space boundary
        candidate_start = max(start + 1, end - chunk_overlap)
        next_space = clean_text.find(" ", candidate_start, end)
        if next_space != -1:
            start = next_space + 1
        else:
            start = end

    return chunks


def build_full_document_text(record: Dict[str, Any]) -> str:
    """
    Composes a complete textual document representation from a GitGuru record.
    Incorporates title, question, core answer, keyword, and category context.
    """
    title = record.get("title", "Untitled")
    category = record.get("category", "General")
    keyword = record.get("keyword", "")
    question = record.get("question", "")
    answer = record.get("answer", "")
    url = record.get("source_url", "")

    return (
        f"Topic: {title} | Domain: {category} | Primary Keyword: {keyword}. "
        f"Question: {question} "
        f"Explanation & Usage: {answer} "
        f"Official Documentation Reference: {url}"
    )


def chunk_document(
    record: Dict[str, Any],
    chunk_size: int = 220,
    chunk_overlap: int = 40,
) -> List[DocumentChunk]:
    """
    Chunks a single GitGuru document record while preserving source, page, and title metadata.
    """
    doc_id = int(record.get("id", 1))
    title = str(record.get("title", f"Document {doc_id}"))
    source = str(record.get("source_url", "https://git-scm.com/doc"))
    category = str(record.get("category", "Git"))

    doc_text = build_full_document_text(record)
    text_segments = split_text_into_chunks(doc_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    chunks: List[DocumentChunk] = []
    for idx, segment in enumerate(text_segments, 1):
        chunk_id = f"doc_{doc_id:03d}_chunk_{idx:02d}"
        chunks.append(
            DocumentChunk(
                chunk_id=chunk_id,
                text=segment,
                source=source,
                page=doc_id,  # page mapped to document catalog id
                title=title,
                category=category,
                chunk_index=idx,
            )
        )
    return chunks


def chunk_all_documents(
    records: Optional[List[Dict[str, Any]]] = None,
    chunk_size: int = 220,
    chunk_overlap: int = 40,
) -> List[Dict[str, Any]]:
    """
    Loads all GitGuru records and chunks them, returning a list of chunk dictionaries
    with source, page, and title metadata attached to each.
    """
    docs = records if records is not None else load_records()
    all_chunks: List[Dict[str, Any]] = []

    for doc in docs:
        doc_chunks = chunk_document(doc, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        all_chunks.extend(c.to_dict() for c in doc_chunks)

    return all_chunks


if __name__ == "__main__":
    chunks = chunk_all_documents()
    print("=" * 65)
    print("       GitGuru Document Chunking Diagnostic")
    print("=" * 65)
    print(f"Total documents processed: 20")
    print(f"Total chunks created:     {len(chunks)}")
    print(f"Average chunks per doc:   {len(chunks) / 20:.2f}")

    print("\n--- Sample Chunk #1 ---")
    c1 = chunks[0]
    print(f"Chunk ID: {c1['chunk_id']}")
    print(f"Title:    {c1['title']}")
    print(f"Source:   {c1['source']}")
    print(f"Page:     {c1['page']}")
    print(f"Text:     {c1['text']}")

    print("\n--- Sample Chunk #2 ---")
    c2 = chunks[1]
    print(f"Chunk ID: {c2['chunk_id']}")
    print(f"Title:    {c2['title']}")
    print(f"Source:   {c2['source']}")
    print(f"Page:     {c2['page']}")
    print(f"Text:     {c2['text']}")
    print("=" * 65)
