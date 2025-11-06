"""High level run orchestration."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Dict, List

from ..domain.configuration import CrawlerConfig
from ..domain.manifest import ArtifactRecord, ManifestEntry
from ..infrastructure.filesystem.manifest_writer import ManifestWriter
from ..infrastructure.filesystem.run_storage import RunStorage
from ..shared.logging import configure_logger
from .assets import AssetService
from .bundles import BundleBuilder
from .delta import write_delta_report
from .metrics import MetricsAggregator, MetricsBundle, generate_badge
from .quality_gates import GateEvaluator, GateResult
from .scanner import FileRecord, SourceWalker, load_cache, update_cache
from .summary import build_run_summary
from .knowledge_graph import KnowledgeGraphBuilder
from .diagrams import DiagramGenerator
from .explain_cards import ExplainCardGenerator


@dataclass(frozen=True)
class RunOutcome:
    run_id: str
    manifest_path: Path
    delta_path: Path
    metrics_path: Path | None
    badges: Dict[str, Path]
    bundles: List[Path]
    gates: GateResult | None
    summary_path: Path | None
    artifacts: List[ArtifactRecord]
    delta: Dict[str, List[str]]
    graph_jsonld: Path | None
    graph_graphml: Path | None
    graph_diff: Path | None
    diagrams: Dict[str, Path]
    diagram_sources: Dict[str, Path]
    diagram_metadata: Path | None
    explain_cards: Dict[str, Path]
    explain_card_metadata: Dict[str, Path]
    explain_card_index: Path | None
    assets: Dict[str, Path]
    asset_metadata: Dict[str, Path]
    asset_index: Path | None
    asset_cards: Dict[str, Path]
    asset_card_metadata: Dict[str, Path]
    asset_card_index: Path | None


class RunService:
    """Coordinates the entire crawl."""

    TOOL_VERSION = "0.2.0"

    def __init__(self, config: CrawlerConfig) -> None:
        self.config = config
        self.logger = configure_logger(config.privacy)
        self.cache_path = config.output.base_directory / "cache_index.txt"

    def execute(self, *, preset: str = "all", incremental: bool | None = None) -> RunOutcome:
        incremental = self.config.sources.incremental if incremental is None else incremental
        storage = RunStorage(self.config)
        storage.cleanup_old_runs()
        run_id = storage.run_id
        # Attach file logging for this run
        log_file = storage.subdirectory("logs") / "run.log"
        file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(file_handler)

        cache_index = {}
        if incremental:
            try:
                cache_index = load_cache(self.cache_path)
            except Exception:
                # If the cache is unreadable or corrupt, continue without it rather than failing the run
                self.logger.warning("Cache file unreadable; proceeding without incremental cache")
                cache_index = {}

        walker = SourceWalker(self.config, cache_index)
        records, delta = walker.walk()
        events = walker.emit_events(records)
        event_instrumentation = walker.instrumentation()
        self.logger.info("Discovered %s files", len(records))
        if not records:
            self.logger.warning(
                "No files discovered. Your include/ignore patterns may be too restrictive (e.g., '*' in ignore)."
            )

        if incremental:
            update_cache(self.cache_path, records)

        delta_path = write_delta_report(storage.subdirectory("delta") / "delta.json", delta)

        manifest_entries = [
            ManifestEntry(
                identifier=record.identifier,
                path=record.path.as_posix(),
                size=record.size,
                digest=record.digest,
                modified=_to_datetime(record.modified),
                status=_status_for(record, delta),
            )
            for record in records
        ]

        metrics_bundle: MetricsBundle | None = None
        metrics_path: Path | None = None
        badges: Dict[str, Path] = {}
        if self.config.features.enable_metrics:
            aggregator = MetricsAggregator(self.config)
            metrics_bundle = aggregator.collect()
            metrics_dir = storage.subdirectory("metrics")
            metrics_path = metrics_dir / "metrics.json"
            metrics_dir.mkdir(parents=True, exist_ok=True)
            metrics_path.write_text(json.dumps(metrics_bundle.to_dict(), indent=2), encoding="utf-8")
            if self.config.features.enable_badges and metrics_bundle.coverage:
                badge_svg = generate_badge("coverage", f"{metrics_bundle.coverage.percent:.1f}%")
                badge_path = storage.subdirectory("badges") / "coverage.svg"
                badge_path.write_text(badge_svg, encoding="utf-8")
                badges["coverage"] = badge_path
            if self.config.features.enable_badges and metrics_bundle.tests:
                badge_svg = generate_badge("tests", f"{metrics_bundle.tests.passed}/{metrics_bundle.tests.total}")
                badge_path = storage.subdirectory("badges") / "tests.svg"
                badge_path.write_text(badge_svg, encoding="utf-8")
                badges["tests"] = badge_path

        bundles: List[Path] = []
        bundle_records: List[FileRecord] = records
        if self.config.features.enable_bundles:
            builder = BundleBuilder()
            built = builder.build(preset, bundle_records)
            for bundle in built:
                relative = Path("bundles") / f"{bundle.name}.txt"
                path = storage.record_artifact(relative, bundle.content.encode("utf-8"))
                bundles.append(path)

        gates: GateResult | None = None
        if self.config.thresholds and self.config.features.enable_metrics and metrics_bundle:
            evaluator = GateEvaluator(self.config)
            gates = evaluator.evaluate(metrics_bundle)
            gate_dir = storage.subdirectory("gates")
            gate_path = gate_dir / "gate.json"
            gate_dir.mkdir(parents=True, exist_ok=True)
            gate_path.write_text(json.dumps(gates.to_dict(), indent=2), encoding="utf-8")

        graph_jsonld: Path | None = None
        graph_graphml: Path | None = None
        graph_diff_path: Path | None = None
        diagram_outputs: Dict[str, Path] = {}
        diagram_sources: Dict[str, Path] = {}
        diagram_metadata_path: Path | None = None
        explain_card_outputs: Dict[str, Path] = {}
        explain_card_metadata: Dict[str, Path] = {}
        explain_card_index_path: Path | None = None
        asset_outputs: Dict[str, Path] = {}
        asset_metadata_paths: Dict[str, Path] = {}
        asset_index_path: Path | None = None
        asset_card_outputs: Dict[str, Path] = {}
        asset_card_metadata_paths: Dict[str, Path] = {}
        asset_card_index_path: Path | None = None
        asset_extractions = []
        asset_cards = []
        if self.config.features.enable_assets:
            asset_service = AssetService(self.config, storage, logger=self.logger)
            asset_artifacts = asset_service.process(records)
            asset_index_path = asset_artifacts.index_path
            for result in asset_artifacts.results:
                asset_outputs[result.extraction.identifier] = result.text_path
                asset_metadata_paths[result.extraction.identifier] = result.metadata_path
                asset_extractions.append(result.extraction)
            if asset_artifacts.card_index_path:
                asset_card_index_path = asset_artifacts.card_index_path
            for card_result in asset_artifacts.cards:
                asset_card_outputs[card_result.card.identifier] = card_result.markdown_path
                asset_card_metadata_paths[card_result.card.identifier] = card_result.metadata_path
                asset_cards.append(card_result.card)
        graph_artifacts = None
        if self.config.features.enable_graph:
            filtered_events = self._filter_events(events)
            builder = KnowledgeGraphBuilder(self.config, storage, logger=self.logger)
            graph_artifacts = builder.build(
                records=records,
                events=filtered_events,
                manifest_entries=manifest_entries,
                delta=delta,
                instrumentation=event_instrumentation,
                assets=asset_extractions,
                asset_cards=asset_cards,
            )
            graph_jsonld = graph_artifacts.jsonld_path
            graph_graphml = graph_artifacts.graphml_path
            if graph_artifacts.diff_json_path and self.config.graph.enable_diff:
                graph_diff_path = graph_artifacts.diff_json_path

            if self.config.features.enable_diagrams:
                generator = DiagramGenerator(self.config, storage, logger=self.logger)
                diagram_artifacts = generator.generate(graph_artifacts.graph)
                diagram_metadata_path = diagram_artifacts.metadata_path
                for result in diagram_artifacts.results:
                    output_path = Path(result.output_path)
                    source_path = Path(result.source_path)
                    diagram_outputs[result.template.name] = output_path
                    diagram_sources[result.template.name] = source_path

        if self.config.features.enable_explain_cards:
            if not graph_artifacts:
                self.logger.warning(
                    "Explain cards requested but knowledge graph disabled; skipping generation"
                )
            else:
                generator = ExplainCardGenerator(self.config, storage, logger=self.logger)
                card_artifacts = generator.generate(
                    graph=graph_artifacts.graph,
                    metrics=metrics_bundle,
                    bundle_paths=bundles,
                )
                explain_card_index_path = card_artifacts.index_path
                for result in card_artifacts.results:
                    explain_card_outputs[result.card.identifier] = result.output_path
                    explain_card_metadata[result.card.identifier] = result.metadata_path

        manifest_writer = ManifestWriter(storage.manifest_path())
        artifacts: List[ArtifactRecord] = []
        # Always include the run log if present
        if log_file.exists():
            artifacts.append(
                ArtifactRecord(
                    path=str(log_file.relative_to(storage.run_dir)),
                    artifact_type="log",
                    digest=ManifestWriter.digest_file(log_file),
                )
            )
        if metrics_path:
            artifacts.append(ArtifactRecord(path=str(metrics_path.relative_to(storage.run_dir)), artifact_type="metrics", digest=ManifestWriter.digest_file(metrics_path)))
        for badge_name, badge_path in badges.items():
            artifacts.append(ArtifactRecord(path=str(badge_path.relative_to(storage.run_dir)), artifact_type=f"badge:{badge_name}", digest=ManifestWriter.digest_file(badge_path)))
        for bundle_path in bundles:
            artifacts.append(ArtifactRecord(path=str(bundle_path.relative_to(storage.run_dir)), artifact_type="bundle", digest=ManifestWriter.digest_file(bundle_path)))
        artifacts.append(ArtifactRecord(path=str(delta_path.relative_to(storage.run_dir)), artifact_type="delta", digest=ManifestWriter.digest_file(delta_path)))
        if graph_jsonld:
            artifacts.append(
                ArtifactRecord(
                    path=str(graph_jsonld.relative_to(storage.run_dir)),
                    artifact_type="graph:jsonld",
                    digest=ManifestWriter.digest_file(graph_jsonld),
                )
            )
        if graph_graphml:
            artifacts.append(
                ArtifactRecord(
                    path=str(graph_graphml.relative_to(storage.run_dir)),
                    artifact_type="graph:graphml",
                    digest=ManifestWriter.digest_file(graph_graphml),
                )
            )
        if graph_diff_path:
            artifacts.append(
                ArtifactRecord(
                    path=str(graph_diff_path.relative_to(storage.run_dir)),
                    artifact_type="graph:diff",
                    digest=ManifestWriter.digest_file(graph_diff_path),
                )
            )
        if diagram_metadata_path:
            artifacts.append(
                ArtifactRecord(
                    path=str(diagram_metadata_path.relative_to(storage.run_dir)),
                    artifact_type="diagram:metadata",
                    digest=ManifestWriter.digest_file(diagram_metadata_path),
                )
            )
        for name, output_path in diagram_outputs.items():
            artifacts.append(
                ArtifactRecord(
                    path=str(output_path.relative_to(storage.run_dir)),
                    artifact_type=f"diagram:{name}",
                    digest=ManifestWriter.digest_file(output_path),
                )
            )
        for name, source_path in diagram_sources.items():
            artifacts.append(
                ArtifactRecord(
                    path=str(source_path.relative_to(storage.run_dir)),
                    artifact_type=f"diagram_source:{name}",
                    digest=ManifestWriter.digest_file(source_path),
                )
            )
        if asset_index_path:
            artifacts.append(
                ArtifactRecord(
                    path=str(asset_index_path.relative_to(storage.run_dir)),
                    artifact_type="assets:index",
                    digest=ManifestWriter.digest_file(asset_index_path),
                )
            )
        for identifier, output_path in asset_outputs.items():
            artifacts.append(
                ArtifactRecord(
                    path=str(output_path.relative_to(storage.run_dir)),
                    artifact_type=f"asset:{identifier}",
                    digest=ManifestWriter.digest_file(output_path),
                )
            )
        for identifier, metadata_path in asset_metadata_paths.items():
            artifacts.append(
                ArtifactRecord(
                    path=str(metadata_path.relative_to(storage.run_dir)),
                    artifact_type=f"asset_metadata:{identifier}",
                    digest=ManifestWriter.digest_file(metadata_path),
                )
            )
        if explain_card_index_path:
            artifacts.append(
                ArtifactRecord(
                    path=str(explain_card_index_path.relative_to(storage.run_dir)),
                    artifact_type="explain_cards:index",
                    digest=ManifestWriter.digest_file(explain_card_index_path),
                )
            )
        for identifier, output_path in explain_card_outputs.items():
            artifacts.append(
                ArtifactRecord(
                    path=str(output_path.relative_to(storage.run_dir)),
                    artifact_type=f"explain_card:{identifier}",
                    digest=ManifestWriter.digest_file(output_path),
                )
            )
        for identifier, metadata_path in explain_card_metadata.items():
            artifacts.append(
                ArtifactRecord(
                    path=str(metadata_path.relative_to(storage.run_dir)),
                    artifact_type=f"explain_card_metadata:{identifier}",
                    digest=ManifestWriter.digest_file(metadata_path),
                )
            )
        if asset_card_index_path:
            artifacts.append(
                ArtifactRecord(
                    path=str(asset_card_index_path.relative_to(storage.run_dir)),
                    artifact_type="asset_cards:index",
                    digest=ManifestWriter.digest_file(asset_card_index_path),
                )
            )
        for identifier, output_path in asset_card_outputs.items():
            artifacts.append(
                ArtifactRecord(
                    path=str(output_path.relative_to(storage.run_dir)),
                    artifact_type=f"asset_card:{identifier}",
                    digest=ManifestWriter.digest_file(output_path),
                )
            )
        for identifier, metadata_path in asset_card_metadata_paths.items():
            artifacts.append(
                ArtifactRecord(
                    path=str(metadata_path.relative_to(storage.run_dir)),
                    artifact_type=f"asset_card_metadata:{identifier}",
                    digest=ManifestWriter.digest_file(metadata_path),
                )
            )

        manifest_path = manifest_writer.write(
            run_id=run_id,
            tool_version=self.TOOL_VERSION,
            config=self.config,
            inputs=manifest_entries,
            artifacts=artifacts,
            seed=self.config.seed,
        )

        summary_path: Path | None = None
        if self.config.features.enable_summary:
            summary_content = build_run_summary(
                config=self.config,
                run_id=run_id,
                manifest_path=manifest_path.relative_to(storage.run_dir),
                delta_path=delta_path.relative_to(storage.run_dir),
                metrics_path=metrics_path.relative_to(storage.run_dir) if metrics_path else None,
                badges={name: path.relative_to(storage.run_dir) for name, path in badges.items()},
                bundles=[path.relative_to(storage.run_dir) for path in bundles],
                graph_json=graph_jsonld.relative_to(storage.run_dir) if graph_jsonld else None,
                graph_graphml=graph_graphml.relative_to(storage.run_dir) if graph_graphml else None,
                graph_diff=graph_diff_path.relative_to(storage.run_dir) if graph_diff_path else None,
                diagrams={
                    name: output.relative_to(storage.run_dir)
                    for name, output in diagram_outputs.items()
                },
                diagram_sources={
                    name: source.relative_to(storage.run_dir)
                    for name, source in diagram_sources.items()
                },
                diagram_metadata=diagram_metadata_path.relative_to(storage.run_dir)
                if diagram_metadata_path
                else None,
                assets={
                    identifier: path.relative_to(storage.run_dir)
                    for identifier, path in asset_outputs.items()
                },
                asset_metadata={
                    identifier: path.relative_to(storage.run_dir)
                    for identifier, path in asset_metadata_paths.items()
                },
                asset_index=asset_index_path.relative_to(storage.run_dir)
                if asset_index_path
                else None,
                asset_cards={
                    identifier: path.relative_to(storage.run_dir)
                    for identifier, path in asset_card_outputs.items()
                },
                asset_card_metadata={
                    identifier: path.relative_to(storage.run_dir)
                    for identifier, path in asset_card_metadata_paths.items()
                },
                asset_card_index=asset_card_index_path.relative_to(storage.run_dir)
                if asset_card_index_path
                else None,
                explain_cards={
                    identifier: path.relative_to(storage.run_dir)
                    for identifier, path in explain_card_outputs.items()
                },
                explain_card_metadata={
                    identifier: path.relative_to(storage.run_dir)
                    for identifier, path in explain_card_metadata.items()
                },
                explain_card_index=explain_card_index_path.relative_to(storage.run_dir)
                if explain_card_index_path
                else None,
                gates=gates,
                tool_version=self.TOOL_VERSION,
                seed=self.config.seed,
            )
            summary_path = storage.summary_path()
            summary_path.write_text(summary_content, encoding="utf-8")

        outcome = RunOutcome(
            run_id=run_id,
            manifest_path=manifest_path,
            delta_path=delta_path,
            metrics_path=metrics_path,
            badges={name: path for name, path in badges.items()},
            bundles=bundles,
            gates=gates,
            summary_path=summary_path,
            artifacts=artifacts,
            delta=delta.to_dict(),
            graph_jsonld=graph_jsonld,
            graph_graphml=graph_graphml,
            graph_diff=graph_diff_path,
            diagrams={name: path for name, path in diagram_outputs.items()},
            diagram_sources={name: path for name, path in diagram_sources.items()},
            diagram_metadata=diagram_metadata_path,
            explain_cards={identifier: path for identifier, path in explain_card_outputs.items()},
            explain_card_metadata={
                identifier: path for identifier, path in explain_card_metadata.items()
            },
            explain_card_index=explain_card_index_path,
            assets={identifier: path for identifier, path in asset_outputs.items()},
            asset_metadata={
                identifier: path for identifier, path in asset_metadata_paths.items()
            },
            asset_index=asset_index_path,
            asset_cards={identifier: path for identifier, path in asset_card_outputs.items()},
            asset_card_metadata={
                identifier: path for identifier, path in asset_card_metadata_paths.items()
            },
            asset_card_index=asset_card_index_path,
        )
        # Flush and detach file handler to persist logs
        try:
            file_handler.flush()
        finally:
            self.logger.removeHandler(file_handler)
            file_handler.close()
        return outcome

    def _filter_events(self, events: List["EntityEvent"]) -> List["EntityEvent"]:
        from .scanner import EntityEvent
        from ..domain.knowledge_graph import NodeType

        filtered: List[EntityEvent] = []
        options = self.config.graph
        for event in events:
            if not options.include_tests and event.is_test:
                continue
            if options.preset == "dependencies" and event.node_type != NodeType.MODULE:
                continue
            if options.preset == "tests" and not event.is_test:
                continue
            filtered.append(event)
        return filtered


def _status_for(record: FileRecord, delta) -> str:
    identifier = record.identifier
    if identifier in delta.added:
        return "added"
    if identifier in delta.changed:
        return "changed"
    return "unchanged"


def _to_datetime(timestamp: float):
    from datetime import UTC, datetime

    return datetime.fromtimestamp(timestamp, UTC)
