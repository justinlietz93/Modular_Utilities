"""Directory walker and delta computation."""
from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Tuple

from ..domain.configuration import CrawlerConfig


@dataclass(frozen=True)
class FileRecord:
    """Represents a discovered source file."""

    identifier: str
    path: Path
    size: int
    digest: str
    modified: float
    cached: bool


@dataclass(frozen=True)
class DeltaReport:
    """Describes changes since last run."""

    added: List[str]
    changed: List[str]
    removed: List[str]
    unchanged: List[str]

    def to_dict(self) -> Dict[str, List[str]]:
        return {
            "added": self.added,
            "changed": self.changed,
            "removed": self.removed,
            "unchanged": self.unchanged,
        }


class SourceWalker:
    """Walks directories respecting include/ignore rules and caches."""

    def __init__(self, config: CrawlerConfig, cache_index: Dict[str, Dict[str, object]] | None = None) -> None:
        self.config = config
        self.cache_index = cache_index or {}
        self.root = config.sources.root
        self.include = [pattern for pattern in config.sources.include if pattern]
        self.ignore = [pattern for pattern in config.sources.ignore if pattern]

    def walk(self) -> Tuple[List[FileRecord], DeltaReport]:
        discovered: List[FileRecord] = []
        current_hashes: Dict[str, FileRecord] = {}

        for path in self._iter_files():
            relative = path.relative_to(self.root).as_posix()
            stat = path.stat()
            digest = self._hash_file(path)
            cached = False
            cached_entry = self.cache_index.get(relative)
            if cached_entry and cached_entry.get("hash") == digest:
                cached = True
            record = FileRecord(
                identifier=relative,
                path=path,
                size=stat.st_size,
                digest=digest,
                modified=stat.st_mtime,
                cached=cached,
            )
            discovered.append(record)
            current_hashes[relative] = record

        previous_paths = set(self.cache_index.keys())
        current_paths = set(current_hashes.keys())
        added = sorted(current_paths - previous_paths)
        removed = sorted(previous_paths - current_paths)
        changed = sorted(
            path
            for path in current_paths & previous_paths
            if self.cache_index[path]["hash"] != current_hashes[path].digest
        )
        unchanged = sorted(current_paths & previous_paths - set(changed))

        return discovered, DeltaReport(added=added, changed=changed, removed=removed, unchanged=unchanged)

    def _iter_files(self) -> Iterator[Path]:
        for dirpath, dirnames, filenames in os.walk(self.root, followlinks=self.config.sources.follow_symlinks):
            dirpath = Path(dirpath)
            dirnames[:] = [
                d
                for d in dirnames
                if not self._is_ignored((dirpath / d).relative_to(self.root))
            ]
            for filename in filenames:
                path = dirpath / filename
                relative = path.relative_to(self.root)
                if self._is_ignored(relative):
                    continue
                if self.include and not any(fnmatch.fnmatch(relative.as_posix(), pattern) for pattern in self.include):
                    continue
                yield path

    def _is_ignored(self, relative: Path) -> bool:
        posix = relative.as_posix()
        for pattern in self.ignore:
            if fnmatch.fnmatch(posix, pattern):
                return True
        return False

    @staticmethod
    def _hash_file(path: Path) -> str:
        digest = sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()


def update_cache(index_path: Path, records: Iterable[FileRecord]) -> Dict[str, Dict[str, object]]:
    """Persist cache metadata for incremental runs."""

    new_index: Dict[str, Dict[str, object]] = {}
    for record in records:
        new_index[record.identifier] = {
            "hash": record.digest,
            "size": record.size,
            "modified": record.modified,
        }
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(os.linesep.join(
        f"{identifier}|{data['hash']}|{data['size']}|{data['modified']}"
        for identifier, data in sorted(new_index.items())
    ), encoding="utf-8")
    return new_index


def load_cache(index_path: Path) -> Dict[str, Dict[str, object]]:
    """Load cache metadata if available."""

    if not index_path.exists():
        return {}
    cache: Dict[str, Dict[str, object]] = {}
    for line in index_path.read_text(encoding="utf-8").splitlines():
        identifier, digest, size, modified = line.split("|")
        cache[identifier] = {
            "hash": digest,
            "size": int(size),
            "modified": float(modified),
        }
    return cache
