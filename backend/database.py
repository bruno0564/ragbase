"""Cliente de ChromaDB (singleton perezoso).

El import de `chromadb` y la apertura del cliente persistente se hacen la primera
vez que se pide la colección, no al importar el módulo. Esto mantiene barato el
import (los tests inyectan una colección falsa) y permite configurar la ruta de
datos con la variable de entorno `CHROMA_PATH`.
"""

import os

_client = None
_collection = None


def get_collection():
    global _client, _collection
    if _collection is None:
        import chromadb

        path = os.getenv("CHROMA_PATH", "./chroma_db")
        _client = chromadb.PersistentClient(path=path)
        _collection = _client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection
