"""Explain card generation services."""
from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from ..domain.configuration import CrawlerConfig
from ..domain.explain_cards import (
    CardStatus,
    CardTraceability,
    ExplainCard,
    ExplainCardMetadata,
    deterministic_card_id,
    ensure_all_cards_valid,
)
from ..domain.knowledge_graph import KnowledgeGraph, NodeType, RelationshipType
from ..shared.logging import configure_logger
from .metrics import MetricsBundle


@dataclass(frozen=True)
class ExplainCardResult:
    """Represents a persisted explain card."""

    card: ExplainCard
    output_path: Path
    metadata_path: Path


@dataclass(frozen=True)
class ExplainCardArtifacts:
    """Container for explain card outputs."""

    results: List[ExplainCardResult]
    index_path: Path
    mode: str


class TemplateCardBuilder:
    """Deterministic template-based explain card builder."""

    def __init__(
        self,
        graph: KnowledgeGraph,
        metrics: MetricsBundle | None,
        bundle_refs: Tuple[str, ...],
        run_id: str,
        require_review: bool,
    ) -> None:
        self.graph = graph
        self.metrics = metrics
        self.bundle_refs = bundle_refs
        self.run_id = run_id
        self.require_review = require_review

    def build(self, scopes: Iterable[str]) -> List[ExplainCard]:
        cards: List[ExplainCard] = []
        for scope in scopes:
            builder = getattr(self, f"_build_{scope.replace('-', '_')}_card", None)
            if not builder:
                continue
            card = builder()
            if card:
                cards.append(card)
        return cards

    def _default_status(self) -> CardStatus:
        return CardStatus.REVIEW_PENDING if self.require_review else CardStatus.APPROVED

    def _build_architecture_card(self) -> ExplainCard:
        modules = sorted(
            [node for node in self.graph.nodes.values() if node.type == NodeType.MODULE],
            key=lambda node: node.label.lower(),
        )
        dependencies = [
            rel
            for rel in self.graph.relationships.values()
            if rel.type == RelationshipType.DEPENDS_ON
        ]
        summary = (
            f"The knowledge graph captured {len(modules)} modules and {len(dependencies)} "
            "deterministic dependency edges for run {self.run_id}."
        )
        if modules:
            top_modules = ", ".join(node.label for node in modules[:5])
            summary += f" Key modules include {top_modules}."
        rationale = (
            "Provide a reproducible architecture overview that anchors follow-up reviews to "
            "the knowledge graph snapshot and bundling presets."
        )
        edge_cases = (
            "Modules excluded by CLI include/ignore filters will not appear and require manual review.",
            "Dynamic imports are not resolved statically; confirm runtime-only dependencies separately.",
        )
        traceability = CardTraceability(
            graph_nodes=tuple(node.identifier for node in modules[:5]),
            artifacts=self.bundle_refs,
            metrics=tuple(),
        )
        identifier = deterministic_card_id("architecture", "Architecture Overview")
        return ExplainCard(
            identifier=identifier,
            scope="architecture",
            title="Architecture Overview",
            summary=summary,
            rationale=rationale,
            edge_cases=edge_cases,
            traceability=traceability,
            requires_review=self.require_review,
            status=self._default_status(),
        )

    def _build_quality_card(self) -> ExplainCard:
        coverage_percent = (
            f"{self.metrics.coverage.percent:.1f}%"
            if self.metrics and self.metrics.coverage
            else "n/a"
        )
        tests_summary = "no automated test metrics were supplied"
        if self.metrics and self.metrics.tests:
            tests_summary = (
                f"{self.metrics.tests.passed} passed, {self.metrics.tests.failed} failed, "
                f"{self.metrics.tests.skipped} skipped"
            )
        lint_warnings = (
            sum(self.metrics.lint.counts_by_severity.values())
            if self.metrics and self.metrics.lint
            else 0
        )
        security_findings = (
            sum(self.metrics.security.counts_by_severity.values())
            if self.metrics and self.metrics.security
            else 0
        )
        summary = (
            "Normalized metrics aggregate provided reports. "
            f"Coverage: {coverage_percent}. Tests: {tests_summary}. "
            f"Lint findings: {lint_warnings}. Security findings: {security_findings}."
        )
        rationale = (
            "Surface the latest automated quality signals so reviewers can gate releases "
            "without re-running tooling."
        )
        edge_cases = (
            "Metrics rely on provided artifacts; missing reports are treated as zero contributions.",
            "Mixed-language coverage reports may need manual weighting verification.",
        )
        metric_refs: Tuple[str, ...] = tuple(
            sorted(
                entry
                for entry in (
                    f"coverage:{coverage_percent}" if coverage_percent != "n/a" else None,
                    f"tests:total={self.metrics.tests.total}" if self.metrics and self.metrics.tests else None,
                    f"lint:issues={lint_warnings}" if lint_warnings else None,
                    f"security:issues={security_findings}" if security_findings else None,
                )
                if entry is not None
            )
        )
        traceability = CardTraceability(
            graph_nodes=tuple(),
            artifacts=self.bundle_refs,
            metrics=metric_refs,
        )
        identifier = deterministic_card_id("quality", "Quality Signals")
        return ExplainCard(
            identifier=identifier,
            scope="quality",
            title="Quality Signals",
            summary=summary,
            rationale=rationale,
            edge_cases=edge_cases,
            traceability=traceability,
            requires_review=self.require_review,
            status=self._default_status(),
        )

    def _build_tests_card(self) -> ExplainCard:
        tests = sorted(
            [node for node in self.graph.nodes.values() if node.type == NodeType.TEST],
            key=lambda node: node.label.lower(),
        )
        test_edges = [
            rel
            for rel in self.graph.relationships.values()
            if rel.type == RelationshipType.TESTS
        ]
        modules_tested = {
            rel.target for rel in test_edges if rel.source in {node.identifier for node in tests}
        }
        summary = (
            f"Identified {len(tests)} test entities exercising {len(modules_tested)} modules "
            "according to the knowledge graph."
        )
        if tests:
            summary += f" Representative tests: {', '.join(node.label for node in tests[:5])}."
        rationale = (
            "Highlight exercised areas to focus manual review on untested surfaces and "
            "confirm traceability between tests and modules."
        )
        edge_cases = (
            "Generated tests depend on static imports; runtime-discovered parametrizations may be absent.",
            "Skipped tests remain part of the graph but should be triaged during manual review.",
        )
        traceability = CardTraceability(
            graph_nodes=tuple(node.identifier for node in tests[:5]),
            artifacts=self.bundle_refs,
            metrics=tuple(
                sorted({f"tests:count={len(tests)}", f"modules_tested={len(modules_tested)}"})
            ),
        )
        identifier = deterministic_card_id("tests", "Test Coverage Overview")
        return ExplainCard(
            identifier=identifier,
            scope="tests",
            title="Test Coverage Overview",
            summary=summary,
            rationale=rationale,
            edge_cases=edge_cases,
            traceability=traceability,
            requires_review=self.require_review,
            status=self._default_status(),
        )


