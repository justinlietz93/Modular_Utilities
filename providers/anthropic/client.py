"""AnthropicProvider adapter.

Uses anthropic>=0.34+ Messages API (client.messages.create) for chat and
supports basic JSON-style structured output request (heuristic prompt suffix).
"""
from __future__ import annotations

import time
from typing import Optional

try:
    import anthropic  # type: ignore
except Exception:  # pragma: no cover
    anthropic = None  # type: ignore

from ..base.interfaces import (
    LLMProvider,
    SupportsJSONOutput,
    ModelListingProvider,
    HasDefaultModel,
)
from ..base.models import (
    ChatRequest,
    ChatResponse,
    ProviderMetadata,
    ContentPart,
)
from ..base.repositories.model_registry import ModelRegistryRepository
from ..base.logging import get_logger, LogContext, log_event
from ..base.errors import ProviderError, ErrorCode, classify_exception
from ..base.resilience.retry import retry, RetryConfig
from ..base.streaming import ChatStreamEvent
from ..base.constants import STRUCTURED_STREAMING_UNSUPPORTED, MISSING_API_KEY_ERROR
from ..base.utils.messages import extract_system_and_user
from ..config import get_provider_config


def _default_model() -> str:
    # Claude 3.5 Sonnet typical default if not specified
    return "claude-3-5-sonnet-20240620"


