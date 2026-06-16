import io
import uuid

import PyPDF2

from .database import get_collection
from .embedder import embed

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def chunk_text(text: str) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + CHUNK_SIZE])
        chunks.append(chunk)
        i += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if c.strip()]


def ingest_pdf(file_bytes: bytes, filename: str) -> int:
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    full_text = " ".join(
        page.extract_text() or "" for page in reader.pages
    )
    return ingest_text(full_text, filename)


def ingest_text(text: str, source: str) -> int:
    chunks = chunk_text(text)
    if not chunks:
        return 0

    collection = get_collection()
    # Re-indexing the same source replaces it instead of duplicating chunks.
    collection.delete(where={"source": source})

    embeddings = embed(chunks)
    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [{"source": source, "chunk": i} for i in range(len(chunks))]

    collection.add(documents=chunks, embeddings=embeddings, ids=ids, metadatas=metadatas)
    return len(chunks)


def list_sources() -> list[str]:
    collection = get_collection()
    result = collection.get(include=["metadatas"])
    sources = {m["source"] for m in result["metadatas"]}
    return sorted(sources)


def delete_source(source: str) -> int:
    """Remove all chunks belonging to a document. Returns how many were removed."""
    collection = get_collection()
    existing = collection.get(where={"source": source})
    count = len(existing["ids"])
    if count:
        collection.delete(where={"source": source})
    return count
