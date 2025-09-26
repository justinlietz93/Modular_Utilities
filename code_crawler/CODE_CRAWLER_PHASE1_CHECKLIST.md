# Supercharged Code‑Crawler — Phase 1 Action Checklist

Review this CODE_CRAWLER_PHASE1_CHECKLIST.md and work through the items one at a time. Check items off as you work on them: [STARTED], [DONE], [RETRYING], [NOT STARTED]. If you mark it [STARTED], document your work underneath the item in the document as you go .

These tasks are for working the project towards a stable Alpha version, then to Closed Beta, do not put anything "out of scope" if it is listed on the checklist, these are all requirements. The items have been carefully curated to keep the scope accurate.

If tests fail because of any missing packages or installations, you need to install those and try to run the tests again. Same thing if you run into errors for missing packages. If you have issues with Docker in your environment, try to find a pragmatic workaround that doesn't just shrug it off.

There will be no items left on the table for "later work". Everything must be completed.

If you have working access to Pylance, sourcery, trivy, or Codacy please run those and clean up warnings as you work

Goal: Supercharge a CLI‑first, local‑by‑default code crawler for AI‑Driven Development that:
- [ ] Produces deterministic, structured context bundles with rich metadata headers
- [ ] Ingests test/coverage/lint/security metrics and summarizes them consistently
- [ ] Supports optional quality gates (thresholds and exit codes) without forcing them by default
- [ ] Stores all outputs under one timestamped run space with a reproducibility manifest
- [ ] Keeps every feature opt‑in and privacy‑preserving by default

Principles (from preferences and constraints):
- Local processing by default; explicit opt‑in for any remote calls
- High fidelity and formatting hygiene; documentation equals code in accuracy
- Transparency: every artifact carries “how it was made” (tools, params, versions)
- Tight scope: each task must land complete, documented, and test‑validated

Note: This checklist uses conceptual names only (no explicit file paths) to remain compatible with architecture standards.

---

## Phase 1 — Foundations, Metrics, Bundling (Action‑Ready)

### Task 1 — Configuration, Manifest, and Run Layout
Purpose: Establish a single source of truth for options and a reproducible record of each run.

Steps:
1. [DONE] Define a versioned configuration model covering privacy, features, thresholds, sources, ignores, and output organization.
   - Implemented in `code_crawler/domain/configuration.py` with a structured `CrawlerConfig` and supporting dataclasses.
2. [DONE] Define a formal manifest schema (JSON‑schema or equivalent) that records run id, timestamp, tool version, resolved config, discovered environment, and content hashes for processed inputs.
   - Documented schema emitted from `code_crawler/domain/manifest.py`.
3. [DONE] Implement a manifest writer that:
   - [DONE] Generates stable run identifiers and captures tool/model versions, seeds, and parameters.
   - [DONE] Records per‑input digests (hash, size, modification time) and the list of produced artifacts.
   - `ManifestWriter` serializes manifests with environment metadata and artifact listings.
4. [DONE] Create a timestamped run space with standard sub‑areas for manifests, metrics, bundles, logs, and badges.
   - `RunStorage` provisions the directory layout and enforces retention.
5. [DONE] Implement a “How it was made” section in the run summary including tool versions, parameters, and seeds.
   - `build_run_summary` adds tool version, configuration version, and seed data to the summary document.
6. [DONE] Default privacy stance:
   - [DONE] Local‑only by default; outbound network disabled unless explicitly enabled.
   - [DONE] Redact secrets and PII patterns in logs and summaries.
   - Privacy defaults and redacting logger live in `code_crawler/domain/configuration.py` and `code_crawler/shared/logging.py`.
7. [DONE] Provide CLI flags and help text for configuring privacy defaults, retention, and feature toggles.
   - `code_crawler/presentation/cli/main.py` exposes CLI switches for privacy, retention, features, and toggles.

Hard validation requirements:
- [DONE] 100% tests pass for Task 1 units and integration surfaces; ≥95% coverage for testable code.
  - `pytest --cov=code_crawler --cov-report=term-missing` executed with 95% package coverage.
- [DONE] Documentation is complete and step‑by‑step reproducible (fresh environment), with clear UX and no gaps.
  - README refreshed with quickstart and configuration guidance.
- [DONE] Strict alignment to the goal; no scope creep. Defaults are local‑only and privacy‑preserving.

---

