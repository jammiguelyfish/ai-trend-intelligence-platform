"""arXiv scraper using the free Atom-based query API."""
from __future__ import annotations

from datetime import datetime
from typing import List
from xml.etree import ElementTree as ET

from backend.app.scraping.http import HttpClient
from backend.app.scraping.schemas import RawItem
from backend.app.utils.logging import get_logger

log = get_logger(__name__)

ARXIV_API = "http://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom"}


async def scrape_arxiv(
    query: str = "cat:cs.AI OR cat:cs.LG OR cat:cs.CL",
    max_results: int = 50,
) -> List[RawItem]:
    url = (
        f"{ARXIV_API}?search_query={query}"
        f"&start=0&max_results={max_results}"
        "&sortBy=submittedDate&sortOrder=descending"
    )
    async with HttpClient() as http:
        xml = await http.get_text(url)
    root = ET.fromstring(xml)
    items: List[RawItem] = []
    for entry in root.findall("a:entry", NS):
        ext_id = (entry.findtext("a:id", default="", namespaces=NS) or "").strip()
        title = (entry.findtext("a:title", default="", namespaces=NS) or "").strip()
        summary = (entry.findtext("a:summary", default="", namespaces=NS) or "").strip()
        published = entry.findtext("a:published", default="", namespaces=NS)
        try:
            pub_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        except ValueError:
            pub_dt = None
        authors = [
            (a.findtext("a:name", default="", namespaces=NS) or "").strip()
            for a in entry.findall("a:author", NS)
        ]
        items.append(
            RawItem(
                source="arxiv",
                external_id=ext_id,
                title=title[:1024],
                url=ext_id,
                author=", ".join(authors)[:256],
                content=summary,
                published_at=pub_dt,
            )
        )
    log.info("arxiv.done", count=len(items))
    return items
