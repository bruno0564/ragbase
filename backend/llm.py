"""Answer generation via a local Ollama model.

This is the *Generation* half of RAG: given the question and the passages
retrieved from ChromaDB, ask a local LLM to write an actual answer grounded
in that context. No API key needed — it talks to Ollama running on localhost.

If Ollama is not running (or the request fails), `generate_answer` returns
``None`` and the caller falls back to just showing the retrieved passages,
so the app keeps working without an LLM.
"""
import os

import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
TIMEOUT_SECONDS = 60

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions using ONLY the "
    "context provided below. If the answer is not contained in the context, "
    "say you don't know — do not make things up. Cite the source document "
    "name when relevant."
)


def _build_prompt(question: str, context_blocks: list[dict]) -> str:
    context = "\n\n".join(
        f"[{b['source']} · chunk {b['chunk']}]\n{b['text']}" for b in context_blocks
    )
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"=== CONTEXT ===\n{context}\n\n"
        f"=== QUESTION ===\n{question}\n\n"
        f"=== ANSWER ===\n"
    )


def generate_answer(question: str, context_blocks: list[dict]) -> str | None:
    """Return an LLM-generated answer, or None if no LLM is available."""
    if not context_blocks:
        return None

    prompt = _build_prompt(question, context_blocks)
    try:
        response = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json().get("response", "").strip() or None
    except (httpx.HTTPError, ValueError):
        # Ollama not running / model missing / bad response — degrade gracefully.
        return None
