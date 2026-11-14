"""A tiny in-process result cache for read-heavy aggregate queries.

The analytics endpoints (summary/timeseries/distribution/monthly-daily)
recompute the same few GROUP BY queries on every filter tweak and on
every month-swipe in the Time Series UI. Postgres itself is fast enough
for this dataset size, but round-tripping + re-aggregating on each
request is wasted work when nothing has changed between requests.

Design: a single global "generation" counter. Every write path that
can change a cached aggregate's answer (ingest, transaction patch,
category/keyword mutation) calls `bump_generation()`. Every cached
read is keyed by `(generation, *args)`, so a stale entry is never
served — it's simply never looked up again once the generation moves
past it, and old entries are dropped once the cache exceeds its cap
instead of being tracked individually. This avoids the correctness
risk of a TTL (serving stale data for N seconds after a write) while
still giving repeated reads between writes a cheap cache hit.
"""
from __future__ import annotations

import functools
import threading
from collections.abc import Callable
from typing import TypeVar

_lock = threading.Lock()
_generation = 0

_MAX_ENTRIES = 256

T = TypeVar("T")


def bump_generation() -> None:
    """Invalidate every cached aggregate. Call this after any write that
    could change a transaction's amount, date, account, or category
    (ingest, recategorize, category/keyword CRUD)."""
    global _generation
    with _lock:
        _generation += 1


def current_generation() -> int:
    with _lock:
        return _generation


def cached(fn: Callable[..., T]) -> Callable[..., T]:
    """Memoize a pure function of its (hashable) arguments, scoped to the
    current generation. The wrapped function's FIRST positional argument
    is assumed to be the SQLAlchemy ``Session`` (our service functions'
    convention) and is excluded from the cache key — a session is
    request-scoped and carries no information the aggregate's answer
    depends on; what matters is the generation counter plus the filter
    arguments that follow it.

    Not thread-pool-safe beyond CPython's GIL for the dict access
    itself, which is sufficient here — a request-serving thread pool
    computing the same aggregate twice in a race just recomputes once
    more, it doesn't corrupt anything.
    """
    cache: dict[tuple, T] = {}

    @functools.wraps(fn)
    def wrapper(db, *args, **kwargs):
        key = (current_generation(), args, tuple(sorted(kwargs.items())))
        try:
            return cache[key]
        except KeyError:
            pass
        except TypeError:
            # Unhashable args (shouldn't happen for our filter dataclasses,
            # but fail open rather than raise from a cache-layer bug).
            return fn(db, *args, **kwargs)

        result = fn(db, *args, **kwargs)
        if len(cache) >= _MAX_ENTRIES:
            cache.clear()
        cache[key] = result
        return result

    wrapper.cache_clear = cache.clear  # type: ignore[attr-defined]
    return wrapper
