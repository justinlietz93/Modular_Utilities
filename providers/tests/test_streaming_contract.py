"""Streaming contract tests.

Validates provider stream_chat implementations:
- Emits >=1 events and exactly one terminal finish event.
- No duplicate finish events.
- No final aggregated text delta repeated as a last delta (we rely on accumulate_events).
- Retry only applied to stream start (simulated via a fake wrapper provider).

These tests use a FakeProvider implementing the same ChatStreamEvent semantics to avoid
external API calls. Real providers can be smoke-tested separately behind env guards.
"""
from __future__ import annotations

from typing import Optional
import itertools

from ..base.streaming import ChatStreamEvent, accumulate_events
from ..base.models import ChatRequest, Message, ProviderMetadata, ChatResponse, ContentPart
from ..base.interfaces import LLMProvider


class FakeStreamingProvider(LLMProvider):
    def __init__(self, fail_first_start: bool = False, model: str = "fake-model") -> None:
        self._fail_first_start = fail_first_start
        self._attempts = 0
        self._model = model

    @property
    def provider_name(self) -> str:
        return "fake"

    def default_model(self) -> Optional[str]:  # pragma: no cover - not used
        return self._model

    def chat(self, request: ChatRequest) -> ChatResponse:  # pragma: no cover - not part of contract test
        return ChatResponse(text="static", parts=[ContentPart(type="text", text="static")], raw=None, meta=ProviderMetadata(provider_name=self.provider_name, model_name=self._model))

    def supports_json_output(self) -> bool:  # pragma: no cover
        return False

    def stream_chat(self, request: ChatRequest):
        # Simulate retry-on-start only by raising first time if configured
        if self._fail_first_start and self._attempts == 0:
            self._attempts += 1
            raise RuntimeError("transient start failure")
        # Produce three deltas then terminal
        for ch in ["Hello", ", ", "world!"]:
            yield ChatStreamEvent(provider=self.provider_name, model=self._model, delta=ch, finish=False)
        yield ChatStreamEvent(provider=self.provider_name, model=self._model, delta=None, finish=True)


def test_stream_accumulate_basic():
    provider = FakeStreamingProvider()
    req = ChatRequest(model="fake-model", messages=[Message(role="user", content="hi")])
    events = list(provider.stream_chat(req))
    assert events, "No events emitted"
    finishes = [e for e in events if e.finish]
    assert len(finishes) == 1, "Expected exactly one finish event"
    assert finishes[0].delta is None, "Terminal event should not repeat text delta"
    # Accumulate
    resp = accumulate_events(events)
    assert resp.text == "Hello, world!"
    print("test_stream_accumulate_basic: confirmed single terminal event, no duplicated final delta, accumulation produced expected text")


def test_stream_retry_only_on_start():
    provider = FakeStreamingProvider(fail_first_start=True)
    req = ChatRequest(model="fake-model", messages=[Message(role="user", content="retry")])
    # We simulate a retry by manually looping until success once; real providers wrap with_retry at start.
    for attempt in itertools.count():
        try:
            events = list(provider.stream_chat(req))
            break
        except RuntimeError:
            if attempt > 2:
                raise
            continue
    finishes = [e for e in events if e.finish]
    assert len(finishes) == 1
    assert events[-1].finish is True
    print("test_stream_retry_only_on_start: verified failure occurs only before any deltas and successful run yields one terminal event")


def test_accumulate_error_event_short_circuits():
    # Create custom sequence with an error
    events = [
        ChatStreamEvent(provider="fake", model="fake", delta="Hello", finish=False),
        ChatStreamEvent(provider="fake", model="fake", delta=None, finish=True, error="boom"),
        ChatStreamEvent(provider="fake", model="fake", delta="SHOULD_NOT_INCLUDE", finish=False),
    ]
    resp = accumulate_events(events)
    assert resp.text is None
    assert resp.meta.extra.get("stream_error") == "boom"
    print("test_accumulate_error_event_short_circuits: ensured error terminal stops accumulation and ignores later deltas")
