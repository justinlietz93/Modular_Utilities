from pathlib import Path

from code_crawler.application.bundles import BundleBuilder
from code_crawler.application.scanner import FileRecord


def test_bundle_builder_splits_large_files(tmp_path: Path) -> None:
    file_a = tmp_path / "a.txt"
    file_b = tmp_path / "b.txt"
    file_a.write_text("first\n" * 20, encoding="utf-8")
    file_b.write_text("second\n" * 20, encoding="utf-8")
    file_c = tmp_path / "c.txt"
    file_c.write_text("\n", encoding="utf-8")

    record_a = FileRecord(
        identifier="a.txt",
        path=file_a,
        size=file_a.stat().st_size,
        digest="a",
        modified=file_a.stat().st_mtime,
        cached=False,
    )
    record_b = FileRecord(
        identifier="b.txt",
        path=file_b,
        size=file_b.stat().st_size,
        digest="b",
        modified=file_b.stat().st_mtime,
        cached=False,
    )

    record_c = FileRecord(
        identifier="c.txt",
        path=file_c,
        size=file_c.stat().st_size,
        digest="c",
        modified=file_c.stat().st_mtime,
        cached=False,
    )

    builder = BundleBuilder(max_bytes=200, max_lines=10)
    bundles = builder.build("all", [record_a, record_b, record_c])
    assert len(bundles) == 3
    assert bundles[0].files[0].identifier == "a.txt"
    assert bundles[1].files[0].identifier == "b.txt"
    assert bundles[2].files[0].synopsis == ""
