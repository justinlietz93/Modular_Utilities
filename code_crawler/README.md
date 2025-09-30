# Code Crawler Utility (Phase 1)

The Code Crawler now delivers a deterministic, privacy-first analysis pipeline designed for AI-assisted development. Every run produces a reproducible manifest, metrics bundle, delta report, and structured context packages suitable for LLM ingestion.

## Key Features

- **Versioned configuration model** with privacy, feature, threshold, source, and output options.
- **Timestamped run spaces** containing manifests, metrics, bundles, logs, badges, and summaries.
- **Incremental scanning** backed by content-addressable caching and precise delta reporting.
- **Metrics ingestion** for tests (JUnit), coverage (LCOV/Cobertura), lint, and security tools (SARIF).
- **Quality gates** that can enforce thresholds without impacting default runs.
- **Deterministic bundle builder** with rich metadata headers and size/line guards.
- **Structured logging** with privacy-aware redaction and configurable retention.
- **Repository knowledge graph** exports in JSON-LD/GraphML with optional diffing and targeted scopes.
- **Automated diagrams** derived from the knowledge graph with Mermaid/PlantUML/Graphviz templates, deterministic fallbacks, caching, and accessibility enforcement.
- **Explain cards** distilling architecture, quality, and test insights into reviewable Markdown with provenance-rich metadata and optional offline local-model enrichment.
- **Non-code asset processing** with local OCR/caption/transcription, metadata-rich indexes, and reviewer-ready asset cards wired into the knowledge graph.

## Quickstart

```bash
python -m code_crawler --input . --preset all
```

Common options:

- `--allow-network` – opt-in to outbound network access.
- `--include/--ignore` – control source selection.
- `--no-incremental` / `--force-rebuild` – bypass the cache when needed.
- `--metrics-test` / `--metrics-coverage` / `--metrics-lint` / `--metrics-security` – provide artifacts for ingestion.
- `--min-coverage`, `--max-failed-tests`, `--max-lint-warnings`, `--max-critical-vulns` – configure quality gates.
- `--preset` – choose bundle presets (`all`, `tests`, `dependencies`, `api`).
- `--no-graph` – skip knowledge graph emission for the current run.
- `--graph-scope` – restrict graph generation to `full`, `code`, `dependencies`, or `tests` scopes.
- `--graph-no-tests` / `--graph-include-tests` – explicitly exclude or include tests regardless of preset.
- `--graph-diff` / `--no-graph-diff` – force-enable or disable graph diff generation.
- `--no-diagrams` – disable diagram generation while keeping graph outputs.
- `--diagram-preset` – select one or more diagram presets (`architecture`, `dependencies`, `tests`).
- `--diagram-format` – request additional render formats (`svg`, `png`).
- `--diagram-theme` – choose `auto`, `light`, or `dark` accessibility themes.
- `--diagram-concurrency` – bound renderer parallelism for local toolchains.
- `--explain-cards` / `--no-explain-cards` – opt in or disable explain card generation (disabled by default).
- `--card-mode` – switch between deterministic `template` mode and `local-llm` (offline adapter) mode.
- `--card-scope` – repeatable flag to restrict explain cards to specific scopes (`architecture`, `quality`, `tests`).
- `--card-require-review` / `--card-auto-approve` – enforce manual review or mark cards as approved once generated.
- `--card-enable-local-model` – allow the generator to call a configured local model adapter when `--card-mode local-llm` is set.
- `--card-local-model` – filesystem path to the local weights/binary used by the adapter (never downloaded automatically).
- `--assets` / `--no-assets` – enable or disable non-code asset extraction (disabled by default).
- `--asset-preview` – cap the number of characters retained in asset previews and index entries.
- `--asset-cards` / `--no-asset-cards` – control whether reviewer-facing asset cards are generated alongside raw extracts.

Configuration files can be supplied via `--config` (JSON). All outputs live under `code_crawler_runs/<timestamp>/` with subdirectories for manifests, metrics, bundles, badges, gates, delta, graphs, and summaries.

## Installation

Install the CLI directly from the repository root using standard Python tooling.

```bash
pip install .
```

