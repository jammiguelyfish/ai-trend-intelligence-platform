"""Reddit scraper using public .json endpoints (no API key)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, List

from backend.app.scraping.http import HttpClient
from backend.app.scraping.schemas import RawItem
from backend.app.utils.logging import get_logger

log = get_logger(__name__)

DEFAULT_SUBREDDITS = [
    "MachineLearning",
    "LocalLLaMA",
    "programming",
    "artificial",
    "dataengineering",
]


async def scrape_reddit(
    subreddits: Iterable[str] = DEFAULT_SUBREDDITS, limit: int = 50
) -> List[RawItem]:
    items: List[RawItem] = []
    async with HttpClient(base_url="https://www.reddit.com") as http:
        for sub in subreddits:
            url = f"/r/{sub}/top.json?limit={limit}&t=day"
            log.info("reddit.fetch", subreddit=sub)
            try:
                data = await http.get_json(url)
            except Exception as e:  # noqa: BLE001
                log.warning("reddit.fail", subreddit=sub, error=str(e))
                continue
            for child in data.get("data", {}).get("children", []):
                d = child.get("data", {})
                items.append(
                    RawItem(
                        source="reddit",
                        external_id=str(d.get("id")),
                        title=d.get("title", "")[:1024],
                        url=f"https://www.reddit.com{d.get('permalink', '')}",
                        author=d.get("author"),
                        content=d.get("selftext", "") or "",
                        score=int(d.get("score") or 0),
                        comments=int(d.get("num_comments") or 0),
                        published_at=datetime.fromtimestamp(
                            d.get("created_utc", 0), tz=timezone.utc
                        ),
                        extra={"subreddit": sub},
                    )
                )
    log.info("reddit.done", count=len(items))
    return items
