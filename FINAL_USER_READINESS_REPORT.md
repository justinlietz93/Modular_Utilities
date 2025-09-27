# Code Crawler Phase 1 — Final User Readiness Report

## Manual Validation Summary
- **Date:** 2025-09-27 (UTC)
- **Environment:** Python 3.12 on containerized Linux (same toolchain as automated tests).
- **Commands Executed:**
  - `python -m code_crawler --input code_crawler --preset all --metrics-test /tmp/manual_validation/junit.xml --metrics-coverage /tmp/manual_validation/coverage.lcov --metrics-lint /tmp/manual_validation/lint.sarif --metrics-security /tmp/manual_validation/security.sarif --explain-cards --assets --card-mode template --card-auto-approve --asset-preview 200 --diagram-format png --diagram-theme dark --seed 42 --min-coverage 80 --max-failed-tests 0 --max-lint-warnings 0 --max-critical-vulns 0` → **exit code 2** (quality gate failure expected to verify enforcement).
  - `python -m code_crawler --input code_crawler --preset all --metrics-test /tmp/manual_validation/junit.xml --metrics-coverage /tmp/manual_validation/coverage.lcov --metrics-lint /tmp/manual_validation/lint.sarif --metrics-security /tmp/manual_validation/security.sarif --explain-cards --assets --card-mode template --card-auto-approve --asset-preview 200 --diagram-format png --diagram-theme dark --seed 42 --min-coverage 50 --max-failed-tests 2 --max-lint-warnings 2 --max-critical-vulns 2` → **exit code 0** (all validations passed with relaxed thresholds).
- **Run IDs Captured:**
  - `20250927-042600` — gate failure scenario with full artifact capture.
  - `20250927-042608` — full-feature success baseline recorded for readiness.

## Feature Verification Highlights
- **Reproducible Bundles & Summary Traceability:** Run `20250927-042608` produced six deterministic bundles recorded in `summary/summary.md`, alongside manifest, delta, metrics, badges, diagrams, assets, explain cards, and knowledge graph exports under the timestamped run directory. This confirms full pipeline integrity when every optional feature is enabled simultaneously.
- **Metrics Aggregation & Gate Behaviour:** The merged metrics JSON for the success run reported totals of three tests (two pass, one fail), 66.67% coverage, two lint findings, and two security findings. The strict run’s gate file enumerated all four threshold violations with descriptive reasons, while the relaxed run confirmed a clean pass, validating both failure and pass paths.
- **Knowledge Graph & Diagrams:** The readiness run generated JSON-LD + GraphML graph exports plus a diff report, and produced PlantUML/Mermaid/Graphviz diagram sources with PNG fallbacks registered in the summary. Renderer availability warnings surfaced as expected due to missing native binaries, but the deterministic fallback assets were still emitted.
- **Explain Cards & Reviewer Workflow:** Architecture, quality, and test cards were created with approved status and traceability metadata, demonstrating deterministic template output under template mode with review auto-approval toggled on for this validation.
- **Non-code Assets:** Asset extraction indexed README, checklist, architecture rules, and explain card reviewer guide documents with previews, metadata manifests, and reviewer cards, confirming the document OCR flow and card generation operate end-to-end.
- **Privacy Defaults:** Despite enabling every feature, the run summary continued to report “Privacy: local only,” validating that outbound network access remains disabled unless explicitly opted in.

## Outstanding Items / Observations
- External diagram renderers (Mermaid CLI, PlantUML, Graphviz) are not installed in this environment; fallback renderers were used and logged with remediation guidance. Users needing native renderer fidelity should install the recommended binaries before production usage.
- No additional defects or regressions were observed. Automated `pytest` remains green.

## Go/No-Go Recommendation
**Go.** The CLI delivers deterministic outputs across bundles, metrics, knowledge graph, diagrams, explain cards, assets, and summaries with both passing and failing gate scenarios validated manually. Users can proceed to closed-beta validation with confidence, provided they install any optional renderer tooling required for custom diagram fidelity.
