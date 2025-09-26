import json
from pathlib import Path

from code_crawler.domain.configuration import CrawlerConfig
from code_crawler.presentation.cli.main import (
    apply_cli,
    build_parser,
    load_config,
    main,
)


def test_cli_version_output(capsys) -> None:
    exit_code = main(["--version"])
    captured = capsys.readouterr().out.strip()
    assert exit_code == 0
    assert captured == "0.2.0"


def test_load_config_reads_json(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"privacy": {"allow_network": True}}), encoding="utf-8")
    config = load_config(config_path)
    assert config.privacy.allow_network is True


def test_load_config_reads_graph_and_diagram_options(tmp_path: Path) -> None:
    payload = {
        "graph": {"preset": "tests", "enable_diff": False, "include_tests": False},
        "diagrams": {
            "presets": ["architecture"],
            "output_formats": ["png"],
            "concurrency": 2,
            "theme": "dark",
        },
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(payload), encoding="utf-8")
    config = load_config(config_path)
    assert config.graph.preset == "tests"
    assert config.graph.enable_diff is False
    assert config.graph.include_tests is False
    assert config.diagrams.presets == ["architecture"]
    assert config.diagrams.output_formats == ["png"]
    assert config.diagrams.concurrency == 2
    assert config.diagrams.theme == "dark"


def test_apply_cli_overrides(tmp_path: Path) -> None:
    config = CrawlerConfig()
    args = type(
        "Args",
        (),
        {
            "input": str(tmp_path),
            "include": ["**/*.py"],
            "ignore": [],
            "no_incremental": False,
            "metrics_test": [],
            "metrics_coverage": [],
            "metrics_lint": [],
            "metrics_security": [],
            "allow_network": True,
            "no_metrics": False,
            "no_badges": True,
            "no_bundles": False,
            "no_diagrams": False,
            "no_summary": True,
            "no_graph": False,
            "explain_cards": False,
            "no_explain_cards": False,
            "assets": False,
            "no_assets": False,
            "retention": 2,
            "force_rebuild": False,
            "seed": 99,
            "min_coverage": 80.0,
            "max_failed_tests": 0,
            "max_lint_warnings": 0,
            "max_critical_vulns": 0,
            "graph_scope": "code",
            "graph_include_tests": False,
            "graph_no_tests": True,
            "graph_diff": False,
            "no_graph_diff": True,
            "diagram_presets": ["dependencies"],
            "diagram_formats": ["SVG"],
            "diagram_concurrency": 3,
            "diagram_theme": "light",
            "asset_preview": None,
            "asset_cards": False,
            "no_asset_cards": False,
            "card_mode": None,
            "card_scopes": None,
            "card_require_review": False,
            "card_auto_approve": False,
            "card_enable_local_model": False,
            "card_local_model": None,
        },
    )
    updated = apply_cli(config, args)
    assert updated.privacy.allow_network is True
    assert updated.features.enable_badges is False
    assert updated.features.enable_summary is False
    assert updated.features.enable_graph is True
    assert updated.features.enable_explain_cards is False
    assert updated.output.retention == 2
    assert updated.thresholds.min_coverage == 80.0
    assert updated.graph.preset == "code"
    assert updated.graph.include_tests is False
    assert updated.graph.enable_diff is False
    assert updated.diagrams.presets == ["dependencies"]
    assert updated.diagrams.output_formats == ["svg"]
    assert updated.diagrams.concurrency == 3
    assert updated.diagrams.theme == "light"
    assert updated.explain_cards.mode == "template"


def test_build_parser_supports_graph_and_diagram_flags() -> None:
    parser = build_parser()
    args = parser.parse_args([
        "--graph-scope",
        "tests",
        "--graph-no-tests",
        "--no-graph-diff",
        "--diagram-preset",
        "architecture",
        "--diagram-format",
        "png",
        "--diagram-theme",
        "dark",
        "--explain-cards",
        "--card-mode",
        "local-llm",
        "--card-scope",
        "architecture",
        "--card-auto-approve",
        "--card-enable-local-model",
        "--card-local-model",
        "weights.bin",
    ])
    assert args.graph_scope == "tests"
    assert args.graph_no_tests is True
    assert args.no_graph_diff is True
    assert args.diagram_presets == ["architecture"]
    assert args.diagram_formats == ["png"]
    assert args.diagram_theme == "dark"
    assert args.explain_cards is True
    assert args.card_mode == "local-llm"
    assert args.card_scopes == ["architecture"]
    assert args.card_auto_approve is True
    assert args.card_enable_local_model is True
    assert args.card_local_model == Path("weights.bin")
