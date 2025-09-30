"""Delta report writer."""
from __future__ import annotations

import json
from pathlib import Path

from .scanner import DeltaReport


def write_delta_report(path: Path, delta: DeltaReport) -> Path:
    path.write_text(json.dumps(delta.to_dict(), indent=2), encoding="utf-8")
    return path
