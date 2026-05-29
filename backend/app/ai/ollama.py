"""Thin async client for a local Ollama server."""
from __future__ import annotations

import httpx

from backend.app.config import settings
from backend.app.utils.logging import get_logger

log = get_logger(__name__)


async def generate(prompt: str, model: str | None = None, temperature: float = 0.2) -> str:
    url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
    payload = {
        "model": model or settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            r = await client.post(url, json=payload)
            r.raise_for_status()
        except httpx.HTTPError as e:
            log.warning("ollama.fail", error=str(e))
            return f"[ollama unavailable: {e}]"
    data = r.json()
    return (data.get("response") or "").strip()


async def summarize(text: str, instruction: str | None = None) -> str:
    instruction = instruction or (
        "Summarize the following developer/AI content into 3-5 concise bullet "
        "points. Highlight the key idea, novelty, and any technical takeaway."
    )
    prompt = f"{instruction}\n\nCONTENT:\n{text[:8000]}\n\nSUMMARY:"
    return await generate(prompt)
