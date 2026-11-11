"""Async HTTP client with retries and rate limiting."""
from __future__ import annotations

import asyncio
from typing import Any

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from backend.app.config import settings
from backend.app.utils.logging import get_logger

log = get_logger(__name__)


def _is_retryable(exc: BaseException) -> bool:
    """Retry network errors, 429 and 5xx; a 4xx like 403 will not fix itself."""
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        return code == 429 or code >= 500
    return isinstance(exc, httpx.HTTPError)


class HttpClient:
    def __init__(self, base_url: str = "", timeout: float = 20.0):
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers={"User-Agent": settings.scrape_user_agent},
            follow_redirects=True,
        )
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> "HttpClient":
        return self

    async def __aexit__(self, *exc) -> None:
        await self._client.aclose()

    async def get_json(self, url: str, **kwargs: Any) -> Any:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(4),
            wait=wait_exponential(min=1, max=10),
            retry=retry_if_exception(_is_retryable),
            reraise=True,
        ):
            with attempt:
                async with self._lock:
                    await asyncio.sleep(settings.scrape_request_delay)
                    r = await self._client.get(url, **kwargs)
                    r.raise_for_status()
                    return r.json()

    async def get_text(self, url: str, **kwargs: Any) -> str:
        async with self._lock:
            await asyncio.sleep(settings.scrape_request_delay)
            r = await self._client.get(url, **kwargs)
            r.raise_for_status()
            return r.text
