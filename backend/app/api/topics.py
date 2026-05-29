from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import db_session
from backend.app.models import Topic

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("")
async def list_topics(session: AsyncSession = Depends(db_session)) -> list[dict]:
    rows = (
        await session.execute(select(Topic).order_by(Topic.size.desc()))
    ).scalars().all()
    return [
        {
            "id": t.id,
            "label": t.label,
            "keywords": t.keywords.split(", ") if t.keywords else [],
            "size": t.size,
        }
        for t in rows
    ]