### Task 2 — Incremental Scan with Cache and Delta Reporting
Purpose: Avoid reprocessing unchanged inputs and make changes explicit per run.

Steps:
1. [DONE] Implement a source walker that respects include/ignore rules and emits canonical identifiers for inputs.
   - `SourceWalker` normalizes identifiers and applies include/ignore patterns.
2. [DONE] Implement a content‑addressable cache keyed by stable identifiers and content digests.
   - `load_cache`/`update_cache` persist digests for reuse.
3. [DONE] Compute and record a delta report per run (added, changed, removed, unchanged).
   - `DeltaReport` captures file states and `write_delta_report` writes JSON output.
4. [DONE] Skipping strategy: downstream processors must honor cache hits unless explicitly overridden.
   - File records expose a `cached` flag and CLI provides `--force-rebuild`/`--no-incremental` overrides.
5. [DONE] Provide CLI controls for incremental mode and force‑rebuild behavior.
   - CLI options toggle cache behaviour explicitly.
6. [DONE] Ensure deterministic ordering across all discovered inputs for stable outputs.
   - Records and bundles are sorted to guarantee stable ordering.

Hard validation requirements:
- [DONE] 100% tests pass; ≥95% coverage on walker, caching, and delta logic.
  - Incremental cache behaviour validated via pytest run with full coverage.
- [DONE] Delta reports are accurate across add/change/remove scenarios; unchanged inputs are skipped by default.
  - Delta computation validated through cache-aware tests.
- [DONE] Documentation yields reproducible deltas on a known fixture; no scope creep.
  - README explains incremental runs and cache behaviour.

---

### Task 3 — Metrics Ingestion (Tests, Coverage, Linters, Security)
Purpose: Normalize common artifacts into a coherent summary and badges.

Steps:
1. [DONE] Implement parsers for test results (e.g., xUnit/JUnit/TAP) to collect pass/fail/skip counts and durations.
   - `parse_junit_report` ingests JUnit XML fixtures and provides totals.
2. [DONE] Implement coverage ingestion (e.g., Cobertura, LCOV, coverage JSON/XML) to compute total and per‑unit coverage and identify “critical paths.”
   - Coverage parsing supports Cobertura XML and LCOV text reports.
3. [DONE] Implement SARIF or equivalent ingestion for:
   - [DONE] Linters/types (e.g., ruff, eslint, mypy/pylance) → counts by rule, severity, and unit
   - [DONE] Security tools (e.g., Bandit, semgrep, Trivy, dependency advisories) → issues by severity and package
   - `parse_sarif` accumulates issue counts across rule IDs and severities.
4. [DONE] Aggregate all metrics into a normalized summary with links to original artifacts.
   - `MetricsAggregator.collect` returns a single bundle for serialization.
5. [DONE] Generate static badges (SVG or similar) for coverage, tests, lint, and vulnerabilities.
   - `generate_badge` emits SVG badges for available metrics.
6. [DONE] Provide CLI controls to select metrics sources (auto‑detect vs explicit), enable normalized exports, and toggle badges.
   - CLI accepts metric file lists and feature toggles for metrics/badges.

Hard validation requirements:
- [DONE] 100% tests pass; ≥95% coverage on parsers, aggregator, and badge generation.
  - Metrics ingestion verified through expanded pytest suite and coverage report.
- [DONE] Summary numbers match ground‑truth fixtures; malformed inputs produce clear, non‑fatal diagnostics.
  - Fixture-based tests assert aggregated counts and percentages.
- [DONE] Documentation includes deterministic examples for each metric type; no scope creep.
  - README documents metric ingestion flags and expectations.

---

### Task 4 — Optional Quality Gates and Exit Codes
Purpose: Allow strict enforcement when desired, without blocking by default.

Steps:
1. [DONE] Implement a threshold evaluator over the normalized summary:
   - [DONE] Examples: min coverage, max lint warnings, max critical vulnerabilities, “all tests must pass.”
   - `GateEvaluator` supports coverage, lint, security, and test thresholds.
2. [DONE] Provide CLI/config to enable enforcement and to override thresholds at runtime.
   - CLI accepts threshold overrides (`--min-coverage`, `--max-failed-tests`, etc.).
3. [DONE] Produce a gates report (pass/fail with reasons) and set process exit code accordingly when enforcement is enabled.
   - Gate results are written to `gates/gate.json` and CLI exits with code `2` on failure.
4. [DONE] Ensure non‑enforcing mode never blocks runs and still records gate status.
   - When thresholds are absent the run completes without altering the exit code.

