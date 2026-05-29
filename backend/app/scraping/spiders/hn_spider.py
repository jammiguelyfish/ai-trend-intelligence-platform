"""Optional Scrapy spider example for Hacker News front page.

Run with:
    scrapy runspider backend/app/scraping/spiders/hn_spider.py -O hn.json
"""
from __future__ import annotations

import scrapy


class HNSpider(scrapy.Spider):
    name = "hn"
    start_urls = ["https://news.ycombinator.com/"]
    custom_settings = {
        "USER_AGENT": "ai-trend-intelligence/1.0",
        "DOWNLOAD_DELAY": 1.0,
        "ROBOTSTXT_OBEY": True,
    }

    def parse(self, response):
        for row in response.css("tr.athing"):
            yield {
                "external_id": row.attrib.get("id"),
                "title": row.css(".titleline a::text").get(default="").strip(),
                "url": row.css(".titleline a::attr(href)").get(),
            }
