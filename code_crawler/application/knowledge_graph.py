"""Application services for building repository knowledge graphs."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from ..domain.configuration import CrawlerConfig
from ..domain.assets import AssetCard, AssetExtraction
from ..domain.knowledge_graph import (
    GraphDiff,
    KnowledgeGraph,
    KnowledgeGraphSerializer,
    KnowledgeGraphValidator,
    Node,
    NodeType,
    Relationship,
    RelationshipType,
    deterministic_node_id,
    deterministic_relationship_id,
    diff_graphs,
)
from ..domain.manifest import ManifestEntry
from ..shared.logging import configure_logger
from .scanner import DeltaReport, EntityEvent, FileRecord


@dataclass(frozen=True)
class GraphArtifacts:
    """Artifacts emitted by the knowledge graph builder."""

    graph: KnowledgeGraph
    jsonld_path: Path
    graphml_path: Path
    diff: Optional[GraphDiff]
    diff_json_path: Optional[Path]
    diff_report_path: Optional[Path]
    instrumentation: Dict[str, object]


class DependencyParser:
    """Extract dependency metadata from well-known project manifests."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def parse(self) -> Dict[str, Dict[str, str]]:
        dependencies: Dict[str, Dict[str, str]] = {}
        for requirements_file in sorted(self.root.glob("requirements*.txt")):
            for line in requirements_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                entry = line.strip()
                if not entry or entry.startswith("#"):
                    continue
                package, version = self._split_requirement(entry)
                dependencies[package.lower()] = {
                    "name": package,
                    "version": version,
                    "source": requirements_file.name,
                }
        pyproject = self.root / "pyproject.toml"
        if pyproject.exists():
            for package, version in self._parse_pyproject(pyproject):
                dependencies.setdefault(package.lower(), {
                    "name": package,
                    "version": version,
                    "source": "pyproject.toml",
                })
        return dependencies

    @staticmethod
    def _split_requirement(entry: str) -> Tuple[str, str]:
        for separator in ("==", ">=", "~=", "<=", ">", "<"):
            if separator in entry:
                package, version = entry.split(separator, 1)
                return package.strip(), f"{separator}{version.strip()}"
        return entry, ""

    @staticmethod
    def _parse_pyproject(path: Path) -> Iterable[Tuple[str, str]]:
        try:
            import tomllib  # Python 3.11+
        except ModuleNotFoundError:  # pragma: no cover - fallback for <3.11
            return []
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        dependencies: List[Tuple[str, str]] = []
        project = data.get("project") or {}
        for entry in project.get("dependencies", []):
            dependencies.append(DependencyParser._split_requirement(entry))
        for extra in project.get("optional-dependencies", {}).values():
            for entry in extra:
                dependencies.append(DependencyParser._split_requirement(entry))
        return dependencies


