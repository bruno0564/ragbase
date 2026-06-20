"""Tests de recuperación y de la función query (generación mockeada)."""

import pytest

from backend import query as query_mod
from backend.ingest import ingest_text
from backend.query import query, retrieve
from tests.conftest import FakeCollection


def test_retrieve_on_empty_index_returns_empty(fake_db: FakeCollection) -> None:
    assert retrieve("anything") == []


def test_retrieve_builds_context_blocks_with_scores(fake_db: FakeCollection) -> None:
    ingest_text("hello world", "doc1")

    blocks = retrieve("hello")

    assert len(blocks) == 1
    assert blocks[0]["source"] == "doc1"
    assert blocks[0]["score"] == 0.9  # 1 - 0.1
    assert blocks[0]["text"] == "hello world"


def test_query_without_llm_returns_passages_only(
    fake_db: FakeCollection, monkeypatch: pytest.MonkeyPatch
) -> None:
    ingest_text("hello world", "doc1")
    monkeypatch.setattr(query_mod, "generate_answer", lambda q, c, h=(): None)

    result = query("hello")

    assert result["answer"] is None
    assert len(result["context"]) == 1


def test_query_with_llm_includes_generated_answer(
    fake_db: FakeCollection, monkeypatch: pytest.MonkeyPatch
) -> None:
    ingest_text("hello world", "doc1")
    captured = {}

    def fake_generate(question, context, history=()):
        captured["history"] = history
        return "the answer"

    monkeypatch.setattr(query_mod, "generate_answer", fake_generate)

    result = query("hello", history=[{"role": "user", "content": "hi"}])

    assert result["answer"] == "the answer"
    assert captured["history"] == [{"role": "user", "content": "hi"}]


def test_query_on_empty_index_has_no_answer(fake_db: FakeCollection) -> None:
    result = query("x")
    assert result["answer"] is None
    assert result["context"] == []
