"""XAIProvider adapter.

Assumes xAI Grok provides an OpenAI-compatible chat completions endpoint.
Adds structured logging and retry with unified error taxonomy.
"""
from __future__ import annotations

from typing import Optional, Any, Tuple, Dict
import time

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

from ..base.interfaces import LLMProvider, SupportsJSONOutput, HasDefaultModel
from ..base.models import ChatRequest, ChatResponse, ProviderMetadata, ContentPart
from ..base.logging import get_logger, log_event, LogContext
from ..base.resilience.retry import retry
from ..base.errors import ProviderError, classify_exception, ErrorCode
from ..base.streaming import ChatStreamEvent
from ..base.constants import STRUCTURED_STREAMING_UNSUPPORTED, MISSING_API_KEY_ERROR
from ..base.utils.messages import extract_system_and_user


class XAIProvider(LLMProvider, SupportsJSONOutput, HasDefaultModel):
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None, registry: Any | None = None):
        self._api_key = api_key
        self._base_url = base_url or "https://api.x.ai/v1"  # placeholder
        self._model = model or "grok-beta"
        self._logger = get_logger("providers.xai")

    @property
    def provider_name(self) -> str:
        return "xai"

    def default_model(self) -> Optional[str]:
        return self._model

    def supports_json_output(self) -> bool:
        return True

    def chat(self, request: ChatRequest) -> ChatResponse:
        model = request.model or self._model
        ctx = LogContext(provider=self.provider_name, model=model)
        log_event(self._logger, "chat.start", ctx, temperature=request.temperature, max_tokens=request.max_tokens)
        if OpenAI is None:
            meta = ProviderMetadata(provider_name=self.provider_name, model_name=model, extra={"error": "openai SDK not installed"})
            log_event(self._logger, "chat.error", ctx, error="openai SDK not installed")
            return ChatResponse(text=None, parts=None, raw=None, meta=meta)
        system_message, user_content = extract_system_and_user(request.messages)
        if not self._api_key:
            meta = ProviderMetadata(provider_name=self.provider_name, model_name=model, extra={"error": MISSING_API_KEY_ERROR})
            log_event(self._logger, "chat.error", ctx, error=MISSING_API_KEY_ERROR)
            return ChatResponse(text=None, parts=None, raw=None, meta=meta)
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        if user_content:
            messages.append({"role": "user", "content": user_content})
        response_format, is_structured = self._prepare_response_format(request)
        client = OpenAI(api_key=self._api_key, base_url=self._base_url)  # type: ignore[arg-type]

        @retry()
        def _invoke() -> tuple[float, object]:
            t0 = time.perf_counter()
            try:
                params: Dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                }
                if response_format:
                    params["response_format"] = response_format
                if request.tools:
                    params["tools"] = request.tools
                resp = client.chat.completions.create(**params)
                latency_ms = (time.perf_counter() - t0) * 1000.0
                return latency_ms, resp
            except Exception as e:
                code = classify_exception(e)
                raise ProviderError(
                    code=code,
                    message=str(e),
                    provider=self.provider_name,
                    model=model,
                    retryable=code in (ErrorCode.RATE_LIMIT, ErrorCode.TIMEOUT, ErrorCode.TRANSIENT),
                    raw=e,
                )

        try:
            latency_ms, resp = _invoke()
        except ProviderError as e:  # pragma: no cover
            log_event(self._logger, "chat.error", ctx, error=str(e), code=e.code.value)
            meta = ProviderMetadata(provider_name=self.provider_name, model_name=model, latency_ms=None, extra={"error": str(e), "code": e.code.value})
            return ChatResponse(text=None, parts=None, raw=None, meta=meta)

        text = getattr(resp.choices[0].message, "content", "") if getattr(resp, "choices", None) else ""
        parts = [ContentPart(type="text", text=text)] if text else None
        meta = ProviderMetadata(
            provider_name=self.provider_name,
            model_name=model,
            latency_ms=latency_ms,
            token_param_used="max_tokens",
            extra={"is_structured": is_structured},
        )
        log_event(self._logger, "chat.success", ctx, latency_ms=latency_ms, structured=is_structured)
        return ChatResponse(text=text or None, parts=parts, raw=None, meta=meta)

    # ---- Streaming ----
    def supports_streaming(self) -> bool:
        return True

    def stream_chat(self, request: ChatRequest):
        model = request.model or self._model
        ctx = LogContext(provider=self.provider_name, model=model)
        log_event(self._logger, "stream.start", ctx, temperature=request.temperature, max_tokens=request.max_tokens)
        if OpenAI is None:
            log_event(self._logger, "stream.error", ctx, error="openai SDK not installed")
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error="openai SDK not installed")
            return

        client = OpenAI(api_key=self._api_key, base_url=self._base_url)  # type: ignore[arg-type]
        system_message, user_content = extract_system_and_user(request.messages)
        if not self._api_key:
            log_event(self._logger, "stream.error", ctx, error=MISSING_API_KEY_ERROR)
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=MISSING_API_KEY_ERROR)
            return
        if request.response_format == "json_object" or request.json_schema or request.tools:
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=STRUCTURED_STREAMING_UNSUPPORTED)
            return
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        if user_content:
            messages.append({"role": "user", "content": user_content})
        response_format, _ = self._prepare_response_format(request)

        try:
            @retry()
            def _start_stream():
                try:
                    params: Dict[str, Any] = {
                        "model": model,
                        "messages": messages,
                        "stream": True,
                        "max_tokens": request.max_tokens,
                        "temperature": request.temperature,
                    }
                    if response_format:
                        params["response_format"] = response_format
                    if request.tools:
                        params["tools"] = request.tools
                    return client.chat.completions.create(**params)
                except Exception as e:
                    code = classify_exception(e)
                    raise ProviderError(code=code, message=str(e), provider=self.provider_name, model=model, retryable=code in (ErrorCode.TRANSIENT, ErrorCode.RATE_LIMIT, ErrorCode.TIMEOUT), raw=e)

            stream = _start_stream()
            emitted_any = False
            try:
                for chunk in stream:
                    delta = None
                    try:
                        delta = chunk.choices[0].delta.content  # OpenAI-style
                    except Exception:
                        delta = None
                    if delta:
                        emitted_any = True
                        yield ChatStreamEvent(provider=self.provider_name, model=model, delta=delta, finish=False)
            except Exception as e:
                code = classify_exception(e)
                log_event(self._logger, "stream.error", ctx, error=str(e), code=code.value)
                yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=str(e))
                return

            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True)
            log_event(self._logger, "stream.end", ctx, emitted=emitted_any)
        except ProviderError as e:
            log_event(self._logger, "stream.error", ctx, error=str(e), code=e.code.value)
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=str(e))
        except Exception as e:  # pragma: no cover
            code = classify_exception(e)
            log_event(self._logger, "stream.error", ctx, error=str(e), code=code.value)
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=str(e))

    # ---- Helpers ----
    # _prepare_messages removed (replaced by shared extract_system_and_user usage)

    def _prepare_response_format(self, request: ChatRequest) -> Tuple[Optional[Dict[str, Any]], bool]:
        is_structured = request.response_format == "json_object"
        if request.json_schema:
            return {"type": "json_schema", "json_schema": request.json_schema}, is_structured
        if is_structured:
            return {"type": "json_object"}, True
        return None, False
