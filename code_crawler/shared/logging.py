"""Shared logging utilities with privacy redaction."""
from __future__ import annotations

import logging
import re
from typing import Iterable, Pattern

from ..domain.configuration import PrivacySettings


class RedactingFormatter(logging.Formatter):
    """Formatter that redacts sensitive patterns."""

    def __init__(self, fmt: str, privacy: PrivacySettings) -> None:
        super().__init__(fmt)
        self._compiled_patterns: Iterable[Pattern[str]] = [
            re.compile(pattern) for pattern in privacy.redaction_patterns
        ]

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401 - doc inherited
        message = super().format(record)
        redacted = message
        for pattern in self._compiled_patterns:
            redacted = pattern.sub("[REDACTED]", redacted)
        return redacted


def configure_logger(privacy: PrivacySettings, level: int = logging.INFO) -> logging.Logger:
    """Configure a root logger with redaction."""

    logger = logging.getLogger("code_crawler")
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    handler.setFormatter(RedactingFormatter("%(asctime)s - %(levelname)s - %(message)s", privacy))
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger
