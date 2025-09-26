"""Application services for non-code asset processing."""
from __future__ import annotations

import json
from hashlib import sha256
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence

from ..domain.assets import (
    AssetCard,
    AssetExtraction,
    AssetType,
    asset_card_identifier,
    asset_identifier,
)
from ..domain.configuration import CrawlerConfig
from ..infrastructure.assets.processors import (
    AudioTranscriber,
    DocumentOcr,
    ImageCaptioner,
    VideoSummariser,
)
from ..shared.logging import configure_logger
from .scanner import FileRecord


@dataclass(frozen=True)
class AssetResult:
    """Persisted extraction for a single asset."""

    extraction: AssetExtraction
    text_path: Path
    metadata_path: Path


@dataclass(frozen=True)
class AssetCardResult:
    """Persisted review card for a single asset."""

    card: AssetCard
    markdown_path: Path
    metadata_path: Path


@dataclass(frozen=True)
class AssetArtifacts:
    """Aggregate outputs from asset processing."""

    results: List[AssetResult]
    cards: List[AssetCardResult]
    index_path: Path | None
    card_index_path: Path | None


class AssetService:
    """Generate textual context and review cards for non-code assets."""

    ASSET_DIR = Path("assets")
    CARD_DIR = ASSET_DIR / "cards"

    def __init__(self, config: CrawlerConfig, storage, logger=None) -> None:
        self.config = config
        self.storage = storage
        self.logger = logger or configure_logger(config.privacy)
        self.document_ocr = DocumentOcr()
        self.image_captioner = ImageCaptioner()
        self.audio_transcriber = AudioTranscriber()
        self.video_summariser = VideoSummariser()

    def process(self, records: Sequence[FileRecord]) -> AssetArtifacts:
        results: List[AssetResult] = []
        index_payload: List[Dict[str, object]] = []
        for record in records:
            asset_type = self._classify(record.path)
            if not asset_type:
                continue
            extraction = self._extract_asset(record, asset_type)
            relative_dir = self.ASSET_DIR / extraction.identifier
            text_path = self.storage.record_artifact(
                relative_dir / "extracted.txt",
                extraction.content.encode("utf-8"),
            )
            metadata_path = self.storage.record_artifact(
                relative_dir / "metadata.json",
                json.dumps(extraction.to_dict(), indent=2).encode("utf-8"),
            )
            results.append(AssetResult(extraction=extraction, text_path=text_path, metadata_path=metadata_path))
            index_payload.append(
                {
                    "identifier": extraction.identifier,
                    "asset_type": extraction.asset_type.value,
                    "summary": extraction.summary,
                    "path": extraction.path.as_posix(),
                    "metadata": str(metadata_path.relative_to(self.storage.run_dir)),
                    "text": str(text_path.relative_to(self.storage.run_dir)),
                }
            )

        index_path: Path | None = None
        if index_payload:
            index_path = self.storage.record_artifact(
                self.ASSET_DIR / "index.json",
                json.dumps({"assets": index_payload}, indent=2).encode("utf-8"),
            )

        card_results: List[AssetCardResult] = []
        card_index_path: Path | None = None
        if results and self.config.assets.generate_cards:
            cards_index: List[Dict[str, object]] = []
            for result in results:
                card = self._build_card(result.extraction)
                markdown_path = self.storage.record_artifact(
                    self.CARD_DIR / f"{card.identifier}.md",
                    card.to_markdown().encode("utf-8"),
                )
                metadata_path = self.storage.record_artifact(
                    self.CARD_DIR / f"{card.identifier}.json",
                    json.dumps(card.to_dict(), indent=2).encode("utf-8"),
                )
                card_results.append(
                    AssetCardResult(card=card, markdown_path=markdown_path, metadata_path=metadata_path)
                )
                cards_index.append(
                    {
                        "identifier": card.identifier,
                        "asset_identifier": card.asset_identifier,
                        "markdown": str(markdown_path.relative_to(self.storage.run_dir)),
                        "metadata": str(metadata_path.relative_to(self.storage.run_dir)),
                    }
                )
            card_index_path = self.storage.record_artifact(
                self.CARD_DIR / "index.json",
                json.dumps({"cards": cards_index}, indent=2).encode("utf-8"),
            )

        return AssetArtifacts(
            results=results,
            cards=card_results,
            index_path=index_path,
            card_index_path=card_index_path,
        )

    def _classify(self, path: Path) -> AssetType | None:
        suffix = path.suffix.lower()
        if suffix in self.config.assets.document_extensions:
            return AssetType.DOCUMENT
        if suffix in self.config.assets.image_extensions:
            return AssetType.IMAGE
        if suffix in self.config.assets.audio_extensions:
            return AssetType.AUDIO
        if suffix in self.config.assets.video_extensions:
            return AssetType.VIDEO
        return None

    def _extract_asset(self, record: FileRecord, asset_type: AssetType) -> AssetExtraction:
        relative_path = record.path.relative_to(self.config.sources.root)
        identifier = asset_identifier(relative_path)
        if asset_type == AssetType.DOCUMENT:
            content, summary, metadata = self.document_ocr.extract(
                record.path, max_chars=self.config.assets.max_preview_chars
            )
        elif asset_type == AssetType.IMAGE:
            summary, metadata = self.image_captioner.caption(record.path)
            content = summary
        elif asset_type == AssetType.AUDIO:
            summary, metadata = self.audio_transcriber.transcribe(record.path)
            content = summary
        else:
            summary, metadata = self.video_summariser.summarise(record.path)
            content = summary
        provenance = ("asset_service", asset_type.value)
        return AssetExtraction(
            identifier=identifier,
            path=relative_path,
            asset_type=asset_type,
            summary=summary,
            content=content,
            provenance=provenance,
            metadata=metadata,
        )

    def _build_card(self, extraction: AssetExtraction) -> AssetCard:
        identifier = asset_card_identifier(extraction.identifier)
        notes: Dict[str, str] = {
            "Provenance": "\n".join(extraction.provenance),
            "Metadata": json.dumps(extraction.metadata, indent=2),
            "Follow-up": "Review asset accuracy and update captions if richer context is required.",
        }
        checksum = sha256(extraction.summary.encode("utf-8")).hexdigest()[:16]
        title = f"Asset Card — {extraction.path.name}"
        return AssetCard(
            identifier=identifier,
            asset_identifier=extraction.identifier,
            title=title,
            asset_type=extraction.asset_type,
            summary=extraction.summary,
            notes=notes,
            provenance=("asset_service", "card"),
            checksum=checksum,
        )
