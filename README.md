# ragbase

RAG (Retrieval-Augmented Generation) system that lets you query your own documents with natural language. Upload PDFs or plain text, and ask questions — the system finds the most relevant passages using semantic similarity.

## How it works

1. **Ingest** — documents are split into overlapping chunks, embedded with a local sentence-transformer model, and stored in ChromaDB (a vector database)
2. **Retrieve** — the question is embedded with the same model, then the closest chunks are retrieved by cosine similarity
3. **Generate** — the retrieved passages are handed to a local LLM (via [Ollama](https://ollama.com)) which writes an answer grounded in that context, with source attribution and similarity scores. Answers **stream** into a chat UI token-by-token (Server-Sent Events), rendered as Markdown, and the conversation keeps **memory** across turns

No OpenAI API key required — both the embedding model (`all-MiniLM-L6-v2`) and the answer-generating LLM run locally.

> **Ollama is optional.** If it isn't running, the system still works — it returns the most relevant passages without a generated answer (pure retrieval).

## Stack

- **Backend** — Python · FastAPI · ChromaDB · sentence-transformers · PyPDF2
- **LLM** — Ollama (local, optional)
- **Frontend** — React · Vite · react-markdown
- **Ops** — Docker Compose · pytest · GitHub Actions

## Run with Docker (everything at once)

```bash
docker compose up --build
docker compose exec ollama ollama pull llama3.2   # first time only
# → frontend at http://localhost:5173
```

Brings up the backend, the React frontend (built and served by nginx) and a
local Ollama, wired together. ChromaDB and the Ollama models persist in volumes.

## Install & run (local)

```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
# → http://localhost:8000  |  docs at /docs

# Frontend
cd frontend
npm install
npm run dev
# → http://localhost:5173

# (Optional) Ollama for generated answers
ollama serve
ollama pull llama3.2
```

### Tests

```bash
pip install -r requirements-dev.txt
pytest          # backend suite — mocks ChromaDB and the embedder, no torch needed
```

### Configuration

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2` | Model used to generate answers |
| `VITE_API_URL` | `http://localhost:8000` | Backend URL the frontend calls |

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/ingest/pdf` | Upload a PDF (multipart/form-data) |
| `POST` | `/ingest/text` | Index raw text with a source label |
| `GET` | `/sources` | List all indexed document names |
| `DELETE` | `/sources/{source}` | Remove a document from the index |
| `POST` | `/query` | Ask a question (optionally with `history`), get an answer + passages |
| `POST` | `/query/stream` | Same, streamed token-by-token over Server-Sent Events |

## Project structure

```
ragbase/
├── backend/
│   ├── main.py        — FastAPI app, endpoints (incl. SSE streaming)
│   ├── ingest.py      — PDF parsing, chunking, embedding, indexing
│   ├── query.py       — retrieval (semantic search) against ChromaDB
│   ├── llm.py         — answer generation/streaming via local Ollama chat API
│   ├── embedder.py    — sentence-transformers wrapper (lazy-loaded)
│   └── database.py    — ChromaDB client singleton
├── frontend/
│   └── src/
│       ├── App.jsx    — chat UI (streaming, Markdown, memory) + upload
│       └── stream.js  — fetch-based Server-Sent Events client
├── tests/             — pytest suite (mocked ChromaDB/embedder)
├── docker-compose.yml — backend + frontend + Ollama
└── requirements.txt
```

## Roadmap

- [x] LLM integration (Ollama local) to generate actual answers from context
- [x] Delete documents from the index
- [x] Streaming responses (Server-Sent Events)
- [x] Markdown rendering for answers
- [x] Conversation memory (multi-turn chat)
- [x] Backend test suite + CI
- [x] One-command Docker setup (backend + frontend + Ollama)
- [ ] Multi-collection support (separate namespaces per topic)
- [ ] Migrate PyPDF2 → pypdf (PyPDF2 is deprecated)
