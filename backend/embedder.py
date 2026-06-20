"""Wrapper del modelo de embeddings (sentence-transformers, local).

El import de `sentence_transformers` y la carga del modelo son perezosos: solo
ocurren la primera vez que se llama a `embed()`. Así importar este módulo es
barato (los tests pueden mockear `embed` sin arrastrar PyTorch) y el arranque de
la API no paga el coste hasta que de verdad se necesita.
"""

_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    return get_model().encode(texts, show_progress_bar=False).tolist()
