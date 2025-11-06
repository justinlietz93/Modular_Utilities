"""Application services for diagram template generation and rendering.

Adds an optional interactive prompt to help install missing local renderers
when running in an interactive terminal. If a renderer (Mermaid CLI, PlantUML,
Graphviz) is unavailable and diagrams are enabled, the user is asked:

    "{tool} is not installed, install now? Y/N, -Y for all or -N for all"

Responding with "-Y" applies "Yes" to all remaining tools; "-N" applies "No".
On non-interactive sessions (e.g., CI) the prompt is skipped and warnings are
logged as before, relying on deterministic fallback renderers.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, replace
import os
import shutil
import subprocess  # nosec B404
import sys
import ctypes
from pathlib import Path
from typing import Dict, List, Mapping, MutableMapping, Optional, Protocol, Sequence

from ..domain.configuration import CrawlerConfig
from ..domain.diagrams import (
    ACCESSIBLE_DARK,
    ACCESSIBLE_LIGHT,
    DiagramFormat,
    DiagramProbeResult,
    DiagramRenderResult,
    DiagramTemplate,
    DiagramTheme,
    merge_themes,
    summarise_accessibility,
)
from ..domain.knowledge_graph import KnowledgeGraph, Node, NodeType, Relationship, RelationshipType
from ..shared.logging import configure_logger


class DiagramRendererPort(Protocol):
    """Port implemented by infrastructure renderers."""

    def probe(self) -> Sequence[DiagramProbeResult]:
        ...

    def render(
        self, template: DiagramTemplate, output_directory: Path, output_formats: Sequence[str]
    ) -> DiagramRenderResult:
        ...


@dataclass(frozen=True)
class DiagramArtifacts:
    """Artifacts generated during diagram processing."""

    templates: Sequence[DiagramTemplate]
    results: Sequence[DiagramRenderResult]
    probes: Sequence[DiagramProbeResult]
    cache_index_path: Path
    accessibility_issues: Mapping[str, List[str]]
    theme_metadata: Mapping[str, Dict[str, object]]
    metadata_path: Path


class DiagramTemplateFactory:
    """Create deterministic diagram templates from the knowledge graph."""

    def __init__(self, config: CrawlerConfig) -> None:
        self.config = config

    def build(self, graph: KnowledgeGraph, theme: DiagramTheme) -> List[DiagramTemplate]:
        templates: List[DiagramTemplate] = []
        presets = set(self.config.diagrams.presets)
        if "architecture" in presets:
            templates.append(self._mermaid_architecture(graph, theme))
            templates.append(self._plantuml_components(graph, theme))
        if "dependencies" in presets:
            templates.append(self._graphviz_dependencies(graph, theme))
        if "tests" in presets:
            templates.append(self._plantuml_tests(graph, theme))
        return [template for template in templates if template.content.strip()]

    def _mermaid_architecture(self, graph: KnowledgeGraph, theme: DiagramTheme) -> DiagramTemplate:
        modules = _sorted_nodes_by_type(graph, NodeType.MODULE)
        relationships = _relationships_of_type(graph, RelationshipType.DEPENDS_ON)
        aliases = {node.identifier: f"m{index}" for index, node in enumerate(modules)}
        lines = [
            "%% Auto-generated architecture map",
            "%%{init: {'theme': 'base', 'themeVariables': {'primaryColor': '%s', 'primaryTextColor': '%s', 'lineColor': '%s', 'fontSize': '%spx'}}}%%"
            % (theme.accent, theme.foreground, theme.accent, theme.font_size),
            "graph TD",
            "classDef module fill:%s33,stroke:%s,color:%s,font-size:%spx;"
            % (theme.accent, theme.accent, theme.foreground, theme.font_size),
        ]
        for node in modules:
            alias = aliases[node.identifier]
            label = node.label.replace("\"", "'")
            lines.append(f"    {alias}[\"{label}\"]:::module")
        for relationship in relationships:
            if relationship.source not in aliases or relationship.target not in aliases:
                continue
            src = aliases[relationship.source]
            dst = aliases[relationship.target]
            lines.append(f"    {src} -->|depends| {dst}")
        if len(lines) == 4:
            lines.append("    note[\"No module dependencies detected\"]")
        content = "\n".join(lines)
        return DiagramTemplate(
            name="architecture_mermaid",
            format=DiagramFormat.MERMAID,
            description="Mermaid component graph connecting modules by dependency edges.",
            content=content + f"\n%% font-size:{theme.font_size}px",
            scope="modules",
            theme=theme,
        )

    def _plantuml_components(self, graph: KnowledgeGraph, theme: DiagramTheme) -> DiagramTemplate:
        modules = _sorted_nodes_by_type(graph, NodeType.MODULE)
        dependencies = _sorted_nodes_by_type(graph, NodeType.DEPENDENCY)
        dep_relationships = [
            relationship
            for relationship in _relationships_of_type(graph, RelationshipType.DEPENDS_ON)
            if relationship.target in {dep.identifier for dep in dependencies}
        ]
        lines = [
            "@startuml",
            f"skinparam backgroundColor {theme.background}",
            f"skinparam componentFontColor {theme.foreground}",
            f"skinparam componentFontSize {theme.font_size}",
            f"skinparam componentBorderColor {theme.accent}",
            f"skinparam componentBackgroundColor {theme.accent}33",
        ]
        for node in modules:
            identifier = node.identifier.replace(":", "_")
            label = node.label.replace("\"", "'")
            lines.append(f"component \"{label}\" as {identifier}")
        for dep in dependencies[:20]:
            identifier = dep.identifier.replace(":", "_")
            label = dep.label.replace("\"", "'")
            lines.append(f"database \"{label}\" as {identifier}")
        for rel in dep_relationships:
            source = rel.source.replace(":", "_")
            target = rel.target.replace(":", "_")
            lines.append(f"{source} ..> {target} : uses")
        if len(lines) == 5:
            lines.append("note \"No external dependencies detected\"")
        lines.append(f"center footer font-size {theme.font_size}px")
        lines.append("@enduml")
        content = "\n".join(lines)
        return DiagramTemplate(
            name="architecture_components",
            format=DiagramFormat.PLANTUML,
            description="PlantUML component diagram linking modules to third-party dependencies.",
            content=content,
            scope="modules+dependencies",
            theme=theme,
        )

    def _graphviz_dependencies(self, graph: KnowledgeGraph, theme: DiagramTheme) -> DiagramTemplate:
        module_nodes = _sorted_nodes_by_type(graph, NodeType.MODULE)
        test_nodes = _sorted_nodes_by_type(graph, NodeType.TEST)
        relationships = _relationships_of_type(graph, RelationshipType.TESTS)
        edges = [rel for rel in relationships if rel.source in {test.identifier for test in test_nodes}]
        lines = [
            "digraph Tests {",
            "  rankdir=LR;",
            "  node [shape=box, style=filled, fontname=Helvetica, fontsize=%d, fillcolor=\"%s\", color=\"%s\", fontcolor=\"%s\"];"
            % (theme.font_size, theme.background, theme.accent, theme.foreground),
            f"  // font-size:{theme.font_size}px",
        ]
        for test in test_nodes[:30]:
            safe_label = test.label.replace("\"", "'")
            lines.append(f"  \"{test.identifier}\" [label=\"{safe_label}\", shape=tab];")
        for module in module_nodes:
            safe_label = module.label.replace("\"", "'")
            lines.append(f"  \"{module.identifier}\" [label=\"{safe_label}\"];")
        for rel in edges:
            if rel.target not in {module.identifier for module in module_nodes}:
                continue
            lines.append(f"  \"{rel.source}\" -> \"{rel.target}\" [label=\"tests\"];")
        lines.append("}")
        content = "\n".join(lines)
        return DiagramTemplate(
            name="tests_graphviz",
            format=DiagramFormat.GRAPHVIZ,
            description="Graphviz DOT diagram mapping tests to covered modules.",
            content=content,
            scope="tests",
            theme=theme,
        )

    def _plantuml_tests(self, graph: KnowledgeGraph, theme: DiagramTheme) -> DiagramTemplate:
        test_nodes = _sorted_nodes_by_type(graph, NodeType.TEST)
        relationships = _relationships_of_type(graph, RelationshipType.TESTS)
        modules = {rel.target for rel in relationships}
        lines = [
            "@startuml",
            f"skinparam backgroundColor {theme.background}",
            f"skinparam activityFontColor {theme.foreground}",
            f"skinparam activityFontSize {theme.font_size}",
            f"skinparam activityBorderColor {theme.accent}",
        ]
        lines.append("start")
        for test in test_nodes[:15]:
            safe_label = test.label.replace("\"", "'")
            lines.append(f":{safe_label};")
        if not test_nodes:
            lines.append("note right: No tests discovered")
        lines.append("stop")
        lines.append(f"center footer font-size {theme.font_size}px")
        lines.append("@enduml")
        content = "\n".join(lines)
        return DiagramTemplate(
            name="tests_sequence",
            format=DiagramFormat.PLANTUML,
            description="PlantUML activity view enumerating discovered tests.",
            content=content,
            scope="tests",
            theme=theme,
        )


class DiagramGenerator:
    """Generate diagram templates and orchestrate rendering."""

    CACHE_NAME = "diagram_cache.json"

    def __init__(
        self,
        config: CrawlerConfig,
        storage,
        renderer: Optional[DiagramRendererPort] = None,
        logger=None,
    ) -> None:
        self.config = config
        self.storage = storage
        self.renderer = renderer
        self.logger = logger or configure_logger(config.privacy)
        self.cache_index_path = storage.base_dir / self.CACHE_NAME

    def generate(self, graph: KnowledgeGraph) -> DiagramArtifacts:
        renderer = self.renderer or _resolve_renderer()
        # Probe installed renderers
        probes = renderer.probe()
        # Optionally offer to install missing renderers when interactive or forced by env
        probes = self._maybe_offer_installs(probes)
        # Recreate renderer to pick up any new installs
        renderer = self.renderer or _resolve_renderer()
        probes = renderer.probe()
        # Quiet availability logs if user explicitly disabled installs/prompts
        _install_mode = os.environ.get("CODE_CRAWLER_INSTALL_RENDERERS", "").strip().lower()
        if _install_mode != "no":
            for probe in probes:
                level = "info" if probe.available else "warning"
                getattr(self.logger, level)(
                    "Renderer %s availability: %s", probe.format.value, probe.details
                )

        themes = self._resolve_themes()
        templates: List[DiagramTemplate] = []
        factory = DiagramTemplateFactory(self.config)
        for theme in themes:
            themed_templates = factory.build(graph, theme)
            for template in themed_templates:
                if theme is ACCESSIBLE_DARK:
                    template = replace(template, name=f"{template.name}_dark", theme=theme)
                templates.append(template)

        accessibility = summarise_accessibility(templates)
        if accessibility:
            details = json.dumps(accessibility, indent=2)
            raise RuntimeError(f"Diagram accessibility validation failed: {details}")

        cache_index: Dict[str, Dict[str, str]] = self._load_cache()
        results: List[DiagramRenderResult] = []
        digests: Dict[str, Dict[str, str]] = dict(cache_index)
        output_formats = self.config.diagrams.output_formats or ["svg"]
        diagrams_dir = self.storage.subdirectory("diagrams")

        for template in templates:
            checksum = template.checksum()
            cached = cache_index.get(template.name)
            if cached and cached.get("checksum") == checksum:
                cached_path = Path(cached["path"])
                source_cached = Path(cached.get("source", cached_path))
                if cached_path.exists():
                    target = diagrams_dir / cached_path.name
                    target.write_bytes(cached_path.read_bytes())
                    source_target = diagrams_dir / source_cached.name
                    if source_cached.exists():
                        source_target.write_bytes(source_cached.read_bytes())
                    else:
                        source_target = target
                    results.append(
                        DiagramRenderResult(
                            template=template,
                            output_path=str(target),
                            source_path=str(source_target),
                            rendered=False,
                            cache_hit=True,
                            diagnostics={"checksum": checksum, "cache_source": str(source_cached)},
                        )
                    )
                    continue

            result = renderer.render(template, diagrams_dir, output_formats)
            output_path = Path(result.output_path)
            source_path = Path(result.source_path)
            results.append(result)
            digests[template.name] = {
                "checksum": checksum,
                "path": str(output_path),
                "source": str(source_path),
            }

        metadata = {
            "themes": merge_themes(ACCESSIBLE_LIGHT, ACCESSIBLE_DARK),
            "probes": [
                {
                    "format": probe.format.value,
                    "available": probe.available,
                    "details": probe.details,
                }
                for probe in probes
            ],
            "templates": [
                {
                    "name": result.template.name,
                    "format": result.template.format.value,
                    "scope": result.template.scope,
                    "description": result.template.description,
                    "output": Path(result.output_path).relative_to(self.storage.run_dir).as_posix(),
                    "source": Path(result.source_path).relative_to(self.storage.run_dir).as_posix(),
                    "rendered": result.rendered,
                    "cache_hit": result.cache_hit,
                    "diagnostics": result.diagnostics,
                }
                for result in results
            ],
        }

        metadata_path = diagrams_dir / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        self._write_cache(digests)
        return DiagramArtifacts(
            templates=templates,
            results=results,
            probes=probes,
            cache_index_path=self.cache_index_path,
            accessibility_issues=accessibility,
            theme_metadata=metadata["themes"],
            metadata_path=metadata_path,
        )

    def _resolve_themes(self) -> Sequence[DiagramTheme]:
        theme = self.config.diagrams.theme
        if theme == "light":
            return [ACCESSIBLE_LIGHT]
        if theme == "dark":
            return [ACCESSIBLE_DARK]
        return [ACCESSIBLE_LIGHT, ACCESSIBLE_DARK]

    def _load_cache(self) -> Dict[str, Dict[str, str]]:
        if not self.cache_index_path.exists():
            return {}
        try:
            return json.loads(self.cache_index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _write_cache(self, digests: Mapping[str, Dict[str, str]]) -> None:
        self.cache_index_path.write_text(
            json.dumps(digests, indent=2), encoding="utf-8"
        )

    # --- Interactive installer helpers ---
    def _maybe_offer_installs(self, probes: Sequence[DiagramProbeResult]) -> Sequence[DiagramProbeResult]:
        """If running interactively and diagrams are enabled, prompt to install missing tools.

        Returns a fresh probe list if installs occurred, else the original list.
        """
        # Environment override takes precedence: CODE_CRAWLER_INSTALL_RENDERERS
        mode = os.environ.get("CODE_CRAWLER_INSTALL_RENDERERS", "").strip().lower()
        try:
            interactive = sys.stdin.isatty() and sys.stdout.isatty()
        except Exception:
            interactive = False

        if mode == "no":
            return probes
        if mode not in {"yes", "ask"}:
            # Default behavior: ask in interactive shells; otherwise skip
            if not interactive:
                return probes

        missing = [p for p in probes if not p.available]
        if not missing:
            return probes

        # If mode == 'yes', apply Yes to all without prompting
        apply_all: str | None = "Y" if mode == "yes" else None  # "Y" or "N" when -Y/-N chosen
        installed_any = False

        for p in missing:
            tool_label, installer = _installer_for_probe(p)
            if not installer:
                # We don't know how to install; just continue
                continue
            answer = None
            if apply_all:
                answer = apply_all
            else:
                prompt = f"{tool_label} is not installed, install now? Y/N, -Y for all or -N for all: "
                try:
                    raw = input(prompt).strip()
                except EOFError:
                    raw = "N"
                if raw in {"Y", "y", "N", "n", "-Y", "-y", "-N", "-n"}:
                    if raw.startswith("-"):
                        apply_all = raw[1:].upper()
                        answer = apply_all
                    else:
                        answer = raw.upper()
                else:
                    answer = "N"

            if answer == "Y":
                try:
                    self.logger.info("Attempting to install %s...", tool_label)
                    installer(self.logger)
                    installed_any = True
                except Exception as e:
                    self.logger.warning("Installer for %s failed: %s", tool_label, e)

        if installed_any:
            # Return a fresh probe list to reflect new availability
            from ..infrastructure.diagramming.renderers import LocalDiagramRenderer

            return LocalDiagramRenderer().probe()
        return probes


def _resolve_renderer() -> DiagramRendererPort:
    from ..infrastructure.diagramming.renderers import LocalDiagramRenderer

    return LocalDiagramRenderer()


def _sorted_nodes_by_type(graph: KnowledgeGraph, node_type: NodeType) -> List[Node]:
    return [node for node in graph.sorted_nodes() if node.type == node_type]


def _relationships_of_type(
    graph: KnowledgeGraph, relationship_type: RelationshipType
) -> List[Relationship]:
    return [rel for rel in graph.sorted_relationships() if rel.type == relationship_type]


# --- Platform-aware installer helpers ---
def _installer_for_probe(probe: DiagramProbeResult):
    """Return a (label, installer_fn|None) tuple for a given missing probe."""
    if probe.format == DiagramFormat.MERMAID:
        return ("Mermaid CLI (mmdc)", _install_mermaid)
    if probe.format == DiagramFormat.PLANTUML:
        return ("PlantUML", _install_plantuml)
    if probe.format == DiagramFormat.GRAPHVIZ:
        return ("Graphviz dot", _install_graphviz)
    return (probe.format.value, None)


def _install_mermaid(logger) -> None:
    npm = shutil.which("npm")
    if not npm:
        logger.warning(
            "npm was not found on PATH. Please install Node.js, then run: npm install -g @mermaid-js/mermaid-cli"
        )
        raise RuntimeError("npm not available")
    subprocess.check_call([npm, "install", "-g", "@mermaid-js/mermaid-cli"])  # nosec B603


def _install_plantuml(logger) -> None:
    # Prefer Windows-friendly managers if present
    scoop = shutil.which("scoop")
    choco = shutil.which("choco")
    if scoop:
        subprocess.check_call([scoop, "install", "plantuml"])  # nosec B603
        return
    if choco:
        if _is_admin():
            subprocess.check_call([choco, "install", "plantuml", "-y"])  # nosec B603
            return
        logger.warning(
            "Chocolatey detected but shell is not elevated. Please run an Administrator PowerShell and execute: choco install plantuml -y"
        )
        raise RuntimeError("chocolatey not elevated")
    # Fallback: print guidance for macOS/Linux
    logger.warning(
        "Could not find an automatic installer (scoop/choco). Install PlantUML manually: brew install plantuml | scoop install plantuml"
    )
    raise RuntimeError("no supported installer found")


def _install_graphviz(logger) -> None:
    scoop = shutil.which("scoop")
    choco = shutil.which("choco")
    if scoop:
        subprocess.check_call([scoop, "install", "graphviz"])  # nosec B603
        return
    if choco:
        if _is_admin():
            subprocess.check_call([choco, "install", "graphviz", "-y"])  # nosec B603
            return
        logger.warning(
            "Chocolatey detected but shell is not elevated. Please run an Administrator PowerShell and execute: choco install graphviz -y"
        )
        raise RuntimeError("chocolatey not elevated")
    logger.warning(
        "Could not find an automatic installer (scoop/choco). Install Graphviz manually: apt install graphviz | brew install graphviz | scoop install graphviz"
    )
    raise RuntimeError("no supported installer found")


def _is_admin() -> bool:
    if os.name != "nt":
        return os.geteuid() == 0 if hasattr(os, "geteuid") else False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False

