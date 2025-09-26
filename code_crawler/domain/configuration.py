"""Domain models for configuration management."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional


CONFIG_VERSION = "1.0.0"


@dataclass(frozen=True)
class PrivacySettings:
    """Privacy defaults for a crawler run."""

    allow_network: bool = False
    redact_secrets: bool = True
    redaction_patterns: List[str] = field(
        default_factory=lambda: [
            r"(?i)api[_-]?key",
            r"(?i)secret",
            r"(?i)password",
            r"(?:sk|pk)_[A-Za-z0-9]{16,64}",
        ]
    )
    retain_logs: bool = True


@dataclass(frozen=True)
class FeatureToggles:
    """Opt-in feature toggles for optional behaviours."""

    enable_metrics: bool = True
    enable_badges: bool = True
    enable_bundles: bool = True
    enable_diagrams: bool = True
    enable_summary: bool = True


@dataclass(frozen=True)
class ThresholdConfig:
    """Optional quality gate thresholds."""

    min_coverage: Optional[float] = None
    max_failed_tests: Optional[int] = None
    max_lint_warnings: Optional[int] = None
    max_critical_vulnerabilities: Optional[int] = None


@dataclass(frozen=True)
class SourceOptions:
    """Rules controlling which files are analysed."""

    root: Path
    include: List[str] = field(default_factory=list)
    ignore: List[str] = field(default_factory=list)
    follow_symlinks: bool = False
    incremental: bool = True


@dataclass(frozen=True)
class OutputOptions:
    """Organisation of run outputs."""

    base_directory: Path = Path("code_crawler_runs")
    retention: int = 5
    manifest_name: str = "manifest.json"
    summary_name: str = "summary.md"


@dataclass(frozen=True)
class MetricSources:
    """Metric source configuration."""

    test_results: List[Path] = field(default_factory=list)
    coverage_reports: List[Path] = field(default_factory=list)
    lint_reports: List[Path] = field(default_factory=list)
    security_reports: List[Path] = field(default_factory=list)


@dataclass(frozen=True)
class CrawlerConfig:
    """Aggregated configuration for a crawler run."""

    version: str = CONFIG_VERSION
    privacy: PrivacySettings = field(default_factory=PrivacySettings)
    features: FeatureToggles = field(default_factory=FeatureToggles)
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    sources: SourceOptions = field(default_factory=lambda: SourceOptions(root=Path.cwd()))
    output: OutputOptions = field(default_factory=OutputOptions)
    metrics: MetricSources = field(default_factory=MetricSources)
    seed: Optional[int] = None

    def to_dict(self) -> Dict[str, object]:
        """Convert the configuration into a JSON serialisable structure."""

        def dataclass_to_dict(obj):
            if hasattr(obj, "__dict__"):
                return {
                    key: dataclass_to_dict(value)
                    for key, value in obj.__dict__.items()
                }
            if isinstance(obj, list):
                return [dataclass_to_dict(item) for item in obj]
            if isinstance(obj, Path):
                return str(obj)
            if isinstance(obj, timedelta):
                return obj.total_seconds()
            return obj

        return dataclass_to_dict(self)


def with_cli_overrides(base_config: CrawlerConfig, overrides: Dict[str, object]) -> CrawlerConfig:
    """Create a new configuration with CLI overrides applied."""

    privacy = base_config.privacy
    if overrides.get("allow_network") is not None:
        privacy = PrivacySettings(
            allow_network=overrides["allow_network"],
            redact_secrets=privacy.redact_secrets,
            redaction_patterns=privacy.redaction_patterns,
            retain_logs=privacy.retain_logs,
        )

    features = base_config.features
    if any(overrides.get(toggle) is not None for toggle in ("enable_metrics", "enable_badges", "enable_bundles", "enable_diagrams", "enable_summary")):
        features = FeatureToggles(
            enable_metrics=overrides.get("enable_metrics", features.enable_metrics),
            enable_badges=overrides.get("enable_badges", features.enable_badges),
            enable_bundles=overrides.get("enable_bundles", features.enable_bundles),
            enable_diagrams=overrides.get("enable_diagrams", features.enable_diagrams),
            enable_summary=overrides.get("enable_summary", features.enable_summary),
        )

    output = base_config.output
    if overrides.get("retention") is not None:
        output = OutputOptions(
            base_directory=output.base_directory,
            retention=int(overrides["retention"]),
            manifest_name=output.manifest_name,
            summary_name=output.summary_name,
        )

    sources = base_config.sources
    incremental = overrides.get("incremental")
    force_rebuild = overrides.get("force_rebuild")
    if incremental is not None or force_rebuild:
        sources = SourceOptions(
            root=sources.root,
            include=sources.include,
            ignore=sources.ignore,
            follow_symlinks=sources.follow_symlinks,
            incremental=False if force_rebuild else bool(incremental),
        )

    return CrawlerConfig(
        version=base_config.version,
        privacy=privacy,
        features=features,
        thresholds=base_config.thresholds,
        sources=sources,
        output=output,
        metrics=base_config.metrics,
        seed=overrides.get("seed", base_config.seed),
    )
