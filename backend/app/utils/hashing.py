"""Hashing helpers used for deduplication."""
from __future__ import annotations

import hashlib


def content_hash(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update((p or "").strip().lower().encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()
