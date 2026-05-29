from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, DateTime, Float, Integer, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Trend(Base):
    __tablename__ = "trends"
    __table_args__ = (
        Index("ix_trends_bucket_term", "bucket", "term", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    bucket: Mapped[str] = mapped_column(String(16))  # e.g. 2026-05-29, 2026-W22
    term: Mapped[str] = mapped_column(String(128))
    count: Mapped[int] = mapped_column(Integer, default=0)
    delta: Mapped[float] = mapped_column(Float, default=0.0)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
