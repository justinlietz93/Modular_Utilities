"""Base shared constants for provider adapters.

Central location to avoid scattering magic strings and default numbers.
"""
from __future__ import annotations

# Structured streaming unsupported sentinel (standardized message)
STRUCTURED_STREAMING_UNSUPPORTED = "structured_streaming_not_supported"

# Missing credential sentinel
MISSING_API_KEY_ERROR = "missing_api_key"

# Default HTTP timeouts (seconds)
DEFAULT_HTTP_TIMEOUT = 60.0          # typical single request timeout
DEFAULT_STREAM_HTTP_TIMEOUT = None   # use server-sent streaming (no overall read timeout)

__all__ = [
    "STRUCTURED_STREAMING_UNSUPPORTED",
    "MISSING_API_KEY_ERROR",
    "DEFAULT_HTTP_TIMEOUT",
    "DEFAULT_STREAM_HTTP_TIMEOUT",
]
