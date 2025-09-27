from pathlib import Path

from code_crawler.application.scanner import SourceWalker, update_cache
from code_crawler.domain.configuration import CrawlerConfig, SourceOptions


def create_config(root: Path) -> CrawlerConfig:
    config = CrawlerConfig()
    return CrawlerConfig(
        privacy=config.privacy,
        features=config.features,
        thresholds=config.thresholds,
        sources=SourceOptions(root=root, include=[], ignore=[]),
        output=config.output,
        metrics=config.metrics,
        seed=config.seed,
        version=config.version,
    )


def test_source_walker_respects_cache(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
    config = create_config(tmp_path)
    walker = SourceWalker(config, cache_index={})
    records, delta = walker.walk()
    assert len(records) == 1
    cache_file = tmp_path.parent / "cache.txt"
    cache_index = update_cache(cache_file, records)
    walker_cached = SourceWalker(config, cache_index=cache_index)
    records_cached, delta_cached = walker_cached.walk()
    assert records_cached[0].cached is True
    assert delta_cached.unchanged == [records_cached[0].identifier]


def test_emit_events_uses_cache(tmp_path: Path) -> None:
    module = tmp_path / "module.py"
    module.write_text("def example():\n    return 1\n", encoding="utf-8")
    config = create_config(tmp_path)
    walker = SourceWalker(config, cache_index={})
    records, _ = walker.walk()
    walker.emit_events(records)
    stats_after_first = walker.instrumentation()
    walker.emit_events(records)
    stats_after_second = walker.instrumentation()
    assert stats_after_second["cache_hits"] >= stats_after_first["cache_hits"]
