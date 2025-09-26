"""Directory walker and delta computation."""
from __future__ import annotations

import ast
import fnmatch
import os
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Tuple

from ..domain.configuration import CrawlerConfig
from ..domain.knowledge_graph import NodeType


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
        self._event_extractor = EventExtractor()

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

    def emit_events(self, records: Iterable[FileRecord]) -> List["EntityEvent"]:
        """Extract structured events for knowledge graph construction."""

        events: List[EntityEvent] = []
        for record in records:
            events.extend(self._event_extractor.events_for(record))
        return events

    def instrumentation(self) -> Dict[str, int]:
        return self._event_extractor.instrumentation()

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


@dataclass(frozen=True)
class EntityEvent:
    """Structured representation of code entities for graph construction."""

    node_id: str
    node_type: NodeType
    name: str
    module: str
    file_path: Path
    lineno: int
    depends_on: Tuple[str, ...]
    docstring: str | None
    is_test: bool


class EventExtractor:
    """Parse source files and emit entity events with digest-aware caching."""

    def __init__(self) -> None:
        self._cache: Dict[str, Tuple[EntityEvent, ...]] = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def events_for(self, record: FileRecord) -> Tuple[EntityEvent, ...]:
        if not record.path.suffix == ".py":
            return ()
        cached = self._cache.get(record.digest)
        if cached is not None:
            self.cache_hits += 1
            return cached
        self.cache_misses += 1
        source = record.path.read_text(encoding="utf-8", errors="ignore")
        events = self._parse_python(record, source)
        self._cache[record.digest] = events
        return events

    def _parse_python(self, record: FileRecord, source: str) -> Tuple[EntityEvent, ...]:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return ()
        module_name = record.identifier.replace("/", ".").removesuffix(".py")
        imports: List[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        unique_imports = tuple(sorted(set(imports)))
        events: List[EntityEvent] = []
        docstring = ast.get_docstring(tree)
        module_event = EntityEvent(
            node_id=f"module:{module_name}",
            node_type=NodeType.MODULE,
            name=module_name,
            module=module_name,
            file_path=record.path,
            lineno=1,
            depends_on=unique_imports,
            docstring=docstring,
            is_test=module_name.endswith("_test") or module_name.startswith("tests."),
        )
        events.append(module_event)

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fq_name = f"{module_name}.{node.name}"
                events.append(
                    EntityEvent(
                        node_id=f"function:{fq_name}",
                        node_type=NodeType.TEST if node.name.startswith("test_") else NodeType.FUNCTION,
                        name=node.name,
                        module=module_name,
                        file_path=record.path,
                        lineno=node.lineno,
                        depends_on=unique_imports,
                        docstring=ast.get_docstring(node),
                        is_test=node.name.startswith("test_") or module_event.is_test,
                    )
                )
            elif isinstance(node, ast.ClassDef):
                fq_name = f"{module_name}.{node.name}"
                is_test = any(
                    base.id.lower().endswith("testcase") if isinstance(base, ast.Name) else False
                    for base in node.bases
                ) or node.name.startswith("Test") or module_event.is_test
                events.append(
                    EntityEvent(
                        node_id=f"class:{fq_name}",
                        node_type=NodeType.TEST if is_test else NodeType.CLASS,
                        name=node.name,
                        module=module_name,
                        file_path=record.path,
                        lineno=node.lineno,
                        depends_on=unique_imports,
                        docstring=ast.get_docstring(node),
                        is_test=is_test,
                    )
                )
        return tuple(events)

    def instrumentation(self) -> Dict[str, int]:
        return {"cache_hits": self.cache_hits, "cache_misses": self.cache_misses}
