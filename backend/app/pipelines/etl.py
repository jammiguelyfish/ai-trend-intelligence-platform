"""ETL pipeline: ingest RawItem batches into the documents table with dedup."""
from __future__ import annotations

import re
from typing import Iterable, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Document, Source
from backend.app.scraping.schemas import RawItem
from backend.app.utils.hashing import content_hash
from backend.app.utils.logging import get_logger

log = get_logger(__name__)

_WS = re.compile(r"\s+")


def _clean(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = _WS.sub(" ", text).strip()
    return text


async def _get_or_create_source(session: AsyncSession, kind: str) -> Source:
    res = await session.execute(select(Source).where(Source.name == kind))
    src = res.scalar_one_or_none()
    if src:
        return src
    src = Source(name=kind, kind=kind, base_url="", enabled=True)
    session.add(src)
    await session.flush()
    return src


async def ingest_items(
    session: AsyncSession, items: Iterable[RawItem]
) -> List[Document]:
    """Persist items, deduplicating by content hash and (source, external_id)."""
    inserted: List[Document] = []
    by_source: dict[str, Source] = {}

    for item in items:
        src = by_source.get(item.source) or await _get_or_create_source(
            session, item.source
        )
        by_source[item.source] = src

        title = _clean(item.title)
        body = _clean(item.content)
        h = content_hash(item.source, item.external_id, title, body)

        # dedup by hash
        exists = await session.execute(
            select(Document.id).where(Document.content_hash == h)
        )
        if exists.scalar_one_or_none():
            continue

        # The table is unique on (source, external_id). Titles and bodies get
        # edited upstream (e.g. Hacker News renames), which changes the hash,
        # so an already-stored item must be skipped here as well.
        seen = await session.execute(
            select(Document.id).where(
                Document.source_id == src.id,
                Document.external_id == item.external_id,
            )
        )
        if seen.scalar_one_or_none():
            continue

        doc = Document(
            source_id=src.id,
            external_id=item.external_id,
            content_hash=h,
            title=title,
            url=item.url,
            author=item.author,
            content=body,
            score=item.score,
            comments=item.comments,
            published_at=item.published_at,
        )
        session.add(doc)
        inserted.append(doc)

    await session.commit()
    log.info("etl.ingest", inserted=len(inserted))
    return inserted