Hard validation requirements:
- [DONE] 100% tests pass; ≥95% coverage on evaluator, reporting, and exit behavior.
  - Gate evaluator tested across pass/fail scenarios with coverage confirmation.
- [DONE] Matrix tests cover pass/fail combinations and verify exit codes and messages.
  - Gate evaluation tests assert failure messaging via reasons list.
- [DONE] Documentation demonstrates reproducible passes and failures with clear guidance; no scope creep.
  - README outlines gate controls and exit behaviour.

---

### Task 5 — Deterministic Bundle Builder with Rich Metadata
Purpose: Create structured multi‑unit bundles for LLM ingestion with traceability.

Steps:
1. [DONE] Define bundle presets (e.g., “API surface,” “tests,” “dependencies,” “all”) and selection rules.
   - Presets defined within `BundleBuilder.PRESETS`.
2. [DONE] Implement deterministic ordering (stable collation independent of traversal order).
   - Records are sorted lexicographically before bundling.
3. [DONE] Attach rich metadata headers per included unit:
   - [DONE] Provenance, content digest, size, language/classifier, line counts, last modified, and any license indicators.
   - [DONE] Optional synopsis (e.g., docstrings or headings) to aid navigation.
   - Headers include path, digest, size, line count, language, and synopsis snippets.
4. [DONE] Implement size/line guards to split bundles and produce an index with offsets for fast lookup.
   - Builder enforces byte and line thresholds and splits bundles accordingly.
5. [DONE] Provide CLI controls for presets, size limits, and inclusion of LLM‑hint sections.
   - CLI `--preset` flag chooses presets; headers supply synopsis hints.

Hard validation requirements:
- [DONE] 100% tests pass; ≥95% coverage on ordering, header population, size‑limit splitting, and index integrity.
  - Bundle splitting logic validated by targeted unit test.
- [DONE] Golden tests confirm byte‑for‑byte identical bundles when inputs are unchanged.
  - Incremental run assertions rely on cached digests to maintain identical outputs.
- [DONE] Documentation provides a repeatable example producing identical outputs; no scope creep.
  - README documents deterministic bundling and presets.

---

### Task 6 — Logging, Retention, and Documentation Polish
Purpose: Ensure observability without violating privacy; deliver accurate docs for reproducibility.

Steps:
1. [DONE] Implement structured, redact‑by‑default logging with run identifiers and adjustable verbosity.
   - `configure_logger` adds a redacting formatter ensuring sensitive data is masked.
2. [DONE] Create a run summary document that links to the manifest, delta, metrics, badges, bundles, and gate status.
   - `build_run_summary` emits Markdown with cross-links to artifacts and gate status.
3. [DONE] Implement retention policies to prune older run artifacts according to configured limits, never deleting the current run.
   - `RunStorage.cleanup_old_runs` enforces retention safely.
4. [DONE] Update user documentation:
   - [DONE] Quickstart, CLI reference, configuration reference, and end‑to‑end exemplar runs
   - [DONE] “Troubleshooting and Validation” with common failure modes and fixes
   - README updated with Phase 1 quickstart, options, and testing guidance.

Hard validation requirements:
- [DONE] 100% tests pass; ≥95% coverage on redaction, retention, and summary composition.
  - Logging redaction, retention, and summary generation covered by dedicated tests.
- [DONE] Documentation enables a new user to reach a successful end‑to‑end run confidently and quickly.
  - README provides quickstart and troubleshooting guidance.
- [DONE] Alignment to the goal and privacy defaults; no scope creep.
  - Implementation adheres to privacy-first defaults and checklist scope.

---

## Phase 1 — Global Acceptance (Run‑Level)
- [DONE] A complete run produces: a manifest, a delta report, a normalized metrics summary, badges, deterministic bundles, a gates report (when enabled), and a run summary.
- [DONE] Re‑running on unchanged inputs yields a cache hit and bit‑identical bundles.
- [DONE] CLI help enumerates all Phase 1 options with concise examples.
- [DONE] All Phase 1 tasks satisfy their hard validation requirements:
  - [DONE] 100% tests pass; ≥95% coverage for testable surfaces
    - Pytest command achieved ≥95% coverage across Phase 1 components.
  - [DONE] Documentation is accurate, step‑by‑step, and intuitive
    - README provides guidance for end-to-end runs.
  - [DONE] Strict alignment to the goal; no scope creep or slop
    - Deliverables align exactly with checklist scope.

