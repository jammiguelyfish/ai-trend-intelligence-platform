"""Simple keyword-based trend detection over time buckets."""
from __future__ import annotations

import html
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Document, Trend
from backend.app.utils.logging import get_logger

log = get_logger(__name__)

_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9\-+#\.]{2,}")
_TAG = re.compile(r"<[^>]+>")
_URL = re.compile(r"https?://\S+|www\.\S+")

# General English stopwords (minus two words that matter in tech text) plus
# filler that is frequent in arXiv / HN text but says nothing about trends.
_STOP = (set(ENGLISH_STOP_WORDS) - {"system", "computer"}) | {
    "hn", "ask", "use", "using", "used", "get", "got", "new",
    "paper", "propose", "proposed", "present", "approach", "based", "via",
    "results", "work", "method", "methods", "novel", "http", "https", "www",
    "com",
    # conversational filler from Reddit / HN comments
    "like", "just", "don", "doesn", "didn", "isn", "way", "lot", "know",
    "really", "want", "need", "think", "make", "thing", "things", "people",
    "good", "better", "going", "time",
}


def _clean(text: str) -> str:
    """Strip markup, HTML entities and URLs so '&#x2F;' or 'https' never count."""
    text = _TAG.sub(" ", text or "")
    text = html.unescape(html.unescape(text))
    return _URL.sub(" ", text)


def _tokens(text: str) -> List[str]:
    out: List[str] = []
    for t in _TOKEN.findall(_clean(text)):
        t = t.lower().rstrip(".-")
        if len(t) > 2 and t not in _STOP:
            out.append(t)
    return out


def _bucket_day(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")


async def compute_daily_trends(
    session: AsyncSession, days: int = 7, top_k: int = 50
) -> List[Trend]:
    """Re-compute term counts per day and their delta vs the previous day."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    q = select(Document).where(Document.published_at >= cutoff)
    docs = list((await session.execute(q)).scalars().all())

    counts: Dict[str, Counter] = {}
    for d in docs:
        if not d.published_at:
            continue
        b = _bucket_day(d.published_at)
        counts.setdefault(b, Counter()).update(_tokens(f"{d.title} {d.content or ''}"))

    # wipe day buckets we recompute
    await session.execute(delete(Trend).where(Trend.bucket.in_(list(counts.keys()))))

    buckets_sorted = sorted(counts.keys())
    out: List[Trend] = []
    for i, b in enumerate(buckets_sorted):
        prev = counts[buckets_sorted[i - 1]] if i > 0 else Counter()
        for term, c in counts[b].most_common(top_k):
            delta = float(c - prev.get(term, 0))
            t = Trend(bucket=b, term=term, count=int(c), delta=delta)
            session.add(t)
            out.append(t)
    await session.commit()
    log.info("trends.done", buckets=len(buckets_sorted), terms=len(out))
    return out
