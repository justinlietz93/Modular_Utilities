"""Metrics ingestion and aggregation."""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class TestSummary:
    passed: int
    failed: int
    skipped: int
    duration: float

    @property
    def total(self) -> int:
        return self.passed + self.failed + self.skipped


@dataclass(frozen=True)
class CoverageSummary:
    covered_lines: int
    total_lines: int

    @property
    def percent(self) -> float:
        if self.total_lines == 0:
            return 100.0
        return (self.covered_lines / self.total_lines) * 100


@dataclass(frozen=True)
class IssueSummary:
    counts_by_severity: Dict[str, int]
    counts_by_rule: Dict[str, int]


@dataclass(frozen=True)
class MetricsBundle:
    tests: TestSummary | None
    coverage: CoverageSummary | None
    lint: IssueSummary | None
    security: IssueSummary | None

    def to_dict(self) -> Dict[str, object]:
        payload: Dict[str, object] = {}
        if self.tests:
            payload["tests"] = {
                "passed": self.tests.passed,
                "failed": self.tests.failed,
                "skipped": self.tests.skipped,
                "duration": self.tests.duration,
                "total": self.tests.total,
            }
        if self.coverage:
            payload["coverage"] = {
                "covered": self.coverage.covered_lines,
                "total": self.coverage.total_lines,
                "percent": round(self.coverage.percent, 2),
            }
        if self.lint:
            payload["lint"] = {
                "severity": self.lint.counts_by_severity,
                "rules": self.lint.counts_by_rule,
            }
        if self.security:
            payload["security"] = {
                "severity": self.security.counts_by_severity,
                "rules": self.security.counts_by_rule,
            }
        return payload


def parse_junit_report(path: Path) -> TestSummary:
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    if root.tag == "testsuites":
        suites = root.findall("testsuite")
    else:
        suites = [root]
    passed = failed = skipped = 0
    duration = 0.0
    for suite in suites:
        passed += int(float(suite.attrib.get("tests", "0"))) - int(float(suite.attrib.get("failures", "0"))) - int(float(suite.attrib.get("skipped", "0"))) - int(float(suite.attrib.get("errors", "0")))
        failed += int(float(suite.attrib.get("failures", "0"))) + int(float(suite.attrib.get("errors", "0")))
        skipped += int(float(suite.attrib.get("skipped", "0")))
        duration += float(suite.attrib.get("time", "0"))
    passed = max(passed, 0)
    return TestSummary(passed=passed, failed=failed, skipped=skipped, duration=duration)


def parse_cobertura(path: Path) -> CoverageSummary:
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    lines_valid = int(float(root.attrib.get("lines-valid", "0")))
    lines_covered = int(float(root.attrib.get("lines-covered", "0")))
    return CoverageSummary(covered_lines=lines_covered, total_lines=lines_valid)


def parse_lcov(path: Path) -> CoverageSummary:
    covered = 0
    total = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("DA:"):
            _, data = line.split(":", 1)
            _, hit = data.split(",")
            total += 1
            if int(hit) > 0:
                covered += 1
    return CoverageSummary(covered_lines=covered, total_lines=total)


def parse_coverage(path: Path) -> CoverageSummary:
    if path.suffix == ".xml":
        return parse_cobertura(path)
    return parse_lcov(path)


def parse_sarif(path: Path) -> IssueSummary:
    data = json.loads(path.read_text(encoding="utf-8"))
    runs = data.get("runs", [])
    counts_by_severity: Dict[str, int] = {}
    counts_by_rule: Dict[str, int] = {}
    for run in runs:
        results = run.get("results", [])
        for result in results:
            level = result.get("level", "warning")
            rule_id = result.get("ruleId", "unknown")
            counts_by_severity[level] = counts_by_severity.get(level, 0) + 1
            counts_by_rule[rule_id] = counts_by_rule.get(rule_id, 0) + 1
    return IssueSummary(counts_by_severity=counts_by_severity, counts_by_rule=counts_by_rule)


class MetricsAggregator:
    """Aggregates metrics from configured sources."""

    def __init__(self, config) -> None:
        self.config = config

    def collect(self) -> MetricsBundle:
        tests = self._collect_tests()
        coverage = self._collect_coverage()
        lint = self._collect_issues(self.config.metrics.lint_reports)
        security = self._collect_issues(self.config.metrics.security_reports)
        return MetricsBundle(tests=tests, coverage=coverage, lint=lint, security=security)

    def _collect_tests(self) -> TestSummary | None:
        summaries: List[TestSummary] = []
        for report in self.config.metrics.test_results:
            if report.exists():
                summaries.append(parse_junit_report(report))
        if not summaries:
            return None
        passed = sum(s.passed for s in summaries)
        failed = sum(s.failed for s in summaries)
        skipped = sum(s.skipped for s in summaries)
        duration = sum(s.duration for s in summaries)
        return TestSummary(passed=passed, failed=failed, skipped=skipped, duration=duration)

    def _collect_coverage(self) -> CoverageSummary | None:
        summaries: List[CoverageSummary] = []
        for report in self.config.metrics.coverage_reports:
            if report.exists():
                summaries.append(parse_coverage(report))
        if not summaries:
            return None
        covered = sum(s.covered_lines for s in summaries)
        total = sum(s.total_lines for s in summaries)
        return CoverageSummary(covered_lines=covered, total_lines=total)

    def _collect_issues(self, paths: Iterable[Path]) -> IssueSummary | None:
        totals: Dict[str, int] = {}
        rules: Dict[str, int] = {}
        for report in paths:
            if not report.exists():
                continue
            summary = parse_sarif(report)
            for severity, count in summary.counts_by_severity.items():
                totals[severity] = totals.get(severity, 0) + count
            for rule, count in summary.counts_by_rule.items():
                rules[rule] = rules.get(rule, 0) + count
        if not totals and not rules:
            return None
        return IssueSummary(counts_by_severity=totals, counts_by_rule=rules)


def generate_badge(label: str, value: str, color: str = "blue") -> str:
    """Generate a simple SVG badge."""

    return (
        "<svg xmlns='http://www.w3.org/2000/svg' width='140' height='20'>"
        "<rect rx='4' width='140' height='20' fill='#555'/>"
        f"<rect rx='4' x='70' width='70' height='20' fill='{color}'/>"
        "<g fill='#fff' text-anchor='middle' font-family='Verdana' font-size='11'>"
        f"<text x='35' y='14'>{label}</text>"
        f"<text x='105' y='14'>{value}</text>"
        "</g></svg>"
    )
