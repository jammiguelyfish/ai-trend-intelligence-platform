"""Semantic search service backed by Chroma + Postgres metadata."""
from __future__ import annotations

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.embeddings import store
from backend.app.embeddings.model import embed_texts
from backend.app.models import Document


async def semantic_search(
    session: AsyncSession, query: str, k: int = 10
) -> List[dict]:
    if not query.strip():
        return []
    vec = embed_texts([query])[0]
    res = store.query(vec.tolist(), n_results=k)

    ids = res.get("ids", [[]])[0]
    distances = res.get("distances", [[]])[0]
    metas = res.get("metadatas", [[]])[0]

    doc_ids = [m.get("document_id") for m in metas if m.get("document_id")]
    if not doc_ids:
        return []

    docs = list(
        (
            await session.execute(select(Document).where(Document.id.in_(doc_ids)))
        )
        .scalars()
        .all()
    )
    by_id = {d.id: d for d in docs}

    results = []
    for cid, dist, meta in zip(ids, distances, metas):
        d = by_id.get(meta.get("document_id"))
        if not d:
            continue
        results.append(
            {
                "id": d.id,
                "chroma_id": cid,
                "score": float(1.0 - dist) if dist is not None else None,
                "title": d.title,
                "url": d.url,
                "source_id": d.source_id,
                "author": d.author,
                "published_at": d.published_at.isoformat() if d.published_at else None,
                "snippet": (d.content or "")[:400],
            }
        )
    return results