class AnthropicProvider(LLMProvider, SupportsJSONOutput, ModelListingProvider, HasDefaultModel):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, registry: Optional[ModelRegistryRepository] = None) -> None:
        cfg = get_provider_config("anthropic")
        key = api_key or cfg.get("api_key") or getattr(anthropic, "api_key", None) or None
        self._api_key = key
        self._model = model or cfg.get("model") or _default_model()
        self._registry = registry or ModelRegistryRepository()
        self._logger = get_logger("providers.anthropic")

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def default_model(self) -> Optional[str]:
        return self._model

    def supports_json_output(self) -> bool:
        return True

    def list_models(self, refresh: bool = False):
        return self._registry.list_models("anthropic", refresh=refresh)

    def chat(self, request: ChatRequest) -> ChatResponse:
        model = request.model or self._model
        ctx = LogContext(provider=self.provider_name, model=model)
        if anthropic is None:
            meta = ProviderMetadata(provider_name=self.provider_name, model_name=model, extra={"error": "anthropic SDK not installed"})
            return ChatResponse(text=None, parts=None, raw=None, meta=meta)

        client = self._create_client()
        system_message, user_content = extract_system_and_user(request.messages)
        if not self._api_key:
            meta = ProviderMetadata(provider_name=self.provider_name, model_name=model, extra={"error": MISSING_API_KEY_ERROR})
            return ChatResponse(text=None, parts=None, raw=None, meta=meta)
        params, is_structured = self._build_params(model, request, system_message, user_content)

        log_event(self._logger, "chat.start", ctx, has_tools=bool(request.tools), has_schema=bool(request.json_schema), max_tokens=request.max_tokens, temperature=request.temperature)
        t0 = time.perf_counter()
        local_retry_config = self._build_retry_config(ctx)

        try:
            resp = retry(local_retry_config)(lambda: self._invoke_messages_create(client, params, model))()
            latency_ms = (time.perf_counter() - t0) * 1000.0
            log_event(self._logger, "chat.end", ctx, latency_ms=latency_ms)
        except ProviderError as e:  # pragma: no cover
            log_event(self._logger, "chat.error", ctx, error=str(e), code=e.code.value)
            meta = ProviderMetadata(provider_name=self.provider_name, model_name=model, latency_ms=None, extra={"error": e.message, "code": e.code.value})
            return ChatResponse(text=None, parts=None, raw=None, meta=meta)
        except Exception as e:  # pragma: no cover
            code = classify_exception(e)
            log_event(self._logger, "chat.error", ctx, error=str(e), code=code.value)
            meta = ProviderMetadata(provider_name=self.provider_name, model_name=model, latency_ms=None, extra={"error": str(e), "code": code.value})
            return ChatResponse(text=None, parts=None, raw=None, meta=meta)

        text_joined = self._extract_text(resp)

        meta = ProviderMetadata(
            provider_name=self.provider_name,
            model_name=model,
            latency_ms=latency_ms,
            token_param_used="max_tokens",
            extra={"is_structured": is_structured},
        )
        parts = [ContentPart(type="text", text=text_joined)] if text_joined else None
        return ChatResponse(text=text_joined or None, parts=parts, raw=None, meta=meta)

    # ---- Streaming ----
    def supports_streaming(self) -> bool:  # runtime-checkable capability
        return anthropic is not None

    def stream_chat(self, request: ChatRequest):
        model = request.model or self._model
        ctx = LogContext(provider=self.provider_name, model=model)
        log_event(self._logger, "stream.start", ctx, temperature=request.temperature, max_tokens=request.max_tokens)

        if anthropic is None:
            log_event(self._logger, "stream.error", ctx, error="anthropic SDK not installed")
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error="anthropic SDK not installed")
            return
        client = self._create_client()
        system_message, user_content = extract_system_and_user(request.messages)
        if not self._api_key:
            log_event(self._logger, "stream.error", ctx, error=MISSING_API_KEY_ERROR)
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=MISSING_API_KEY_ERROR)
            return
        if request.response_format == "json_object" or request.json_schema or request.tools:
            # Standardized rejection for structured streaming (future: implement accumulation)
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=STRUCTURED_STREAMING_UNSUPPORTED)
            return
        params, _ = self._build_params(model, request, system_message, user_content)

        # Start stream with retry; the iteration itself should not retry mid-stream
        stream_retry_config = self._build_retry_config(ctx, phase="stream.start")

        try:
            stream_ctx = retry(stream_retry_config)(lambda: self._start_stream_context(client, params, model))()
            # Context manager: ensure final event
            try:
                with stream_ctx as stream:
                    # Prefer text_stream if available for granular deltas
                    emitted_any = False
                    try:
                        for delta in self._iter_text_deltas(stream):
                            emitted_any = True
                            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=delta, finish=False)
                    except Exception as e:
                        code = classify_exception(e)
                        log_event(self._logger, "stream.error", ctx, error=str(e), code=code.value)
                        yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=str(e))
                        return

                    # Terminal event with optional final message in raw
                    final_raw = None
                    try:
                        final_raw = stream.get_final_message()
                    except Exception:
                        pass
                    yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, raw=final_raw)
                    log_event(self._logger, "stream.end", ctx, emitted=emitted_any)
            finally:
                # stream_ctx should clean itself via context manager
                pass
        except ProviderError as e:
            log_event(self._logger, "stream.error", ctx, error=str(e), code=e.code.value)
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=str(e))

    # ---- Internal helpers ----
    # _extract_messages removed in favor of shared helper extract_system_and_user

    def _build_params(self, model: str, request: ChatRequest, system_message: Optional[str], user_content: str):
        is_structured = request.response_format == "json_object"
        params = {
            "model": model,
            "max_tokens": request.max_tokens or 512,
            "temperature": request.temperature,
            "system": system_message,
            "messages": [{"role": "user", "content": user_content}],
        }
        if request.tools:
            params["tools"] = request.tools
        elif request.json_schema:
            params["tools"] = [
                {
                    "name": "json_output",
                    "description": "Return JSON adhering to provided schema",
                    "input_schema": request.json_schema,
                }
            ]
            params["tool_choice"] = {"type": "tool", "name": "json_output"}
        return params, is_structured

    def _extract_text(self, resp) -> str:
        try:
            content = getattr(resp, "content", []) or []
            return "\n".join(
                getattr(c, "text", "")
                for c in content
                if getattr(c, "type", None) == "text" and getattr(c, "text", "")
            )
        except Exception:
            return ""

    # ---- Internal refactored helpers ----
    def _build_retry_config(self, ctx: LogContext, phase: Optional[str] = None) -> RetryConfig:
        retry_cfg_raw = {}
        try:
            retry_cfg_raw = get_provider_config(self.provider_name).get("retry", {}) or {}
        except Exception:
            retry_cfg_raw = {}
        max_attempts = int(retry_cfg_raw.get("max_attempts", 3))
        delay_base = float(retry_cfg_raw.get("delay_base", 2.0))

        def _attempt_logger(*, attempt: int, max_attempts: int, delay, error: ProviderError | None):  # type: ignore[override]
            log_event(self._logger, "retry.attempt", ctx, phase=phase, attempt=attempt, max_attempts=max_attempts, delay=delay, error_code=(error.code.value if error else None), will_retry=bool(error and delay is not None))

        return RetryConfig(max_attempts=max_attempts, delay_base=delay_base, attempt_logger=_attempt_logger)

    def _create_client(self):
        return anthropic.Anthropic(api_key=self._api_key) if self._api_key else anthropic.Anthropic()

    def _invoke_messages_create(self, client, params, model: str):
        try:
            return client.messages.create(**params)
        except Exception as e:  # pragma: no cover
            code = classify_exception(e)
            raise ProviderError(code=code, message=str(e), provider=self.provider_name, model=model, retryable=code in (ErrorCode.TRANSIENT, ErrorCode.RATE_LIMIT, ErrorCode.TIMEOUT), raw=e)

    def _start_stream_context(self, client, params, model: str):
        try:
            return client.messages.stream(**params)
        except Exception as e:  # pragma: no cover
            code = classify_exception(e)
            raise ProviderError(code=code, message=str(e), provider=self.provider_name, model=model, retryable=code in (ErrorCode.TRANSIENT, ErrorCode.RATE_LIMIT, ErrorCode.TIMEOUT), raw=e)

    def _iter_text_deltas(self, stream):
        text_iter = getattr(stream, "text_stream", None)
        if text_iter is not None:
            for delta in text_iter:
                if delta:
                    yield delta
            return
        # Fallback: iterate over raw events and extract text
        for ev in stream:
            text = getattr(ev, "text", None) or getattr(getattr(ev, "delta", None), "text", None)
            if text:
                yield text
