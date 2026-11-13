"""Keyword and phrase trend detection over daily buckets."""
from __future__ import annotations

import html
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

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
    # academic filler
    "introduce", "introduces", "effectively", "providing", "provides",
    "leverages", "exhibits", "demonstrate", "demonstrates", "show", "shows",
    "achieve", "achieves", "single", "real", "run", "runs", "description",
    "semantically", "pass", "average", "existing", "recent", "different",
}


def _clean(text: str) -> str:
    """Strip markup, HTML entities and URLs so '&#x2F;' or 'https' never count."""
    text = _TAG.sub(" ", text or "")
    text = html.unescape(html.unescape(text))
    return _URL.sub(" ", text)


def _singular(word: str) -> str:
    """Fold plurals so "agents" and "agent" count as one term."""
    if len(word) > 4 and word.endswith("s") and not word.endswith(("ss", "us", "is", "as")):
        return word[:-1]
    return word


def _sequence(text: str) -> List[Optional[str]]:
    """Tokens in order; stopwords/short words become None so phrases can't span them."""
    out: List[Optional[str]] = []
    for t in _TOKEN.findall(_clean(text)):
        t = _singular(t.lower().rstrip(".-"))
        out.append(t if len(t) > 2 and t not in _STOP else None)
    return out


def _tokens(text: str) -> List[str]:
    return [t for t in _sequence(text) if t]


def _terms(text: str) -> List[str]:
    """Unigrams plus bigrams of adjacent meaningful words ("vector database")."""
    seq = _sequence(text)
    terms = [t for t in seq if t]
    terms += [
        f"{a} {b}"
        for a, b in zip(seq, seq[1:])
        if a and b and a != b
    ]
    return terms


def _prune_subsumed(counts: Counter, min_phrase: int = 2) -> Counter:
    """Drop one-off phrases, and words that mostly occur inside a kept phrase.

    Without this "vector" and "database" would both rank next to
    "vector database", listing the same story three times.
    """
    phrases = {t: c for t, c in counts.items() if " " in t and c >= min_phrase}
    covered: Dict[str, int] = {}
    for phrase, c in phrases.items():
        for w in phrase.split():
            covered[w] = max(covered.get(w, 0), c)
    out: Counter = Counter()
    for term, c in counts.items():
        if " " in term:
            if term in phrases:
                out[term] = c
        elif covered.get(term, 0) < 0.6 * c:
            out[term] = c
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
        counts.setdefault(b, Counter()).update(_terms(f"{d.title} {d.content or ''}"))

    # wipe day buckets we recompute
    await session.execute(delete(Trend).where(Trend.bucket.in_(list(counts.keys()))))

    buckets_sorted = sorted(counts.keys())
    out: List[Trend] = []
    for i, b in enumerate(buckets_sorted):
        # Compare with the average of up to a week of earlier days instead of
        # just yesterday, so one quiet day doesn't make everything "rising".
        window = [counts[x] for x in buckets_sorted[max(0, i - 7):i]]
        kept = _prune_subsumed(counts[b])
        # Phrases are rarer than single words, so rank the two kinds separately
        # or they would never reach the list.
        words = [(x, c) for x, c in kept.most_common() if " " not in x][: top_k * 3 // 5]
        phrases = [(x, c) for x, c in kept.most_common() if " " in x][: top_k * 2 // 5]
        for term, c in sorted(words + phrases, key=lambda tc: -tc[1]):
            baseline = sum(w.get(term, 0) for w in window) / len(window) if window else 0.0
            delta = round(float(c) - baseline, 2)
            t = Trend(bucket=b, term=term, count=int(c), delta=delta)
            session.add(t)
            out.append(t)
    await session.commit()
    log.info("trends.done", buckets=len(buckets_sorted), terms=len(out))
    return out
