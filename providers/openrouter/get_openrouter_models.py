"""
OpenRouter: get models

Behavior
- Attempts to fetch model listings via OpenRouter HTTP API (OpenAI-compatible style):
  GET https://openrouter.ai/api/v1/models
- Persists to JSON at: src/providers/openrouter/openrouter-models.json
- If API key (optional for public listing) or HTTP client unavailable/fails, falls back to cached JSON.

Entry points recognized by the ModelRegistryRepository:
- run()  (preferred)
- get_models()/fetch_models()/update_models()/refresh_models() also provided for convenience
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import os

try:
	import requests  # type: ignore
except Exception:
	requests = None  # type: ignore

from ..base.get_models_base import save_provider_models, load_cached_models
from ..base.repositories.keys import KeysRepository

PROVIDER = "openrouter"


def _resolve_key() -> Optional[str]:
	return KeysRepository().get_api_key(PROVIDER)


def _resolve_base_url() -> str:
	return os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")


def _fetch_via_http(api_key: Optional[str], base_url: str) -> List[Dict[str, Any]]:
	if requests is None:
		raise RuntimeError("requests library not available")
	url = base_url.rstrip("/") + "/models"
	headers = {"Accept": "application/json"}
	if api_key:
		headers["Authorization"] = f"Bearer {api_key}"
	resp = requests.get(url, headers=headers, timeout=20)
	resp.raise_for_status()
	data = resp.json()
	raw = data.get("data", data) if isinstance(data, dict) else data
	items: List[Dict[str, Any]] = []
	for it in raw or []:
		if isinstance(it, dict):
			mid = it.get("id") or it.get("model") or it.get("name") or str(it)
			name = it.get("name") or it.get("id") or str(it)
			row = {"id": str(mid), "name": str(name)}
			for k in ("created", "context_length", "capabilities", "description", "pricing"):
				if k in it:
					row[k] = it[k]
			items.append(row)
		else:
			items.append({"id": str(it), "name": str(it)})
	return items


def run() -> List[Dict[str, Any]]:
	key = _resolve_key()
	base = _resolve_base_url()
	if True:  # attempt fetch regardless of key; listing may be public
		try:
			items = _fetch_via_http(key, base)
			if items:
				save_provider_models(PROVIDER, items, fetched_via="api", metadata={"source": "openrouter_http"})
				return items
		except Exception:
			pass
	snap = load_cached_models(PROVIDER)
	return [m.to_dict() for m in snap.models]


def get_models() -> List[Dict[str, Any]]:  # alias
	return run()


def fetch_models() -> List[Dict[str, Any]]:
	return run()


def update_models() -> List[Dict[str, Any]]:
	return run()


def refresh_models() -> List[Dict[str, Any]]:
	return run()


if __name__ == "__main__":
	models = run()
	print(f"[openrouter] loaded {len(models)} models")
