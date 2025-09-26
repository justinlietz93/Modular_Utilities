from pathlib import Path

from code_crawler.application.quality_gates import GateResult
from code_crawler.application.summary import build_run_summary
from code_crawler.domain.configuration import CrawlerConfig


def test_build_run_summary_includes_gates(tmp_path: Path) -> None:
    config = CrawlerConfig()
    manifest = Path("manifests/manifest.json")
    delta = Path("delta/delta.json")
    badges = {"coverage": Path("badges/coverage.svg")}
    bundles = [Path("bundles/all_1.txt")]
    summary = build_run_summary(
        config=config,
        run_id="20240101-000000",
        manifest_path=manifest,
        delta_path=delta,
        metrics_path=Path("metrics/metrics.json"),
        badges=badges,
        bundles=bundles,
        gates=GateResult(passed=False, reasons=["Coverage below minimum"]),
        tool_version="0.2.0",
        seed=42,
    )
    assert "How it was made" in summary
    assert "Coverage below minimum" in summary
