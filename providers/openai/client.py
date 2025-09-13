"""
OpenAIProvider adapter

Implements the provider-agnostic interfaces defined in
[interfaces.py](Cogito/src/providers/base/interfaces.py) using the existing
OpenAI client implementation at [openai_client.py](Cogito/src/providers/openai_client.py).

This adapter:
- Accepts a normalized [ChatRequest](Cogito/src/providers/base/models.py:1)
- Invokes [call_openai_with_retry()](Cogito/src/providers/openai_client.py:51)
- Returns a normalized [ChatResponse](Cogito/src/providers/base/models.py:1)
- Exposes model registry listing via [ModelRegistryRepository](Cogito/src/providers/base/repositories/model_registry.py:1)

Notes
- Non-invasive: no changes to existing openai_client behavior.
- Stays contained within providers/ as requested.
"""

from __future__ import annotations

import json
import time
from typing import Optional, List, Iterator

from ..base.interfaces import (
    LLMProvider,
    SupportsJSONOutput,
    SupportsResponsesAPI,
    ModelListingProvider,
    HasDefaultModel,
    SupportsStreaming,
)
from ..base.models import (
    ChatRequest,
    ChatResponse,
    ProviderMetadata,
    ContentPart,
)
from ..base.streaming import ChatStreamEvent
from ..base.errors import ProviderError, ErrorCode, classify_exception
from ..base.repositories.model_registry import ModelRegistryRepository
from ..config import get_provider_config
from ..base.logging import get_logger, LogContext, log_event
from ..base.resilience.retry import retry
from ..base.constants import STRUCTURED_STREAMING_UNSUPPORTED, MISSING_API_KEY_ERROR
from ..base.utils.messages import extract_system_and_user
import json as _json_for_openai

try:  # Prefer real SDK if present
    from openai import OpenAI as _OpenAIClient  # type: ignore
except Exception:  # pragma: no cover
    _OpenAIClient = None  # type: ignore


def call_openai_with_retry(
    prompt_template: str,
    context: dict,
    config: dict,
    is_structured: bool = False,
    max_tokens: int | None = None,
):
    """Minimal helper kept for backwards compatibility with legacy call path.

    NOTE: Prefer using OpenAIProvider.chat via normalized DTOs. This function is
    intentionally light; retry/backoff logic can be layered later.
    """
    if _OpenAIClient is None:
        raise RuntimeError("openai SDK not installed; install extras [openai]")
    api_cfg = (config or {}).get("api", {}).get("openai", {})
    api_key = api_cfg.get("api_key")
    model = api_cfg.get("model") or context.get("model") or "gpt-4o-mini"
    system_message = api_cfg.get("system_message")
    temperature = api_cfg.get("temperature")

    user_content = prompt_template.format(**(context or {}))
    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": user_content})

    params = {
        "model": model,
        "messages": messages,
    }
    if temperature is not None:
        params["temperature"] = float(temperature)
    if max_tokens is not None:
        params["max_tokens"] = int(max_tokens)

    client = _OpenAIClient(api_key=api_key)
    resp = client.chat.completions.create(**params)
    text = resp.choices[0].message.content if getattr(resp, "choices", None) else ""
    if is_structured:
        try:
            return _json_for_openai.loads(text), model
        except Exception:
            return {"text": text}, model
    return text, model


