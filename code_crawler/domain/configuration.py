"""Domain models for configuration management."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple


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
    enable_graph: bool = True
    enable_explain_cards: bool = False
    enable_assets: bool = False


@dataclass(frozen=True)
class DiagramOptions:
    """Configuration for diagram generation."""

    presets: List[str] = field(
        default_factory=lambda: ["architecture", "dependencies", "tests"]
    )
    output_formats: List[str] = field(default_factory=lambda: ["svg"])
    concurrency: int = 1
    theme: str = "auto"


@dataclass(frozen=True)
class ExplainCardOptions:
    """Configuration for explain card generation."""

    scopes: List[str] = field(
        default_factory=lambda: ["architecture", "quality", "tests"]
    )
    mode: str = "template"
    require_review: bool = True
    enable_local_model: bool = False
    local_model_path: Optional[Path] = None


@dataclass(frozen=True)
class AssetOptions:
    """Configuration for non-code asset processing."""

    document_extensions: Tuple[str, ...] = (
        ".md",
        ".rst",
        ".txt",
        ".pdf",
    )
    image_extensions: Tuple[str, ...] = (
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
    )
    audio_extensions: Tuple[str, ...] = (
        ".wav",
        ".mp3",
        ".ogg",
    )
    video_extensions: Tuple[str, ...] = (
        ".mp4",
        ".mov",
        ".mkv",
    )
    max_preview_chars: int = 600
    generate_cards: bool = True


@dataclass(frozen=True)
class GraphOptions:
    """Configuration for knowledge graph generation."""

    preset: str = "full"
    enable_diff: bool = True
    include_tests: bool = True


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
    graph: GraphOptions = field(default_factory=GraphOptions)
    diagrams: DiagramOptions = field(default_factory=DiagramOptions)
    explain_cards: ExplainCardOptions = field(default_factory=ExplainCardOptions)
    assets: AssetOptions = field(default_factory=AssetOptions)
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
    if any(
        overrides.get(toggle) is not None
        for toggle in (
            "enable_metrics",
            "enable_badges",
            "enable_bundles",
            "enable_diagrams",
            "enable_summary",
            "enable_graph",
            "enable_explain_cards",
            "enable_assets",
        )
    ):
        features = FeatureToggles(
            enable_metrics=overrides.get("enable_metrics", features.enable_metrics),
            enable_badges=overrides.get("enable_badges", features.enable_badges),
            enable_bundles=overrides.get("enable_bundles", features.enable_bundles),
            enable_diagrams=overrides.get("enable_diagrams", features.enable_diagrams),
            enable_summary=overrides.get("enable_summary", features.enable_summary),
            enable_graph=overrides.get("enable_graph", features.enable_graph),
            enable_explain_cards=overrides.get(
                "enable_explain_cards", features.enable_explain_cards
            ),
            enable_assets=overrides.get("enable_assets", features.enable_assets),
        )

    output = base_config.output
    # Allow overriding base_directory and retention independently
    if overrides.get("output_dir") is not None or overrides.get("retention") is not None:
        out_dir = overrides.get("output_dir", output.base_directory)
        if isinstance(out_dir, str):
            out_dir = Path(out_dir)
        output = OutputOptions(
            base_directory=out_dir,
            retention=int(overrides.get("retention", output.retention)),
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

    graph = base_config.graph
    if any(overrides.get(key) is not None for key in ("graph_preset", "graph_include_tests", "graph_enable_diff")):
        graph = GraphOptions(
            preset=overrides.get("graph_preset", graph.preset),
            enable_diff=overrides.get("graph_enable_diff", graph.enable_diff),
            include_tests=overrides.get("graph_include_tests", graph.include_tests),
        )

    diagrams = base_config.diagrams
    if any(
        overrides.get(key) is not None
        for key in (
            "diagram_presets",
            "diagram_formats",
            "diagram_concurrency",
            "diagram_theme",
        )
    ):
        diagrams = DiagramOptions(
            presets=overrides.get("diagram_presets", diagrams.presets),
            output_formats=overrides.get("diagram_formats", diagrams.output_formats),
            concurrency=overrides.get("diagram_concurrency", diagrams.concurrency),
            theme=overrides.get("diagram_theme", diagrams.theme),
        )

    explain_cards = base_config.explain_cards
    if any(
        overrides.get(key) is not None
        for key in (
            "card_scopes",
            "card_mode",
            "card_require_review",
            "card_enable_local_model",
            "card_model_path",
        )
    ):
        scopes = overrides.get("card_scopes", explain_cards.scopes)
        mode = overrides.get("card_mode", explain_cards.mode)
        require_review = overrides.get(
            "card_require_review", explain_cards.require_review
        )
        enable_local_model = overrides.get(
            "card_enable_local_model", explain_cards.enable_local_model
        )
        model_path = overrides.get("card_model_path", explain_cards.local_model_path)
        if isinstance(model_path, str):
            model_path = Path(model_path)
        explain_cards = ExplainCardOptions(
            scopes=list(scopes),
            mode=mode,
            require_review=bool(require_review),
            enable_local_model=bool(enable_local_model),
            local_model_path=model_path,
        )

    assets = base_config.assets
    if overrides.get("asset_preview_chars") is not None or overrides.get(
        "asset_generate_cards"
    ) is not None:
        assets = AssetOptions(
            document_extensions=assets.document_extensions,
            image_extensions=assets.image_extensions,
            audio_extensions=assets.audio_extensions,
            video_extensions=assets.video_extensions,
            max_preview_chars=int(
                overrides.get("asset_preview_chars", assets.max_preview_chars)
            ),
            generate_cards=bool(
                overrides.get("asset_generate_cards", assets.generate_cards)
            ),
        )

    return CrawlerConfig(
        version=base_config.version,
        privacy=privacy,
        features=features,
        thresholds=base_config.thresholds,
        sources=sources,
        output=output,
        metrics=base_config.metrics,
        graph=graph,
        diagrams=diagrams,
        explain_cards=explain_cards,
        assets=assets,
        seed=overrides.get("seed", base_config.seed),
    )
