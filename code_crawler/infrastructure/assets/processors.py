"""Local processors for non-code assets."""
from __future__ import annotations

import contextlib
import imghdr
import wave
from pathlib import Path
from typing import Dict, Tuple


class DocumentOcr:
    """Lightweight text extraction for document assets."""

    ENCODINGS = ("utf-8", "utf-16", "latin-1")

    def extract(self, path: Path, *, max_chars: int) -> Tuple[str, str, Dict[str, object]]:
        text = self._read_text(path)
        normalised = " ".join(text.split())
        preview = normalised[:max_chars]
        metadata = {
            "characters": len(normalised),
            "preview_length": len(preview),
            "source": "document_ocr",
        }
        return preview, preview, metadata

    def _read_text(self, path: Path) -> str:
        for encoding in self.ENCODINGS:
            try:
                return path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        return path.read_bytes().decode("utf-8", errors="ignore")


class ImageCaptioner:
    """Deterministic captioning using image metadata only."""

    def caption(self, path: Path) -> Tuple[str, Dict[str, object]]:
        image_type = imghdr.what(path)
        width, height = self._dimensions(path, image_type)
        size = path.stat().st_size
        descriptor = image_type or path.suffix.lstrip(".") or "unknown"
        summary = (
            f"{descriptor} image '{path.name}'"
            f" with dimensions {width or '?'}x{height or '?'} and size {size} bytes."
        )
        metadata = {
            "image_type": descriptor,
            "width": width,
            "height": height,
            "bytes": size,
            "source": "image_captioner",
        }
        return summary, metadata

    def _dimensions(self, path: Path, image_type: str | None) -> Tuple[int | None, int | None]:
        if image_type == "png":
            header = path.read_bytes()[:24]
            if len(header) >= 24 and header[12:16] == b"IHDR":
                return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")
        if image_type == "gif":
            header = path.read_bytes()[:10]
            if len(header) >= 10:
                width = int.from_bytes(header[6:8], "little")
                height = int.from_bytes(header[8:10], "little")
                return width, height
        return None, None


class AudioTranscriber:
    """Summarise audio files using wave metadata when available."""

    def transcribe(self, path: Path) -> Tuple[str, Dict[str, object]]:
        if path.suffix.lower() != ".wav":
            size = path.stat().st_size
            summary = f"Audio asset '{path.name}' ({size} bytes)"
            return summary, {"bytes": size, "source": "audio_transcriber"}
        with contextlib.closing(wave.open(str(path), "rb")) as handle:
            frames = handle.getnframes()
            framerate = handle.getframerate()
            channels = handle.getnchannels()
            duration = frames / float(framerate) if framerate else 0.0
            summary = (
                f"WAV audio '{path.name}' with {channels} channel(s)"
                f" lasting {duration:.2f} seconds"
            )
            metadata = {
                "frames": frames,
                "framerate": framerate,
                "channels": channels,
                "duration_seconds": round(duration, 2),
                "source": "audio_transcriber",
            }
            return summary, metadata


class VideoSummariser:
    """Summarise basic video metadata without decoding."""

    def summarise(self, path: Path) -> Tuple[str, Dict[str, object]]:
        size = path.stat().st_size
        summary = f"Video asset '{path.name}' approximated via filesize ({size} bytes)"
        metadata = {
            "bytes": size,
            "source": "video_summariser",
        }
        return summary, metadata
