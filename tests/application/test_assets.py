from __future__ import annotations

import wave
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from code_crawler.application.assets import AssetService
from code_crawler.application.scanner import FileRecord
from code_crawler.domain.configuration import CrawlerConfig, OutputOptions, SourceOptions
from code_crawler.infrastructure.filesystem.run_storage import RunStorage


def _make_png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Minimal 1x1 PNG
    path.write_bytes(
        bytes.fromhex(
            "89504E470D0A1A0A0000000D4948445200000001000000010806000000"
            "1F15C4890000000A49444154789C6360000002000154A20B5700000000"
            "49454E44AE426082"
        )
    )


def _make_wav(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(8000)
        wav_file.writeframes(b"\x00\x00" * 800)


def _record_for(path: Path, root: Path) -> FileRecord:
    stat = path.stat()
    digest = sha256(path.read_bytes()).hexdigest()
    return FileRecord(
        identifier=path.relative_to(root).as_posix(),
        path=path,
        size=stat.st_size,
        digest=digest,
        modified=stat.st_mtime,
        cached=False,
    )


def test_asset_service_extracts_and_records(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    doc_path = project_root / "docs" / "note.txt"
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text("This is a sample asset document used for OCR testing.", encoding="utf-8")
    image_path = project_root / "images" / "diagram.png"
    _make_png(image_path)
    audio_path = project_root / "audio" / "clip.wav"
    _make_wav(audio_path)

    base_config = CrawlerConfig()
    features = replace(base_config.features, enable_assets=True)
    config = replace(
        base_config,
        features=features,
        sources=SourceOptions(root=project_root),
        output=OutputOptions(base_directory=tmp_path / "runs"),
    )
    storage = RunStorage(config)
    service = AssetService(config, storage)

    records = [
        _record_for(doc_path, project_root),
        _record_for(image_path, project_root),
        _record_for(audio_path, project_root),
    ]

    artifacts = service.process(records)

    assert len(artifacts.results) == 3
    assert artifacts.index_path is not None
    assert artifacts.card_index_path is not None

    for result in artifacts.results:
        assert result.text_path.exists()
        assert result.metadata_path.exists()

    for card in artifacts.cards:
        assert card.markdown_path.exists()
        assert card.metadata_path.exists()
