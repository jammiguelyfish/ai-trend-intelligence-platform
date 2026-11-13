"""Read-side helpers for trends."""
from __future__ import annotations

from typing import List

from sqlalchemy import case, select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Trend


async def list_trends(
    session: AsyncSession, bucket: str | None = None, limit: int = 50
) -> List[dict]:
    # No bucket means "today": the latest day, not every day mixed together
    # (which would list the same term once per day).
    if not bucket:
        bucket = (await session.execute(select(func.max(Trend.bucket)))).scalar_one_or_none()
    q = select(Trend)
    if bucket:
        q = q.where(Trend.bucket == bucket)
    # A two-word phrase says more per mention than a single word and is rarer,
    # so weight it up; otherwise generic words like "model" always win.
    weight = case((Trend.term.like("% %"), 2.0), else_=1.0)
    q = q.order_by(desc(Trend.delta * weight), desc(Trend.count)).limit(limit)
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
