from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .ingest import ingest_pdf, ingest_text, list_sources
from .query import query

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
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")
    content = await file.read()
    chunks = ingest_pdf(content, file.filename)
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


class QueryPayload(BaseModel):
    question: str


@app.post("/query")
def ask(payload: QueryPayload):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    return query(payload.question)
