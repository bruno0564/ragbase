import json
from collections.abc import Iterator
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .ingest import delete_source, ingest_pdf, ingest_text, list_sources
from .llm import stream_answer
from .query import query, retrieve

app = FastAPI(title="ragbase")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def healthcheck():
    return {"status": "ok"}


@app.post("/ingest/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")
    content = await file.read()
    # ingest_pdf is CPU-bound (parsing + embeddings); keep it off the event loop.
    chunks = await run_in_threadpool(ingest_pdf, content, file.filename)
    return {"filename": file.filename, "chunks_indexed": chunks}


class TextPayload(BaseModel):
    text: str
    source: str = "manual"


@app.post("/ingest/text")
def upload_text(payload: TextPayload):
    chunks = ingest_text(payload.text, payload.source)
    return {"source": payload.source, "chunks_indexed": chunks}


@app.get("/sources")
def get_sources():
    return {"sources": list_sources()}


@app.delete("/sources/{source}")
def remove_source(source: str):
    removed = delete_source(source)
    if removed == 0:
        raise HTTPException(status_code=404, detail="Source not found")
    return {"source": source, "chunks_removed": removed}


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class QueryPayload(BaseModel):
    question: str
    # Turnos previos de la conversación, para que el modelo mantenga el hilo.
    history: list[Turn] = []


@app.post("/query")
def ask(payload: QueryPayload):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    history = [turn.model_dump() for turn in payload.history]
    return query(payload.question, history)


def _sse(event: str, data: dict) -> str:
    """Formatea un evento Server-Sent Events."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.post("/query/stream")
def ask_stream(payload: QueryPayload):
    """Versión en streaming de /query (Server-Sent Events).

    Emite primero el contexto recuperado (para pintar las fuentes ya), luego la
    respuesta del LLM token a token, y por último un evento `done`.
    """
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    history = [turn.model_dump() for turn in payload.history]
    context_blocks = retrieve(question)

    def events() -> Iterator[str]:
        yield _sse("context", {"context": context_blocks})
        streamed = False
        for chunk in stream_answer(question, context_blocks, history):
            streamed = True
            yield _sse("token", {"text": chunk})
        # Si no hubo tokens (Ollama apagado o sin contexto), el front cae a mostrar
        # solo los pasajes. `answer` marca si se generó respuesta.
        yield _sse("done", {"answer": streamed})

    return StreamingResponse(events(), media_type="text/event-stream")
