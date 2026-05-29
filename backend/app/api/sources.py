from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import db_session
from backend.app.models import Source

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("")
async def list_sources(session: AsyncSession = Depends(db_session)) -> list[dict]:
    rows = (await session.execute(select(Source))).scalars().all()
    return [
        {"id": s.id, "name": s.name, "kind": s.kind, "enabled": s.enabled}
        for s in rows
    ]
