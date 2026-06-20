from collections.abc import Sequence

from .database import get_collection
from .embedder import embed
from .llm import Message, generate_answer

TOP_K = 5


def retrieve(question: str) -> list[dict]:
    """Recupera los pasajes más relevantes para la pregunta (sin generar respuesta).

    Es la mitad de *Retrieval* de RAG, aislada para que la pueda reutilizar tanto
    la respuesta completa (`query`) como el endpoint de streaming, que necesita el
    contexto antes de empezar a emitir tokens.
    """
    collection = get_collection()
    if collection.count() == 0:
        return []

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
        context_blocks.append(
            {
                "text": doc,
                "source": meta["source"],
                "chunk": meta["chunk"],
                "score": round(1 - dist, 4),
            }
        )
    return context_blocks


def query(question: str, history: Sequence[Message] = ()) -> dict:
    context_blocks = retrieve(question)
    answer = generate_answer(question, context_blocks, history) if context_blocks else None

    return {
        "question": question,
        "answer": answer,
        "context": context_blocks,
    }
