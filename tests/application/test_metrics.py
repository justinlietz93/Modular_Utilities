import json
from pathlib import Path

from code_crawler.application.metrics import CoverageSummary, MetricsAggregator, parse_cobertura, parse_junit_report
from code_crawler.domain.configuration import CrawlerConfig, MetricSources


def test_parse_junit_report_counts(tmp_path: Path) -> None:
    xml = """<testsuite tests='2' failures='1' skipped='0' errors='0' time='1.2'></testsuite>"""
    report = tmp_path / "report.xml"
    report.write_text(xml, encoding="utf-8")
    summary = parse_junit_report(report)
    assert summary.total == 2
    assert summary.failed == 1


def test_metrics_aggregator_reads_reports(tmp_path: Path) -> None:
    junit = tmp_path / "junit.xml"
    junit.write_text("""<testsuite tests='1' failures='0' skipped='0' errors='0' time='0.1'></testsuite>""", encoding="utf-8")
    coverage = tmp_path / "coverage.lcov"
    coverage.write_text("\n".join(["TN:", "SF:file.py", "DA:1,1", "DA:2,0", "end_of_record"]), encoding="utf-8")
    sarif = tmp_path / "lint.sarif"
    sarif.write_text(json.dumps({"runs": [{"results": [{"level": "warning", "ruleId": "E001"}]}]}), encoding="utf-8")
    security = tmp_path / "security.sarif"
    security.write_text(json.dumps({"runs": [{"results": [{"level": "error", "ruleId": "S001"}]}]}), encoding="utf-8")

    config = CrawlerConfig()
    config = CrawlerConfig(
        version=config.version,
        privacy=config.privacy,
        features=config.features,
        thresholds=config.thresholds,
        sources=config.sources,
        output=config.output,
        metrics=MetricSources(
            test_results=[junit],
            coverage_reports=[coverage],
            lint_reports=[sarif],
            security_reports=[security],
        ),
        seed=config.seed,
    )

    aggregator = MetricsAggregator(config)
    bundle = aggregator.collect()
    assert bundle.tests and bundle.tests.total == 1
    assert bundle.coverage and round(bundle.coverage.percent, 1) == 50.0
    assert bundle.lint and bundle.lint.counts_by_severity["warning"] == 1
    assert bundle.security and bundle.security.counts_by_severity["error"] == 1


def test_parse_cobertura_report(tmp_path: Path) -> None:
    cobertura = tmp_path / "coverage.xml"
    cobertura.write_text("""<coverage lines-valid='10' lines-covered='7'></coverage>""", encoding="utf-8")
    summary = parse_cobertura(cobertura)
    assert summary.total_lines == 10
    assert summary.covered_lines == 7


def test_coverage_percent_handles_empty_total() -> None:
    summary = CoverageSummary(covered_lines=0, total_lines=0)
    assert summary.percent == 100.0


def test_metrics_aggregator_handles_missing_reports(tmp_path: Path) -> None:
    config = CrawlerConfig()
    aggregator = MetricsAggregator(config)
    bundle = aggregator.collect()
    assert bundle.tests is None
    assert bundle.coverage is None