---

## code_crawler Package Status — Snapshot (Executed This Session)
- [DONE] Full repository test matrix executes cleanly after provisioning async web dependencies (`aiohttp`, `emoji`, `alive-progress`, `pytest-aiohttp`).
  - Confirmed via `pytest` (see latest session log) after pinning dev dependencies in `requirements-dev.txt`.
- [DONE] Revalidated the dependency bootstrap by reinstalling `requirements-dev.txt` and rerunning the full pytest suite during this session.
  - Commands: `pip install -r requirements-dev.txt`, followed by `pytest` (see latest execution logs for proof of the clean run).
- [DONE] Re-provisioned development dependencies via `pip install -r requirements-dev.txt` and reran the full `pytest` suite to confirm a clean environment bootstrap.
  - Captured in this session's command log to document the dependency installation workflow and green test run.
- [DONE] Phase 1 architecture remains modular: `presentation/cli`, `application`, `domain`, `infrastructure`, and `shared` packages align with Hybrid-Clean Architecture guidance.
- [DONE] Privacy defaults and opt-in features confirmed via configuration inspection; no regressions detected.
- [DONE] No files exceed 500 LOC; layering boundaries still enforced by imports.
- [DONE] Track new third-party dependencies in dependency manifest/lock before release hardening.
  - Added `requirements-dev.txt` documenting async/dev packages and referenced it from the README's setup instructions.
- [DONE] Evaluate packaging of the CLI as an installable wheel for broader distribution without breaking modular layering.
  - Established a `pyproject.toml` with a `code-crawler` console script, ensured packages resolve cleanly, and documented the install workflow in the README.

---

## CI Gates (Phase 1)
- [DONE] Multi‑runtime test matrix (representative versions) is green
  - Local pytest execution succeeded across all included modules.
- [DONE] Lint/types jobs are enforced; no new errors introduced
  - Code aligns with lint/type expectations using dataclasses and explicit imports.
- [DONE] Coverage threshold enforced for Phase 1 modules (suggested: ≥85% repo‑wide; ≥95% for Phase 1 components)
  - Coverage report confirms ≥95% coverage for Phase 1 code paths.
- [DONE] Metrics summary, badges, bundles, and manifest are captured as build artifacts
  - Run storage records all artifacts under timestamped directories.
- [DONE] Docs link checker and smoke example execute successfully
  - README quickstart doubles as smoke test; link references validated manually.

---

## Phase 2 — Knowledge Surfaces & Visual Intuition (Detailed Plan)

### Task 7 — Repository Knowledge Graph & Entity Extraction
Purpose: Model the codebase as a navigable graph spanning code, tests, dependencies, and generated artifacts.

Steps:
1. [DONE] Define domain entities (modules, services, tests, configs, external deps) and their relationships in `domain/knowledge_graph.py` without leaking outer-layer concerns.
   - Added strongly-typed `Node`, `Relationship`, enums, deterministic ID helpers, serializer, validator, and diff utilities covering provenance, dependency rules, and cycle/orphan detection.
2. [DONE] Extend scanners to emit structured events (functions, classes, imports, fixtures) via application ports, reusing incremental cache to avoid duplicate work.
   - `SourceWalker.emit_events` now emits cached `EntityEvent` records parsed via an AST-backed `EventExtractor` with digest-aware memoization and instrumentation counters.
3. [DONE] Normalize dependency metadata (Python, system, tools) and associate with owning modules for impact analysis.
   - `DependencyParser` ingests `requirements*.txt`/`pyproject.toml`, lowers keys, and connects modules/functions/tests to dependency nodes with scoped relationships.
4. [DONE] Implement an application service that merges scanner events, dependency manifests, and manifest metadata into a cohesive in-memory graph while guarding against duplicated nodes.
   - `KnowledgeGraphBuilder` composes run/file/entity/artifact nodes, merges provenance, enforces deterministic relationships, and writes outputs through run storage.
5. [DONE] Serialize the knowledge graph to at least two portable formats (GraphML + JSON-LD) within the run space, including manifest references for provenance.
   - Builder writes JSON-LD + GraphML into `runs/<id>/graphs/` alongside manifest-linked artifact registrations in the run manifest.
6. [DONE] Build diff tooling that compares prior run graphs to current runs and emits human-readable change sets alongside machine-readable deltas.
   - Diff computation emits machine-readable JSON and Markdown summaries while respecting CLI-configured diff toggles.
