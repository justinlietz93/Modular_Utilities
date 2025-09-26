"""Quality gate evaluation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from ..domain.configuration import CrawlerConfig
from .metrics import MetricsBundle


@dataclass(frozen=True)
class GateResult:
    passed: bool
    reasons: List[str]

    def to_dict(self) -> Dict[str, object]:
        return {"passed": self.passed, "reasons": self.reasons}


class GateEvaluator:
    """Evaluate metrics against configured thresholds."""

    def __init__(self, config: CrawlerConfig) -> None:
        self.config = config

    def evaluate(self, metrics: MetricsBundle) -> GateResult:
        reasons: List[str] = []
        thresholds = self.config.thresholds
        if thresholds.min_coverage is not None and metrics.coverage:
            if metrics.coverage.percent < thresholds.min_coverage:
                reasons.append(
                    f"Coverage {metrics.coverage.percent:.2f}% below minimum {thresholds.min_coverage:.2f}%"
                )
        if thresholds.max_failed_tests is not None and metrics.tests:
            if metrics.tests.failed > thresholds.max_failed_tests:
                reasons.append(
                    f"Failed tests {metrics.tests.failed} exceed {thresholds.max_failed_tests}"
                )
        if thresholds.max_lint_warnings is not None and metrics.lint:
            warnings = metrics.lint.counts_by_severity.get("warning", 0)
            if warnings > thresholds.max_lint_warnings:
                reasons.append(
                    f"Lint warnings {warnings} exceed {thresholds.max_lint_warnings}"
                )
        if thresholds.max_critical_vulnerabilities is not None and metrics.security:
            critical = metrics.security.counts_by_severity.get("error", 0) + metrics.security.counts_by_severity.get("critical", 0)
            if critical > thresholds.max_critical_vulnerabilities:
                reasons.append(
                    f"Critical vulnerabilities {critical} exceed {thresholds.max_critical_vulnerabilities}"
                )
        passed = not reasons
        return GateResult(passed=passed, reasons=reasons)