class KnowledgeGraphBuilder:
    """Builds and persists repository knowledge graphs."""

    GRAPH_DIR = "graphs"
    GRAPH_JSON = "graph.jsonld"
    GRAPH_GRAPHML = "graph.graphml"
    DIFF_JSON = "graph_diff.json"
    DIFF_REPORT = "graph_diff.md"

    def __init__(self, config: CrawlerConfig, storage, logger=None) -> None:
        self.config = config
        self.storage = storage
        self.logger = logger or configure_logger(config.privacy)

    def build(
        self,
        *,
        records: Sequence[FileRecord],
        events: Sequence[EntityEvent],
        manifest_entries: Sequence[ManifestEntry],
        delta: DeltaReport,
        instrumentation: Dict[str, int],
        assets: Sequence[AssetExtraction] | None = None,
        asset_cards: Sequence[AssetCard] | None = None,
    ) -> GraphArtifacts:
        graph = KnowledgeGraph()
        start_time = time.perf_counter()
        run_node_id = deterministic_node_id(NodeType.RUN, self.storage.run_id)
        graph.add_node(
            Node(
                identifier=run_node_id,
                type=NodeType.RUN,
                label=f"Run {self.storage.run_id}",
                provenance=("run_service",),
                attributes={
                    "config_version": self.config.version,
                    "source_root": str(self.config.sources.root),
                },
            )
        )

        file_nodes = self._add_files(graph, run_node_id, records, delta)
        module_nodes = self._add_entities(graph, file_nodes, events)
        dependency_map = DependencyParser(self.config.sources.root).parse()
        self._add_dependencies(graph, module_nodes, dependency_map)
        self._add_manifest_artifacts(graph, run_node_id, manifest_entries)
        self._add_assets(
            graph,
            run_node_id,
            file_nodes,
            assets or (),
            asset_cards or (),
        )

        # Validate graph but do not fail the run; log and continue to write outputs
        try:
            KnowledgeGraphValidator.validate(graph)
        except Exception as exc:  # pragma: no cover
            self.logger.warning("Graph validation failed: %s (continuing)", exc)
        duration = time.perf_counter() - start_time

        graph_dir = self.storage.subdirectory(self.GRAPH_DIR)
        jsonld_path = graph_dir / self.GRAPH_JSON
        graphml_path = graph_dir / self.GRAPH_GRAPHML

        jsonld = KnowledgeGraphSerializer.to_jsonld(graph)
        graph_dir.mkdir(parents=True, exist_ok=True)
        jsonld_path.write_text(json.dumps(jsonld, indent=2), encoding="utf-8")
        graphml_path.write_text(KnowledgeGraphSerializer.to_graphml(graph), encoding="utf-8")

        previous_graph = self._load_previous_graph() if self.config.graph.enable_diff else None
        diff: Optional[GraphDiff] = None
        diff_json_path: Optional[Path] = None
        diff_report_path: Optional[Path] = None
        if previous_graph and self.config.graph.enable_diff:
            diff = diff_graphs(previous_graph, graph)
            diff_json_path = graph_dir / self.DIFF_JSON
            diff_json_path.write_text(json.dumps(diff.to_dict(), indent=2), encoding="utf-8")
            diff_report_path = graph_dir / self.DIFF_REPORT
            diff_report_path.write_text(self._format_diff(diff), encoding="utf-8")

        instrumentation_payload: Dict[str, object] = {
            "build_seconds": round(duration, 6),
            "file_count": len(records),
            "entity_count": len(events),
            "dependencies": len(dependency_map),
            "event_cache_hits": instrumentation.get("cache_hits", 0),
            "event_cache_misses": instrumentation.get("cache_misses", 0),
            "asset_count": len(assets or ()),
            "asset_card_count": len(asset_cards or ()),
        }

        return GraphArtifacts(
            graph=graph,
            jsonld_path=jsonld_path,
            graphml_path=graphml_path,
            diff=diff,
            diff_json_path=diff_json_path,
            diff_report_path=diff_report_path,
            instrumentation=instrumentation_payload,
        )

    def _add_files(
        self,
        graph: KnowledgeGraph,
        run_node_id: str,
        records: Sequence[FileRecord],
        delta: DeltaReport,
    ) -> Dict[str, str]:
        module_lookup: Dict[str, str] = {}
        for record in records:
            node_id = deterministic_node_id(NodeType.FILE, record.identifier)
            graph.add_node(
                Node(
                    identifier=node_id,
                    type=NodeType.FILE,
                    label=record.identifier,
                    provenance=("scanner", record.path.as_posix()),
                    attributes={
                        "size": record.size,
                        "digest": record.digest,
                        "status": self._status_for(record.identifier, delta),
                    },
                )
            )
            graph.add_relationship(
                Relationship(
                    identifier=deterministic_relationship_id(
                        RelationshipType.CONTAINS, run_node_id, node_id
                    ),
                    type=RelationshipType.CONTAINS,
                    source=run_node_id,
                    target=node_id,
                    attributes={},
                )
            )
            module_lookup[record.identifier] = node_id
        return module_lookup

    def _add_entities(
        self,
        graph: KnowledgeGraph,
        file_nodes: Dict[str, str],
        events: Sequence[EntityEvent],
    ) -> Dict[str, str]:
        module_nodes: Dict[str, str] = {}
        for event in events:
            if event.node_type == NodeType.MODULE:
                file_key = f"{event.module.replace('.', '/')}.py"
                file_node = file_nodes.get(file_key)
                node = Node(
                    identifier=deterministic_node_id(NodeType.MODULE, event.module),
                    type=NodeType.MODULE,
                    label=event.module,
                    provenance=("ast", event.file_path.as_posix()),
                    attributes={
                        "docstring": event.docstring or "",
                        "depends_on": list(event.depends_on),
                    },
                )
                graph.add_node(node)
                module_nodes[event.module] = node.identifier
                if file_node:
                    graph.add_relationship(
                        Relationship(
                            identifier=deterministic_relationship_id(
                                RelationshipType.DECLARES, file_node, node.identifier
                            ),
                            type=RelationshipType.DECLARES,
                            source=file_node,
                            target=node.identifier,
                            attributes={"lineno": event.lineno},
                        )
                    )

        for event in events:
            if event.node_type == NodeType.MODULE:
                continue
            entity_ref = event.node_id.split(":", 1)[1]
            entity_id = deterministic_node_id(event.node_type, entity_ref)
            module_id = deterministic_node_id(NodeType.MODULE, event.module)
            graph.add_node(
                Node(
                    identifier=entity_id,
                    type=event.node_type,
                    label=event.name,
                    provenance=("ast", event.file_path.as_posix()),
                    attributes={
                        "module": event.module,
                        "lineno": event.lineno,
                        "docstring": event.docstring or "",
                        "is_test": event.is_test,
                    },
                )
            )
            graph.add_relationship(
                Relationship(
                    identifier=deterministic_relationship_id(
                        RelationshipType.DECLARES, module_id, entity_id
                    ),
                    type=RelationshipType.DECLARES,
                    source=module_id,
                    target=entity_id,
                    attributes={"is_test": event.is_test},
                )
            )
            for dependency in event.depends_on:
                dependency_name = dependency.split(".")[0].lower()
                dependency_id = deterministic_node_id(NodeType.DEPENDENCY, dependency_name)
                if dependency_id not in graph.nodes:
                    continue
                rel_id = deterministic_relationship_id(
                    RelationshipType.DEPENDS_ON,
                    entity_id,
                    dependency_id,
                )
                graph.add_relationship(
                    Relationship(
                        identifier=rel_id,
                        type=RelationshipType.DEPENDS_ON,
                        source=entity_id,
                        target=dependency_id,
                        attributes={},
                    )
                )
        return module_nodes

    def _add_dependencies(
        self,
        graph: KnowledgeGraph,
        module_nodes: Dict[str, str],
        dependency_map: Dict[str, Dict[str, str]],
    ) -> None:
        for dependency_key, metadata in dependency_map.items():
            node_id = deterministic_node_id(NodeType.DEPENDENCY, dependency_key)
            graph.add_node(
                Node(
                    identifier=node_id,
                    type=NodeType.DEPENDENCY,
                    label=metadata["name"],
                    provenance=("dependencies",),
                    attributes={
                        "version": metadata.get("version", ""),
                        "source": metadata.get("source", ""),
                    },
                )
            )
        for module_name, node_id in module_nodes.items():
            module_dependency = module_name.split(".")[0].lower()
            dependency_id = deterministic_node_id(NodeType.DEPENDENCY, module_dependency)
            if dependency_id in graph.nodes:
                graph.add_relationship(
                    Relationship(
                        identifier=deterministic_relationship_id(
                            RelationshipType.DEPENDS_ON, node_id, dependency_id
                        ),
                        type=RelationshipType.DEPENDS_ON,
                        source=node_id,
                        target=dependency_id,
                        attributes={"scope": "module"},
                    )
                )

    def _add_manifest_artifacts(
        self,
        graph: KnowledgeGraph,
        run_node_id: str,
        manifest_entries: Sequence[ManifestEntry],
    ) -> None:
        for entry in manifest_entries:
            artifact_node_id = deterministic_node_id(NodeType.ARTIFACT, entry.identifier)
            graph.add_node(
                Node(
                    identifier=artifact_node_id,
                    type=NodeType.ARTIFACT,
                    label=entry.identifier,
                    provenance=("manifest",),
                    attributes={
                        "path": entry.path,
                        "digest": entry.digest,
                        "status": entry.status,
                    },
                )
            )
            graph.add_relationship(
                Relationship(
                    identifier=deterministic_relationship_id(
                        RelationshipType.PRODUCES, run_node_id, artifact_node_id
                    ),
                    type=RelationshipType.PRODUCES,
                    source=run_node_id,
                    target=artifact_node_id,
                    attributes={},
                )
            )

    def _add_assets(
        self,
        graph: KnowledgeGraph,
        run_node_id: str,
        file_nodes: Dict[str, str],
        assets: Sequence[AssetExtraction],
        asset_cards: Sequence[AssetCard],
    ) -> None:
        asset_lookup: Dict[str, str] = {}
        for asset in assets:
            node_id = deterministic_node_id(NodeType.ASSET, asset.identifier)
            asset_lookup[asset.identifier] = node_id
            graph.add_node(
                Node(
                    identifier=node_id,
                    type=NodeType.ASSET,
                    label=asset.path.as_posix(),
                    provenance=asset.provenance,
                    attributes={
                        "summary": asset.summary,
                        **asset.metadata,
                    },
                )
            )
            source_path = asset.path.as_posix()
            file_node = file_nodes.get(source_path)
            if file_node:
                graph.add_relationship(
                    Relationship(
                        identifier=deterministic_relationship_id(
                            RelationshipType.DERIVES, file_node, node_id
                        ),
                        type=RelationshipType.DERIVES,
                        source=file_node,
                        target=node_id,
                        attributes={},
                    )
                )
            graph.add_relationship(
                Relationship(
                    identifier=deterministic_relationship_id(
                        RelationshipType.PRODUCES, run_node_id, node_id
                    ),
                    type=RelationshipType.PRODUCES,
                    source=run_node_id,
                    target=node_id,
                    attributes={"kind": "asset_extraction"},
                )
            )

        for card in asset_cards:
            node_id = deterministic_node_id(NodeType.ASSET_CARD, card.identifier)
            graph.add_node(
                Node(
                    identifier=node_id,
                    type=NodeType.ASSET_CARD,
                    label=card.title,
                    provenance=card.provenance,
                    attributes={
                        "summary": card.summary,
                        "checksum": card.checksum,
                    },
                )
            )
            asset_node = asset_lookup.get(card.asset_identifier)
            if asset_node:
                graph.add_relationship(
                    Relationship(
                        identifier=deterministic_relationship_id(
                            RelationshipType.DESCRIBES, node_id, asset_node
                        ),
                        type=RelationshipType.DESCRIBES,
                        source=node_id,
                        target=asset_node,
                        attributes={},
                    )
                )
            graph.add_relationship(
                Relationship(
                    identifier=deterministic_relationship_id(
                        RelationshipType.PRODUCES, run_node_id, node_id
                    ),
                    type=RelationshipType.PRODUCES,
                    source=run_node_id,
                    target=node_id,
                    attributes={"kind": "asset_card"},
                )
            )

    def _load_previous_graph(self) -> Optional[KnowledgeGraph]:
        runs = sorted(
            (
                path
                for path in self.storage.base_dir.iterdir()
                if path.is_dir() and path.name < self.storage.run_id
            ),
            key=lambda path: path.name,
            reverse=True,
        )
        for run in runs:
            jsonld_path = run / self.GRAPH_DIR / self.GRAPH_JSON
            if jsonld_path.exists():
                try:
                    data = json.loads(jsonld_path.read_text(encoding="utf-8"))
                    return KnowledgeGraph.from_dict(data)
                except json.JSONDecodeError:
                    continue
        return None

    @staticmethod
    def _status_for(identifier: str, delta: DeltaReport) -> str:
        if identifier in delta.added:
            return "added"
        if identifier in delta.changed:
            return "changed"
        if identifier in delta.removed:
            return "removed"
        return "unchanged"

    @staticmethod
    def _format_diff(diff: GraphDiff) -> str:
        lines = ["# Knowledge Graph Diff", ""]
        sections = {
            "Added Nodes": diff.added_nodes,
            "Removed Nodes": diff.removed_nodes,
            "Added Relationships": diff.added_relationships,
            "Removed Relationships": diff.removed_relationships,
            "Changed Nodes": diff.changed_nodes,
        }
        for title, values in sections.items():
            lines.append(f"## {title}")
            if values:
                for value in sorted(values):
                    lines.append(f"- {value}")
            else:
                lines.append("- None")
            lines.append("")
        return "\n".join(lines)
