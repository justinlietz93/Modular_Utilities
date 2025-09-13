"""Capability enumeration & detection utilities.

Non-invasive: adapters need not declare anything; we infer based on implemented
runtime-checkable protocols to keep incremental adoption low-risk.
"""
from __future__ import annotations

from typing import Protocol, FrozenSet

from .interfaces import (
    LLMProvider,
    SupportsStreaming,
    SupportsJSONOutput,
    SupportsResponsesAPI,
    ModelListingProvider,
    HasDefaultModel,
)

# String constants (avoid Enum overhead for simple set operations)
CAP_STREAMING = "streaming"
CAP_JSON = "json_output"
CAP_RESPONSES_API = "responses_api"
CAP_MODEL_LISTING = "model_listing"
CAP_DEFAULT_MODEL = "default_model"


def detect_capabilities(provider: LLMProvider) -> FrozenSet[str]:  # type: ignore[type-arg]
    caps: set[str] = set()
    if isinstance(provider, SupportsStreaming) and getattr(provider, "supports_streaming", lambda: False)():
        caps.add(CAP_STREAMING)
    if isinstance(provider, SupportsJSONOutput) and getattr(provider, "supports_json_output", lambda: False)():
        caps.add(CAP_JSON)
    if isinstance(provider, SupportsResponsesAPI):
        caps.add(CAP_RESPONSES_API)
    if isinstance(provider, ModelListingProvider):
        caps.add(CAP_MODEL_LISTING)
    if isinstance(provider, HasDefaultModel) and getattr(provider, "default_model", lambda: None)() is not None:
        caps.add(CAP_DEFAULT_MODEL)
    return frozenset(caps)


__all__ = [
    "CAP_STREAMING",
    "CAP_JSON",
    "CAP_RESPONSES_API",
    "CAP_MODEL_LISTING",
    "CAP_DEFAULT_MODEL",
    "detect_capabilities",
]
