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
1. [ ] Define a versioned configuration model covering privacy, features, thresholds, sources, ignores, and output organization.
2. [ ] Define a formal manifest schema (JSON‑schema or equivalent) that records run id, timestamp, tool version, resolved config, discovered environment, and content hashes for processed inputs.
3. [ ] Implement a manifest writer that:
   - [ ] Generates stable run identifiers and captures tool/model versions, seeds, and parameters.
   - [ ] Records per‑input digests (hash, size, modification time) and the list of produced artifacts.
4. [ ] Create a timestamped run space with standard sub‑areas for manifests, metrics, bundles, logs, and badges.
5. [ ] Implement a “How it was made” section in the run summary including tool versions, parameters, and seeds.
6. [ ] Default privacy stance:
   - [ ] Local‑only by default; outbound network disabled unless explicitly enabled.
   - [ ] Redact secrets and PII patterns in logs and summaries.
7. [ ] Provide CLI flags and help text for configuring privacy defaults, retention, and feature toggles.

Hard validation requirements:
- [ ] 100% tests pass for Task 1 units and integration surfaces; ≥95% coverage for testable code.
- [ ] Documentation is complete and step‑by‑step reproducible (fresh environment), with clear UX and no gaps.
- [ ] Strict alignment to the goal; no scope creep. Defaults are local‑only and privacy‑preserving.

---

### Task 2 — Incremental Scan with Cache and Delta Reporting
Purpose: Avoid reprocessing unchanged inputs and make changes explicit per run.

Steps:
1. [ ] Implement a source walker that respects include/ignore rules and emits canonical identifiers for inputs.
2. [ ] Implement a content‑addressable cache keyed by stable identifiers and content digests.
3. [ ] Compute and record a delta report per run (added, changed, removed, unchanged).
4. [ ] Skipping strategy: downstream processors must honor cache hits unless explicitly overridden.
5. [ ] Provide CLI controls for incremental mode and force‑rebuild behavior.
6. [ ] Ensure deterministic ordering across all discovered inputs for stable outputs.

Hard validation requirements:
- [ ] 100% tests pass; ≥95% coverage on walker, caching, and delta logic.
- [ ] Delta reports are accurate across add/change/remove scenarios; unchanged inputs are skipped by default.
- [ ] Documentation yields reproducible deltas on a known fixture; no scope creep.

---

### Task 3 — Metrics Ingestion (Tests, Coverage, Linters, Security)
Purpose: Normalize common artifacts into a coherent summary and badges.

Steps:
1. [ ] Implement parsers for test results (e.g., xUnit/JUnit/TAP) to collect pass/fail/skip counts and durations.
2. [ ] Implement coverage ingestion (e.g., Cobertura, LCOV, coverage JSON/XML) to compute total and per‑unit coverage and identify “critical paths.”
3. [ ] Implement SARIF or equivalent ingestion for:
   - [ ] Linters/types (e.g., ruff, eslint, mypy/pylance) → counts by rule, severity, and unit
   - [ ] Security tools (e.g., Bandit, semgrep, Trivy, dependency advisories) → issues by severity and package
4. [ ] Aggregate all metrics into a normalized summary with links to original artifacts.
5. [ ] Generate static badges (SVG or similar) for coverage, tests, lint, and vulnerabilities.
6. [ ] Provide CLI controls to select metrics sources (auto‑detect vs explicit), enable normalized exports, and toggle badges.

Hard validation requirements:
- [ ] 100% tests pass; ≥95% coverage on parsers, aggregator, and badge generation.
- [ ] Summary numbers match ground‑truth fixtures; malformed inputs produce clear, non‑fatal diagnostics.
- [ ] Documentation includes deterministic examples for each metric type; no scope creep.

---

### Task 4 — Optional Quality Gates and Exit Codes
Purpose: Allow strict enforcement when desired, without blocking by default.

Steps:
1. [ ] Implement a threshold evaluator over the normalized summary:
   - [ ] Examples: min coverage, max lint warnings, max critical vulnerabilities, “all tests must pass.”
