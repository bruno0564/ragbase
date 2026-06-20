"""Tests de los endpoints HTTP (TestClient, dependencias mockeadas)."""

import pytest
from fastapi.testclient import TestClient

import backend.main as main
from backend.main import app

client = TestClient(app)


def test_healthcheck() -> None:
    assert client.get("/").json() == {"status": "ok"}


def test_ingest_text_returns_chunk_count(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "ingest_text", lambda text, source: 3)

    r = client.post("/ingest/text", json={"text": "hi", "source": "doc"})

    assert r.json() == {"source": "doc", "chunks_indexed": 3}


def test_ingest_pdf_rejects_non_pdf() -> None:
    r = client.post("/ingest/pdf", files={"file": ("x.txt", b"data", "text/plain")})
    assert r.status_code == 400


def test_query_returns_answer_and_context(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        main, "query", lambda q, h: {"question": q, "answer": "a", "context": []}
    )

    r = client.post("/query", json={"question": "hello"})

    assert r.status_code == 200
    assert r.json()["answer"] == "a"


def test_query_rejects_blank_question() -> None:
    r = client.post("/query", json={"question": "   "})
    assert r.status_code == 400


def test_sources_listing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "list_sources", lambda: ["a", "b"])
    assert client.get("/sources").json() == {"sources": ["a", "b"]}


def test_delete_unknown_source_is_404(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "delete_source", lambda s: 0)
    assert client.delete("/sources/x").status_code == 404


def test_stream_endpoint_emits_sse_events(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        main, "retrieve", lambda q: [{"source": "d", "chunk": 0, "text": "t", "score": 0.9}]
    )
    monkeypatch.setattr(main, "stream_answer", lambda q, c, h: iter(["Hel", "lo"]))

    r = client.post("/query/stream", json={"question": "hi"})

    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    body = r.text
    assert "event: context" in body
    assert "event: token" in body
    assert "event: done" in body
    assert "Hel" in body and "lo" in body