For contributor workflows, install the development extras or use the provided Makefile helper:

```bash
pip install -e .[dev]
# or
make setup
```

This publishes the `code-crawler` console script exposed in `pyproject.toml`.

## Environment Setup

```bash
pip install -e .[dev]
pytest
```

Or leverage the convenience wrappers:

```bash
make setup
make test
```

The pinned development requirements capture async HTTP tooling (`aiohttp`, `pytest-aiohttp`, `pytest-asyncio`), progress indicators (`alive-progress`), and Unicode helpers (`emoji`) required for the repository test matrix.

## Run Outputs

Each run emits:

1. **Manifest** – schema-backed record of inputs, tool versions, hashes, and produced artifacts.
2. **Delta report** – JSON report detailing added, changed, removed, and unchanged files.
3. **Metrics summary** – aggregated counts for tests, coverage, lint, and security data.
4. **Quality gates** – pass/fail status when thresholds are enabled.
5. **Badges** – static SVG assets for coverage and test health (opt-in).
6. **Knowledge graph exports** – JSON-LD + GraphML representations of modules, entities, dependencies, and artifacts.
7. **Graph diff report** – optional JSON + Markdown change sets comparing the latest run with the prior graph.
8. **Diagram suite** – Mermaid/PlantUML/DOT templates alongside rendered SVG/PNG assets and a metadata index capturing probes, accessibility themes, and generation diagnostics.
9. **Bundles** – deterministic text packages with metadata headers and synopsis fields.
10. **Asset extracts** – `assets/index.json`, per-asset text previews, metadata manifests, and optional reviewer cards when enabled.
11. **Explain cards** – Markdown rationale notes plus `cards/index.json` and per-card metadata documenting traceability, review status, and generation mode.
12. **Run summary** – Markdown overview including “How it was made” details.

Re-running on unchanged inputs uses cached digests to skip redundant work and produces byte-identical bundles.

## Current Status Snapshot

- ✅ Repository tests pass locally on Python 3.12 (`pytest`).
- ✅ Phase 1 hard validations hold: deterministic bundles, manifest emission, and privacy defaults remain intact.
- ✅ Architecture guardrails respected — no files exceed 500 LOC and layering boundaries remain unchanged.
- ✅ Phase 2 Task 7 foundations in progress: knowledge graph domain, builder, diff tooling, and CLI workflows are active with validation tests.
- ✅ CLI packaging ready: `pyproject.toml` exposes an installable `code-crawler` entry point and wheel builds succeed locally.
- ✅ Diagram pipeline operational: cached templates, renderer probes, accessible themes, and manifest registration verified via automated tests.
- ✅ Phase 3 asset pipeline landed: OCR/caption/transcription and asset cards ship with local-only defaults, CLI toggles, knowledge graph integration, and regression tests.

## Diagram Generation & Renderer Setup

The diagram generator translates the knowledge graph into multiple visual formats per run:

| Preset | Formats | Description |
| ------ | ------- | ----------- |
| `architecture` | Mermaid, PlantUML | Module-to-module and component-to-dependency relationships |
| `dependencies` | Graphviz DOT | Test coverage fan-out and dependency surfaces |
| `tests` | PlantUML | Deterministic activity views for discovered tests |

Rendered assets and their source templates are written to `runs/<timestamp>/diagrams/` alongside `metadata.json`, which records:

- renderer availability probes (Mermaid CLI, PlantUML, Graphviz `dot`),
- accessibility themes applied (`light`, `dark`),
- per-template digests, cache hits, and diagnostics.

### Local Renderer Installation (Offline Friendly)

- **Mermaid CLI:** `npm install -g @mermaid-js/mermaid-cli`
- **PlantUML:** `brew install plantuml` (macOS) / `scoop install plantuml` (Windows) / download the standalone JAR.
- **Graphviz (`dot`):** `apt install graphviz` (Debian/Ubuntu) / `brew install graphviz` (macOS) / `choco install graphviz` (Windows).

When these binaries are unavailable, the `LocalDiagramRenderer` falls back to deterministic SVG/PNG renderers to keep runs offline-friendly. The metadata file flags fallbacks so you can re-render with native tools later without breaking reproducibility.

