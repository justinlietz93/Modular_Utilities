import json
import json
from pathlib import Path

from code_crawler.application.run_service import RunService
from code_crawler.domain.configuration import (
    CrawlerConfig,
    MetricSources,
    OutputOptions,
    SourceOptions,
    ThresholdConfig,
)


def build_config(root: Path) -> CrawlerConfig:
    config = CrawlerConfig()
    return CrawlerConfig(
        version=config.version,
        privacy=config.privacy,
        features=config.features,
        thresholds=config.thresholds,
        sources=SourceOptions(root=root, include=[], ignore=[]),
        output=OutputOptions(base_directory=root / "runs"),
        metrics=MetricSources(),
        seed=42,
    )


def test_run_service_creates_manifest(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    (source / "file.py").write_text("print('hello')\n", encoding="utf-8")

    junit = source / "junit.xml"
    junit.write_text("""<testsuite tests='1' failures='0' skipped='0' errors='0' time='0.1'></testsuite>""", encoding="utf-8")
    coverage = source / "coverage.lcov"
    coverage.write_text("\n".join(["TN:", "SF:file.py", "DA:1,1", "end_of_record"]), encoding="utf-8")
    sarif = source / "lint.sarif"
    sarif.write_text(json.dumps({"runs": [{"results": [{"level": "warning", "ruleId": "L001"}]}]}), encoding="utf-8")

    config = build_config(source)
    config = CrawlerConfig(
        version=config.version,
        privacy=config.privacy,
        features=config.features,
        thresholds=ThresholdConfig(min_coverage=50.0, max_failed_tests=0, max_lint_warnings=5),
        sources=config.sources,
        output=config.output,
        metrics=MetricSources(
            test_results=[junit],
            coverage_reports=[coverage],
            lint_reports=[sarif],
            security_reports=[],
        ),
        seed=config.seed,
    )
    service = RunService(config)
    outcome = service.execute(preset="all")

    assert outcome.manifest_path.exists()
    manifest_data = json.loads(outcome.manifest_path.read_text(encoding="utf-8"))
    assert manifest_data["run_id"] == outcome.run_id
    assert outcome.summary_path and outcome.summary_path.exists()
    assert outcome.gates and outcome.gates.passed is True
    assert outcome.diagrams
    assert all(path.exists() for path in outcome.diagrams.values())
    assert outcome.diagram_metadata and outcome.diagram_metadata.exists()
    assert outcome.explain_cards == {}
    assert outcome.explain_card_metadata == {}
    assert outcome.explain_card_index is None
    assert outcome.assets == {}
    assert outcome.asset_metadata == {}
    assert outcome.asset_index is None
    assert outcome.asset_cards == {}
    assert outcome.asset_card_metadata == {}
    assert outcome.asset_card_index is None
