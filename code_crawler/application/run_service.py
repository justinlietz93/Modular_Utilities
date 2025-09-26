"""High level run orchestration."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from ..domain.configuration import CrawlerConfig
from ..domain.manifest import ArtifactRecord, ManifestEntry
from ..infrastructure.filesystem.manifest_writer import ManifestWriter
from ..infrastructure.filesystem.run_storage import RunStorage
from ..shared.logging import configure_logger
from .bundles import BundleBuilder
from .delta import write_delta_report
from .metrics import MetricsAggregator, MetricsBundle, generate_badge
from .quality_gates import GateEvaluator, GateResult
from .scanner import FileRecord, SourceWalker, load_cache, update_cache
from .summary import build_run_summary


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

        cache_index = {}
        if incremental:
            cache_index = load_cache(self.cache_path)

        walker = SourceWalker(self.config, cache_index)
        records, delta = walker.walk()
        self.logger.info("Discovered %s files", len(records))

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

        manifest_writer = ManifestWriter(storage.manifest_path())
        artifacts: List[ArtifactRecord] = []
        if metrics_path:
            artifacts.append(ArtifactRecord(path=str(metrics_path.relative_to(storage.run_dir)), artifact_type="metrics", digest=ManifestWriter.digest_file(metrics_path)))
        for badge_name, badge_path in badges.items():
            artifacts.append(ArtifactRecord(path=str(badge_path.relative_to(storage.run_dir)), artifact_type=f"badge:{badge_name}", digest=ManifestWriter.digest_file(badge_path)))
        for bundle_path in bundles:
            artifacts.append(ArtifactRecord(path=str(bundle_path.relative_to(storage.run_dir)), artifact_type="bundle", digest=ManifestWriter.digest_file(bundle_path)))
        artifacts.append(ArtifactRecord(path=str(delta_path.relative_to(storage.run_dir)), artifact_type="delta", digest=ManifestWriter.digest_file(delta_path)))

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
                gates=gates,
                tool_version=self.TOOL_VERSION,
                seed=self.config.seed,
            )
            summary_path = storage.summary_path()
            summary_path.write_text(summary_content, encoding="utf-8")

        return RunOutcome(
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
        )


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
