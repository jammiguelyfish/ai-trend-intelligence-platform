"""GitHub trending scraper (no API key) using the public HTML page."""
from __future__ import annotations

from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from backend.app.scraping.http import HttpClient
from backend.app.scraping.schemas import RawItem
from backend.app.utils.logging import get_logger

log = get_logger(__name__)

GITHUB_TRENDING_URL = "https://github.com/trending"


async def scrape_github_trending(language: str = "") -> List[RawItem]:
    url = GITHUB_TRENDING_URL + (f"/{language}" if language else "")
    async with HttpClient() as http:
        html = await http.get_text(url)
    soup = BeautifulSoup(html, "lxml")
    items: List[RawItem] = []
    for art in soup.select("article.Box-row"):
        a = art.select_one("h2 a")
        if not a:
            continue
        repo = a.get_text(strip=True).replace("\n", "").replace(" ", "")
        href = urljoin("https://github.com", a.get("href", ""))
        desc_el = art.select_one("p")
        description = desc_el.get_text(strip=True) if desc_el else ""
        stars_el = art.select_one('a[href$="/stargazers"]')
        stars = 0
        if stars_el:
            try:
                stars = int(stars_el.get_text(strip=True).replace(",", ""))
            except ValueError:
                stars = 0
        items.append(
            RawItem(
                source="github",
                external_id=repo,
                title=repo,
                url=href,
                content=description,
                score=stars,
                extra={"language": language or "all"},
            )
        )
    log.info("github.done", count=len(items))
    return items
