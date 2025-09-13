"""providers package

Unified abstraction surface for multiple AI model providers.

This module now exposes a stable, minimal API suitable for external import
after packaging via the repository root ``pyproject.toml``.

Public API (re-exported):
    - Exceptions: ProviderError, ApiCallError, ApiResponseError, JsonParsingError, JsonProcessingError
    - call_with_retry: Legacy helper for higher-level prompt template calls.
    - create(): Convenience factory wrapper (lightweight; may evolve).

Future: plugin entry points (``providers.plugins``) can be loaded via
``load_plugin(name)`` to register third-party providers.
"""

import logging
import json
import re
from typing import Dict, Any, Tuple, Union

# Re-export error types (new taxonomy)
from .base.errors import (
    ProviderError,
    ErrorCode,
)

# Base abstractions (optional exports). Guard imports in case of refactors.
try:  # pragma: no cover - defensive
    from .base.factory import ProviderFactory  # type: ignore
    from .base.get_models_base import load_cached_models, save_provider_models  # type: ignore
    from .base.interfaces import (  # type: ignore
        LLMProvider,
        SupportsJSONOutput,
        SupportsResponsesAPI,
        ModelListingProvider,
        HasDefaultModel,
    )
except Exception:  # pragma: no cover
    ProviderFactory = None  # type: ignore
    load_cached_models = None  # type: ignore
    save_provider_models = None  # type: ignore
    LLMProvider = SupportsJSONOutput = SupportsResponsesAPI = ModelListingProvider = HasDefaultModel = None  # type: ignore

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Exceptions
    "ProviderError",
    "ErrorCode",
    # Core helpers
    "call_with_retry",
    "create",
    # Base (optional) abstractions
    "ProviderFactory",
    "LLMProvider",
    "SupportsJSONOutput",
    "SupportsResponsesAPI",
    "ModelListingProvider",
    "HasDefaultModel",
    # Registry helpers
    "load_cached_models",
    "save_provider_models",
]

logger = logging.getLogger(__name__)


def _safe_format(template: str, context: Dict[str, Any]) -> str:
    """Best-effort placeholder replacement without raising on missing keys."""
    try:
        formatted = template
        for k, v in context.items():
            formatted = formatted.replace(f"{{{k}}}", str(v))
        return formatted
    except Exception as e:
        logger.debug(f"Safe format failed: {e}")
        return template


def _clean_json_markers(s: str) -> str:
    """Strip common code fences from LLM JSON replies."""
    s = s.strip()
    if s.startswith("```json"):
        s = s[7:]
    elif s.startswith("```"):
        s = s[3:]
    if s.endswith("```"):
        s = s[:-3]
    return s.strip()


def _attempt_json_repair(s: str) -> str:
    """
    Attempt to repair common JSON formatting issues:
    - Trim to the first JSON object/array envelope
    - Remove code fences and trailing commas
    - Balance braces/brackets and quotes
    """
    # Trim to JSON envelope
    first_obj = s.find("{")
    first_arr = s.find("[")
    idx_candidates = [i for i in [first_obj, first_arr] if i != -1]
    if idx_candidates:
        start = min(idx_candidates)
        s = s[start:]

    # Clean code fences if any slipped through
    s = _clean_json_markers(s)

    # Remove trailing commas before a closing brace/bracket
    s = re.sub(r",\s*(\}|\])", r"\1", s)

    # Balance braces/brackets
    open_braces = s.count("{")
    close_braces = s.count("}")
    if open_braces > close_braces:
        s += "}" * (open_braces - close_braces)

    open_brackets = s.count("[")
    close_brackets = s.count("]")
    if open_brackets > close_brackets:
        s += "]" * (open_brackets - close_brackets)

    # Balance quotes in a naive but effective way
    s_wo_escaped = re.sub(r'\\"', "", s)
    if s_wo_escaped.count('"') % 2 == 1:
        s += '"'

    return s


def call_with_retry(
    prompt_template: str,
    context: Dict[str, Any],
    config: Dict[str, Any],
    is_structured: bool = True,
) -> Tuple[Union[str, Dict[str, Any]], str]:
    """
    Provider-agnostic call with retry that delegates to the configured provider.
    Returns a tuple of (response, model_used_label).
    """
    api_cfg = (config or {}).get("api", {}) or {}
    primary = api_cfg.get("primary_provider") or api_cfg.get("provider") or "gemini"
    provider = str(primary).lower()

    if provider == "gemini":
        # Legacy path not yet re-implemented; instruct user to migrate.
        raise ProviderError(code=ErrorCode.UNSUPPORTED, message="Legacy gemini path removed; use create('gemini').chat(ChatRequest(...))", provider="gemini")

    if provider == "openai":
        # Reuse inlined helper from adapter
        try:
            from .openai.client import call_openai_with_retry  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ProviderError(code=ErrorCode.UNKNOWN, message=f"OpenAI helper unavailable: {e}", provider="openai") from e
        resp, model = call_openai_with_retry(
            prompt_template=prompt_template,
            context=context,
            config=config,
            is_structured=is_structured,
        )
        return resp, model

    if provider in {"openrouter", "ollama"}:
        raise ProviderError(code=ErrorCode.UNSUPPORTED, message=f"Legacy call_with_retry path for '{provider}' removed. Use create('{provider}').chat(ChatRequest(...)) instead.", provider=provider)

    raise ProviderError(code=ErrorCode.UNSUPPORTED, message=f"Unknown or unsupported provider: {provider}", provider=provider)


def create(provider_name: str, **kwargs):
    """Instantiate a provider adapter via ``ProviderFactory`` if available.

    Falls back to raising ProviderError if the factory layer is not present.
    This keeps existing lightweight usage patterns while enabling external callers
    to do ``from providers import create`` after installation.
    """
    if ProviderFactory is None:  # type: ignore
        raise ProviderError(code=ErrorCode.UNKNOWN, message="ProviderFactory not available in this build", provider="unknown")
    try:
        return ProviderFactory.create(provider_name, **kwargs)  # type: ignore[attr-defined]
    except Exception as e:  # Wrap in unified error type
        raise ProviderError(code=ErrorCode.UNKNOWN, message=f"Failed to create provider '{provider_name}': {e}", provider=provider_name) from e


def load_plugin(entry_point_name: str):  # pragma: no cover - future extension
    """Load a plugin registered under the ``providers.plugins`` entry point group.

    Example (pyproject.toml):
        [project.entry-points."providers.plugins"]
        my_custom = "my_pkg.custom_provider:CustomProvider"
    """
    try:
        from importlib import metadata
    except ImportError:  # pragma: no cover
        import importlib_metadata as metadata  # type: ignore

    eps = metadata.entry_points()
    group = eps.select(group="providers.plugins") if hasattr(eps, "select") else eps.get("providers.plugins", [])
    for ep in group:
        if ep.name == entry_point_name:
            return ep.load()
    raise LookupError(f"No provider plugin named '{entry_point_name}'")