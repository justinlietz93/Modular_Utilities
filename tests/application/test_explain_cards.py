import hashlib
import json
from pathlib import Path

from code_crawler.application.explain_cards import ExplainCardGenerator
from code_crawler.domain.configuration import (
    CrawlerConfig,
    ExplainCardOptions,
    FeatureToggles,
    OutputOptions,
)
from code_crawler.domain.knowledge_graph import (
    KnowledgeGraph,
    Node,
    NodeType,
    Relationship,
    RelationshipType,
)
from code_crawler.infrastructure.filesystem.run_storage import RunStorage


def build_config(base_dir: Path, *, mode: str = "template", enable_local: bool = False) -> CrawlerConfig:
    config = CrawlerConfig()
    features = FeatureToggles(
        enable_metrics=config.features.enable_metrics,
        enable_badges=config.features.enable_badges,
        enable_bundles=config.features.enable_bundles,
        enable_diagrams=config.features.enable_diagrams,
        enable_summary=config.features.enable_summary,
        enable_graph=config.features.enable_graph,
        enable_explain_cards=True,
    )
    explain_cards = ExplainCardOptions(
        scopes=["architecture", "quality", "tests"],
        mode=mode,
        require_review=True,
        enable_local_model=enable_local,
        local_model_path=base_dir / "local-model.bin" if enable_local else None,
    )
    return CrawlerConfig(
        version=config.version,
        privacy=config.privacy,
        features=features,
        thresholds=config.thresholds,
        sources=config.sources,
        output=OutputOptions(base_directory=base_dir),
        metrics=config.metrics,
        graph=config.graph,
        diagrams=config.diagrams,
        explain_cards=explain_cards,
        seed=42,
    )


def build_graph() -> KnowledgeGraph:
    graph = KnowledgeGraph()
    module = Node(
        identifier="module:alpha",
        type=NodeType.MODULE,
        label="alpha",
        provenance=("test",),
        attributes={},
    )
    test_node = Node(
        identifier="test:test_alpha",
        type=NodeType.TEST,
        label="test_alpha",
        provenance=("test",),
        attributes={},
    )
    dependency = Node(
        identifier="dependency:requests",
        type=NodeType.DEPENDENCY,
        label="requests",
        provenance=("requirements.txt",),
        attributes={"version": "==2.31.0"},
    )
    graph.add_node(module)
    graph.add_node(test_node)
    graph.add_node(dependency)
    graph.add_relationship(
        Relationship(
            identifier="tests:test:test_alpha->module:alpha",
            type=RelationshipType.TESTS,
            source=test_node.identifier,
            target=module.identifier,
            attributes={},
        )
    )
    graph.add_relationship(
        Relationship(
            identifier="depends_on:module:alpha->dependency:requests",
            type=RelationshipType.DEPENDS_ON,
            source=module.identifier,
            target=dependency.identifier,
            attributes={},
        )
    )
    return graph


def test_explain_card_generator_creates_markdown_and_metadata(tmp_path: Path) -> None:
    config = build_config(tmp_path / "runs")
    storage = RunStorage(config)
    bundle_path = storage.record_artifact(Path("bundles/sample.txt"), b"bundle")
    generator = ExplainCardGenerator(config, storage)
    artifacts = generator.generate(
        graph=build_graph(),
        metrics=None,
        bundle_paths=[bundle_path],
    )

    assert artifacts.index_path.exists()
    rendered = [result.output_path for result in artifacts.results]
    metadata_files = [result.metadata_path for result in artifacts.results]
    assert rendered and metadata_files
    content = rendered[0].read_text(encoding="utf-8")
    assert "## Rationale" in content
    assert "## Edge Cases" in content
    metadata = json.loads(metadata_files[0].read_text(encoding="utf-8"))
    assert metadata["status"] == "review_pending"
    assert metadata["requires_review"] is True
    assert metadata["review_history"][0]["status"] == "review_pending"
    assert metadata["checksum"] == hashlib.sha256(content.encode("utf-8")).hexdigest()


def test_local_model_mode_falls_back_when_missing(tmp_path: Path) -> None:
    config = build_config(tmp_path / "runs", mode="local-llm", enable_local=True)
    storage = RunStorage(config)
    generator = ExplainCardGenerator(config, storage)
    artifacts = generator.generate(
        graph=build_graph(),
        metrics=None,
        bundle_paths=[],
    )
    metadata = json.loads(artifacts.results[0].metadata_path.read_text(encoding="utf-8"))
    assert metadata["mode"] == "template-fallback"
