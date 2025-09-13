from __future__ import annotations

import functools
import time
from typing import Callable, TypeVar

T = TypeVar("T")


def cache_result(maxsize: int = 128, ttl: int = 3600):
    cache = {}
    timestamps = {}

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            key = str((args, frozenset(sorted(kwargs.items()))))
            now = time.time()
            if key in cache and now - timestamps[key] < ttl:
                return cache[key]
            result = func(*args, **kwargs)
            if len(cache) >= maxsize:
                oldest = min(timestamps.items(), key=lambda x: x[1])[0]
                cache.pop(oldest, None)
                timestamps.pop(oldest, None)
            cache[key] = result
            timestamps[key] = now
            return result

        return wrapper

    return decorator
