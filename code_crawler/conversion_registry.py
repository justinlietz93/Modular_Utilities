"""Conversion registry providing a modular plugin system for content transforms.

The previous implementation hard-coded HTML->Markdown logic and site-specific
filters. This registry enables pluggable converters that declare the (from, to)
formats they support and apply optional path-based logic.
"""

from typing import Protocol, Optional, Dict, List, Tuple, Iterable

class ContentConverter(Protocol):
    from_fmt: str
    to_fmt: str
    name: str

    def can_handle(self, path: str, ext: str) -> bool: ...
    def convert(self, text: str, path: str) -> str: ...

_registry: Dict[Tuple[str,str], List[ContentConverter]] = {}

def register(converter: ContentConverter):
    key = (converter.from_fmt.lower(), converter.to_fmt.lower())
    _registry.setdefault(key, []).append(converter)

def get_converters(from_fmt: str, to_fmt: str) -> Iterable[ContentConverter]:
    return _registry.get((from_fmt.lower(), to_fmt.lower()), [])

def convert_content(from_fmt: str, to_fmt: str, text: str, path: str, ext: str) -> Optional[str]:
    for conv in get_converters(from_fmt, to_fmt):
        if conv.can_handle(path, ext):
            try:
                return conv.convert(text, path)
            except Exception as e:  # pragma: no cover - defensive
                return f"Conversion error ({conv.name}): {e}\n{text}"
    return None

__all__ = ['register','get_converters','convert_content','ContentConverter']
