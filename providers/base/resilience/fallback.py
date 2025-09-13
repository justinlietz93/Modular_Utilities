from __future__ import annotations

import functools
from typing import Callable, TypeVar

T = TypeVar("T")


def with_fallback(_fallback_provider: str = "openai"):
    """Placeholder fallback decorator.

    Keep minimal until a real ProviderSelector exists at composition root.
    For now, simply re-raises to avoid silent surprises.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return func(*args, **kwargs)

        return wrapper

    return decorator
