from __future__ import annotations

"""Batch refresh utility for provider model registries (canonical location).

CLI Examples:
  python -m providers.utils.refresh_all_models
  python -m providers.utils.refresh_all_models --only openai,anthropic --parallel 3
  python -m providers.utils.refresh_all_models --json --fail-on-error
"""

from dataclasses import dataclass, asdict
from importlib import import_module
from time import perf_counter
from typing import Any, Callable, Dict, List, Optional
import argparse
import concurrent.futures as cf
import json
import sys

DEFAULT_PROVIDERS = [
    "openai",
    "anthropic",
    "gemini",
    "deepseek",
    "openrouter",
    "ollama",
    "xai",
]

FETCHER_NAME_TEMPLATE = "providers.{provider}.get_{provider}_models"
ENTRYPOINT_CANDIDATES = ["run", "get_models", "fetch_models", "update_models", "refresh_models", "main"]


@dataclass
class ProviderRefreshResult:
    provider: str
    ok: bool
    count: Optional[int]
    duration_ms: float
    error: Optional[str] = None
    fetched_via: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _select_entrypoint(mod) -> Callable[[], Any]:
    for name in ENTRYPOINT_CANDIDATES:
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn
    raise AttributeError("No valid entrypoint found in module")


def refresh_provider(provider: str) -> ProviderRefreshResult:
    t0 = perf_counter()
    try:
        module_name = FETCHER_NAME_TEMPLATE.format(provider=provider)
        mod = import_module(module_name)
        fn = _select_entrypoint(mod)
        data = fn()
        count = None
        if isinstance(data, list):
            count = len(data)
        elif isinstance(data, dict):
            count = 1
        return ProviderRefreshResult(provider=provider, ok=True, count=count, duration_ms=(perf_counter() - t0) * 1000.0)
    except Exception as e:  # noqa: BLE001
        return ProviderRefreshResult(provider=provider, ok=False, count=None, duration_ms=(perf_counter() - t0) * 1000.0, error=str(e)[:300])


def refresh_all(providers: List[str], parallel: int = 1) -> List[ProviderRefreshResult]:
    if parallel <= 1:
        return [refresh_provider(p) for p in providers]
    results: List[ProviderRefreshResult] = []
    with cf.ThreadPoolExecutor(max_workers=parallel) as executor:
        future_map = {executor.submit(refresh_provider, p): p for p in providers}
        for fut in cf.as_completed(future_map):
            results.append(fut.result())
    ordered: Dict[str, ProviderRefreshResult] = {r.provider: r for r in results}
    return [ordered[p] for p in providers]


def _parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch refresh provider model registries")
    parser.add_argument("--only", help="Comma-separated subset of providers", default=None)
    parser.add_argument("--parallel", type=int, default=1, help="Parallel threads (default 1)")
    parser.add_argument("--json", action="store_true", help="Output JSON report only")
    parser.add_argument("--fail-on-error", action="store_true", help="Exit 1 if any provider fails")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv or [])
    providers = DEFAULT_PROVIDERS
    if args.only:
        providers = [p.strip() for p in args.only.split(",") if p.strip()]
    results = refresh_all(providers, parallel=max(1, args.parallel))
    report = {
        "summary": {
            "total": len(results),
            "ok": sum(1 for r in results if r.ok),
            "failed": sum(1 for r in results if not r.ok),
        },
        "results": [r.to_dict() for r in results],
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("Provider Model Refresh Results:\n")
        for r in results:
            status = "OK" if r.ok else "FAIL"
            print(f"- {r.provider:10} {status:4} count={r.count!s:>4} time={r.duration_ms:7.1f}ms" + (f" err={r.error}" if r.error else ""))
        print("\nSummary: {ok}/{total} succeeded, {failed} failed".format(**report["summary"]))
    if args.fail_on_error and any(not r.ok for r in results):
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))