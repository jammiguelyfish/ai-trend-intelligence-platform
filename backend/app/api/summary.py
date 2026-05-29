from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import db_session
from backend.app.services.summary import summarize_document

router = APIRouter(prefix="/summary", tags=["summary"])


class SummaryRequest(BaseModel):
    document_id: int


@router.post("")
async def create_summary(
    payload: SummaryRequest, session: AsyncSession = Depends(db_session)
) -> dict:
    s = await summarize_document(session, payload.document_id)
    if not s:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": s.id,
        "document_id": s.document_id,
        "model": s.model,
        "content": s.content,
    }
