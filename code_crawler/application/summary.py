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
    if gates:
        lines.extend(["", "## Quality Gates", "", f"- Passed: {'yes' if gates.passed else 'no'}"])
        for reason in gates.reasons:
            lines.append(f"  - {reason}")
    lines.append("")
    return "\n".join(lines)
