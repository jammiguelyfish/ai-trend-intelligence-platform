"""ChromaDB persistent vector store wrapper."""
from __future__ import annotations

from functools import lru_cache
from typing import List, Sequence

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.app.config import settings

_COLLECTION = "documents"


@lru_cache(maxsize=1)
def _client():
    return chromadb.PersistentClient(
        path=settings.chroma_persist_dir,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def _collection():
    return _client().get_or_create_collection(
        name=_COLLECTION, metadata={"hnsw:space": "cosine"}
    )


def upsert(
    ids: Sequence[str],
    embeddings: Sequence[Sequence[float]],
    metadatas: Sequence[dict],
    documents: Sequence[str],
) -> None:
    if not ids:
        return
    _collection().upsert(
        ids=list(ids),
        embeddings=[list(e) for e in embeddings],
        metadatas=list(metadatas),
        documents=list(documents),
    )


def query(
    embedding: Sequence[float], n_results: int = 10, where: dict | None = None
) -> dict:
    return _collection().query(
        query_embeddings=[list(embedding)],
        n_results=n_results,
        where=where,
    )


def count() -> int:
    return _collection().count()
