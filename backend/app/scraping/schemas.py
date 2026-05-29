"""Normalized item shape produced by every scraper."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RawItem(BaseModel):
    source: str
    external_id: str
    title: str
    url: Optional[str] = None
    author: Optional[str] = None
    content: Optional[str] = ""
    score: int = 0
    comments: int = 0
    published_at: Optional[datetime] = None
    extra: dict = Field(default_factory=dict)
