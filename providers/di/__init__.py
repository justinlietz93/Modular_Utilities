"""DI container scaffold for providers layer.

This is intentionally minimal—no external library dependency. Acts as a
composition root entry point for future orchestration layers.
"""
from __future__ import annotations

from .container import ProvidersContainer, build_container

__all__ = ["ProvidersContainer", "build_container"]
