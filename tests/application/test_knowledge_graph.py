import json
from datetime import UTC, datetime
from pathlib import Path

from code_crawler.application.knowledge_graph import DependencyParser, KnowledgeGraphBuilder
from code_crawler.application.scanner import SourceWalker
from code_crawler.domain.assets import (
    AssetCard,
    AssetExtraction,
    AssetType,
    asset_card_identifier,
    asset_identifier,
)
from code_crawler.domain.configuration import CrawlerConfig, OutputOptions, SourceOptions
from code_crawler.domain.knowledge_graph import (
    NodeType,
    RelationshipType,
    deterministic_node_id,
)
from code_crawler.domain.manifest import ManifestEntry
from code_crawler.infrastructure.filesystem.run_storage import RunStorage


def test_knowledge_graph_builder_creates_artifacts(tmp_path: Path) -> None:
    source_file = tmp_path / "example.py"
    source_file.write_text(
        """
import json

class Example:
    def method(self):
        return json.dumps({})
"""
    )
    config = CrawlerConfig(
        sources=SourceOptions(root=tmp_path, include=[], ignore=[]),
        output=OutputOptions(base_directory=tmp_path / "runs"),
    )
    storage = RunStorage(config)
    walker = SourceWalker(config, {})
    records, delta = walker.walk()
    events = walker.emit_events(records)
    instrumentation = walker.instrumentation()
    manifest_entries = []
    for record in records:
        manifest_entries.append(
            ManifestEntry(
                identifier=record.identifier,
                path=record.path.as_posix(),
                size=record.size,
                digest=record.digest,
                modified=datetime.fromtimestamp(record.modified, UTC),
                status="added",
            )
        )

    builder = KnowledgeGraphBuilder(config, storage)
    artifacts = builder.build(
        records=records,
        events=events,
        manifest_entries=manifest_entries,
        delta=delta,
        instrumentation=instrumentation,
    )

    assert artifacts.jsonld_path.exists()
    assert any(node.type.value == "module" for node in artifacts.graph.nodes.values())

def test_dependency_parser_reads_requirements_and_pyproject(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("requests>=2.0\n# comment", encoding="utf-8")
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
dependencies = ["httpx==0.24"]
[project.optional-dependencies]
extras = ["rich>=13"]
""",
        encoding="utf-8",
    )
    parser = DependencyParser(tmp_path)
    deps = parser.parse()
    assert deps["requests"]["source"] == "requirements.txt"
    assert deps["httpx"]["source"] == "pyproject.toml"
    assert deps["rich"]["source"] == "pyproject.toml"


def test_knowledge_graph_builder_writes_diff(tmp_path: Path) -> None:
    graph_root = tmp_path / "runs"
    previous = graph_root / "00000000-000000"
    (previous / "graphs").mkdir(parents=True, exist_ok=True)
    previous_graph = {
        "nodes": [
            {
                "id": "run:00000000-000000",
                "type": "run",
                "label": "old",
                "provenance": ["run"],
                "attributes": {},
            }
        ],
        "relationships": [],
    }
    (previous / "graphs" / "graph.jsonld").write_text(json.dumps(previous_graph), encoding="utf-8")

    source_file = tmp_path / "module.py"
    source_file.write_text("def thing():\n    return 42\n", encoding="utf-8")
    config = CrawlerConfig(
        sources=SourceOptions(root=tmp_path, include=[], ignore=[]),
        output=OutputOptions(base_directory=graph_root),
    )
    storage = RunStorage(config)
    walker = SourceWalker(config, {})
    records, delta = walker.walk()
    events = walker.emit_events(records)
    instrumentation = walker.instrumentation()
    manifest_entries = [
        ManifestEntry(
            identifier=record.identifier,
            path=record.path.as_posix(),
            size=record.size,
            digest=record.digest,
            modified=datetime.fromtimestamp(record.modified, UTC),
            status="added",
        )
        for record in records
    ]
    builder = KnowledgeGraphBuilder(config, storage)
    artifacts = builder.build(
        records=records,
        events=events,
        manifest_entries=manifest_entries,
        delta=delta,
        instrumentation=instrumentation,
    )
    assert artifacts.diff_json_path is not None
    assert artifacts.diff_json_path.exists()


def test_knowledge_graph_includes_assets(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    asset_file = tmp_path / "docs" / "note.txt"
    asset_file.write_text("important asset", encoding="utf-8")
    config = CrawlerConfig(
        sources=SourceOptions(root=tmp_path, include=[], ignore=[]),
        output=OutputOptions(base_directory=tmp_path / "runs"),
    )
    storage = RunStorage(config)
    walker = SourceWalker(config, {})
    records, delta = walker.walk()
    events = walker.emit_events(records)
    instrumentation = walker.instrumentation()
    manifest_entries = [
        ManifestEntry(
            identifier=record.identifier,
            path=record.path.as_posix(),
            size=record.size,
            digest=record.digest,
            modified=datetime.fromtimestamp(record.modified, UTC),
            status="added",
        )
        for record in records
    ]

    asset_id = asset_identifier(Path("docs/note.txt"))
    extraction = AssetExtraction(
        identifier=asset_id,
        path=Path("docs/note.txt"),
        asset_type=AssetType.DOCUMENT,
        summary="Document asset summary",
        content="Document asset summary",
        provenance=("test",),
        metadata={"length": 18},
    )
    card = AssetCard(
        identifier=asset_card_identifier(asset_id),
        asset_identifier=asset_id,
        title="Asset Card",
        asset_type=AssetType.DOCUMENT,
        summary="Document asset summary",
        notes={"Provenance": "test"},
        provenance=("test", "card"),
        checksum="abc123",
    )

    builder = KnowledgeGraphBuilder(config, storage)
    artifacts = builder.build(
        records=records,
        events=events,
        manifest_entries=manifest_entries,
        delta=delta,
        instrumentation=instrumentation,
        assets=[extraction],
        asset_cards=[card],
    )

    asset_node_id = deterministic_node_id(NodeType.ASSET, asset_id)
    assert asset_node_id in artifacts.graph.nodes
    assert artifacts.graph.nodes[asset_node_id].attributes["summary"] == "Document asset summary"
    assert any(
        rel.type == RelationshipType.DESCRIBES for rel in artifacts.graph.relationships.values()
    )
