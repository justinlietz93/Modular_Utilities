import json
from dataclasses import replace
from pathlib import Path

from code_crawler.application.diagrams import DiagramGenerator
from code_crawler.domain.configuration import CrawlerConfig, DiagramOptions, OutputOptions
from code_crawler.domain.knowledge_graph import (
    KnowledgeGraph,
    Node,
    NodeType,
    Relationship,
    RelationshipType,
)
from code_crawler.infrastructure.filesystem.run_storage import RunStorage


def _build_graph() -> KnowledgeGraph:
    graph = KnowledgeGraph()
    module_a = Node(
        identifier="module:a",
        type=NodeType.MODULE,
        label="module_a",
        provenance=("test",),
        attributes={},
    )
    module_b = Node(
        identifier="module:b",
        type=NodeType.MODULE,
        label="module_b",
        provenance=("test",),
        attributes={},
    )
    dependency = Node(
        identifier="dependency:requests",
        type=NodeType.DEPENDENCY,
        label="requests",
        provenance=("test",),
        attributes={},
    )
    test_node = Node(
        identifier="test:test_example",
        type=NodeType.TEST,
        label="test_example",
        provenance=("test",),
        attributes={},
    )
    graph.add_node(module_a)
    graph.add_node(module_b)
    graph.add_node(dependency)
    graph.add_node(test_node)
    graph.add_relationship(
        Relationship(
            identifier="depends:module:a->module:b",
            type=RelationshipType.DEPENDS_ON,
            source=module_a.identifier,
            target=module_b.identifier,
            attributes={},
        )
    )
    graph.add_relationship(
        Relationship(
            identifier="depends:module:a->dependency:requests",
            type=RelationshipType.DEPENDS_ON,
            source=module_a.identifier,
            target=dependency.identifier,
            attributes={},
        )
    )
    graph.add_relationship(
        Relationship(
            identifier="tests:test:test_example->module:a",
            type=RelationshipType.TESTS,
            source=test_node.identifier,
            target=module_a.identifier,
            attributes={},
        )
    )
    return graph


def test_diagram_generator_writes_outputs_and_metadata(tmp_path: Path) -> None:
    config = CrawlerConfig(output=OutputOptions(base_directory=tmp_path))
    storage = RunStorage(config)
    graph = _build_graph()
    generator = DiagramGenerator(config, storage)
    artifacts = generator.generate(graph)
    diagrams_dir = storage.subdirectory("diagrams")
    metadata_path = diagrams_dir / "metadata.json"
    assert metadata_path.exists()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["templates"]
    rendered_paths = [Path(result.output_path) for result in artifacts.results]
    assert all(path.exists() for path in rendered_paths)
    assert any(result.template.name.endswith("_dark") for result in artifacts.results)


def test_diagram_generator_uses_cache_on_second_run(tmp_path: Path) -> None:
    config = CrawlerConfig(output=OutputOptions(base_directory=tmp_path))
    storage = RunStorage(config)
    graph = _build_graph()
    generator = DiagramGenerator(config, storage)
    first = generator.generate(graph)
    second = generator.generate(graph)
    assert all(result.cache_hit for result in second.results)
    first_bytes = sorted(Path(result.output_path).read_bytes() for result in first.results)
    second_bytes = sorted(Path(result.output_path).read_bytes() for result in second.results)
    assert first_bytes == second_bytes


def test_diagram_generator_png_fallback(tmp_path: Path) -> None:
    config = CrawlerConfig(output=OutputOptions(base_directory=tmp_path))
    config = replace(config, diagrams=DiagramOptions(output_formats=["png"]))
    storage = RunStorage(config)
    graph = _build_graph()
    generator = DiagramGenerator(config, storage)
    artifacts = generator.generate(graph)
    png_outputs = [Path(result.output_path) for result in artifacts.results if result.output_path.endswith(".png")]
    assert png_outputs
    sample = png_outputs[0].read_bytes()
    # PNG fallback header
    assert sample.startswith(b"\x89PNG")
