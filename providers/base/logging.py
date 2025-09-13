"""Base structured logging utilities for provider layer.

Rationale:
- Central place to configure consistent JSON (or plain) logging.
- Avoid sprinkling ad-hoc logger setup across adapters.
- Keep file small (<500 LOC rule) and dependency‑free.
"""
from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

ISO = "%Y-%m-%dT%H:%M:%S.%fZ"


class JsonFormatter(logging.Formatter):
    """Lightweight JSON formatter.

    Includes standard fields and merges extra record attributes (excluding private/logging internals).
    """

    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - trivial formatting
        base = {
            "ts": datetime.now(timezone.utc).strftime(ISO),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for k, v in record.__dict__.items():
            if k.startswith("_"):
                continue
            if k in ("msg", "args", "levelname", "levelno", "name", "pathname", "filename", "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName", "processName", "process"):
                continue
            # Avoid overwriting base keys
            if k not in base:
                base[k] = v
        return json.dumps(base, ensure_ascii=False)


@dataclass
class LogContext:
    provider: Optional[str] = None
    model: Optional[str] = None
    request_id: Optional[str] = None
    # Arbitrary additional metadata
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        extra = data.pop("extra", {}) or {}
        data.update({k: v for k, v in extra.items() if v is not None})
        return {k: v for k, v in data.items() if v is not None}


def get_logger(name: str = "providers", json_mode: bool = True, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if getattr(logger, "_configured_base_logger", False):  # idempotent
        return logger
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    if json_mode:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.handlers[:] = [handler]
    logger._configured_base_logger = True  # type: ignore[attr-defined]
    return logger


def log_event(logger: logging.Logger, event: str, ctx: LogContext | None = None, **fields: Any) -> None:
    payload = {"event": event}
    if ctx:
        payload.update(ctx.to_dict())
    payload.update({k: v for k, v in fields.items() if v is not None})
    logger.info(json.dumps(payload, ensure_ascii=False))


__all__ = [
    "LogContext",
    "get_logger",
    "log_event",
]
