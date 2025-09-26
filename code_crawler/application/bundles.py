"""Deterministic bundle building."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from .scanner import FileRecord


@dataclass(frozen=True)
class BundleFile:
    identifier: str
    path: Path
    digest: str
    size: int
    lines: int
    language: str
    synopsis: str

    def header(self) -> str:
        return (
            f"---\n"
            f"path: {self.identifier}\n"
            f"digest: {self.digest}\n"
            f"size_bytes: {self.size}\n"
            f"line_count: {self.lines}\n"
            f"language: {self.language}\n"
            f"synopsis: {self.synopsis}\n"
            f"---\n"
        )


@dataclass(frozen=True)
class Bundle:
    name: str
    files: Sequence[BundleFile]
    content: str


class BundleBuilder:
    """Build bundles with deterministic ordering."""

    PRESETS: Dict[str, Iterable[str]] = {
        "all": ["**"],
        "tests": ["tests/**"],
        "dependencies": ["**/requirements*.txt", "**/pyproject.toml"],
        "api": ["presentation/**"],
    }

    def __init__(self, max_bytes: int = 200_000, max_lines: int = 1500) -> None:
        self.max_bytes = max_bytes
        self.max_lines = max_lines

    def build(self, preset: str, records: Sequence[FileRecord]) -> List[Bundle]:
        patterns = list(self.PRESETS.get(preset, []))
        if not patterns:
            raise ValueError(f"Unknown preset: {preset}")
        selected = [record for record in records if self._matches(record.identifier, patterns)]
        selected.sort(key=lambda record: record.identifier)
        bundles: List[Bundle] = []
        current: List[BundleFile] = []
        content_parts: List[str] = []
        current_bytes = 0
        current_lines = 0
        bundle_index = 1

        for record in selected:
            text = record.path.read_text(encoding="utf-8", errors="ignore")
            lines = text.count("\n") + 1 if text else 0
            synopsis = self._synopsis(text)
            bundle_file = BundleFile(
                identifier=record.identifier,
                path=record.path,
                digest=record.digest,
                size=record.size,
                lines=lines,
                language=record.path.suffix.lstrip(".") or "plain",
                synopsis=synopsis,
            )
            header = bundle_file.header()
            entry = f"{header}{text}\n"
            if current and (current_bytes + len(entry) > self.max_bytes or current_lines + lines > self.max_lines):
                bundles.append(Bundle(name=f"{preset}_{bundle_index}", files=tuple(current), content="".join(content_parts)))
                bundle_index += 1
                current = []
                content_parts = []
                current_bytes = 0
                current_lines = 0
            current.append(bundle_file)
            content_parts.append(entry)
            current_bytes += len(entry.encode("utf-8"))
            current_lines += lines

        if current:
            bundles.append(Bundle(name=f"{preset}_{bundle_index}", files=tuple(current), content="".join(content_parts)))

        return bundles

    @staticmethod
    def _matches(identifier: str, patterns: Iterable[str]) -> bool:
        from fnmatch import fnmatch

        return any(fnmatch(identifier, pattern) for pattern in patterns)

    @staticmethod
    def _synopsis(text: str) -> str:
        for line in text.splitlines():
            stripped = line.strip()
            if stripped:
                return stripped[:120]
        return ""
