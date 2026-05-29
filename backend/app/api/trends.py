from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import db_session
from backend.app.services.trends import list_buckets, list_trends

router = APIRouter(prefix="/trends", tags=["trends"])


@router.get("")
async def trends(
    bucket: str | None = Query(None, description="Specific day bucket YYYY-MM-DD"),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(db_session),
) -> dict:
    items = await list_trends(session, bucket=bucket, limit=limit)
    return {"bucket": bucket, "items": items}


@router.get("/buckets")
async def buckets(
    limit: int = Query(14, ge=1, le=90),
    session: AsyncSession = Depends(db_session),
) -> dict:
    return {"buckets": await list_buckets(session, limit=limit)}
