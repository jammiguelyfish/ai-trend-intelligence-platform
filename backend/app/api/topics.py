from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import db_session
from backend.app.models import Document, DocumentTopic, Topic

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("")
async def list_topics(session: AsyncSession = Depends(db_session)) -> list[dict]:
    rows = (
        await session.execute(select(Topic).order_by(Topic.size.desc()))
    ).scalars().all()
    out = []
    for t in rows:
        # the documents closest to the cluster centre are its best examples
        examples = (
            await session.execute(
                select(Document.id, Document.title, Document.url)
                .join(DocumentTopic, DocumentTopic.document_id == Document.id)
                .where(DocumentTopic.topic_id == t.id)
                .order_by(DocumentTopic.score.desc())
                .limit(3)
            )
        ).all()
        out.append(
            {
                "id": t.id,
                "label": t.label,
                "keywords": t.keywords.split(", ") if t.keywords else [],
                "size": t.size,
                "examples": [{"id": i, "title": ti, "url": u} for i, ti, u in examples],
            }
        )
    return out
