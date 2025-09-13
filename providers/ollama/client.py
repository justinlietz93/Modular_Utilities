"""OllamaProvider adapter.

Uses local Ollama HTTP API (default localhost:11434) for chat-like generation.
"""
from __future__ import annotations

from typing import Optional, Dict, Any
import time
import httpx
import json

from ..base.interfaces import LLMProvider, SupportsJSONOutput, HasDefaultModel
from ..base.models import ChatRequest, ChatResponse, ProviderMetadata, ContentPart
from ..base.logging import get_logger, LogContext, log_event
from ..base.errors import ProviderError, ErrorCode, classify_exception
from ..base.resilience.retry import retry
from ..base.streaming import ChatStreamEvent
from ..base.constants import STRUCTURED_STREAMING_UNSUPPORTED
from ..base.utils.messages import extract_system_and_user


class OllamaProvider(LLMProvider, SupportsJSONOutput, HasDefaultModel):
    def __init__(self, host: Optional[str] = None, model: Optional[str] = None, registry: Any | None = None):
        self._host = host or "http://localhost:11434"
        self._model = model or "llama3"
        self._logger = get_logger("providers.ollama")

    @property
    def provider_name(self) -> str:
        return "ollama"

    def default_model(self) -> Optional[str]:
        return self._model

    def supports_json_output(self) -> bool:
        return True

    def chat(self, request: ChatRequest) -> ChatResponse:
        model = request.model or self._model
        ctx = LogContext(provider=self.provider_name, model=model)
        system_message, user_content = extract_system_and_user(request.messages)
        prompt_parts = []
        if system_message:
            prompt_parts.append(f"[SYSTEM]\n{system_message}")
        if user_content:
            prompt_parts.append(user_content)
        prompt = "\n".join(prompt_parts)
        is_structured = request.response_format == "json_object"
        payload: Dict[str, Any] = {"model": model, "prompt": prompt, "stream": False}
        if request.json_schema or is_structured:
            # Ollama `format: json` triggers JSON mode for models that support it
            payload["format"] = "json"
        log_event(self._logger, "chat.start", ctx, has_tools=bool(request.tools), has_schema=bool(request.json_schema), max_tokens=request.max_tokens, temperature=request.temperature)
        t0 = time.perf_counter()
        try:
            def _invoke():
                try:
                    with httpx.Client(timeout=120.0) as client:
                        return client.post(f"{self._host}/api/generate", json=payload)
                except Exception as e:
                    code = classify_exception(e)
                    raise ProviderError(code=code, message=str(e), provider=self.provider_name, model=model, retryable=code in (ErrorCode.TRANSIENT, ErrorCode.RATE_LIMIT, ErrorCode.TIMEOUT), raw=e)
            resp = retry()(_invoke)()
            latency_ms = (time.perf_counter() - t0) * 1000.0
            resp.raise_for_status()
            data = resp.json()
            text = data.get("response")
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
        meta = ProviderMetadata(provider_name=self.provider_name, model_name=model, latency_ms=latency_ms, token_param_used=None, extra={"is_structured": is_structured})
        parts = [ContentPart(type="text", text=text)] if text else None
        return ChatResponse(text=text or None, parts=parts, raw=None, meta=meta)

    # ---- Streaming ----
    def supports_streaming(self) -> bool:
        return True

    def stream_chat(self, request: ChatRequest):
        model = request.model or self._model
        ctx = LogContext(provider=self.provider_name, model=model)
        log_event(self._logger, "stream.start", ctx, temperature=request.temperature, max_tokens=request.max_tokens)

        # Prepare prompt similar to chat(), but stream=True
        system_message, user_content = extract_system_and_user(request.messages)
        if request.response_format == "json_object" or request.json_schema or request.tools:
            # Standardized rejection until structured streaming accumulation supported
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=STRUCTURED_STREAMING_UNSUPPORTED)
            return
        prompt_parts = []
        if system_message:
            prompt_parts.append(f"[SYSTEM]\n{system_message}")
        if user_content:
            prompt_parts.append(user_content)
        prompt = "\n".join(prompt_parts)
        payload: Dict[str, Any] = {"model": model, "prompt": prompt, "stream": True}
        if request.json_schema or (request.response_format == "json_object"):
            payload["format"] = "json"

        try:
            @retry()
            def _start_stream():
                try:
                    client = httpx.Client(timeout=None)
                    return client.stream("POST", f"{self._host}/api/generate", json=payload)
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
                            data = json.loads(line)
                        except Exception:
                            continue
                        # Ollama stream chunks contain 'response' and a 'done' flag eventually
                        chunk = data.get("response")
                        if chunk:
                            emitted_any = True
                            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=chunk, finish=False)
                        if data.get("done") is True:
                            break
                except Exception as e:
                    code = classify_exception(e)
                    log_event(self._logger, "stream.error", ctx, error=str(e), code=code.value)
                    yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=str(e))
                    return
                finally:
                    yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True)
                    log_event(self._logger, "stream.end", ctx, emitted=emitted_any)
        except ProviderError as e:
            log_event(self._logger, "stream.error", ctx, error=str(e), code=e.code.value)
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=str(e))
        except Exception as e:  # pragma: no cover
            code = classify_exception(e)
            log_event(self._logger, "stream.error", ctx, error=str(e), code=code.value)
            yield ChatStreamEvent(provider=self.provider_name, model=model, delta=None, finish=True, error=str(e))
