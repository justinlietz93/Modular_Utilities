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
        graph_json=None,
        graph_graphml=None,
        graph_diff=None,
        diagrams={"architecture": Path("diagrams/architecture.svg")},
        diagram_sources={"architecture": Path("diagrams/architecture.mmd")},
        diagram_metadata=Path("diagrams/metadata.json"),
        assets={"asset:1": Path("assets/asset.txt")},
        asset_metadata={"asset:1": Path("assets/asset.json")},
        asset_index=Path("assets/index.json"),
        asset_cards={"asset-card:1": Path("assets/cards/asset_card.md")},
        asset_card_metadata={"asset-card:1": Path("assets/cards/asset_card.json")},
        asset_card_index=Path("assets/cards/index.json"),
        explain_cards={"card:architecture:123": Path("cards/card_architecture.md")},
        explain_card_metadata={"card:architecture:123": Path("cards/card_architecture.json")},
        explain_card_index=Path("cards/index.json"),
        gates=GateResult(passed=False, reasons=["Coverage below minimum"]),
        tool_version="0.2.0",
        seed=42,
    )
    assert "How it was made" in summary
    assert "Coverage below minimum" in summary
    assert "Diagram (architecture)" in summary
    assert "Asset index" in summary
    assert "Asset card index" in summary
    assert "Explain card" in summary
    assert "Explain card index" in summary
