"""Unified configuration layer for providers.

Goals
-----
* Centralize defaults (models, base URLs, system messages).
* Merge sources in a predictable order:
    1. Built-in defaults
    2. Environment variables (e.g. OPENAI_MODEL, OPENAI_API_KEY)
    3. Optional external config file (JSON or YAML) pointed to by PROVIDERS_CONFIG_FILE
    4. In-code overrides passed to helper
* Provide a single call site: ``get_provider_config(provider: str)``.
* Keep zero hard dependency on PyYAML (load YAML only if available).

Environment Variable Conventions
--------------------------------
<PROVIDER>_MODEL, <PROVIDER>_API_KEY, <PROVIDER>_BASE_URL, <PROVIDER>_SYSTEM_MESSAGE
e.g. OPENAI_MODEL, OPENROUTER_BASE_URL.

External Config File (Optional)
-------------------------------
If PROVIDERS_CONFIG_FILE is set to a path, we attempt to load JSON first.
If that fails and PyYAML is installed, attempt YAML. Structure example:

```
openai:
  model: gpt-4o-mini
  api_key: ${OPENAI_API_KEY}
openrouter:
  model: openrouter/auto
  base_url: https://openrouter.ai/api/v1
  system_message: "You are helpful."
```

Public API
----------
* get_provider_config(provider: str, overrides: dict | None = None) -> dict
* get_model(provider: str) -> str | None
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import json
import os

try:  # Optional YAML support
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore

from ..base.repositories.keys import KeysRepository


# -------------------- Defaults --------------------

DEFAULTS: Dict[str, Dict[str, Any]] = {
    "openai": {"model": "gpt-4o-mini"},
    "anthropic": {"model": "claude-3-5-sonnet-20240620"},
    "gemini": {"model": "gemini-1.5-flash"},
    "deepseek": {"model": "deepseek-chat"},
    "openrouter": {
        "model": "openrouter/auto",
        "base_url": "https://openrouter.ai/api/v1",
        "system_message": "You are a helpful assistant.",
    },
    "ollama": {"model": "llama3", "host": "http://localhost:11434"},
    "xai": {"model": "grok-beta", "base_url": "https://api.x.ai/v1"},
}


ENV_FIELD_MAP = {
    "model": "MODEL",
    "api_key": "API_KEY",
    "base_url": "BASE_URL",
    "system_message": "SYSTEM_MESSAGE",
    "host": "HOST",
}


_FILE_CACHE: Optional[Dict[str, Any]] = None
_DOTENV_LOADED = False


def _load_dotenv_once() -> None:
    """Lightweight .env loader (no external dependency).

    Parses KEY=VALUE lines, ignoring comments and blank lines. Does not override
    existing environment variables. Safe to call multiple times.
    """
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    path = os.getenv("DOTENV_FILE", ".env")
    if not os.path.isfile(path):  # no file present
        _DOTENV_LOADED = True
        return
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    finally:
        _DOTENV_LOADED = True


def _load_external_config() -> Dict[str, Any]:
    global _FILE_CACHE
    if _FILE_CACHE is not None:
        return _FILE_CACHE
    path = os.getenv("PROVIDERS_CONFIG_FILE")
    if not path:
        _FILE_CACHE = {}
        return _FILE_CACHE
    p = Path(path)
    if not p.exists():
        _FILE_CACHE = {}
        return _FILE_CACHE
    text = p.read_text(encoding="utf-8")
    data: Dict[str, Any] = {}
    # Try JSON first
    try:
        data = json.loads(text)
    except Exception:
        if yaml is not None:  # pragma: no cover (depends on optional lib)
            try:
                data = yaml.safe_load(text) or {}
            except Exception:
                data = {}
        else:
            data = {}
    if not isinstance(data, dict):
        data = {}
    _FILE_CACHE = data
    return data


def _env_overrides(provider: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    prefix = provider.upper()
    for field, suffix in ENV_FIELD_MAP.items():
        val = os.getenv(f"{prefix}_{suffix}")
        if val is not None:
            out[field] = val
    return out


def get_provider_config(provider: str, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return merged configuration for a provider.

    Merge order (later wins): defaults -> external config -> env vars -> key repo -> overrides
    """
    # Ensure .env is loaded before reading env vars
    _load_dotenv_once()
    name = (provider or "").lower().strip()
    cfg: Dict[str, Any] = {}

    # 1. Defaults
    cfg.update(DEFAULTS.get(name, {}))

    # 2. External config file section
    file_cfg = _load_external_config().get(name)
    if isinstance(file_cfg, dict):
        cfg.update(file_cfg)

    # 3. Env overrides
    cfg.update(_env_overrides(name))

    # 4. API key via KeysRepository (only if not already set)
    if "api_key" not in cfg or not cfg.get("api_key"):
        key = KeysRepository().get_api_key(name)
        if key:
            cfg["api_key"] = key

    # 5. Explicit overrides arg
    if overrides:
        cfg.update({k: v for k, v in overrides.items() if v is not None})

    return cfg


def get_model(provider: str) -> Optional[str]:
    return get_provider_config(provider).get("model")


__all__ = [
    "get_provider_config",
    "get_model",
    "DEFAULTS",
]
