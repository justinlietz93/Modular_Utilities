"""Run summary generation."""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, Iterable

from ..domain.configuration import CrawlerConfig
from .quality_gates import GateResult


def build_run_summary(
    config: CrawlerConfig,
    run_id: str,
    manifest_path: Path,
    delta_path: Path,
    metrics_path: Path | None,
    badges: Dict[str, Path],
    bundles: Iterable[Path],
    graph_json: Path | None,
    graph_graphml: Path | None,
    graph_diff: Path | None,
    diagrams: Dict[str, Path],
    diagram_sources: Dict[str, Path],
    diagram_metadata: Path | None,
    assets: Dict[str, Path],
    asset_metadata: Dict[str, Path],
    asset_index: Path | None,
    asset_cards: Dict[str, Path],
    asset_card_metadata: Dict[str, Path],
    asset_card_index: Path | None,
    explain_cards: Dict[str, Path],
    explain_card_metadata: Dict[str, Path],
    explain_card_index: Path | None,
    gates: GateResult | None,
    tool_version: str,
    seed: int | None,
) -> str:
    """Create markdown summary for the run."""

    lines = [
        f"# Code Crawler Run {run_id}",
        "",
        "## How it was made",
        "",
        f"- Tool version: {tool_version}",
        f"- Configuration version: {config.version}",
        f"- Seed: {seed if seed is not None else 'not set'}",
        f"- Generated at: {datetime.now(UTC).isoformat()}",
        f"- Privacy: {'network allowed' if config.privacy.allow_network else 'local only'}",
        "",
        "## Artifacts",
        "",
        f"- Manifest: [{manifest_path.name}]({manifest_path.as_posix()})",
        f"- Delta report: [{delta_path.name}]({delta_path.as_posix()})",
    ]
    if metrics_path:
        lines.append(f"- Metrics summary: [{metrics_path.name}]({metrics_path.as_posix()})")
    for name, badge_path in badges.items():
        lines.append(f"- Badge ({name}): [{badge_path.name}]({badge_path.as_posix()})")
    for bundle in bundles:
        lines.append(f"- Bundle: [{bundle.name}]({bundle.as_posix()})")
    if graph_json:
        lines.append(f"- Knowledge graph (JSON-LD): [{graph_json.name}]({graph_json.as_posix()})")
    if graph_graphml:
        lines.append(f"- Knowledge graph (GraphML): [{graph_graphml.name}]({graph_graphml.as_posix()})")
    if graph_diff:
        lines.append(f"- Knowledge graph diff: [{graph_diff.name}]({graph_diff.as_posix()})")
    for name, path in sorted(diagrams.items()):
        lines.append(f"- Diagram ({name}): [{path.name}]({path.as_posix()})")
    for name, source_path in sorted(diagram_sources.items()):
        lines.append(
            f"  - Source ({name}): [{source_path.name}]({source_path.as_posix()})"
        )
    if diagram_metadata:
        lines.append(
            f"- Diagram metadata: [{diagram_metadata.name}]({diagram_metadata.as_posix()})"
        )
    if asset_index:
        lines.append(
            f"- Asset index: [{asset_index.name}]({asset_index.as_posix()})"
        )
    for identifier, path in sorted(assets.items()):
        lines.append(
            f"- Asset ({identifier}): [{path.name}]({path.as_posix()})"
        )
        metadata_path = asset_metadata.get(identifier)
        if metadata_path:
            lines.append(
                f"  - Metadata: [{metadata_path.name}]({metadata_path.as_posix()})"
            )
    if asset_card_index:
        lines.append(
            f"- Asset card index: [{asset_card_index.name}]({asset_card_index.as_posix()})"
        )
    for identifier, path in sorted(asset_cards.items()):
        lines.append(
            f"- Asset card ({identifier}): [{path.name}]({path.as_posix()})"
        )
        metadata_path = asset_card_metadata.get(identifier)
        if metadata_path:
            lines.append(
                f"  - Metadata: [{metadata_path.name}]({metadata_path.as_posix()})"
            )
    if explain_card_index:
        lines.append(
            f"- Explain card index: [{explain_card_index.name}]({explain_card_index.as_posix()})"
        )
    for identifier, path in sorted(explain_cards.items()):
        lines.append(f"- Explain card ({identifier}): [{path.name}]({path.as_posix()})")
        metadata_path = explain_card_metadata.get(identifier)
        if metadata_path:
            lines.append(
                f"  - Metadata: [{metadata_path.name}]({metadata_path.as_posix()})"
            )
    if gates:
        lines.extend(["", "## Quality Gates", "", f"- Passed: {'yes' if gates.passed else 'no'}"])
        for reason in gates.reasons:
            lines.append(f"  - {reason}")
    lines.append("")
    return "\n".join(lines)
