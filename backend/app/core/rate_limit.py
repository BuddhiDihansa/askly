"""
Simple in-memory rate limiter.

Why in-memory (not Redis) for now: this project runs as a single backend
process, so a plain dict is enough to stop obvious abuse (credential
stuffing on /login, spamming the paid Groq/Tavily APIs via /chat).

Limitation to be upfront about: this resets if the server restarts, and
won't work correctly if you ever run multiple backend instances behind a
load balancer (each instance would have its own counters). If this project
scales to multiple instances, swap this for Redis-backed rate limiting.
"""
import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

# {key: [timestamp, timestamp, ...]} - timestamps of recent requests
_hits: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(key: str, max_per_minute: int) -> None:
    """Raises 429 if `key` has made more than `max_per_minute` calls
    in the last 60 seconds. Call this at the top of a route."""
    now = time.time()
    window_start = now - 60

    # drop timestamps older than the 60s window, keep the recent ones
    recent = [t for t in _hits[key] if t > window_start]

    if len(recent) >= max_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests - please wait a moment and try again.",
        )

    recent.append(now)
    _hits[key] = recent


def client_ip(request: Request) -> str:
    """Best-effort client identifier for rate limiting by IP."""
    if request.client:
        return request.client.host
    return "unknown"
