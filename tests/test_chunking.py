"""Tests del troceado de texto."""

from backend.ingest import CHUNK_OVERLAP, CHUNK_SIZE, chunk_text


def test_short_text_is_a_single_chunk() -> None:
    assert chunk_text("hello world") == ["hello world"]


def test_blank_text_yields_no_chunks() -> None:
    assert chunk_text("   ") == []


def test_long_text_splits_with_overlap() -> None:
    words = [f"w{i}" for i in range(CHUNK_SIZE + 100)]
    chunks = chunk_text(" ".join(words))

    assert len(chunks) >= 2
    first, second = chunks[0].split(), chunks[1].split()
    assert len(first) == CHUNK_SIZE
    # El segundo chunk arranca CHUNK_SIZE-CHUNK_OVERLAP palabras después (solapa).
    assert second[0] == words[CHUNK_SIZE - CHUNK_OVERLAP]
