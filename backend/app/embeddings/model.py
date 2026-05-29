"""Local sentence-transformers embedding model (lazy-loaded singleton)."""
from __future__ import annotations

from functools import lru_cache
from typing import List

import numpy as np

from backend.app.config import settings
from backend.app.utils.logging import get_logger

log = get_logger(__name__)


@lru_cache(maxsize=1)
def _load_model():
    from sentence_transformers import SentenceTransformer

    log.info("embeddings.load", model=settings.embedding_model)
    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: List[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    model = _load_model()
    return model.encode(
        texts,
        batch_size=settings.embedding_batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )


def embedding_dim() -> int:
    return int(_load_model().get_sentence_embedding_dimension())
