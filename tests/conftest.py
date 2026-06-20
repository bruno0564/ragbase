"""Utilidades de test: un ChromaDB falso en memoria.

Permite ejercitar ingest/query sin levantar ChromaDB ni cargar el modelo de
embeddings (que arrastraría PyTorch). Los imports perezosos de `embedder` y
`database` hacen que importar el backend sea barato; aquí además inyectamos una
colección falsa y un `embed` determinista.
"""

import pytest

from backend import ingest as ingest_mod
from backend import query as query_mod


class FakeCollection:
    """Imitación mínima de una colección de ChromaDB para los tests."""

    def __init__(self) -> None:
        self.rows: list[dict] = []  # {id, document, embedding, metadata}

    def count(self) -> int:
        return len(self.rows)

    def add(self, documents, embeddings, ids, metadatas) -> None:
        for doc, emb, id_, meta in zip(documents, embeddings, ids, metadatas):
            self.rows.append({"id": id_, "document": doc, "embedding": emb, "metadata": meta})

    def delete(self, where=None) -> None:
        if where and "source" in where:
            self.rows = [r for r in self.rows if r["metadata"].get("source") != where["source"]]
        else:
            self.rows = []

    def get(self, where=None, include=None) -> dict:
        rows = self.rows
        if where and "source" in where:
            rows = [r for r in rows if r["metadata"].get("source") == where["source"]]
        return {"ids": [r["id"] for r in rows], "metadatas": [r["metadata"] for r in rows]}

    def query(self, query_embeddings, n_results, include=None) -> dict:
        rows = self.rows[:n_results]
        # Distancias crecientes deterministas: 0.1, 0.2, ... -> scores 0.9, 0.8, ...
        return {
            "documents": [[r["document"] for r in rows]],
            "metadatas": [[r["metadata"] for r in rows]],
            "distances": [[round(0.1 * (i + 1), 4) for i in range(len(rows))]],
        }


def _fake_embed(texts: list[str]) -> list[list[float]]:
    """Embedding determinista y trivial — no se usa para medir similitud real."""
    return [[float(len(t)), 0.0, 0.0] for t in texts]


@pytest.fixture
def fake_db(monkeypatch: pytest.MonkeyPatch) -> FakeCollection:
    collection = FakeCollection()
    monkeypatch.setattr(ingest_mod, "get_collection", lambda: collection)
    monkeypatch.setattr(query_mod, "get_collection", lambda: collection)
    monkeypatch.setattr(ingest_mod, "embed", _fake_embed)
    monkeypatch.setattr(query_mod, "embed", _fake_embed)
    return collection
