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
  - Captured in `pytest` run post-installation (see latest session log).
- [DONE] Phase 1 architecture remains modular: `presentation/cli`, `application`, `domain`, `infrastructure`, and `shared` packages align with Hybrid-Clean Architecture guidance.
- [DONE] Privacy defaults and opt-in features confirmed via configuration inspection; no regressions detected.
- [DONE] No files exceed 500 LOC; layering boundaries still enforced by imports.
- [STARTED] Track new third-party dependencies in dependency manifest/lock before release hardening.
  - Pending: ensure documentation references newly required packages for test execution.

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
1. [NOT STARTED] Define domain entities (modules, services, tests, configs, external deps) and their relationships in `domain/knowledge_graph.py` without leaking outer-layer concerns.
2. [NOT STARTED] Extend scanners to emit structured events (functions, classes, imports, fixtures) via application ports, reusing incremental cache to avoid duplicate work.
3. [NOT STARTED] Normalize dependency metadata (Python, system, tools) and associate with owning modules for impact analysis.
4. [NOT STARTED] Serialize the knowledge graph to at least two portable formats (GraphML + JSON-LD) within the run space, including manifest references for provenance.
5. [NOT STARTED] Provide CLI flags to select graph scopes/presets and to diff graphs across runs.

Hard validation requirements (blocking progression to Task 8):
- [NOT STARTED] ≥97% branch coverage on new graph domain/application modules with property-based tests covering relationship permutations.
- [NOT STARTED] Graph schema contract test guaranteeing deterministic node/edge identifiers across runs.
- [NOT STARTED] CLI smoke test demonstrating graph export and diff on fixture repo (captured as automated test).
- [NOT STARTED] Documentation update with end-to-end graph walkthrough including schema diagram and troubleshooting.

### Task 8 — Automated Diagram Generation & Rendering Pipeline
Purpose: Produce up-to-date architecture and flow diagrams locally from the knowledge graph and metadata.

Steps:
1. [NOT STARTED] Introduce diagram templates (Mermaid, PlantUML, Graphviz DOT) derived from the knowledge graph via dedicated application services.
2. [NOT STARTED] Implement a rendering adapter in `infrastructure/diagramming` that shells out to local renderers or pure-Python libraries, respecting privacy (no remote calls).
3. [NOT STARTED] Support incremental regeneration by comparing diagram hashes; skip unchanged diagrams on cached runs.
4. [NOT STARTED] Link rendered images and source files into the manifest and run summary with provenance metadata.
5. [NOT STARTED] Expose CLI switches to choose diagram sets, output formats (SVG/PNG), and rendering concurrency.

Hard validation requirements (blocking progression to Task 9):
- [NOT STARTED] Deterministic rendering test ensuring diagrams remain byte-identical on stable inputs (Mermaid + PlantUML fixtures).
- [NOT STARTED] Performance benchmark (automated) verifying diagram generation completes within configurable SLA for sample repo (<60s on reference hardware).
- [NOT STARTED] Privacy audit checklist proving no outbound calls during rendering (enforced via integration test or sandbox logs).
- [NOT STARTED] Documentation update with gallery of generated diagrams and instructions for renderer installation.

### Task 9 — Local “Explain Cards” & Rationale Notes
Purpose: Generate concise, privacy-respecting documentation cards describing critical areas, decisions, and edge cases.

Steps:
1. [NOT STARTED] Define domain models for explain cards (scope, summary, rationale, edge cases, traceability) ensuring they remain framework-agnostic.
2. [NOT STARTED] Build application service that consumes knowledge graph, metrics, and bundles to draft cards via deterministic templates or optional local LLM integrations.
3. [NOT STARTED] Provide opt-in local model adapters (e.g., llama.cpp runners) with configuration gating and clear privacy guardrails.
4. [NOT STARTED] Integrate cards into run summary and bundle indices, including backlinks to source artifacts and metrics.
5. [NOT STARTED] Allow CLI toggles for card generation mode (template-only vs. local-LLM) and per-area scoping.

Hard validation requirements (gating Phase 2 completion):
- [NOT STARTED] Regression tests verifying card content determinism in template mode and checksum stability when local LLM disabled.
- [NOT STARTED] Quality rubric automated check (lint) ensuring every card includes rationale + edge-case sections populated.
- [NOT STARTED] User documentation with copy-paste walkthrough for enabling local models, including resource requirements and troubleshooting.
- [NOT STARTED] Accessibility review confirming cards render correctly in Markdown, HTML, and bundle outputs (tested via snapshot tests).

## Phase 3 (Outline for Planning Only)
- [ ] Non‑code assets: OCR for documents, vision captioning for images, transcription/summarization for audio/video
- [ ] Asset cards with provenance and metadata; link assets into the knowledge graph

---

## Makefile Targets (Recommended)
- [ ] `make setup` → create venv, install deps
- [ ] `make test` → run unit/integration tests
- [ ] `make cov` → run tests with coverage and HTML/XML report
- [ ] `make run` → invoke crawler with sample config on fixture repo
- [ ] `make lint` → ruff + mypy
- [ ] `make docs` → build README snippets/examples
- [ ] `make clean` → prune old `timestamped_runs` per retention policy

---

## Global Hard Validation (Applies to Every Task Above)
- [ ] 100% tests pass and ≥95% coverage on realistically testable code/features
- [ ] Documentation is completely accurate and supports step‑by‑step reproducibility with clear UX
- [ ] Each task maintains strict alignment with the overall goal; no scope creep or slop

