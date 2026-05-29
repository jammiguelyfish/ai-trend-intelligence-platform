"""Hacker News scraper using the free Firebase API."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import List

from backend.app.scraping.http import HttpClient
from backend.app.scraping.schemas import RawItem
from backend.app.utils.logging import get_logger

log = get_logger(__name__)

HN_BASE = "https://hacker-news.firebaseio.com/v0"


async def _fetch_item(http: HttpClient, item_id: int) -> RawItem | None:
    try:
        d = await http.get_json(f"{HN_BASE}/item/{item_id}.json")
    except Exception as e:  # noqa: BLE001
        log.warning("hn.item_fail", id=item_id, error=str(e))
        return None
    if not d or d.get("type") != "story":
        return None
    return RawItem(
        source="hackernews",
        external_id=str(d.get("id")),
        title=d.get("title", "")[:1024],
        url=d.get("url") or f"https://news.ycombinator.com/item?id={d.get('id')}",
        author=d.get("by"),
        content=d.get("text", "") or "",
        score=int(d.get("score") or 0),
        comments=int(d.get("descendants") or 0),
        published_at=datetime.fromtimestamp(d.get("time", 0), tz=timezone.utc),
    )


async def scrape_hackernews(limit: int = 75) -> List[RawItem]:
    async with HttpClient() as http:
        ids = await http.get_json(f"{HN_BASE}/topstories.json")
        ids = ids[:limit]
        log.info("hn.fetch", count=len(ids))
        results = await asyncio.gather(*[_fetch_item(http, i) for i in ids])
    items = [r for r in results if r is not None]
    log.info("hn.done", count=len(items))
    return items
