"""Answer generation via a local Ollama model.

This is the *Generation* half of RAG: given the question, the passages retrieved
from ChromaDB and the prior turns of the conversation, ask a local LLM to write
an answer grounded in that context. No API key needed — it talks to Ollama
running on localhost via its chat API (`/api/chat`), which takes a list of
role/content messages and so supports multi-turn memory natively.

If Ollama is not running (or the request fails), the generation functions
degrade gracefully — `generate_answer` returns ``None`` and `stream_answer`
yields nothing — so the app keeps working as pure retrieval without an LLM.
"""

import json
import os
from collections.abc import Iterator, Sequence

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

# Un turno de conversación: {"role": "user" | "assistant", "content": str}.
Message = dict[str, str]


def _system_message(context_blocks: list[dict]) -> str:
    context = "\n\n".join(
        f"[{b['source']} · chunk {b['chunk']}]\n{b['text']}" for b in context_blocks
    )
    return f"{SYSTEM_PROMPT}\n\n=== CONTEXT ===\n{context}"


def _messages(
    question: str, context_blocks: list[dict], history: Sequence[Message]
) -> list[Message]:
    """Construye la lista de mensajes para Ollama: sistema+contexto, historial, pregunta.

    El contexto recuperado va en el mensaje de sistema (es de este turno), y el
    historial previo se intercala para que el modelo mantenga el hilo.
    """
    messages: list[Message] = [{"role": "system", "content": _system_message(context_blocks)}]
    for turn in history:
        if turn.get("role") in ("user", "assistant") and turn.get("content"):
            messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": question})
    return messages


def generate_answer(
    question: str, context_blocks: list[dict], history: Sequence[Message] = ()
) -> str | None:
    """Return a full LLM-generated answer, or None if no LLM is available."""
    if not context_blocks:
        return None

    try:
        response = httpx.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": _messages(question, context_blocks, history),
                "stream": False,
            },
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "").strip() or None
    except (httpx.HTTPError, ValueError, KeyError):
        # Ollama not running / model missing / bad response — degrade gracefully.
        return None


def stream_answer(
    question: str, context_blocks: list[dict], history: Sequence[Message] = ()
) -> Iterator[str]:
    """Yield the answer in chunks as Ollama produces them (chat API, stream=True).

    On any failure it simply stops yielding, so the caller can fall back to the
    retrieved passages just like with `generate_answer`.
    """
    if not context_blocks:
        return

    payload = {
        "model": OLLAMA_MODEL,
        "messages": _messages(question, context_blocks, history),
        "stream": True,
    }
    try:
        with httpx.stream(
            "POST", f"{OLLAMA_URL}/api/chat", json=payload, timeout=TIMEOUT_SECONDS
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except ValueError:
                    continue
                chunk = data.get("message", {}).get("content", "")
                if chunk:
                    yield chunk
    except httpx.HTTPError:
        return
