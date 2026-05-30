# ragbase

RAG (Retrieval-Augmented Generation) system that lets you query your own documents with natural language. Upload PDFs or plain text, and ask questions — the system finds the most relevant passages using semantic similarity.

## How it works

1. **Ingest** — documents are split into overlapping chunks, embedded with a local sentence-transformer model, and stored in ChromaDB (a vector database)
2. **Query** — the question is embedded with the same model, then the closest chunks are retrieved by cosine similarity
3. **Answer** — the relevant context is returned with source attribution and similarity scores

No OpenAI API key required — the embedding model (`all-MiniLM-L6-v2`) runs locally.

## Stack

- **Backend** — Python · FastAPI · ChromaDB · sentence-transformers · PyPDF2
- **Frontend** — React · Vite

## Install & run

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
```

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/ingest/pdf` | Upload a PDF (multipart/form-data) |
| `POST` | `/ingest/text` | Index raw text with a source label |
| `GET` | `/sources` | List all indexed document names |
| `POST` | `/query` | Ask a question, get top-k relevant passages |

## Project structure

```
ragbase/
├── backend/
│   ├── main.py        — FastAPI app, endpoints
│   ├── ingest.py      — PDF parsing, chunking, embedding, indexing
│   ├── query.py       — semantic search against ChromaDB
│   ├── embedder.py    — sentence-transformers wrapper
│   └── database.py    — ChromaDB client singleton
├── frontend/
│   └── src/
│       └── App.jsx    — upload + query UI
└── requirements.txt
```

## Roadmap

- [ ] LLM integration (Ollama local / OpenAI) to generate actual answers from context
- [ ] Delete documents from the index
- [ ] Multi-collection support (separate namespaces per topic)
- [ ] Streaming responses
- [ ] Markdown rendering for answers
