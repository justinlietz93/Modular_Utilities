"""Domain models for explain cards."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, Tuple


class CardValidationError(ValueError):
    """Raised when explain card content is invalid."""


class CardStatus(str, Enum):
    """Enumerates the lifecycle state for an explain card."""

    REVIEW_PENDING = "review_pending"
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"


@dataclass(frozen=True)
class CardTraceability:
    """Traceability metadata anchoring a card to source context."""

    graph_nodes: Tuple[str, ...] = field(default_factory=tuple)
    artifacts: Tuple[str, ...] = field(default_factory=tuple)
    metrics: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, object]:
        return {
            "graph_nodes": list(self.graph_nodes),
            "artifacts": list(self.artifacts),
            "metrics": list(self.metrics),
        }


@dataclass(frozen=True)
class ExplainCard:
    """Structured explanation artefact summarising repository knowledge."""

    identifier: str
    scope: str
    title: str
    summary: str
    rationale: str
    edge_cases: Tuple[str, ...]
    traceability: CardTraceability
    requires_review: bool = True
    status: CardStatus = CardStatus.REVIEW_PENDING
    reviewer_notes: Tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> None:
        """Ensure mandatory sections are populated."""

        if not self.summary.strip():
            raise CardValidationError("Summary must not be empty")
        if not self.rationale.strip():
            raise CardValidationError("Rationale must not be empty")
        if not self.edge_cases:
            raise CardValidationError("At least one edge case is required")

    def to_markdown(self) -> str:
        """Render the card as deterministic markdown."""

        self.validate()
        lines = [
            f"# {self.title}",
            "",
            f"**Scope:** {self.scope}",
            f"**Review status:** {self.status.value}",
            f"**Requires review:** {'yes' if self.requires_review else 'no'}",
            "",
            "## Summary",
            "",
            self.summary.strip(),
            "",
            "## Rationale",
            "",
            self.rationale.strip(),
            "",
            "## Edge Cases",
            "",
        ]
        for case in self.edge_cases:
            lines.append(f"- {case.strip()}")
        if self.reviewer_notes:
            lines.extend(["", "## Reviewer Notes", ""])
            for note in self.reviewer_notes:
                lines.append(f"- {note.strip()}")
        lines.extend([
            "",
            "## Traceability",
            "",
        ])
        if self.traceability.graph_nodes:
            lines.append("**Graph nodes:**")
            for node in self.traceability.graph_nodes:
                lines.append(f"- `{node}`")
        if self.traceability.artifacts:
            lines.append("**Artifacts:**")
            for artifact in self.traceability.artifacts:
                lines.append(f"- `{artifact}`")
        if self.traceability.metrics:
            lines.append("**Metrics:**")
            for metric in self.traceability.metrics:
                lines.append(f"- `{metric}`")
        lines.append("")
        return "\n".join(lines)

    def checksum(self) -> str:
        """Generate a stable checksum for the rendered markdown."""

        content = self.to_markdown().encode("utf-8")
        return hashlib.sha256(content).hexdigest()


@dataclass(frozen=True)
class ExplainCardMetadata:
    """Metadata persisted alongside rendered cards."""

    identifier: str
    scope: str
    status: CardStatus
    requires_review: bool
    checksum: str
    mode: str
    generator: str
    traceability: CardTraceability
    review_history: Tuple[Dict[str, str], ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.identifier,
            "scope": self.scope,
            "status": self.status.value,
            "requires_review": self.requires_review,
            "checksum": self.checksum,
            "mode": self.mode,
            "generator": self.generator,
            "traceability": self.traceability.to_dict(),
            "review_history": list(self.review_history),
        }


def deterministic_card_id(scope: str, title: str) -> str:
    """Create a deterministic identifier for a card."""

    digest = hashlib.sha1(f"{scope}:{title}".encode("utf-8")).hexdigest()
    return f"card:{scope}:{digest[:12]}"


def ensure_all_cards_valid(cards: Iterable[ExplainCard]) -> None:
    """Validate a collection of cards."""

    for card in cards:
        card.validate()
