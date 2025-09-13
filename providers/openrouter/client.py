"""OpenRouterProvider adapter.

Lightweight chat adapter using OpenRouter API (OpenAI-compatible style) via httpx.
"""
from __future__ import annotations

from typing import Optional, List, Dict, Any
import time
import httpx
import json

from ..base.interfaces import LLMProvider, SupportsJSONOutput, HasDefaultModel
from ..base.models import ChatRequest, ChatResponse, ProviderMetadata, ContentPart
from ..base.logging import get_logger, LogContext, log_event
from ..base.errors import ProviderError, ErrorCode, classify_exception
from ..base.resilience.retry import retry
from ..config import get_provider_config
from ..base.streaming import ChatStreamEvent
from ..base.constants import STRUCTURED_STREAMING_UNSUPPORTED, MISSING_API_KEY_ERROR
from ..base.utils.messages import extract_system_and_user


class OpenRouterProvider(LLMProvider, SupportsJSONOutput, HasDefaultModel):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None, registry: Any | None = None) -> None:
        cfg = get_provider_config("openrouter")
        self._api_key = api_key or cfg.get("api_key")
        self._model = model or cfg.get("model", "openrouter/auto")
        self._base_url = base_url or cfg.get("base_url", "https://openrouter.ai/api/v1")
        self._system_message = cfg.get("system_message")
        self._logger = get_logger("providers.openrouter")

    @property
    def provider_name(self) -> str:
        return "openrouter"

    def default_model(self) -> Optional[str]:
        return self._model

    def supports_json_output(self) -> bool:
        return True

    def chat(self, request: ChatRequest) -> ChatResponse:
        model = request.model or self._model
        ctx = LogContext(provider=self.provider_name, model=model)
        system_message, user_content = extract_system_and_user(request.messages)
        if not self._api_key:
            meta = ProviderMetadata(provider_name=self.provider_name, model_name=model, extra={"error": MISSING_API_KEY_ERROR})
            return ChatResponse(text=None, parts=None, raw=None, meta=meta)
        is_structured = request.response_format == "json_object"
        if request.json_schema:
            response_format = {"type": "json_schema", "json_schema": request.json_schema}
        elif is_structured:
            response_format = {"type": "json_object"}
        else:
            response_format = None
        messages: List[Dict[str, Any]] = []
        sys_msg = system_message or self._system_message
        if sys_msg:
            messages.append({"role": "system", "content": sys_msg})
        messages.append({"role": "user", "content": user_content})
        payload = {
            "model": model,
            "messages": messages,
            **({"max_tokens": request.max_tokens} if request.max_tokens is not None else {}),
            **({"temperature": request.temperature} if request.temperature is not None else {}),
        }
        if response_format:
            payload["response_format"] = response_format
        if request.tools:
            payload["tools"] = request.tools
        headers = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        log_event(self._logger, "chat.start", ctx, has_tools=bool(request.tools), has_schema=bool(request.json_schema), max_tokens=request.max_tokens, temperature=request.temperature)
        t0 = time.perf_counter()
        try:
            def _invoke():
                try:
                    with httpx.Client(timeout=60.0) as client:
                        return client.post(f"{self._base_url}/chat/completions", json=payload, headers=headers)
                except Exception as e:
                    code = classify_exception(e)
                    raise ProviderError(code=code, message=str(e), provider=self.provider_name, model=model, retryable=code in (ErrorCode.TRANSIENT, ErrorCode.RATE_LIMIT, ErrorCode.TIMEOUT), raw=e)
            resp = retry()(_invoke)()
            latency_ms = (time.perf_counter() - t0) * 1000.0
            resp.raise_for_status()
            data = resp.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content")
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
        if is_structured and text:
            try:
                parsed = json.loads(text)
                return ChatResponse(text=json.dumps(parsed), parts=[ContentPart(type="json", text=json.dumps(parsed))], raw=None, meta=meta)
            except Exception:
                pass
        parts = [ContentPart(type="text", text=text)] if text else None
        return ChatResponse(text=text or None, parts=parts, raw=None, meta=meta)

    # ---- Streaming ----
    def supports_streaming(self) -> bool:
        return True

    def stream_chat(self, request: ChatRequest):
        model = request.model or self._model
        ctx = LogContext(provider=self.provider_name, model=model)
        log_event(self._logger, "stream.start", ctx, temperature=request.temperature, max_tokens=request.max_tokens)

        # Prepare payload similar to chat(), but with stream flag
        system_message, user_content = extract_system_and_user(request.messages)
        if not self._api_key:
            log_event(self._logger, "stream.error", ctx, error=MISSING_API_KEY_ERROR)
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=MISSING_API_KEY_ERROR)
            return
        if request.response_format == "json_object" or request.json_schema or request.tools:
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=STRUCTURED_STREAMING_UNSUPPORTED)
            return
        is_structured = request.response_format == "json_object"
        if request.json_schema:
            response_format = {"type": "json_schema", "json_schema": request.json_schema}
        elif is_structured:
            response_format = {"type": "json_object"}
        else:
            response_format = None
        messages: List[Dict[str, Any]] = []
        sys_msg = system_message or self._system_message
        if sys_msg:
            messages.append({"role": "system", "content": sys_msg})
        messages.append({"role": "user", "content": user_content})
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
            **({"max_tokens": request.max_tokens} if request.max_tokens is not None else {}),
            **({"temperature": request.temperature} if request.temperature is not None else {}),
        }
        if response_format:
            payload["response_format"] = response_format
        if request.tools:
            payload["tools"] = request.tools
        headers = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        try:
            @retry()
            def _start_stream():
                try:
                    client = httpx.Client(timeout=None)
                    # The caller will iterate; we return the open response for chunking
                    return client.stream("POST", f"{self._base_url}/chat/completions", json=payload, headers=headers)
                except Exception as e:
                    code = classify_exception(e)
                    raise ProviderError(code=code, message=str(e), provider=self.provider_name, model=model, retryable=code in (ErrorCode.TRANSIENT, ErrorCode.RATE_LIMIT, ErrorCode.TIMEOUT), raw=e)

            with _start_stream() as resp:
                emitted_any = False
                try:
                    resp.raise_for_status()
                    for line in resp.iter_lines():
                        if not line:
                            continue
                        try:
                            # OpenAI-style SSE: lines may be like 'data: {json}'
                            if line.startswith(b"data:"):
                                line = line[5:].strip()
                            if line == b"[DONE]":
                                break
                            data = json.loads(line)
                            delta = data.get("choices", [{}])[0].get("delta", {}).get("content")
                            if delta:
                                emitted_any = True
                                yield ChatStreamEvent(provider=self.provider_name, model=model, delta=delta, finish=False)
                        except Exception:
                            # Be tolerant of non-JSON keepalive lines
                            continue
                except Exception as e:
                    code = classify_exception(e)
                    log_event(self._logger, "stream.error", ctx, error=str(e), code=code.value)
                    yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=str(e))
                    return
                finally:
                    # Terminal event
                    yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True)
                    log_event(self._logger, "stream.end", ctx, emitted=emitted_any)
        except ProviderError as e:
            log_event(self._logger, "stream.error", ctx, error=str(e), code=e.code.value)
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=str(e))
        except Exception as e:  # pragma: no cover
            code = classify_exception(e)
            log_event(self._logger, "stream.error", ctx, error=str(e), code=code.value)
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=str(e))
