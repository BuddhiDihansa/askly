"""
Text -> vector embeddings, used for semantic search (see retrieval.py).

The model is loaded lazily (only on first use, not at import time) so
that starting the server doesn't require downloading a ~90MB model
file up front - it downloads once, on the first chat/document request,
and is cached in memory after that.
"""
import numpy as np

from app.core.config import settings

_model = None


def model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        try:
            _model = SentenceTransformer(settings.embedding_model)
        except Exception as e:
            raise RuntimeError(
                f"Could not load embedding model '{settings.embedding_model}'. "
                f"Check your internet connection (first run downloads the model) "
                f"and that the model name is correct. Original error: {e}"
            )
    return _model


def encode(texts: list[str]) -> list[list[float]]:
    # normalize_embeddings=True scales every vector to length 1. This is
    # what lets cosine() below use a plain dot product instead of the
    # full cosine similarity formula (dot product / (|a| * |b|)) -
    # cheaper to compute, same result, once both vectors are unit length.
    return model().encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()


def cosine(a: list[float], b: list[float]) -> float:
    return float(np.dot(np.asarray(a), np.asarray(b)))