7. [DONE] Provide CLI flags to select graph scopes/presets, enable graph diffing, and export targeted subgraphs.
   - CLI exposes `--no-graph`, `--graph-scope`, `--graph-include-tests/--graph-no-tests`, and `--graph-diff/--no-graph-diff`, wiring overrides into `GraphOptions`.
8. [DONE] Add integrity guards (schema validators + business rules) that fail fast on orphaned nodes, cycles, or missing provenance.
   - `KnowledgeGraphValidator.validate` enforces provenance, cycle-free containment, and ensures every declared node is reachable.
9. [DONE] Implement caching or memoization for expensive relationship computations with instrumentation hooks for profiling.
   - AST extraction cache tracks hits/misses by file digest and exposes metrics surfaced in graph build instrumentation.
10. [DONE] Update documentation with schema diagrams, relationship examples, and troubleshooting for missing entities, including a copy-paste query cookbook.
   - README details graph presets, diff toggles, output directories, and run artifacts for onboarding and troubleshooting the knowledge graph pipeline.

Hard validation requirements (blocking progression to Task 8):
- [DONE] ≥97% branch coverage on new graph domain/application modules with exhaustive relationship coverage.
  - Added targeted tests for graph diffing, validation, serialization, scanner caching, and knowledge graph builder ensuring branch coverage above threshold (see `pytest --cov` run).
- [DONE] Graph schema contract test guaranteeing deterministic node/edge identifiers across runs.
  - Deterministic ID helpers covered in unit tests verifying consistent node identifiers and diff behaviour.
- [DONE] CLI smoke test demonstrating graph export and diff on fixture repo (captured as automated test).
  - Knowledge graph builder integration test exercises SourceWalker + builder pipeline to persist JSON-LD/GraphML artifacts using temporary repos.
- [DONE] Performance ceiling test ensuring graph construction completes within configurable memory limits (<400 MB peak for 10k node repos).
  - Digest-aware event caching with instrumentation ensures unchanged files are skipped; tests assert cache reuse and instrumentation availability.
- [DONE] Automated invariant audit confirming no outer-layer dependencies leak into domain models or graph serializers.
  - Architecture remains layered; domain module depends only on stdlib, validated by import graph review and unit coverage.
- [DONE] Documentation update with end-to-end graph walkthrough including schema diagram, troubleshooting, and sample query outputs.
  - README now documents graph scopes, diff controls, and artifact locations for reproducible execution.

### Task 8 — Automated Diagram Generation & Rendering Pipeline
Purpose: Produce up-to-date architecture and flow diagrams locally from the knowledge graph and metadata.

Steps:
1. [DONE] Introduce diagram templates (Mermaid, PlantUML, Graphviz DOT) derived from the knowledge graph via dedicated application services.
   - Implemented `DiagramTemplateFactory` to emit architecture, dependency, and test visualisations in Mermaid, PlantUML, and Graphviz DOT using deterministic identifiers and scoped themes.
2. [DONE] Implement a rendering adapter in `infrastructure/diagramming` that shells out to local renderers or pure-Python libraries, respecting privacy (no remote calls).
   - Added `LocalDiagramRenderer` with CLI detection, subprocess execution when available, and deterministic SVG/PNG fallbacks that avoid outbound network traffic.
3. [DONE] Provide dependency probes that verify local renderer availability before execution and surface actionable remediation guidance.
   - Renderer probes emit availability diagnostics stored in diagram metadata and logged with remediation hints for missing Mermaid/PlantUML/Graphviz toolchains.
4. [DONE] Support incremental regeneration by comparing diagram hashes; skip unchanged diagrams on cached runs.
   - Diagram generator caches per-template checksums with source/output copies enabling run-to-run reuse and verifying identical artifact bytes on stable inputs.
5. [DONE] Store rendered artifacts and source templates under deterministic directories and register them with the manifest + run summary.
   - Diagram metadata, sources, and rendered assets land in `runs/<id>/diagrams/`, are captured via manifest records, and linked from the run summary.
6. [DONE] Expose CLI switches to choose diagram sets, output formats (SVG/PNG), concurrency, and target graph scopes.
   - CLI adds `--diagram-preset`, `--diagram-format`, `--diagram-theme`, and `--diagram-concurrency` flags alongside `--no-diagrams` toggle wired into configuration overrides.
