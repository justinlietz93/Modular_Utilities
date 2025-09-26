from pathlib import Path

from code_crawler.domain.configuration import (
    CrawlerConfig,
    FeatureToggles,
    with_cli_overrides,
)


def test_with_cli_overrides_allows_network_toggle(tmp_path: Path) -> None:
    config = CrawlerConfig()
    overrides = {"allow_network": True, "seed": 123}
    updated = with_cli_overrides(config, overrides)
    assert updated.privacy.allow_network is True
    assert updated.seed == 123


def test_with_cli_overrides_disables_features() -> None:
    config = CrawlerConfig(features=FeatureToggles())
    overrides = {"enable_metrics": False, "enable_summary": False}
    updated = with_cli_overrides(config, overrides)
    assert updated.features.enable_metrics is False
    assert updated.features.enable_summary is False
