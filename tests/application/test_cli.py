import json
from pathlib import Path

from code_crawler.domain.configuration import CrawlerConfig
from code_crawler.presentation.cli.main import apply_cli, load_config, main


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
            "no_summary": True,
            "retention": 2,
            "force_rebuild": False,
            "seed": 99,
            "min_coverage": 80.0,
            "max_failed_tests": 0,
            "max_lint_warnings": 0,
            "max_critical_vulns": 0,
        },
    )
    updated = apply_cli(config, args)
    assert updated.privacy.allow_network is True
    assert updated.features.enable_badges is False
    assert updated.features.enable_summary is False
    assert updated.output.retention == 2
    assert updated.thresholds.min_coverage == 80.0
