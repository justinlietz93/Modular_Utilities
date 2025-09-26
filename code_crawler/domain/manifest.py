"""Manifest schema and helpers."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict


MANIFEST_SCHEMA: Dict[str, object] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "CodeCrawlerRunManifest",
    "type": "object",
    "required": [
        "run_id",
        "timestamp",
        "tool_version",
        "configuration",
        "environment",
        "inputs",
        "artifacts",
    ],
    "properties": {
        "run_id": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "tool_version": {"type": "string"},
        "seed": {"type": ["integer", "null"]},
        "configuration": {"type": "object"},
        "environment": {
            "type": "object",
            "properties": {
                "python_version": {"type": "string"},
                "platform": {"type": "string"},
            },
        },
        "inputs": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "path", "size", "hash", "modified"],
                "properties": {
                    "id": {"type": "string"},
                    "path": {"type": "string"},
                    "size": {"type": "integer"},
                    "hash": {"type": "string"},
                    "modified": {"type": "string", "format": "date-time"},
                    "status": {"type": "string"},
                },
            },
        },
        "artifacts": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["path", "type"],
                "properties": {
                    "path": {"type": "string"},
                    "type": {"type": "string"},
                    "hash": {"type": "string"},
                },
            },
        },
    },
}


@dataclass(frozen=True)
class ManifestEntry:
    """Single entry for manifest inputs."""

    identifier: str
    path: str
    size: int
    digest: str
    modified: datetime
    status: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.identifier,
            "path": self.path,
            "size": self.size,
            "hash": self.digest,
            "modified": self.modified.isoformat(),
            "status": self.status,
        }


@dataclass(frozen=True)
class ArtifactRecord:
    """Records generated artifact metadata."""

    path: str
    artifact_type: str
    digest: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "path": self.path,
            "type": self.artifact_type,
            "hash": self.digest,
        }