2. [ ] Provide CLI/config to enable enforcement and to override thresholds at runtime.
3. [ ] Produce a gates report (pass/fail with reasons) and set process exit code accordingly when enforcement is enabled.
4. [ ] Ensure non‑enforcing mode never blocks runs and still records gate status.

Hard validation requirements:
- [ ] 100% tests pass; ≥95% coverage on evaluator, reporting, and exit behavior.
- [ ] Matrix tests cover pass/fail combinations and verify exit codes and messages.
- [ ] Documentation demonstrates reproducible passes and failures with clear guidance; no scope creep.

---

### Task 5 — Deterministic Bundle Builder with Rich Metadata
Purpose: Create structured multi‑unit bundles for LLM ingestion with traceability.

Steps:
1. [ ] Define bundle presets (e.g., “API surface,” “tests,” “dependencies,” “all”) and selection rules.
2. [ ] Implement deterministic ordering (stable collation independent of traversal order).
3. [ ] Attach rich metadata headers per included unit:
   - [ ] Provenance, content digest, size, language/classifier, line counts, last modified, and any license indicators.
   - [ ] Optional synopsis (e.g., docstrings or headings) to aid navigation.
4. [ ] Implement size/line guards to split bundles and produce an index with offsets for fast lookup.
5. [ ] Provide CLI controls for presets, size limits, and inclusion of LLM‑hint sections.

Hard validation requirements:
- [ ] 100% tests pass; ≥95% coverage on ordering, header population, size‑limit splitting, and index integrity.
- [ ] Golden tests confirm byte‑for‑byte identical bundles when inputs are unchanged.
- [ ] Documentation provides a repeatable example producing identical outputs; no scope creep.

---

### Task 6 — Logging, Retention, and Documentation Polish
Purpose: Ensure observability without violating privacy; deliver accurate docs for reproducibility.

Steps:
1. [ ] Implement structured, redact‑by‑default logging with run identifiers and adjustable verbosity.
2. [ ] Create a run summary document that links to the manifest, delta, metrics, badges, bundles, and gate status.
3. [ ] Implement retention policies to prune older run artifacts according to configured limits, never deleting the current run.
4. [ ] Update user documentation:
   - [ ] Quickstart, CLI reference, configuration reference, and end‑to‑end exemplar runs
   - [ ] “Troubleshooting and Validation” with common failure modes and fixes

Hard validation requirements:
- [ ] 100% tests pass; ≥95% coverage on redaction, retention, and summary composition.
- [ ] Documentation enables a new user to reach a successful end‑to‑end run confidently and quickly.
- [ ] Alignment to the goal and privacy defaults; no scope creep.

---

## Phase 1 — Global Acceptance (Run‑Level)
- [ ] A complete run produces: a manifest, a delta report, a normalized metrics summary, badges, deterministic bundles, a gates report (when enabled), and a run summary.
- [ ] Re‑running on unchanged inputs yields a cache hit and bit‑identical bundles.
- [ ] CLI help enumerates all Phase 1 options with concise examples.
- [ ] All Phase 1 tasks satisfy their hard validation requirements:
  - [ ] 100% tests pass; ≥95% coverage for testable surfaces
  - [ ] Documentation is accurate, step‑by‑step, and intuitive
  - [ ] Strict alignment to the goal; no scope creep or slop

---

## CI Gates (Phase 1)
- [ ] Multi‑runtime test matrix (representative versions) is green
- [ ] Lint/types jobs are enforced; no new errors introduced
- [ ] Coverage threshold enforced for Phase 1 modules (suggested: ≥85% repo‑wide; ≥95% for Phase 1 components)
- [ ] Metrics summary, badges, bundles, and manifest are captured as build artifacts
- [ ] Docs link checker and smoke example execute successfully

---

## Phase 2 (Outline for Planning Only)
- [ ] Knowledge graph of code, tests, dependencies; export in standard graph formats
- [ ] Automatic diagram source generation (e.g., Mermaid/Markmap/PlantUML/Graphviz) with local rendering to images
- [ ] “Explain cards” per area (optional, local models) including rationale and edge‑case notes

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