### Accessibility Validation

Diagram themes are WCAG-checked for contrast ratios and font sizing. Violations raise runtime errors, ensuring generated outputs remain legible in both light and dark contexts. Customize themes via `--diagram-theme` or update the domain presets if stricter guidelines are required.

## Non-code Assets & Reviewer Cards

Enable non-code asset extraction with `--assets` to process documents, images, audio, and video files discovered during the crawl. The pipeline remains local-first and privacy-preserving:

- **Documents** – lightweight OCR uses offline text extraction with configurable preview lengths (`--asset-preview`).
- **Images** – deterministic captions rely on file metadata (type, dimensions, byte size) and avoid outbound calls.
- **Audio/Video** – local analyzers surface duration and format metadata for `.wav` and other media without streaming data remotely.

Each run emits:

- `assets/index.json` – inventory of discovered assets, summaries, and references to extracted text and metadata.
- `assets/<asset-id>/extracted.txt` – normalized text preview suitable for downstream bundle inclusion.
- `assets/<asset-id>/metadata.json` – provenance, checksums, and analyzer diagnostics.
- `assets/cards/` (optional) – reviewer cards with Markdown summaries and metadata (toggle via `--asset-cards/--no-asset-cards`).

Asset nodes and cards are stitched into the knowledge graph, enabling diagrams, bundles, and explain cards to reference non-code artefacts consistently. Because all processing happens locally, sensitive documents never leave the run directory.

## Explain Cards & Review Workflow

Explain cards translate the knowledge graph, metrics bundle, and current run artifacts into reviewer-friendly Markdown. Generation is **disabled by default**; enable it with `--explain-cards` or by setting `features.enable_explain_cards` in your configuration file.

- **Scopes:** use `--card-scope` multiple times (or configure `explain_cards.scopes`) to select `architecture`, `quality`, and/or `tests` perspectives.
- **Modes:**
  - `template` (default) yields deterministic summaries seeded entirely from the knowledge graph and metrics.
  - `local-llm` activates the offline adapter when both `--card-enable-local-model` and `--card-local-model /path/to/weights` are provided. If the model path is missing, the generator falls back to `template-fallback` mode and records the behaviour in metadata.
- **Outputs:** each run writes Markdown cards, per-card metadata JSON, and an aggregated `cards/index.json` under `runs/<timestamp>/cards/`.
- **Review workflow:** metadata includes a `review_history` array seeded with `review_pending`. After editing a card, update the Markdown content and amend the corresponding metadata file (`status`, `requires_review`, and append to `review_history`) to capture reviewer identity and decision time. Approved cards should set `status` to `approved`.
- **Checklist:** follow [`EXPLAIN_CARD_REVIEW_CHECKLIST.md`](./EXPLAIN_CARD_REVIEW_CHECKLIST.md) to record manual approvals and store provenance alongside metadata updates.
- **Traceability:** metadata references related knowledge graph nodes, bundle identifiers, and metrics keys so reviewers can trace insights back to their sources.

Because explain cards may summarize sensitive code, they inherit the crawler’s privacy defaults: no outbound calls occur unless a local model path is explicitly supplied, and all artifacts stay within the run directory for manual inspection.

## Testing

```bash
pytest --cov=code_crawler --cov-report=term-missing
```

Ensure coverage remains above 95% for the newly added components. All tests must pass on supported Python runtimes.

## Makefile Targets

Use the provided shortcuts to keep workflows consistent:

| Target | Description |
| ------ | ----------- |
| `make setup` | Create a virtual environment and install the project with dev extras. |
| `make test` | Run the pytest suite. |
| `make cov` | Execute pytest with coverage reporting. |
| `make run` | Execute a minimal local crawl against the `code_crawler/` package. |
| `make lint` | Run Ruff and MyPy checks over sources and tests. |
| `make docs` | Refresh CLI help text under `build/cli_help.txt`. |
| `make clean` | Remove the virtual environment, build outputs, and cached run directories. |
| `make wheel` | Build a distributable wheel using `python -m build`. |
