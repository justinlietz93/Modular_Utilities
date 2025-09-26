"""Filesystem-backed manifest writer."""
from __future__ import annotations

import json
import platform
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Iterable

from ...domain.configuration import CrawlerConfig
from ...domain.manifest import ArtifactRecord, ManifestEntry, MANIFEST_SCHEMA


class ManifestWriter:
    """Writes manifest files and supporting metadata."""

    def __init__(self, manifest_path: Path) -> None:
        self.manifest_path = manifest_path

    def write(
        self,
        run_id: str,
        tool_version: str,
        config: CrawlerConfig,
        inputs: Iterable[ManifestEntry],
        artifacts: Iterable[ArtifactRecord],
        seed: int | None,
    ) -> Path:
        """Serialise the manifest to JSON."""

        payload = {
            "$schema": MANIFEST_SCHEMA["$schema"],
            "schema": MANIFEST_SCHEMA,
            "run_id": run_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "tool_version": tool_version,
            "seed": seed,
            "configuration": config.to_dict(),
            "environment": {
                "python_version": platform.python_version(),
                "platform": platform.platform(),
            },
            "inputs": [entry.to_dict() for entry in inputs],
            "artifacts": [artifact.to_dict() for artifact in artifacts],
        }

        self.manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return self.manifest_path

    @staticmethod
    def digest_file(path: Path) -> str:
        """Compute the sha256 digest for a file."""

        h = sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
