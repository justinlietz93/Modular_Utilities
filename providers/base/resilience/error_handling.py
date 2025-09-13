from __future__ import annotations

import functools
from typing import Callable, TypeVar

from ..errors import ProviderError, ErrorCode

T = TypeVar("T")


def with_error_handling(func: Callable[..., T]) -> Callable[..., T]:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except ProviderError:
            raise
        except Exception as e:
            # Wrap unknown exceptions as transient
            raise ProviderError(code=ErrorCode.UNKNOWN, message=str(e), provider="unknown") from e

    return wrapper
