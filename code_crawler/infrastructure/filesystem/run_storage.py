"""Run space management."""
from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, List

from ...domain.configuration import CrawlerConfig


class RunStorage:
    """Manage timestamped run directories and retention."""

    SUBDIRECTORIES = {
        "manifests": "manifests",
        "metrics": "metrics",
        "bundles": "bundles",
        "logs": "logs",
        "badges": "badges",
        "delta": "delta",
        "gates": "gates",
        "summary": "summary",
    }

    def __init__(self, config: CrawlerConfig) -> None:
        self.config = config
        self.base_dir = config.output.base_directory
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.run_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        self.run_dir = self.base_dir / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.subdirs = {
            key: self.run_dir / value for key, value in self.SUBDIRECTORIES.items()
        }
        for path in self.subdirs.values():
            path.mkdir(parents=True, exist_ok=True)

    def manifest_path(self) -> Path:
        return self.subdirs["manifests"] / self.config.output.manifest_name

    def summary_path(self) -> Path:
        return self.subdirs["summary"] / self.config.output.summary_name

    def cleanup_old_runs(self) -> None:
        """Remove older runs beyond the retention limit."""

        if self.config.output.retention <= 0:
            return

        runs: List[Path] = sorted(
            (child for child in self.base_dir.iterdir() if child.is_dir()),
            key=lambda path: path.name,
            reverse=True,
        )
        for old_run in runs[self.config.output.retention :]:
            shutil.rmtree(old_run, ignore_errors=True)

    def record_artifact(self, relative_path: Path, content: bytes) -> Path:
        """Write an artifact relative to the run directory."""

        target_path = self.run_dir / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(content)
        return target_path

    def resolve(self, *parts: str) -> Path:
        return self.run_dir.joinpath(*parts)

    def subdirectory(self, name: str) -> Path:
        return self.subdirs[name]

    def list_artifacts(self) -> Iterable[Path]:
        for directory in self.subdirs.values():
            for path in directory.rglob("*"):
                if path.is_file():
                    yield path.relative_to(self.run_dir)
