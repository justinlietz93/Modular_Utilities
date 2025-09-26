"""Domain models for non-code asset processing."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Dict, Mapping, Tuple


class AssetType(str, Enum):
    """Supported non-code asset categories."""

    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


@dataclass(frozen=True)
class AssetExtraction:
    """Canonical representation of extracted asset context."""

    identifier: str
    path: Path
    asset_type: AssetType
    summary: str
    content: str
    provenance: Tuple[str, ...]
    metadata: Mapping[str, object] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            "identifier": self.identifier,
            "path": self.path.as_posix(),
            "asset_type": self.asset_type.value,
            "summary": self.summary,
            "content": self.content,
            "provenance": list(self.provenance),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class AssetCard:
    """A reviewer-friendly note describing an extracted asset."""

    identifier: str
    asset_identifier: str
    title: str
    asset_type: AssetType
    summary: str
    notes: Mapping[str, str]
    provenance: Tuple[str, ...]
    checksum: str

    def to_markdown(self) -> str:
        lines = [
            f"# {self.title}",
            "",
            f"- Asset: `{self.asset_identifier}`",
            f"- Type: {self.asset_type.value}",
            f"- Summary checksum: `{self.checksum}`",
            "",
            "## Summary",
            "",
            self.summary.strip(),
        ]
        for heading, content in self.notes.items():
            lines.extend(["", f"## {heading}", "", content.strip()])
        lines.append("")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, object]:
        return {
            "identifier": self.identifier,
            "asset_identifier": self.asset_identifier,
            "title": self.title,
            "asset_type": self.asset_type.value,
            "summary": self.summary,
            "notes": dict(self.notes),
            "provenance": list(self.provenance),
            "checksum": self.checksum,
        }


def asset_identifier(path: Path) -> str:
    """Create a deterministic identifier for an asset path."""

    digest = sha256(path.as_posix().encode("utf-8")).hexdigest()
    return f"asset:{digest[:16]}"


def asset_card_identifier(asset_id: str) -> str:
    """Create a deterministic identifier for an asset card."""

    digest = sha256(asset_id.encode("utf-8")).hexdigest()
    return f"asset-card:{digest[:16]}"
