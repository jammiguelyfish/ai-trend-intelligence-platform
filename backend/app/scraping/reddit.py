"""Reddit scraper: public .json endpoints, with an Atom-feed fallback.

Reddit now answers unauthenticated ``.json`` requests with 403, but the Atom
feed (``.rss``) is still served. It carries no score / comment counts, and is
rate-limited to roughly one request per minute, so the fallback asks for all
subreddits at once through the multireddit syntax (``r/a+b+c``).
"""
from __future__ import annotations

import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Iterable, List

import httpx
from bs4 import BeautifulSoup

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

_ATOM = "{http://www.w3.org/2005/Atom}"
_RATE_LIMIT_WAIT = 60  # seconds to wait before retrying a 429 on the feed


def parse_atom(xml_text: str) -> List[RawItem]:
    """Convert a Reddit Atom feed into RawItems."""
    items: List[RawItem] = []
    for entry in ET.fromstring(xml_text).findall(f"{_ATOM}entry"):
        ext_id = (entry.findtext(f"{_ATOM}id") or "").removeprefix("t3_")
        title = entry.findtext(f"{_ATOM}title") or ""
        if not ext_id or not title:
            continue
        link = entry.find(f"{_ATOM}link")
        category = entry.find(f"{_ATOM}category")
        body = BeautifulSoup(
            entry.findtext(f"{_ATOM}content") or "", "html.parser"
        ).select_one("div.md")
        stamp = entry.findtext(f"{_ATOM}published") or entry.findtext(f"{_ATOM}updated")
        items.append(
            RawItem(
                source="reddit",
                external_id=ext_id,
                title=title[:1024],
                url=link.get("href") if link is not None else None,
                author=(entry.findtext(f"{_ATOM}author/{_ATOM}name") or "").removeprefix("/u/")
                or None,
                content=body.get_text(" ", strip=True) if body else "",
                published_at=datetime.fromisoformat(stamp) if stamp else None,
                extra={"subreddit": category.get("term") if category is not None else None},
            )
        )
    return items


async def _scrape_atom(
    http: HttpClient, subreddits: List[str], limit: int
) -> List[RawItem]:
    url = f"/r/{'+'.join(subreddits)}/top/.rss?t=day&limit={min(100, limit * len(subreddits))}"
    for attempt in (1, 2):
        log.info("reddit.fetch_atom", subreddits=subreddits, attempt=attempt)
        try:
            return parse_atom(await http.get_text(url))
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt == 1:
                log.info("reddit.rate_limited", wait=_RATE_LIMIT_WAIT)
                await asyncio.sleep(_RATE_LIMIT_WAIT)
                continue
            log.warning("reddit.atom_fail", error=str(e))
        except Exception as e:  # noqa: BLE001
            log.warning("reddit.atom_fail", error=str(e))
        break
    return []


async def scrape_reddit(
    subreddits: Iterable[str] = DEFAULT_SUBREDDITS, limit: int = 50
) -> List[RawItem]:
    subs = list(subreddits)
    items: List[RawItem] = []
    async with HttpClient(base_url="https://www.reddit.com") as http:
        for sub in subs:
            url = f"/r/{sub}/top.json?limit={limit}&t=day"
            log.info("reddit.fetch", subreddit=sub)
            try:
                data = await http.get_json(url)
            except httpx.HTTPStatusError as e:
                log.warning("reddit.fail", subreddit=sub, error=str(e))
                if e.response.status_code in (401, 403):
                    break  # blocked outright: other subreddits will be too
                continue
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
        if not items:
            items = await _scrape_atom(http, subs, limit)
    log.info("reddit.done", count=len(items))
    return items