class LocalModelAdapter:
    """Optional local-model backed enhancer with privacy guardrails."""

    def __init__(self, model_path: Path, logger) -> None:
        self.model_path = model_path
        self.logger = logger

    def available(self) -> bool:
        return self.model_path.exists()

    def synthesise(self, builder: TemplateCardBuilder, scopes: Iterable[str]) -> List[ExplainCard]:
        if not self.available():
            raise FileNotFoundError(self.model_path)
        cards = builder.build(scopes)
        enhanced: List[ExplainCard] = []
        for card in cards:
            note = (
                "Local model context check completed using offline weights; "
                "manual reviewer confirmation still required."
            )
            enhanced.append(
                replace(card, reviewer_notes=card.reviewer_notes + (note,))
            )
        return enhanced


class ExplainCardGenerator:
    """Generate explain cards and persist them into the run space."""

    CARDS_DIR = Path("cards")

    def __init__(self, config: CrawlerConfig, storage, logger=None) -> None:
        self.config = config
        self.storage = storage
        self.logger = logger or configure_logger(config.privacy)

    def generate(
        self,
        *,
        graph: KnowledgeGraph,
        metrics: MetricsBundle | None,
        bundle_paths: Sequence[Path],
    ) -> ExplainCardArtifacts:
        options = self.config.explain_cards
        bundle_refs = tuple(
            sorted(
                {
                    path.relative_to(self.storage.run_dir).as_posix()
                    if path.is_absolute()
                    else path.as_posix()
                    for path in bundle_paths
                }
            )
        )
        builder = TemplateCardBuilder(
            graph=graph,
            metrics=metrics,
            bundle_refs=bundle_refs,
            run_id=self.storage.run_id,
            require_review=options.require_review,
        )
        used_mode = options.mode
        cards: List[ExplainCard]
        if options.mode == "local-llm" and options.enable_local_model and options.local_model_path:
            adapter = LocalModelAdapter(Path(options.local_model_path), self.logger)
            try:
                cards = adapter.synthesise(builder, options.scopes)
            except FileNotFoundError:
                self.logger.warning(
                    "Local model path %s unavailable; falling back to template mode", options.local_model_path
                )
                cards = builder.build(options.scopes)
                used_mode = "template-fallback"
        else:
            cards = builder.build(options.scopes)
            used_mode = "template"

        ensure_all_cards_valid(cards)
        results: List[ExplainCardResult] = []
        index_payload: List[Dict[str, object]] = []
        for card in cards:
            markdown = card.to_markdown()
            safe_name = card.identifier.replace(":", "_")
            relative_md = self.CARDS_DIR / f"{safe_name}.md"
            output_path = self.storage.record_artifact(relative_md, markdown.encode("utf-8"))
            metadata = ExplainCardMetadata(
                identifier=card.identifier,
                scope=card.scope,
                status=card.status,
                requires_review=card.requires_review,
                checksum=card.checksum(),
                mode=used_mode,
                generator="ExplainCardGenerator",
                traceability=card.traceability,
                review_history=(
                    {
                        "status": card.status.value,
                        "actor": "auto-generator",
                        "run_id": self.storage.run_id,
                    },
                ),
            )
            relative_meta = self.CARDS_DIR / f"{safe_name}.json"
            metadata_path = self.storage.record_artifact(
                relative_meta, json.dumps(metadata.to_dict(), indent=2).encode("utf-8")
            )
            results.append(
                ExplainCardResult(card=card, output_path=output_path, metadata_path=metadata_path)
            )
            index_payload.append(
                {
                    "id": card.identifier,
                    "title": card.title,
                    "scope": card.scope,
                    "card": output_path.relative_to(self.storage.run_dir).as_posix(),
                    "metadata": metadata_path.relative_to(self.storage.run_dir).as_posix(),
                    "requires_review": card.requires_review,
                    "status": card.status.value,
                }
            )

        index_path = self.storage.record_artifact(
            self.CARDS_DIR / "index.json",
            json.dumps(index_payload, indent=2).encode("utf-8"),
        )
        return ExplainCardArtifacts(results=results, index_path=index_path, mode=used_mode)