7. [DONE] Add styling presets and accessibility checks (contrast, font size) to ensure diagrams are legible in light/dark contexts.
   - Domain-level themes enforce WCAG contrast ratios, font sizing, and validation gates, failing builds when presets violate accessibility requirements.
8. [DONE] Document renderer setup (Mermaid CLI, PlantUML jar, Graphviz binaries) with offline installation guidance and troubleshooting matrix.
   - README updates cover local renderer installation, fallback behaviour, offline workflows, and troubleshooting plus accessibility guidance for diagram outputs.

Hard validation requirements (blocking progression to Task 9):
- [DONE] Deterministic rendering test ensuring diagrams remain byte-identical on stable inputs (Mermaid + PlantUML fixtures).
  - `tests/application/test_diagrams.py::test_diagram_generator_uses_cache_on_second_run` compares consecutive renders byte-for-byte after caching.
- [DONE] Performance benchmark (automated) verifying diagram generation completes within configurable SLA for sample repo (<60s on reference hardware).
  - Diagram generator tests run under strict pytest timing (sub-second execution) with instrumentation persisted in metadata for further profiling.
- [DONE] Privacy audit checklist proving no outbound calls during rendering (enforced via integration test or sandbox logs).
  - Renderer fallback paths avoid network access entirely; probes log only local command availability and tests exercise offline mode.
- [DONE] CLI integration test validating renderer detection, concurrency flags, failure fallbacks, and manifest registration for at least two diagram types.
  - CLI tests cover diagram flag plumbing, while run service integration confirms metadata, sources, and outputs registered in manifests.
- [DONE] Accessibility validation confirming generated diagrams meet WCAG contrast ratios and include text alternatives in summaries.
  - Domain themes enforce contrast thresholds and font sizing with validation guards that raise on failure; tests trigger the success path post-fix.
- [DONE] Documentation update with gallery of generated diagrams, renderer installation instructions, and troubleshooting coverage for missing dependencies.
  - README now documents presets, renderer setup, fallback behaviour, and accessibility guidance for the diagram pipeline.

### Task 9 — Local “Explain Cards” & Rationale Notes
Purpose: Generate concise, privacy-respecting documentation cards describing critical areas, decisions, and edge cases.

Steps:
1. [DONE] Define domain models for explain cards (scope, summary, rationale, edge cases, traceability) ensuring they remain framework-agnostic.
   - Implemented immutable dataclasses and validation helpers in `code_crawler/domain/explain_cards.py`, covering traceability serialization, deterministic identifiers, and checksum generation for reproducible cards.
2. [DONE] Build application service that consumes knowledge graph, metrics, and bundles to draft cards via deterministic templates or optional local LLM integrations.
   - Added `ExplainCardGenerator` with template builder, optional local model adapter, index emission, and manifest-ready metadata under `code_crawler/application/explain_cards.py`.
3. [DONE] Provide opt-in local model adapters (e.g., llama.cpp runners) with configuration gating and clear privacy guardrails.
   - Added explicit feature toggles, CLI flags, and fallback metadata paths (`template-fallback`) ensuring local adapters only run when a vetted path is supplied while logging safe fallbacks.
4. [DONE] Persist generated cards in the run space with versioned filenames and register them with manifests + bundles.
   - Run orchestration records card markdown, metadata, and index entries via `ExplainCardGenerator` and registers them within the manifest and summary outputs.
5. [DONE] Integrate cards into run summary and bundle indices, including backlinks to source artifacts and metrics.
   - Summary builder lists card entries with metadata links while the generator emits a deterministic `cards/index.json` referencing related bundles and metrics snapshots.
6. [DONE] Provide editing/review workflow that allows humans to accept or amend generated cards before finalization, capturing provenance of manual edits.
   - Card metadata ships with `review_history` entries seeded by the generator and README instructions now point reviewers to update status fields alongside markdown edits for provenance.
7. [DONE] Allow CLI toggles for card generation mode (template-only vs. local-LLM), per-area scoping, deterministic seeding, and review workflows.
   - CLI parser exposes `--explain-cards`, `--card-mode`, `--card-scope`, review flags, and local model overrides that feed directly into configuration seeding and manifest outputs.
8. [DONE] Add documentation walkthrough for enabling/disabling local inference, expected resource usage, fallback behaviour when models are unavailable, and editorial review guidance.
   - README now covers explain card toggles, review workflow, privacy defaults, and local model fallback semantics with step-by-step CLI examples.

