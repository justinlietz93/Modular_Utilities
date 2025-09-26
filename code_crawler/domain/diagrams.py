"""Domain models for diagram generation and validation."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Dict, Iterable, List, Tuple


class DiagramFormat(str, Enum):
    """Supported diagram template formats."""

    MERMAID = "mermaid"
    PLANTUML = "plantuml"
    GRAPHVIZ = "graphviz"


@dataclass(frozen=True)
class DiagramTheme:
    """Styling preset that should remain accessible in light/dark modes."""

    name: str
    background: str
    foreground: str
    accent: str
    font_size: int = 14

    def validate(self) -> List[str]:
        """Return a list of accessibility violations for the theme."""

        issues: List[str] = []
        if self.font_size < 12:
            issues.append(
                f"Theme '{self.name}' font size {self.font_size}px is smaller than 12px minimum."
            )
        contrast_fg = _contrast_ratio(self.background, self.foreground)
        if contrast_fg < 4.5:
            issues.append(
                (
                    f"Theme '{self.name}' foreground contrast {contrast_fg:.2f} < 4.5"
                    " (WCAG AA body text requirement)."
                )
            )
        contrast_accent = _contrast_ratio(self.background, self.accent)
        if contrast_accent < 3.0:
            issues.append(
                (
                    f"Theme '{self.name}' accent contrast {contrast_accent:.2f} < 3.0"
                    " (minimum for non-text graphics)."
                )
            )
        return issues


ACCESSIBLE_LIGHT = DiagramTheme(
    name="light",
    background="#ffffff",
    foreground="#1b1d23",
    accent="#3366ff",
    font_size=14,
)

ACCESSIBLE_DARK = DiagramTheme(
    name="dark",
    background="#0b1622",
    foreground="#f4f7fb",
    accent="#64ffda",
    font_size=14,
)


@dataclass(frozen=True)
class DiagramTemplate:
    """A rendered diagram template derived from repository metadata."""

    name: str
    format: DiagramFormat
    description: str
    content: str
    scope: str
    theme: DiagramTheme = ACCESSIBLE_LIGHT

    def checksum(self) -> str:
        """Return a deterministic checksum for incremental regeneration."""

        payload = f"{self.name}\n{self.format.value}\n{self.scope}\n{self.content}\n{self.theme.name}"
        return sha256(payload.encode("utf-8")).hexdigest()

    def validate(self) -> List[str]:
        """Return validation failures for the template."""

        issues = self.theme.validate()
        if not self.content.strip():
            issues.append(f"Template '{self.name}' has no content to render.")
        if "font-size" not in self.content and self.theme.font_size:
            issues.append(
                f"Template '{self.name}' should declare font-size for readability."
            )
        return issues


@dataclass(frozen=True)
class DiagramProbeResult:
    """Outcome of probing renderer dependencies."""

    format: DiagramFormat
    available: bool
    details: str


@dataclass(frozen=True)
class DiagramRenderResult:
    """Metadata captured when rendering a diagram."""

    template: DiagramTemplate
    output_path: str
    source_path: str
    rendered: bool
    cache_hit: bool
    diagnostics: Dict[str, object]


def render_plan_digest(templates: Iterable[DiagramTemplate]) -> str:
    """Produce a digest representing the set of templates to generate."""

    checksums = sorted(template.checksum() for template in templates)
    payload = "\n".join(checksums)
    return sha256(payload.encode("utf-8")).hexdigest()


def _contrast_ratio(color_a: str, color_b: str) -> float:
    """Calculate the WCAG contrast ratio between two hex colours."""

    luminance_a = _relative_luminance(color_a)
    luminance_b = _relative_luminance(color_b)
    lighter = max(luminance_a, luminance_b)
    darker = min(luminance_a, luminance_b)
    return (lighter + 0.05) / (darker + 0.05)


def _relative_luminance(color: str) -> float:
    color = color.lstrip("#")
    if len(color) != 6:
        raise ValueError(f"Expected 6-digit hex colour, got '{color}'")
    rgb = [int(color[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = []
    for channel in rgb:
        if channel <= 0.03928:
            linear.append(channel / 12.92)
        else:
            linear.append(((channel + 0.055) / 1.055) ** 2.4)
    r, g, b = linear
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def summarise_accessibility(templates: Iterable[DiagramTemplate]) -> Dict[str, List[str]]:
    """Return accessibility issues per template name."""

    return {template.name: template.validate() for template in templates if template.validate()}


def merge_themes(light: DiagramTheme, dark: DiagramTheme) -> Dict[str, Dict[str, object]]:
    """Expose combined light/dark theme metadata for documentation."""

    return {
        "light": _theme_to_dict(light),
        "dark": _theme_to_dict(dark),
    }


def _theme_to_dict(theme: DiagramTheme) -> Dict[str, object]:
    return {
        "name": theme.name,
        "background": theme.background,
        "foreground": theme.foreground,
        "accent": theme.accent,
        "font_size": theme.font_size,
    }

