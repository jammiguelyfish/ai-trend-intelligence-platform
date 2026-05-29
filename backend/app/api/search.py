from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import db_session
from backend.app.services.search import semantic_search

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search(
    q: str = Query(..., min_length=1, description="Natural-language query"),
    k: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(db_session),
) -> dict:
    results = await semantic_search(session, q, k=k)
    return {"query": q, "count": len(results), "results": results}