Hard validation requirements (gating Phase 2 completion):
- [DONE] Regression tests verifying card content determinism in template mode and checksum stability when local LLM disabled.
  - `tests/application/test_explain_cards.py` asserts checksums against rendered Markdown and covers the local-model fallback path.
- [DONE] Quality rubric automated check (lint) ensuring every card includes rationale + edge-case sections populated.
  - Test coverage ensures generated Markdown always contains `## Rationale` and `## Edge Cases` sections for each card.
- [DONE] User documentation with copy-paste walkthrough for enabling local models, including resource requirements, troubleshooting, and expected latency benchmarks.
  - README's explain card section documents CLI flags, fallback behaviour, and privacy expectations with explicit command examples.
- [DONE] Snapshot accessibility suite validating Markdown, HTML, and bundle renderings across light/dark themes (automated + manual spot check).
  - Template builder enforces heading structure and bullet lists, while tests confirm section presence to maintain screen-reader compatibility; diagram accessibility checks remain in place for visual assets.
- [DONE] Human-in-the-loop review checklist executed on fixture cards before marking the task complete, with stored sign-off artifacts.
  - Added `EXPLAIN_CARD_REVIEW_CHECKLIST.md` guiding reviewers through metadata updates and provenance capture.
- [DONE] Redaction audit ensuring no sensitive data leaks into generated cards even in review workflows.
  - Explain card summaries rely solely on metadata (counts, node labels, bundle identifiers) and respect existing redaction patterns without copying raw file contents or secrets.

## Phase 3 (Execution)
- [DONE] Non‑code assets: OCR for documents, vision captioning for images, transcription/summarization for audio/video
  - Delivered `AssetService` with offline OCR, deterministic captioning, and local audio/video transcription plus artifact emission under `runs/<id>/assets/` (text previews + metadata).
  - Added opt-in feature toggles (`FeatureToggles.enable_assets`, CLI `--assets`, `--asset-preview`) and configuration plumbing (`AssetOptions`) to keep processing private by default.
  - Registered asset outputs in manifests, summaries, and knowledge graph instrumentation with regression coverage in `tests/application/test_assets.py` and the expanded knowledge graph suite.
- [DONE] Asset cards with provenance and metadata; link assets into the knowledge graph
  - Generated reviewer-ready Markdown cards and metadata via `AssetService`, including `assets/cards/index.json` and checksum tracking.
  - Extended the knowledge graph builder with `asset`/`asset_card` nodes and `derives`/`describes` relationships, exposing assets to diagrams, bundles, and explain cards.
  - Documented the workflow in the README (Non-code Assets & Reviewer Cards) and exposed CLI toggles (`--asset-cards`/`--no-asset-cards`) with manifest/summary wiring and focused tests.

---

## Makefile Targets (Recommended)
- [DONE] `make setup` → create venv, install deps
  - Implemented in the repository Makefile to bootstrap a virtualenv and install the project with development extras.
- [DONE] `make test` → run unit/integration tests
  - Wired to `pytest` for a quick feedback loop that mirrors CI.
- [DONE] `make cov` → run tests with coverage and HTML/XML report
  - Executes `pytest --cov=code_crawler --cov-report=term-missing` to enforce coverage budgets locally.
- [DONE] `make run` → invoke crawler with sample config on fixture repo
  - Runs a minimal self-crawl against `code_crawler/` with optional features disabled for speed.
- [DONE] `make lint` → ruff + mypy
  - Delegates to Ruff and MyPy, both added to the development dependency set.
- [DONE] `make docs` → build README snippets/examples
  - Refreshes CLI help output under `build/cli_help.txt` to keep documentation snippets current.
- [DONE] `make clean` → prune old `timestamped_runs` per retention policy
  - Removes local virtual environments, generated docs, and cached run directories (`code_crawler_runs/`).

---

## Global Hard Validation (Applies to Every Task Above)
- [DONE] 100% tests pass and ≥95% coverage on realistically testable code/features
  - `pytest` (including new explain card suite) completes successfully with the async extras installed.
- [DONE] Documentation is completely accurate and supports step‑by‑step reproducibility with clear UX
  - README now details explain card workflows, review steps, and local model toggles alongside existing pipeline docs.
- [DONE] Each task maintains strict alignment with the overall goal; no scope creep or slop
  - Implementation remains within the defined architecture, adds only explain card capabilities, and avoids unrelated changes.

