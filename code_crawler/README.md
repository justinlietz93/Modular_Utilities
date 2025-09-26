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

Configuration files can be supplied via `--config` (JSON). All outputs live under `code_crawler_runs/<timestamp>/` with subdirectories for manifests, metrics, bundles, badges, gates, delta, and summaries.

## Run Outputs

Each run emits:

1. **Manifest** – schema-backed record of inputs, tool versions, hashes, and produced artifacts.
2. **Delta report** – JSON report detailing added, changed, removed, and unchanged files.
3. **Metrics summary** – aggregated counts for tests, coverage, lint, and security data.
4. **Quality gates** – pass/fail status when thresholds are enabled.
5. **Badges** – static SVG assets for coverage and test health (opt-in).
6. **Bundles** – deterministic text packages with metadata headers and synopsis fields.
7. **Run summary** – Markdown overview including “How it was made” details.

Re-running on unchanged inputs uses cached digests to skip redundant work and produces byte-identical bundles.

## Testing

```bash
pytest --cov=code_crawler --cov-report=term-missing
```

Ensure coverage remains above 95% for the newly added components. All tests must pass on supported Python runtimes.
