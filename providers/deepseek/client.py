"""DeepseekProvider adapter (placeholder / basic chat implementation).

Assumes Deepseek exposes an OpenAI-compatible API endpoint with standard Chat Completions.
Customize base_url / headers as needed.
"""
from __future__ import annotations

from typing import Optional, Any
import time

try:
    from openai import OpenAI  # reuse OpenAI client for compatibility
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

from ..base.interfaces import LLMProvider, SupportsJSONOutput, HasDefaultModel
from ..base.models import ChatRequest, ChatResponse, ProviderMetadata, ContentPart
from ..base.logging import get_logger, LogContext, log_event
from ..base.errors import ProviderError, ErrorCode, classify_exception
from ..base.resilience.retry import retry
from ..base.streaming import ChatStreamEvent
from ..base.constants import STRUCTURED_STREAMING_UNSUPPORTED, MISSING_API_KEY_ERROR
from ..base.utils.messages import extract_system_and_user


class DeepseekProvider(LLMProvider, SupportsJSONOutput, HasDefaultModel):
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None, registry: Any | None = None):
        self._api_key = api_key
        self._base_url = base_url or "https://api.deepseek.com/v1"  # example; adjust if different
        self._model = model or "deepseek-chat"
        self._logger = get_logger("providers.deepseek")

    @property
    def provider_name(self) -> str:
        return "deepseek"

    def default_model(self) -> Optional[str]:
        return self._model

    def supports_json_output(self) -> bool:
        return True

    def chat(self, request: ChatRequest) -> ChatResponse:
        model = request.model or self._model
        ctx = LogContext(provider=self.provider_name, model=model)
        if OpenAI is None:
            meta = ProviderMetadata(provider_name=self.provider_name, model_name=model, extra={"error": "openai SDK not installed"})
            return ChatResponse(text=None, parts=None, raw=None, meta=meta)

        client = OpenAI(api_key=self._api_key, base_url=self._base_url)  # type: ignore[arg-type]
        system_message, user_content = extract_system_and_user(request.messages)
        if not self._api_key:
            meta = ProviderMetadata(provider_name=self.provider_name, model_name=model, extra={"error": MISSING_API_KEY_ERROR})
            return ChatResponse(text=None, parts=None, raw=None, meta=meta)
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": user_content})
        is_structured = request.response_format == "json_object"
        if request.json_schema:
            # Use OpenAI JSON schema style response_format if supported
            response_format = {"type": "json_schema", "json_schema": request.json_schema}
        elif is_structured:
            response_format = {"type": "json_object"}
        else:
            response_format = None
        log_event(self._logger, "chat.start", ctx, has_tools=bool(request.tools), has_schema=bool(request.json_schema), max_tokens=request.max_tokens, temperature=request.temperature)
        t0 = time.perf_counter()
        try:
            params = {
                "model": model,
                "messages": messages,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
            }
            if response_format:
                params["response_format"] = response_format
            if request.tools:
                params["tools"] = request.tools
            def _invoke():
                try:
                    return client.chat.completions.create(**params)
                except Exception as e:
                    code = classify_exception(e)
                    raise ProviderError(code=code, message=str(e), provider=self.provider_name, model=model, retryable=code in (ErrorCode.TRANSIENT, ErrorCode.RATE_LIMIT, ErrorCode.TIMEOUT), raw=e)
            resp = retry()(_invoke)()
            latency_ms = (time.perf_counter() - t0) * 1000.0
            text = resp.choices[0].message.content if resp.choices else ""
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
        meta = ProviderMetadata(provider_name=self.provider_name, model_name=model, latency_ms=latency_ms, token_param_used="max_tokens", extra={"is_structured": is_structured})
        parts = [ContentPart(type="text", text=text)] if text else None
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
        messages.append({"role": "user", "content": user_content})

        is_structured = request.response_format == "json_object"
        if request.json_schema:
            response_format = {"type": "json_schema", "json_schema": request.json_schema}
        elif is_structured:
            response_format = {"type": "json_object"}
        else:
            response_format = None

        try:
            @retry()
            def _start_stream():
                try:
                    params: dict = {
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
