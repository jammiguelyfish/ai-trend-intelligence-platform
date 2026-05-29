"""Read-side helpers for trends."""
from __future__ import annotations

from typing import List

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Trend


async def list_trends(
    session: AsyncSession, bucket: str | None = None, limit: int = 50
) -> List[dict]:
    q = select(Trend)
    if bucket:
        q = q.where(Trend.bucket == bucket)
    q = q.order_by(desc(Trend.delta), desc(Trend.count)).limit(limit)
    rows = (await session.execute(q)).scalars().all()
    return [
        {
            "bucket": r.bucket,
            "term": r.term,
            "count": r.count,
            "delta": r.delta,
        }
        for r in rows
    ]


async def list_buckets(session: AsyncSession, limit: int = 14) -> List[str]:
    q = select(Trend.bucket).distinct().order_by(desc(Trend.bucket)).limit(limit)
    return [b for (b,) in (await session.execute(q)).all()]
