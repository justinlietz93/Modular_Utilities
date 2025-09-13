from __future__ import annotations

"""Minimal dependency injection container for providers.

Goals:
- Centralize construction of shared repositories/services.
- Decouple upstream code from direct factory calls (optionally remove ProviderFactory later).
- Keep zero external dependencies per architecture rules.

This can evolve to include caching, tracing, metrics, etc., without touching
adapter call sites.
"""

from typing import Any, Dict

from ..base.factory import ProviderFactory
from ..base.repositories.model_registry import ModelRegistryRepository


class ProvidersContainer:
    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self._config = config or {}
        self._singletons: Dict[str, Any] = {}
        self._providers: Dict[str, Any] = {}

    # ---- Shared singletons ----
    def model_registry(self) -> ModelRegistryRepository:
        if "model_registry" not in self._singletons:
            self._singletons["model_registry"] = ModelRegistryRepository()
        return self._singletons["model_registry"]

    # ---- Providers ----
    def provider(self, name: str):  # returns LLMProvider (duck-typed)
        key = name.lower()
        if key not in self._providers:
            self._providers[key] = ProviderFactory.create(key, registry=self.model_registry())
        return self._providers[key]

    def clear(self):  # testing convenience
        self._providers.clear()
        self._singletons.clear()


def build_container(config: Dict[str, Any] | None = None) -> ProvidersContainer:
    return ProvidersContainer(config=config)

__all__ = ["ProvidersContainer", "build_container"]
