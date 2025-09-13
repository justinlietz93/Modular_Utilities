"""GeminiProvider adapter.

Uses google-generativeai (google-generativeai>=0.8.0) GenerativeModel API.
Supports simple text chat and heuristic JSON output capture.
"""
from __future__ import annotations

import time
from typing import Optional

try:
    import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover
    genai = None  # type: ignore

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
from ..config import get_provider_config
from ..base.streaming import ChatStreamEvent
from ..base.constants import STRUCTURED_STREAMING_UNSUPPORTED, MISSING_API_KEY_ERROR
from ..base.utils.messages import extract_system_and_user


def _default_model() -> str:
    return "gemini-1.5-flash"


class GeminiProvider(LLMProvider, SupportsJSONOutput, ModelListingProvider, HasDefaultModel):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, registry: Optional[ModelRegistryRepository] = None) -> None:
        self._api_key = api_key
        self._model = model or _default_model()
        self._registry = registry or ModelRegistryRepository()
        if genai and api_key:
            genai.configure(api_key=api_key)
        self._logger = get_logger("providers.gemini")

    @property
    def provider_name(self) -> str:
        return "gemini"

    def default_model(self) -> Optional[str]:
        return self._model

    def supports_json_output(self) -> bool:
        return True

    def list_models(self, refresh: bool = False):
        return self._registry.list_models("gemini", refresh=refresh)

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Synchronous chat generation with retry and optional JSON schema."""
        model = request.model or self._model
        ctx = LogContext(provider=self.provider_name, model=model)
        if genai is None:
            meta = ProviderMetadata(provider_name=self.provider_name, model_name=model, extra={"error": "google-generativeai SDK not installed"})
            return ChatResponse(text=None, parts=None, raw=None, meta=meta)
        _system_message, user_content = extract_system_and_user(request.messages)
        if not self._api_key:  # Early credential check
            meta = ProviderMetadata(provider_name=self.provider_name, model_name=model, extra={"error": MISSING_API_KEY_ERROR})
            return ChatResponse(text=None, parts=None, raw=None, meta=meta)
        is_structured = request.response_format == "json_object"

        gen_model = self._build_model(model, request)
        log_event(self._logger, "chat.start", ctx, has_tools=bool(request.tools), has_schema=bool(request.json_schema), max_tokens=request.max_tokens, temperature=request.temperature)
        t0 = time.perf_counter()
        retry_config = self._build_retry_config(ctx)
        try:
            resp = retry(retry_config)(lambda: self._start_generation(gen_model, user_content, request.tools, stream=False))()
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

        text = getattr(resp, "text", "") or ""
        meta = ProviderMetadata(provider_name=self.provider_name, model_name=model, latency_ms=latency_ms, token_param_used="max_output_tokens", extra={"is_structured": is_structured})
        parts = [ContentPart(type="text", text=text)] if text else None
        return ChatResponse(text=text or None, parts=parts, raw=None, meta=meta)

    # ---- Streaming ----
    def supports_streaming(self) -> bool:  # runtime-checkable capability
        return True

    def stream_chat(self, request: ChatRequest):
        model = request.model or self._model
        ctx = LogContext(provider=self.provider_name, model=model)
        log_event(self._logger, "stream.start", ctx, temperature=request.temperature, max_tokens=request.max_tokens)
        if genai is None:
            log_event(self._logger, "stream.error", ctx, error="google-generativeai SDK not installed")
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error="google-generativeai SDK not installed")
            return
        _system_message, user_content = extract_system_and_user(request.messages)
        if not self._api_key:
            log_event(self._logger, "stream.error", ctx, error=MISSING_API_KEY_ERROR)
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=MISSING_API_KEY_ERROR)
            return
        if request.response_format == "json_object" or request.json_schema or request.tools:
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=STRUCTURED_STREAMING_UNSUPPORTED)
            return

        gen_model = self._build_model(model, request)
        retry_config = self._build_retry_config(ctx, phase="stream.start")
        try:
            stream = retry(retry_config)(lambda: self._start_generation(gen_model, user_content, request.tools, stream=True))()
            emitted_any = False
            try:
                for chunk in stream:
                    text = self._extract_text_from_chunk(chunk)
                    if text:
                        emitted_any = True
                        yield ChatStreamEvent(provider=self.provider_name, model=model, delta=text, finish=False)
            except Exception as e:
                code = classify_exception(e)
                log_event(self._logger, "stream.error", ctx, error=str(e), code=code.value)
                yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=str(e))
                return
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True)
            log_event(self._logger, "stream.end", ctx, emitted=emitted_any)
        except ProviderError as e:  # pragma: no cover
            log_event(self._logger, "stream.error", ctx, error=str(e), code=e.code.value)
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=str(e))
        except Exception as e:  # pragma: no cover
            code = classify_exception(e)
            log_event(self._logger, "stream.error", ctx, error=str(e), code=code.value)
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=str(e))

    # ---- Internal refactored helpers ----
    def _build_model(self, model: str, request: ChatRequest):
        gen_kwargs = {}
        if request.json_schema:
            gen_kwargs["generation_config"] = {
                "response_mime_type": "application/json",
                "response_schema": request.json_schema,
            }
        return genai.GenerativeModel(model, **gen_kwargs)

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

    def _start_generation(self, gen_model, user_content: str, tools, stream: bool):
        try:
            if tools:
                return gen_model.generate_content(user_content, tools=tools, stream=stream)
            return gen_model.generate_content(user_content, stream=stream)
        except Exception as e:  # pragma: no cover
            code = classify_exception(e)
            raise ProviderError(code=code, message=str(e), provider=self.provider_name, model=self._model, retryable=code in (ErrorCode.TRANSIENT, ErrorCode.RATE_LIMIT, ErrorCode.TIMEOUT), raw=e)

    def _extract_text_from_chunk(self, chunk) -> Optional[str]:  # type: ignore[override]
        text = None
        try:
            text = getattr(chunk, "text", None)
            if text:
                return text
            candidates = getattr(chunk, "candidates", None)
            if candidates:
                content = getattr(candidates[0], "content", None)
                parts = getattr(content, "parts", None) if content else None
                if parts:
                    for p in parts:
                        t = getattr(p, "text", None)
                        if t:
                            return t
        except Exception:  # pragma: no cover
            return None
        return None