class OpenAIProvider(
    LLMProvider,
    SupportsJSONOutput,
    SupportsResponsesAPI,
    ModelListingProvider,
    HasDefaultModel,
    SupportsStreaming,
):
    """
        Adapter for OpenAI which conforms to provider-agnostic contracts.
        Construction:
            provider = OpenAIProvider()
            response = provider.chat(ChatRequest(...))
    """

    def __init__(self, default_model: Optional[str] = None, registry: Optional[ModelRegistryRepository] = None) -> None:
        cfg = get_provider_config("openai")
        self._default_model = default_model or cfg.get("model") or "o3-mini"
        self._registry = registry or ModelRegistryRepository()
        # Provider-scoped structured logger
        self._logger = get_logger("providers.openai")

    @property
    def provider_name(self) -> str:
        return "openai"

    def default_model(self) -> Optional[str]:
        return self._default_model

    def supports_json_output(self) -> bool:
        return True

    def uses_responses_api(self, model: str) -> bool:
        lower = (model or "").lower()
        return ("o1" in lower) or ("o3-mini" in lower)

    def supports_streaming(self) -> bool:  # type: ignore[override]
        return _OpenAIClient is not None

    def list_models(self, refresh: bool = False):
        return self._registry.list_models("openai", refresh=refresh)

    # -------------------- Core Chat --------------------

    def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Execute a single chat request via existing call_openai_with_retry, normalizing the result.
        """
        # Resolve model with request override
        model = (request.model or self._default_model)
        ctx = LogContext(provider=self.provider_name, model=model)

        # Unified extraction via shared helper
        system_message, user_content = extract_system_and_user(request.messages)  # assistant/tool roles ignored for now
        # Early credential sentinel (config-based key only; could extend to env var fetch later)
        cfg_key = get_provider_config("openai").get("api", {}).get("openai", {}).get("api_key")
        if not cfg_key:
            meta = ProviderMetadata(provider_name=self.provider_name, model_name=model, extra={"error": MISSING_API_KEY_ERROR})
            return ChatResponse(text=None, parts=None, raw=None, meta=meta)

        # Build config payload as expected by call_openai_with_retry
        api_config = {
            "api": {
                "openai": {
                    "model": model,
                    # request.max_tokens maps to the appropriate OpenAI param internally
                    **({"max_tokens": request.max_tokens} if request.max_tokens is not None else {}),
                    # temperature is omitted downstream if the chosen model family disallows it
                    **({"temperature": request.temperature} if request.temperature is not None else {}),
                    **({"system_message": system_message} if system_message else {}),
                }
            }
        }

        # Structured output?
        is_structured = (request.response_format == "json_object")

        # Invoke provider with retry and measure latency
        log_event(
            self._logger,
            "chat.start",
            ctx,
            response_format=request.response_format,
            has_json_schema=bool(request.json_schema),
            tools_count=len(request.tools or []) if request.tools else 0,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        def _invoke():
            try:
                return call_openai_with_retry(
                    prompt_template="{content}",
                    context={"content": user_content},
                    config=api_config,
                    is_structured=is_structured,
                    # Also pass max_tokens explicitly to cooperate with responses.create path
                    max_tokens=request.max_tokens if request.max_tokens is not None else None,
                )
            except Exception as e:  # Map to ProviderError for retry policy
                code = classify_exception(e)
                raise ProviderError(
                    code=code,
                    message=str(e),
                    provider=self.provider_name,
                    model=model,
                    retryable=code in (ErrorCode.TRANSIENT, ErrorCode.RATE_LIMIT, ErrorCode.TIMEOUT),
                    raw=e,
                )

        t0 = time.perf_counter()
        try:
            resp, model_used = retry()( _invoke )()
            latency_ms = (time.perf_counter() - t0) * 1000.0
            log_event(self._logger, "chat.end", ctx, latency_ms=latency_ms, used_model=model_used, structured=is_structured)
        except ProviderError as e:
            log_event(self._logger, "chat.error", ctx, error=str(e), code=e.code.value)
            # Normalize failures into a ChatResponse with error metadata
            meta = ProviderMetadata(
                provider_name=self.provider_name,
                model_name=model,
                http_status=None,
                request_id=None,
                latency_ms=None,
                extra={
                    "error": e.message,
                    "phase": "call_openai_with_retry",
                    "error_code": e.code.value,
                },
            )
            return ChatResponse(text=None, parts=None, raw=None, meta=meta)
        except Exception as e:  # Safety net
            code = classify_exception(e)
            log_event(self._logger, "chat.error", ctx, error=str(e), code=code.value)
            meta = ProviderMetadata(
                provider_name=self.provider_name,
                model_name=model,
                http_status=None,
                request_id=None,
                latency_ms=None,
                extra={
                    "error": str(e),
                    "phase": "unexpected",
                    "error_code": code.value,
                },
            )
            return ChatResponse(text=None, parts=None, raw=None, meta=meta)

        # Build metadata (limited visibility since underlying client hides HTTP details)
        meta = ProviderMetadata(
            provider_name=self.provider_name,
            model_name=str(model_used),
            token_param_used=None,          # Not directly exposed by call_openai_with_retry
            temperature_included=None,      # Not directly exposed by call_openai_with_retry
            http_status=None,               # Not returned by the high-level client
            request_id=None,                # Not returned by the high-level client
            latency_ms=latency_ms,
            extra={
                "is_structured": is_structured,
                "used_responses_api": self.uses_responses_api(str(model_used)),
                "response_format": request.response_format,
            },
        )

        # Normalize output into text/parts
        if isinstance(resp, dict):
            # Structured JSON returned; represent as a single JSON part and provide a text serialization
            try:
                text = json.dumps(resp, ensure_ascii=False)
            except Exception:
                text = str(resp)
            parts = [ContentPart(type="json", text=text, data=None)]
            return ChatResponse(text=text, parts=parts, raw=None, meta=meta)

        # Fallback: plain text or unknown object
        if isinstance(resp, str):
            return ChatResponse(text=resp, parts=None, raw=None, meta=meta)

        # Last resort: string-coerce unknown types
        return ChatResponse(text=str(resp), parts=None, raw=None, meta=meta)

    # -------------------- Streaming Chat --------------------

    def stream_chat(self, request: ChatRequest) -> Iterator[ChatStreamEvent]:  # type: ignore[override]
        """Stream tokens/deltas for a chat request.

        Limitations (initial implementation):
          - Disabled when response_format == 'json_object' or json_schema/tools present.
          - Falls back to single non-stream delta if SDK unavailable.
        """
        if not self.supports_streaming():
            yield ChatStreamEvent(provider=self.provider_name, model=request.model, delta=None, finish=True, error="openai SDK not installed")
            return

        if request.response_format == "json_object" or request.json_schema or request.tools:
            yield ChatStreamEvent(provider=self.provider_name, model=request.model, delta=None, finish=True, error=STRUCTURED_STREAMING_UNSUPPORTED)
            return

        model = request.model or self._default_model
        ctx = LogContext(provider=self.provider_name, model=model)

        # Build messages preserving system + user (assistant omitted by helper design); assistant context could be re-added later
        system_message, user_content = extract_system_and_user(request.messages)
        messages: List[dict] = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        if user_content:
            messages.append({"role": "user", "content": user_content})

        # Early credential sentinel
        cfg_key = get_provider_config("openai").get("api", {}).get("openai", {}).get("api_key")
        if not cfg_key:
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=MISSING_API_KEY_ERROR)
            return

        params = {"model": model, "messages": messages, "stream": True}
        if request.max_tokens is not None:
            params["max_tokens"] = int(request.max_tokens)
        if request.temperature is not None:
            params["temperature"] = float(request.temperature)

        # Resolve API key similarly to legacy path
        cfg = get_provider_config("openai")
        api_cfg = (cfg or {}).get("api", {}).get("openai", {})
        api_key = api_cfg.get("api_key")
        client = _OpenAIClient(api_key=api_key)

        log_event(
            self._logger,
            "stream.start",
            ctx,
            has_api_key=bool(api_key),
            max_tokens=params.get("max_tokens"),
            temperature=params.get("temperature"),
        )

        assembled: List[str] = []
        try:
            # Establish stream with retry (only the start; mid-stream failures are surfaced as error events)
            def _start_stream():
                try:
                    return client.chat.completions.create(**params)  # type: ignore[arg-type]
                except Exception as e:
                    code = classify_exception(e)
                    raise ProviderError(
                        code=code,
                        message=str(e),
                        provider=self.provider_name,
                        model=model,
                        retryable=code in (ErrorCode.TRANSIENT, ErrorCode.RATE_LIMIT, ErrorCode.TIMEOUT),
                        raw=e,
                    )

            stream = retry()(_start_stream)()
            for chunk in stream:  # SDK yields incremental objects
                try:
                    # chat.completions streaming shape (delta.content)
                    delta = getattr(chunk.choices[0].delta, "content", None) if getattr(chunk, "choices", None) else None
                except Exception:  # pragma: no cover - defensive
                    delta = None
                if delta:
                    assembled.append(delta)
                    yield ChatStreamEvent(provider=self.provider_name, model=model, delta=delta, finish=False, raw=None)
            # Terminal event: do NOT emit aggregated text again (avoid duplication in accumulator)
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True)
            log_event(self._logger, "stream.end", ctx, tokens=len(assembled))
        except ProviderError as e:  # pragma: no cover - error path
            log_event(self._logger, "stream.error", ctx, error=str(e), code=e.code.value)
            yield ChatStreamEvent(
                provider=self.provider_name,
                model=model,
                delta=None,
                finish=True,
                error=f"{e.code.value}:{e.message[:260]}",
            )
        except Exception as e:  # pragma: no cover - safety net
            code = classify_exception(e)
            log_event(self._logger, "stream.error", ctx, error=str(e), code=code.value)
            yield ChatStreamEvent(
                provider=self.provider_name,
                model=model,
                delta=None,
                finish=True,
                error=f"{code.value}:{str(e)[:260]}",
            )
