from pathlib import Path

from code_crawler.domain.configuration import CrawlerConfig, OutputOptions
from code_crawler.infrastructure.filesystem.run_storage import RunStorage


def test_run_storage_retention(tmp_path: Path) -> None:
    config = CrawlerConfig(output=OutputOptions(base_directory=tmp_path, retention=1))
    first = RunStorage(config)
    (first.run_dir / "manifests").mkdir(exist_ok=True)
    first.cleanup_old_runs()
    second = RunStorage(config)
    second.cleanup_old_runs()
    runs = sorted(p for p in tmp_path.iterdir() if p.is_dir())
    assert len(runs) == 1
    assert runs[0] == second.run_dir
    artifact_path = second.record_artifact(Path("bundles/test.txt"), b"data")
    listed = list(second.list_artifacts())
    assert Path("bundles/test.txt") in listed
    assert artifact_path.exists()
