"""Lightweight in-memory sliding-window rate limiter for auth endpoints.

This protects login/register against credential-stuffing and account-creation
abuse without extra infrastructure. It is per-process: if you run multiple
uvicorn workers or replicas, move this to Redis (or put a rate limiter in
front of the app, e.g. Cloudflare / nginx) so limits apply globally.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

_lock = threading.Lock()
_hits: dict[str, deque[float]] = defaultdict(deque)


def check_rate_limit(key: str, limit: int, window_seconds: int) -> bool:
    """Record one attempt for ``key``. Return True if allowed, False if over limit."""
    now = time.monotonic()
    with _lock:
        bucket = _hits[key]
        while bucket and bucket[0] <= now - window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True


def clear_rate_limits() -> None:
    """Reset all buckets (used by tests)."""
    with _lock:
        _hits.clear()
