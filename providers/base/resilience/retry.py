from __future__ import annotations

import time
import functools
from dataclasses import dataclass
from typing import Callable, TypeVar, Iterable, Protocol

from ..errors import ProviderError, ErrorCode

T = TypeVar("T")


class AttemptLogger(Protocol):  # pragma: no cover - structural protocol
    def __call__(self, *, attempt: int, max_attempts: int, delay: float | None, error: ProviderError | None) -> None: ...


@dataclass(frozen=True)
class RetryConfig:
    max_attempts: int = 3
    delay_base: float = 2.0  # exponential base (attempt^base)
    retryable_codes: tuple[ErrorCode, ...] = (
        ErrorCode.TRANSIENT,
        ErrorCode.RATE_LIMIT,
        ErrorCode.TIMEOUT,
    )
    attempt_logger: AttemptLogger | None = None

    def delays(self) -> Iterable[float]:
        for attempt in range(self.max_attempts - 1):
            yield self.delay_base ** attempt


DEFAULT_RETRY_CONFIG = RetryConfig()


def with_retry(max_attempts: int = 3, delay_base: float = 2.0):
    """Backward-compatible decorator (kept for existing imports).

    Prefer using `retry(config: RetryConfig = DEFAULT_RETRY_CONFIG)` moving forward.
    """
    return retry(RetryConfig(max_attempts=max_attempts, delay_base=delay_base))


def retry(config: RetryConfig = DEFAULT_RETRY_CONFIG):
    """Return a decorator applying standardized retry policy.

    - Retries only on configured retryable error codes
    - Exponential backoff using delay_base ** attempt
    - Preserves original function signature
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exc: ProviderError | None = None
            for attempt, delay in enumerate(list(config.delays()) + [None]):  # final attempt has delay None
                try:
                    result = func(*args, **kwargs)
                    if config.attempt_logger:
                        config.attempt_logger(attempt=attempt, max_attempts=config.max_attempts, delay=None, error=None)
                    return result
                except ProviderError as e:
                    last_exc = e
                    # Log attempt outcome
                    if config.attempt_logger:
                        config.attempt_logger(attempt=attempt, max_attempts=config.max_attempts, delay=delay, error=e)
                    if (e.code in config.retryable_codes) and (delay is not None):
                        time.sleep(delay)
                        continue
                    raise
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator

__all__ = [
    "RetryConfig",
    "DEFAULT_RETRY_CONFIG",
    "retry",
    "with_retry",  # legacy alias
]
