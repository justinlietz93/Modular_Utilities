from code_crawler.application.metrics import CoverageSummary, IssueSummary, MetricsBundle, TestSummary
from code_crawler.application.quality_gates import GateEvaluator
from code_crawler.domain.configuration import CrawlerConfig, ThresholdConfig


def test_gate_evaluator_flags_low_coverage() -> None:
    config = CrawlerConfig(thresholds=ThresholdConfig(min_coverage=90.0))
    metrics = MetricsBundle(
        tests=TestSummary(passed=1, failed=0, skipped=0, duration=0.1),
        coverage=CoverageSummary(covered_lines=45, total_lines=100),
        lint=None,
        security=None,
    )
    evaluator = GateEvaluator(config)
    result = evaluator.evaluate(metrics)
    assert result.passed is False
    assert any("Coverage" in reason for reason in result.reasons)


def test_gate_evaluator_passes_all_thresholds() -> None:
    config = CrawlerConfig(
        thresholds=ThresholdConfig(
            min_coverage=70.0,
            max_failed_tests=1,
            max_lint_warnings=5,
            max_critical_vulnerabilities=0,
        )
    )
    metrics = MetricsBundle(
        tests=TestSummary(passed=2, failed=0, skipped=0, duration=0.2),
        coverage=CoverageSummary(covered_lines=80, total_lines=100),
        lint=IssueSummary(counts_by_severity={"warning": 1}, counts_by_rule={"X": 1}),
        security=IssueSummary(counts_by_severity={"warning": 0}, counts_by_rule={}),
    )
    evaluator = GateEvaluator(config)
    result = evaluator.evaluate(metrics)
    assert result.passed is True


def test_gate_evaluator_flags_lint_and_security() -> None:
    config = CrawlerConfig(
        thresholds=ThresholdConfig(max_lint_warnings=0, max_critical_vulnerabilities=0)
    )
    metrics = MetricsBundle(
        tests=None,
        coverage=None,
        lint=IssueSummary(counts_by_severity={"warning": 2}, counts_by_rule={}),
        security=IssueSummary(counts_by_severity={"critical": 1}, counts_by_rule={}),
    )
    evaluator = GateEvaluator(config)
    result = evaluator.evaluate(metrics)
    assert result.passed is False
    assert any("Lint" in reason or "Critical" in reason for reason in result.reasons)
