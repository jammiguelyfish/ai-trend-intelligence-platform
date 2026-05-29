"""Pipeline that turns Documents into Embeddings + Chroma vectors."""
from __future__ import annotations

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.embeddings import store
from backend.app.embeddings.model import embed_texts, embedding_dim
from backend.app.models import Document, Embedding
from backend.app.utils.logging import get_logger

log = get_logger(__name__)


async def embed_pending(session: AsyncSession, limit: int = 500) -> int:
    """Embed any Documents that don't yet have an Embedding row."""
    q = (
        select(Document)
        .outerjoin(Embedding, Embedding.document_id == Document.id)
        .where(Embedding.id.is_(None))
        .limit(limit)
    )
    docs: List[Document] = list((await session.execute(q)).scalars().all())
    if not docs:
        log.info("embed.none_pending")
        return 0

    texts = [f"{d.title}\n\n{d.content or ''}".strip() for d in docs]
    vectors = embed_texts(texts)
    dim = embedding_dim()

    ids = [f"doc-{d.id}" for d in docs]
    metas = [
        {
            "document_id": d.id,
            "source_id": d.source_id,
            "title": d.title,
            "url": d.url or "",
            "published_at": d.published_at.isoformat() if d.published_at else "",
        }
        for d in docs
    ]
    store.upsert(ids, vectors.tolist(), metas, texts)

    for d, cid in zip(docs, ids):
        session.add(
            Embedding(
                document_id=d.id,
                model=settings.embedding_model,
                dim=dim,
                chroma_id=cid,
            )
        )
    await session.commit()
    log.info("embed.done", count=len(docs))
    return len(docs)
