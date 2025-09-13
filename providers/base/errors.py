"""Unified provider error taxonomy.

Adapters should catch provider SDK exceptions and map them to ProviderError with
an appropriate ErrorCode. Upstream layers can rely on the error code for retry,
metrics tagging, or fallbacks without parsing raw messages.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ErrorCode(str, Enum):
    AUTH = "auth"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    TRANSIENT = "transient"
    UNSUPPORTED = "unsupported"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


@dataclass
class ProviderError(Exception):
    code: ErrorCode
    message: str
    provider: str
    model: Optional[str] = None
    retryable: bool = False
    raw: Optional[Exception] = None

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.provider}:{self.model or '-'} {self.code.value}: {self.message}"


def classify_exception(exc: Exception) -> ErrorCode:
    msg = str(exc).lower()
    if "rate" in msg and "limit" in msg:
        return ErrorCode.RATE_LIMIT
    if "timeout" in msg or "timed out" in msg:
        return ErrorCode.TIMEOUT
    if "auth" in msg or "api key" in msg or "unauthorized" in msg:
        return ErrorCode.AUTH
    if "unsupported" in msg or "not supported" in msg:
        return ErrorCode.UNSUPPORTED
    return ErrorCode.UNKNOWN


__all__ = [
    "ErrorCode",
    "ProviderError",
    "classify_exception",
]
