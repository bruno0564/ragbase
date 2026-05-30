from .database import get_collection
from .embedder import embed

TOP_K = 5


def query(question: str) -> dict:
    collection = get_collection()

    if collection.count() == 0:
        return {"answer": None, "sources": [], "context": []}

    q_embedding = embed([question])[0]
    results = collection.query(
        query_embeddings=[q_embedding],
        n_results=min(TOP_K, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    context_blocks = []
    for doc, meta, dist in zip(docs, metas, distances):
        context_blocks.append({
            "text": doc,
            "source": meta["source"],
            "chunk": meta["chunk"],
            "score": round(1 - dist, 4),
        })

    context_text = "\n\n---\n\n".join(b["text"] for b in context_blocks)

    return {
        "question": question,
        "context": context_blocks,
        "raw_context": context_text,
    }
