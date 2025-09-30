"""Infrastructure adapters that render diagram templates locally."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Sequence

from ...domain.diagrams import (
    DiagramFormat,
    DiagramProbeResult,
    DiagramRenderResult,
    DiagramTemplate,
)


class LocalDiagramRenderer:
    """Render diagrams using installed tooling or deterministic fallbacks."""

    def __init__(self) -> None:
        self._mermaid_cli = shutil.which("mmdc")
        self._plantuml_cli = shutil.which("plantuml")
        self._graphviz_cli = shutil.which("dot")

    def probe(self) -> Sequence[DiagramProbeResult]:
        return [
            DiagramProbeResult(
                format=DiagramFormat.MERMAID,
                available=bool(self._mermaid_cli),
                details=self._probe_message(
                    "Mermaid CLI (mmdc)", self._mermaid_cli, "npm install -g @mermaid-js/mermaid-cli"
                ),
            ),
            DiagramProbeResult(
                format=DiagramFormat.PLANTUML,
                available=bool(self._plantuml_cli),
                details=self._probe_message(
                    "PlantUML", self._plantuml_cli, "brew install plantuml | scoop install plantuml"
                ),
            ),
            DiagramProbeResult(
                format=DiagramFormat.GRAPHVIZ,
                available=bool(self._graphviz_cli),
                details=self._probe_message(
                    "Graphviz dot", self._graphviz_cli, "apt install graphviz | brew install graphviz"
                ),
            ),
        ]

    def render(
        self, template: DiagramTemplate, output_directory: Path, output_formats: Sequence[str]
    ) -> DiagramRenderResult:
        output_directory.mkdir(parents=True, exist_ok=True)
        source_path = self._write_source(template, output_directory)
        diagnostics: Dict[str, object] = {
            "used_cli": False,
            "fallback": False,
            "requested_formats": list(output_formats),
        }

        rendered_path = source_path
        for fmt in output_formats:
            fmt = fmt.lower()
            if fmt == "svg":
                rendered_path = self._render_svg(template, source_path, output_directory, diagnostics)
            elif fmt == "png":
                rendered_path = self._render_png(template, source_path, output_directory, diagnostics)

        return DiagramRenderResult(
            template=template,
            output_path=str(rendered_path),
            source_path=str(source_path),
            rendered=True,
            cache_hit=False,
            diagnostics=diagnostics,
        )

    def _render_svg(
        self,
        template: DiagramTemplate,
        source_path: Path,
        output_directory: Path,
        diagnostics: Dict[str, object],
    ) -> Path:
        target = output_directory / f"{source_path.stem}.svg"
        if template.format == DiagramFormat.MERMAID and self._mermaid_cli:
            self._execute([self._mermaid_cli, "-i", str(source_path), "-o", str(target)])
            diagnostics["used_cli"] = True
            return target
        if template.format == DiagramFormat.PLANTUML and self._plantuml_cli:
            self._execute([self._plantuml_cli, "-tsvg", str(source_path)])
            cli_target = source_path.with_suffix(".svg")
            if cli_target.exists():
                cli_target.replace(target)
            diagnostics["used_cli"] = True
            return target
        if template.format == DiagramFormat.GRAPHVIZ and self._graphviz_cli:
            self._execute([self._graphviz_cli, "-Tsvg", str(source_path), "-o", str(target)])
            diagnostics["used_cli"] = True
            return target
        diagnostics["fallback"] = True
        target.write_text(_fallback_svg(template), encoding="utf-8")
        return target

    def _render_png(
        self,
        template: DiagramTemplate,
        source_path: Path,
        output_directory: Path,
        diagnostics: Dict[str, object],
    ) -> Path:
        target = output_directory / f"{source_path.stem}.png"
        if template.format == DiagramFormat.MERMAID and self._mermaid_cli:
            self._execute([self._mermaid_cli, "-i", str(source_path), "-o", str(target)])
            diagnostics["used_cli"] = True
            return target
        if template.format == DiagramFormat.PLANTUML and self._plantuml_cli:
            self._execute([self._plantuml_cli, "-tpng", str(source_path)])
            cli_target = source_path.with_suffix(".png")
            if cli_target.exists():
                cli_target.replace(target)
            diagnostics["used_cli"] = True
            return target
        if template.format == DiagramFormat.GRAPHVIZ and self._graphviz_cli:
            self._execute([self._graphviz_cli, "-Tpng", str(source_path), "-o", str(target)])
            diagnostics["used_cli"] = True
            return target
        diagnostics["fallback"] = True
        target.write_bytes(_fallback_png(template))
        return target

    def _write_source(self, template: DiagramTemplate, output_directory: Path) -> Path:
        extension = {
            DiagramFormat.MERMAID: ".mmd",
            DiagramFormat.PLANTUML: ".puml",
            DiagramFormat.GRAPHVIZ: ".dot",
        }[template.format]
        source_path = output_directory / f"{template.name}{extension}"
        source_path.write_text(template.content, encoding="utf-8")
        return source_path

    @staticmethod
    def _probe_message(tool: str, path: str | None, remediation: str) -> str:
        if path:
            return f"{tool} detected at {path}"
        return f"{tool} unavailable. Install via: {remediation}" \
            " or rely on built-in fallback renderer."

    @staticmethod
    def _execute(command: List[str]) -> None:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _fallback_svg(template: DiagramTemplate) -> str:
    lines = template.content.splitlines() or ["(empty diagram)"]
    padding = 16
    line_height = template.theme.font_size + 6
    width = max(len(line) for line in lines) * (template.theme.font_size // 2) + padding * 2
    height = line_height * len(lines) + padding * 2
    svg_lines = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        f"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{width}\" height=\"{height}\" role=\"img\" aria-label=\"{template.description}\">",
        f"  <rect x=\"0\" y=\"0\" width=\"100%\" height=\"100%\" fill=\"{template.theme.background}\" />",
    ]
    y = padding + template.theme.font_size
    for line in lines:
        svg_lines.append(
            f"  <text x=\"{padding}\" y=\"{y}\" font-family=\"monospace\" font-size=\"{template.theme.font_size}\" fill=\"{template.theme.foreground}\">{_escape_xml(line)}</text>"
        )
        y += line_height
    svg_lines.append("</svg>")
    return "\n".join(svg_lines)


def _fallback_png(template: DiagramTemplate) -> bytes:
    # Minimal PNG (1x1) placeholder encoded as bytes to guarantee deterministic output.
    # This avoids external dependencies while signalling that rich rendering is unavailable.
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        + b"\x00\x00\x00\x06bKGD\xff\xff\xff\xff\xff\xff\xc5\xed\xd5~"
        + b"\x00\x00\x00\x0cIDAT\x08\x1d\x63\x60\x60\x60\x00\x00\x00\x05\x00\x01\x0d\n\x02B"
        + b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def _escape_xml(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

