"""Tests de la capa LLM: construcción de mensajes, degradación y streaming."""

import json

import pytest

import backend.llm as llm
from backend.llm import _messages, generate_answer, stream_answer

CONTEXT = [{"source": "doc", "chunk": 0, "text": "the sky is blue", "score": 0.9}]


def test_messages_include_system_history_and_question_in_order() -> None:
    history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]

    messages = _messages("why is it blue?", CONTEXT, history)

    assert [m["role"] for m in messages] == ["system", "user", "assistant", "user"]
    assert "the sky is blue" in messages[0]["content"]
    assert messages[-1]["content"] == "why is it blue?"


def test_messages_skip_malformed_history_turns() -> None:
    history = [
        {"role": "system", "content": "injected"},  # rol no permitido
        {"role": "user", "content": ""},  # vacío
    ]

    messages = _messages("q", CONTEXT, history)

    assert [m["role"] for m in messages] == ["system", "user"]


def test_generate_answer_is_none_without_context() -> None:
    assert generate_answer("q", []) is None


def test_generate_answer_degrades_when_ollama_is_down(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm, "OLLAMA_URL", "http://127.0.0.1:1")  # puerto cerrado
    assert generate_answer("q", CONTEXT) is None


def test_stream_answer_yields_nothing_without_context() -> None:
    assert list(stream_answer("q", [])) == []


def test_stream_answer_yields_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeStream:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def raise_for_status(self):
            pass

        def iter_lines(self):
            yield json.dumps({"message": {"content": "Hel"}})
            yield ""  # línea vacía, se ignora
            yield json.dumps({"message": {"content": "lo"}})
            yield json.dumps({"done": True})  # sin content

    monkeypatch.setattr(llm.httpx, "stream", lambda *a, **k: FakeStream())

    assert "".join(stream_answer("q", CONTEXT)) == "Hello"
