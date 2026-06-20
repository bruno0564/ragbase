"""Tests de indexado, listado y borrado de fuentes (con ChromaDB falso)."""

from backend.ingest import delete_source, ingest_text, list_sources
from tests.conftest import FakeCollection


def test_ingest_indexes_and_lists(fake_db: FakeCollection) -> None:
    n = ingest_text("hello world foo bar", "doc1")
    assert n == 1
    assert list_sources() == ["doc1"]


def test_reingesting_same_source_replaces_instead_of_duplicating(
    fake_db: FakeCollection,
) -> None:
    ingest_text("a b c", "doc1")
    ingest_text("d e f", "doc1")
    assert fake_db.count() == 1
    assert list_sources() == ["doc1"]


def test_delete_source_removes_its_chunks(fake_db: FakeCollection) -> None:
    ingest_text("a b c", "doc1")
    ingest_text("d e f", "doc2")
    removed = delete_source("doc1")
    assert removed == 1
    assert list_sources() == ["doc2"]


def test_delete_unknown_source_returns_zero(fake_db: FakeCollection) -> None:
    assert delete_source("nope") == 0


def test_blank_text_indexes_nothing(fake_db: FakeCollection) -> None:
    assert ingest_text("   ", "doc1") == 0
    assert list_sources() == []
