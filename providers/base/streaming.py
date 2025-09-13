"""Streaming primitives for provider layer.

Keeps streaming concerns separate from core request/response DTOs to
respect single-responsibility and keep existing files small (<500 LOC rule).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Iterator, List

from .models import ChatResponse, ContentPart, ProviderMetadata


@dataclass
class ChatStreamEvent:
    """Represents an incremental delta from a streaming provider.

    Fields:
      provider: canonical provider name
      model: model id/name
      delta: textual delta (may be empty for control events)
      finish: True on final event
      error: optional error string (finish implicitly True when error)
      raw: provider SDK chunk (optional for debugging)
    """
    provider: str
    model: str
    delta: str | None
    finish: bool = False
    error: str | None = None
    raw: Any | None = None

    def is_error(self) -> bool:
        return self.error is not None


def accumulate_events(events: Iterable[ChatStreamEvent]) -> ChatResponse:
    """Accumulate a sequence of ChatStreamEvent into a ChatResponse.

    - Concatenates text deltas.
    - If an error event is encountered, returns a ChatResponse with error metadata.
    - Metadata is minimal; providers can enrich later via a terminal event convention.
    """
    events_list: List[ChatStreamEvent] = list(events)
    if not events_list:
        meta = ProviderMetadata(provider_name="unknown", model_name="unknown")
        return ChatResponse(text="", parts=None, raw=None, meta=meta)

    provider = events_list[0].provider
    model = events_list[0].model
    error_event = next((e for e in events_list if e.error), None)
    if error_event:
        meta = ProviderMetadata(provider_name=provider, model_name=model, extra={"stream_error": error_event.error})
        return ChatResponse(text=None, parts=None, raw=None, meta=meta)

    text_parts: List[str] = [e.delta for e in events_list if e.delta]
    full_text = "".join(text_parts)
    parts = [ContentPart(type="text", text=full_text)] if full_text else None
    meta = ProviderMetadata(provider_name=provider, model_name=model, extra={"stream_events": len(events_list)})
    return ChatResponse(text=full_text, parts=parts, raw=None, meta=meta)


__all__ = [
    "ChatStreamEvent",
    "accumulate_events",
]
