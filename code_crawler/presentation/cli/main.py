"""CLI entry point."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Dict, Iterable, Optional

from ...application.run_service import RunService
from ...domain.configuration import (
    CrawlerConfig,
    FeatureToggles,
    MetricSources,
    OutputOptions,
    PrivacySettings,
    SourceOptions,
    ThresholdConfig,
    with_cli_overrides,
)


def load_config(path: Optional[Path]) -> CrawlerConfig:
    if not path:
        return CrawlerConfig()
    data = json.loads(path.read_text(encoding="utf-8"))
    config = CrawlerConfig()
    if "privacy" in data:
        privacy = data["privacy"]
        config = replace(
            config,
            privacy=PrivacySettings(
                allow_network=privacy.get("allow_network", config.privacy.allow_network),
                redact_secrets=privacy.get("redact_secrets", config.privacy.redact_secrets),
                redaction_patterns=privacy.get("redaction_patterns", config.privacy.redaction_patterns),
                retain_logs=privacy.get("retain_logs", config.privacy.retain_logs),
            ),
        )
    if "features" in data:
        features = data["features"]
        config = replace(
            config,
            features=FeatureToggles(
                enable_metrics=features.get("enable_metrics", config.features.enable_metrics),
                enable_badges=features.get("enable_badges", config.features.enable_badges),
                enable_bundles=features.get("enable_bundles", config.features.enable_bundles),
                enable_diagrams=features.get("enable_diagrams", config.features.enable_diagrams),
                enable_summary=features.get("enable_summary", config.features.enable_summary),
            ),
        )
    if "thresholds" in data:
        thresholds = data["thresholds"]
        config = replace(
            config,
            thresholds=ThresholdConfig(
                min_coverage=thresholds.get("min_coverage"),
                max_failed_tests=thresholds.get("max_failed_tests"),
                max_lint_warnings=thresholds.get("max_lint_warnings"),
                max_critical_vulnerabilities=thresholds.get("max_critical_vulnerabilities"),
            ),
        )
    if "output" in data:
        output = data["output"]
        config = replace(
            config,
            output=OutputOptions(
                base_directory=Path(output.get("base_directory", config.output.base_directory)),
                retention=output.get("retention", config.output.retention),
                manifest_name=output.get("manifest_name", config.output.manifest_name),
                summary_name=output.get("summary_name", config.output.summary_name),
            ),
        )
    if "metrics" in data:
        metrics = data["metrics"]
        config = replace(
            config,
            metrics=MetricSources(
                test_results=[Path(p) for p in metrics.get("test_results", [])],
                coverage_reports=[Path(p) for p in metrics.get("coverage_reports", [])],
                lint_reports=[Path(p) for p in metrics.get("lint_reports", [])],
                security_reports=[Path(p) for p in metrics.get("security_reports", [])],
            ),
        )
    if "seed" in data:
        config = replace(config, seed=data["seed"])
    return config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Supercharged code crawler")
    parser.add_argument("--input", default=".", help="Input directory")
    parser.add_argument("--config", type=Path, help="Configuration JSON file")
    parser.add_argument("--include", nargs="*", default=[], help="Include glob patterns")
    parser.add_argument("--ignore", nargs="*", default=[], help="Ignore glob patterns")
    parser.add_argument("--allow-network", action="store_true", help="Enable outbound network")
    parser.add_argument("--no-metrics", action="store_true", help="Disable metrics ingestion")
    parser.add_argument("--no-badges", action="store_true", help="Disable badge generation")
    parser.add_argument("--no-bundles", action="store_true", help="Disable bundle builder")
    parser.add_argument("--no-summary", action="store_true", help="Disable summary generation")
    parser.add_argument("--preset", default="all", help="Bundle preset to use")
    parser.add_argument("--no-incremental", action="store_true", help="Disable cache reuse")
    parser.add_argument("--force-rebuild", action="store_true", help="Force rebuild regardless of cache")
    parser.add_argument("--seed", type=int, help="Seed for deterministic operations")
    parser.add_argument("--retention", type=int, help="Retention count for runs")
    parser.add_argument("--metrics-test", nargs="*", default=[], help="JUnit XML files")
    parser.add_argument("--metrics-coverage", nargs="*", default=[], help="Coverage reports (lcov or Cobertura XML)")
    parser.add_argument("--metrics-lint", nargs="*", default=[], help="Lint SARIF reports")
    parser.add_argument("--metrics-security", nargs="*", default=[], help="Security SARIF reports")
    parser.add_argument("--min-coverage", type=float, help="Minimum coverage threshold")
    parser.add_argument("--max-failed-tests", type=int, help="Maximum failed tests")
    parser.add_argument("--max-lint-warnings", type=int, help="Maximum lint warnings")
    parser.add_argument("--max-critical-vulns", type=int, help="Maximum critical vulnerabilities")
    parser.add_argument("--version", action="store_true", help="Print version and exit")
    return parser


def apply_cli(config: CrawlerConfig, args: argparse.Namespace) -> CrawlerConfig:
    config = replace(
        config,
        sources=SourceOptions(
            root=Path(args.input).resolve(),
            include=args.include or config.sources.include,
            ignore=args.ignore or config.sources.ignore,
            follow_symlinks=config.sources.follow_symlinks,
            incremental=not args.no_incremental,
        ),
        metrics=MetricSources(
            test_results=[Path(p) for p in args.metrics_test] or config.metrics.test_results,
            coverage_reports=[Path(p) for p in args.metrics_coverage] or config.metrics.coverage_reports,
            lint_reports=[Path(p) for p in args.metrics_lint] or config.metrics.lint_reports,
            security_reports=[Path(p) for p in args.metrics_security] or config.metrics.security_reports,
        ),
    )

    overrides: Dict[str, object] = {
        "allow_network": args.allow_network,
        "enable_metrics": None if not args.no_metrics else False,
        "enable_badges": None if not args.no_badges else False,
        "enable_bundles": None if not args.no_bundles else False,
        "enable_summary": None if not args.no_summary else False,
        "retention": args.retention,
        "incremental": None if args.force_rebuild else (not args.no_incremental),
        "force_rebuild": args.force_rebuild,
        "seed": args.seed,
    }

    config = with_cli_overrides(config, overrides)
    thresholds = ThresholdConfig(
        min_coverage=args.min_coverage if args.min_coverage is not None else config.thresholds.min_coverage,
        max_failed_tests=args.max_failed_tests if args.max_failed_tests is not None else config.thresholds.max_failed_tests,
        max_lint_warnings=args.max_lint_warnings if args.max_lint_warnings is not None else config.thresholds.max_lint_warnings,
        max_critical_vulnerabilities=args.max_critical_vulns if args.max_critical_vulns is not None else config.thresholds.max_critical_vulnerabilities,
    )
    config = replace(config, thresholds=thresholds)
    if args.seed is not None:
        config = replace(config, seed=args.seed)
    return config


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.version:
        print(RunService.TOOL_VERSION)
        return 0

    config = load_config(args.config)
    config = apply_cli(config, args)

    service = RunService(config)
    outcome = service.execute(preset=args.preset, incremental=config.sources.incremental)
    print(f"Run {outcome.run_id} complete. Manifest: {outcome.manifest_path}")
    if outcome.gates and not outcome.gates.passed:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
