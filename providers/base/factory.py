"""
Provider Factory

Purpose
- Centralized, provider-agnostic creation of LLMProvider adapters.
- Lazy-imports provider adapters to avoid heavy dependencies at import time.
- No side effects: strictly returns instances or raises a clear error.

Contracts
- Returns instances implementing [LLMProvider](Cogito/src/providers/base/interfaces.py:1).

Scope
- Providers supported in this scaffolding: openai (others to be added later).
"""

from __future__ import annotations

from typing import Any, Dict, Type


class UnknownProviderError(Exception):
    pass


def create_provider(provider: str, **kwargs: Any):
    """Compatibility helper: delegate to ProviderFactory.create()."""
    return ProviderFactory.create(provider, **kwargs)


class ProviderFactory:
    """
    Create provider adapters based on a canonical name (e.g., 'openai').
    """

    # Map canonical provider names to import paths and class names
    _PROVIDERS: Dict[str, Dict[str, str]] = {
        "openai": {"module": "providers.openai.client", "class": "OpenAIProvider"},
        "anthropic": {"module": "providers.anthropic.client", "class": "AnthropicProvider"},
        "gemini": {"module": "providers.gemini.client", "class": "GeminiProvider"},
        "deepseek": {"module": "providers.deepseek.client", "class": "DeepseekProvider"},
        "openrouter": {"module": "providers.openrouter.client", "class": "OpenRouterProvider"},
        "ollama": {"module": "providers.ollama.client", "class": "OllamaProvider"},
        "xai": {"module": "providers.xai.client", "class": "XAIProvider"},
    }

    @classmethod
    def create(cls, provider: str, **kwargs: Any):
        """
        Create a provider adapter instance.

        Args:
            provider: Canonical provider name (e.g., 'openai')
            **kwargs: Adapter-specific constructor kwargs (optional)

        Returns:
            Instance implementing LLMProvider

        Raises:
            UnknownProviderError: if provider is not registered or cannot be imported.
        """
        name = (provider or "").lower().strip()
        spec = cls._PROVIDERS.get(name)
        if not spec:
            raise UnknownProviderError(f"Unknown provider '{provider}'")

        module_path, class_name = spec["module"], spec["class"]

        try:
            mod = __import__(module_path, fromlist=[class_name])
            klass: Type = getattr(mod, class_name)
            return klass(**kwargs)  # type: ignore[call-arg]
        except Exception as e:
            raise UnknownProviderError(f"Failed to initialize provider '{provider}': {e}") from e