# Code Crawler Quickstart Guide 🚀

The Code Crawler is your AI-powered codebase analysis companion that transforms your repository into actionable intelligence. Think of it as a CT scan for your code—revealing structure, dependencies, quality metrics, and insights that power your entire development workflow.

## Table of Contents
- [Why Code Crawler?](#why-code-crawler)
- [Installation](#installation)
- [Quick Start (30 seconds)](#quick-start-30-seconds)
- [Core Features & Use Cases](#core-features--use-cases)
- [Real-World Workflow Examples](#real-world-workflow-examples)
- [Advanced Configuration](#advanced-configuration)
- [CI/CD Integration](#cicd-integration)
- [Pro Tips & Best Practices](#pro-tips--best-practices)

## Why Code Crawler?

### The Problem It Solves
Ever onboarded a new developer who spent days just understanding your codebase structure? Or struggled to feed your entire project context to an LLM because of token limits? Code Crawler solves these problems by creating **deterministic, privacy-first, LLM-ready** snapshots of your repository.

### What Makes It Priceless
- **Zero-Config Intelligence**: Run once, get comprehensive insights
- **Privacy-First**: All processing happens locally—no data leaves your machine
- **Deterministic**: Same input = same output, every time
- **Incremental**: Smart caching means blazing-fast subsequent runs
- **LLM-Optimized**: Bundles are perfectly formatted for AI consumption

## Installation

```bash
# From the repository root
pip install -e .

# Or using the Makefile
make setup

# Verify installation
code-crawler --version
```

## Quick Start (30 seconds)

```bash
# Analyze your entire codebase with all features
code-crawler --input . --preset all

# Results appear in: code_crawler_runs/<timestamp>/
```

That's it! You now have:
- 📊 Comprehensive metrics dashboard
- 🗺️ Knowledge graph of your entire codebase
- 📈 Visual architecture diagrams
- 📦 LLM-ready context bundles
- 📝 Explain cards summarizing key insights

## Core Features & Use Cases

### 1. **LLM Context Generation** 🤖

**The Use Case**: You're using GitHub Copilot, ChatGPT, or Claude to help with code. Token limits are killing you.

```bash
# Generate compact, information-dense bundles
code-crawler --input . --preset api --no-diagrams --no-explain-cards
```

**What You Get**:
- Deterministic text bundles with metadata headers
- Size/line guards prevent overwhelming the LLM
- Structured context perfect for RAG pipelines

**Workflow Integration**:
```bash
# Generate context for a specific feature
code-crawler --input . --include "src/auth/**" --preset all

# Copy the bundle to clipboard for ChatGPT
cat code_crawler_runs/latest/bundles/api_bundle.txt | pbcopy

# Now paste into ChatGPT with your question!
```

### 2. **Onboarding New Developers** 👨‍💻

**The Use Case**: New team member needs to understand your 50k+ line codebase.

```bash
# Generate comprehensive onboarding package
code-crawler --input . --preset all --explain-cards
```

**What You Get**:
- **Explain Cards**: Markdown summaries of architecture, quality, tests
- **Architecture Diagrams**: Visual module relationships
- **Dependency Graph**: See what connects to what
- **Test Coverage**: Know what's protected and what's not

**Onboarding Workflow**:
1. Share the `run_summary.md` first—high-level overview
2. Point them to explain cards for deep dives
3. Use diagrams for visual learners
4. Reference knowledge graph for "where is X defined?"

### 3. **Quality Gates & CI/CD** ✅

**The Use Case**: Prevent bugs before merge—enforce quality thresholds.

```bash
# Integrate test results and enforce gates
code-crawler --input . \
  --metrics-test junit-report.xml \
  --metrics-coverage coverage.xml \
  --min-coverage 80 \
  --max-failed-tests 0 \
  --max-lint-warnings 10
```

**What Happens**:
- ❌ Fails if coverage drops below 80%
- ❌ Fails if any tests fail
- ❌ Fails if lint warnings exceed 10
- ✅ Generates beautiful badges for your README

**CI/CD Pipeline Example** (GitHub Actions):
```yaml
- name: Run Tests
  run: pytest --junitxml=junit.xml --cov --cov-report=xml

- name: Quality Gates
  run: |
    code-crawler --input . \
      --metrics-test junit.xml \
      --metrics-coverage coverage.xml \
      --min-coverage 80 \
      --max-failed-tests 0
  continue-on-error: false

- name: Upload Badges
  uses: actions/upload-artifact@v3
  with:
    name: badges
    path: code_crawler_runs/latest/badges/*.svg
```

### 4. **Dependency Analysis** 📦

**The Use Case**: Track how changes ripple through your codebase.

```bash
# Generate dependency graph focused view
code-crawler --input . --preset dependencies --graph-scope dependencies
```

**What You Get**:
- JSON-LD representation of all dependencies
- GraphML for importing into Neo4j/Gephi
- DOT diagrams showing dependency fans
- Delta reports: what changed since last run

**Practical Applications**:
- **Impact Analysis**: "If I change module X, what breaks?"
- **Refactoring Safety**: See all consumers before modifying an API
- **Security Audits**: Track external dependency usage

### 5. **Incremental Scanning & Delta Reports** 📊

**The Use Case**: Daily standup—what changed in the codebase overnight?

```bash
# First run (baseline)
code-crawler --input .

# Make changes, commit, then run again
code-crawler --input .

# Check the delta report
cat code_crawler_runs/latest/delta/report.json
```

**Delta Report Shows**:
```json
{
  "added": ["src/new_feature.py"],
  "modified": ["src/auth.py", "tests/test_auth.py"],
  "removed": ["src/deprecated.py"],
  "unchanged": 1247
}
```

**Workflow Integration**:
- Run nightly in CI
- Email delta report to team
- Auto-generate "what changed" for changelogs

### 6. **Knowledge Graph + Graph Diffs** 🧠

**The Use Case**: Treat your codebase as a queryable database.

```bash
# Generate full knowledge graph with diffs
code-crawler --input . --graph-scope full --graph-diff
```

**What You Get**:
- **Nodes**: Modules, classes, functions, tests, dependencies
- **Edges**: Imports, calls, extends, implements, tests
- **Formats**: JSON-LD (queryable), GraphML (visualizable)

**Power User Tricks**:

**Query with jq**:
```bash
# Find all modules that import 'requests'
cat code_crawler_runs/latest/graphs/knowledge_graph.json | \
  jq '.edges[] | select(.type=="imports" and .target=="requests") | .source'

# Count test coverage by module
cat code_crawler_runs/latest/graphs/knowledge_graph.json | \
  jq '[.nodes[] | select(.type=="module")] | group_by(.name) | map({module: .[0].name, tests: [.[] | select(.tested)] | length})'
```

**Import into Neo4j**:
```cypher
// Load GraphML into Neo4j for powerful queries
CALL apoc.import.graphml("code_crawler_runs/latest/graphs/knowledge_graph.graphml", {})
```

### 7. **Non-Code Asset Processing** 🖼️

**The Use Case**: Your repo has docs, images, config files—not just code.

```bash
# Process everything including assets
code-crawler --input . --assets --asset-cards
```

**What You Get**:
- **Document OCR**: Extract text from PDFs, images
- **Image Metadata**: Dimensions, format, file size
- **Asset Cards**: Reviewer-friendly summaries
- **Knowledge Graph Integration**: Assets linked to code

**Creative Use Cases**:
- **Documentation Search**: Index all docs for semantic search
- **License Compliance**: Scan images for copyright info
- **Config Audits**: Track all .env, .json, .yaml files

### 8. **Diagram Generation** 📐

**The Use Case**: Architecture reviews need visuals, not text walls.

```bash
# Generate all diagram types
code-crawler --input . --diagram-preset architecture dependencies tests
```

**Diagram Types**:

| Preset | Format | Shows |
|--------|--------|-------|
| `architecture` | Mermaid, PlantUML | Module-to-module relationships |
| `dependencies` | Graphviz DOT | External dependency fans |
| `tests` | PlantUML | Test coverage flows |

**Rendering Options**:
```bash
# Want PNGs for presentation?
code-crawler --input . --diagram-format svg png

# Dark mode for your IDE?
code-crawler --input . --diagram-theme dark

# Accessibility-first (WCAG compliance)
code-crawler --input . --diagram-theme auto  # Validates contrast ratios
```

**Installation of Renderers** (optional, for native rendering):
```bash
# Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# PlantUML (macOS)
brew install plantuml

# Graphviz
brew install graphviz  # macOS
apt install graphviz   # Ubuntu
```

### 9. **Explain Cards (AI Summaries)** 💡

**The Use Case**: Executive summary of your codebase for non-technical stakeholders.

```bash
# Generate explain cards (disabled by default)
code-crawler --input . --explain-cards --card-scope architecture quality tests
```

**Modes**:
1. **Template Mode** (default): Deterministic, no LLM calls
2. **Local LLM Mode**: Enriched with local model (privacy-preserved)

**Example Local LLM Setup**:
```bash
# Using a local Ollama model
code-crawler --input . \
  --explain-cards \
  --card-mode local-llm \
  --card-enable-local-model \
  --card-local-model /path/to/local/model
```

**Review Workflow**:
1. Cards start with `review_pending` status
2. Reviewer edits Markdown + updates metadata
3. Mark as `approved` when satisfied
4. Metadata tracks full review history

**Use Cases**:
- **Stakeholder Reports**: "Here's what's in our codebase"
- **Security Audits**: "Explain authentication flow"
- **Technical Debt**: "What needs refactoring?"

## Real-World Workflow Examples

### Workflow 1: The Daily Developer

```bash
#!/bin/bash
# save as: daily_scan.sh

# Morning routine: check what changed
code-crawler --input . --preset all --no-diagrams

# Open the run summary
open code_crawler_runs/latest/run_summary.md

# Check delta report
cat code_crawler_runs/latest/delta/report.json | jq '.modified'

# If significant changes, regenerate diagrams
if [ $(cat code_crawler_runs/latest/delta/report.json | jq '.modified | length') -gt 5 ]; then
  code-crawler --input . --preset all --no-bundles --no-metrics
fi
```

### Workflow 2: The Code Reviewer

```bash
# Before reviewing PR #123
git checkout feature/new-auth

# Run scan on feature branch
code-crawler --input . --preset all

# Compare with main branch
git checkout main
code-crawler --input . --preset all

# Diff the knowledge graphs
diff code_crawler_runs/<feature_timestamp>/graphs/knowledge_graph.json \
     code_crawler_runs/<main_timestamp>/graphs/knowledge_graph.json
```

### Workflow 3: The Technical Writer

```bash
# Generate comprehensive documentation bundle
code-crawler --input . \
  --preset all \
  --explain-cards \
  --card-scope architecture \
  --assets \
  --asset-cards

# Convert explain cards to publishable docs
cp code_crawler_runs/latest/cards/*.md docs/architecture/
cp code_crawler_runs/latest/diagrams/*.svg docs/images/
```

### Workflow 4: The Open Source Maintainer

```bash
# Pre-release checklist
code-crawler --input . \
  --preset all \
  --metrics-test pytest_report.xml \
  --metrics-coverage coverage.xml \
  --min-coverage 90 \
  --max-failed-tests 0

# Generate badges for README
cp code_crawler_runs/latest/badges/*.svg .github/badges/

# Update ARCHITECTURE.md with latest diagram
cp code_crawler_runs/latest/diagrams/architecture.svg docs/
```

## Advanced Configuration

### Configuration File Approach

Create `code_crawler_config.json`:
```json
{
  "source": {
    "include": ["src/**", "lib/**"],
    "ignore": ["**/node_modules/**", "**/.*", "**/__pycache__/**"]
  },
  "features": {
    "enable_incremental": true,
    "enable_bundles": true,
    "enable_graph": true,
    "enable_diagrams": true,
    "enable_explain_cards": false
  },
  "thresholds": {
    "min_coverage": 80.0,
    "max_failed_tests": 0,
    "max_lint_warnings": 10,
    "max_critical_vulnerabilities": 0
  },
  "bundles": {
    "presets": ["all"],
    "max_file_size": 1048576,
    "max_lines": 10000
  },
  "knowledge_graph": {
    "scope": "full",
    "include_tests": true,
    "enable_diff": true
  },
  "diagrams": {
    "presets": ["architecture", "dependencies"],
    "formats": ["svg", "png"],
    "theme": "auto",
    "concurrency": 4
  },
  "explain_cards": {
    "scopes": ["architecture", "quality"],
    "mode": "template",
    "require_review": true
  },
  "assets": {
    "enabled": false,
    "preview_length": 500,
    "generate_cards": false
  }
}
```

**Use it**:
```bash
code-crawler --config code_crawler_config.json
```

### Privacy & Security Configuration

```json
{
  "privacy": {
    "allow_network": false,
    "redact_patterns": [
      "password",
      "api_key",
      "secret",
      "token"
    ]
  },
  "output": {
    "retention_days": 30
  }
}
```

## CI/CD Integration

### GitHub Actions Complete Example

`.github/workflows/code_analysis.yml`:
```yaml
name: Code Analysis

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  analyze:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
      with:
        fetch-depth: 0  # Full history for delta reports
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install Code Crawler
      run: |
        pip install -e .
    
    - name: Run Tests with Coverage
      run: |
        pip install pytest pytest-cov
        pytest --junitxml=junit.xml --cov --cov-report=xml
    
    - name: Run Code Crawler
      run: |
        code-crawler --input . \
          --preset all \
          --metrics-test junit.xml \
          --metrics-coverage coverage.xml \
          --min-coverage 75 \
          --max-failed-tests 0 \
          --explain-cards \
          --card-scope quality
    
    - name: Upload Analysis Results
      uses: actions/upload-artifact@v3
      with:
        name: code-analysis
        path: code_crawler_runs/latest/
    
    - name: Comment PR with Results
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          const summary = fs.readFileSync('code_crawler_runs/latest/run_summary.md', 'utf8');
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: summary
          });
```

### GitLab CI Example

`.gitlab-ci.yml`:
```yaml
code_analysis:
  stage: test
  image: python:3.10
  script:
    - pip install -e .
    - pytest --junitxml=junit.xml --cov --cov-report=xml
    - code-crawler --input . --preset all --metrics-test junit.xml --metrics-coverage coverage.xml
  artifacts:
    paths:
      - code_crawler_runs/latest/
    reports:
      junit: junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

## Pro Tips & Best Practices

### 🎯 Tip 1: Use Presets Wisely
```bash
# Development: Fast, focused
code-crawler --input . --preset api --no-diagrams

# CI/CD: Comprehensive quality checks
code-crawler --input . --preset all --min-coverage 80

# Documentation: Visual + narrative
code-crawler --input . --preset all --explain-cards --diagram-format png
```

### 🎯 Tip 2: Leverage Incremental Mode
```bash
# First run is slow, but creates cache
code-crawler --input .

# Subsequent runs are lightning fast (only scans changes)
code-crawler --input .

# Force full rebuild when needed
code-crawler --input . --force-rebuild
```

### 🎯 Tip 3: Smart Include/Ignore Patterns
```bash
# Focus on production code only
code-crawler --input . --include "src/**" --ignore "**/test_*.py"

# Analyze a specific microservice
code-crawler --input . --include "services/auth/**"

# Exclude generated code
code-crawler --input . --ignore "**/generated/**" "**/dist/**"
```

### 🎯 Tip 4: Chain Commands for Workflows
```bash
# Generate bundle, then search it
code-crawler --input . --preset api && \
  grep "authentication" code_crawler_runs/latest/bundles/api_bundle.txt

# Run analysis, then copy results to docs
code-crawler --input . --preset all && \
  cp code_crawler_runs/latest/diagrams/*.svg docs/architecture/
```

### 🎯 Tip 5: Use Aliases for Common Tasks
```bash
# Add to ~/.bashrc or ~/.zshrc
alias cc='code-crawler --input .'
alias cc-full='code-crawler --input . --preset all'
alias cc-quick='code-crawler --input . --no-diagrams --no-bundles --no-explain-cards'

# Now just type:
cc-quick
```

### 🎯 Tip 6: Knowledge Graph Queries
```bash
# Find all untested modules
cat code_crawler_runs/latest/graphs/knowledge_graph.json | \
  jq '.nodes[] | select(.type=="module" and .tested==false) | .name'

# Find circular dependencies
cat code_crawler_runs/latest/graphs/knowledge_graph.json | \
  jq '[.edges[] | select(.type=="imports")] | group_by(.source) | map(select(length > 1))'

# Find highest-impact modules (most dependencies)
cat code_crawler_runs/latest/graphs/knowledge_graph.json | \
  jq '[.edges[] | .target] | group_by(.) | map({module: .[0], count: length}) | sort_by(.count) | reverse | .[0:10]'
```

### 🎯 Tip 7: Badge Generation for READMEs
```bash
# Generate badges
code-crawler --input . --metrics-coverage coverage.xml

# Add to README.md
echo "![Coverage](./code_crawler_runs/latest/badges/coverage.svg)" >> README.md
```

### 🎯 Tip 8: Privacy-First Practices
```bash
# Ensure no network calls
code-crawler --input . --no-allow-network

# Redact sensitive patterns
code-crawler --input . --config privacy_config.json

# Clear old runs regularly
find code_crawler_runs -type d -mtime +30 -exec rm -rf {} \;
```

## Common Issues & Solutions

### Issue: "Cache is stale"
**Solution**: Force a rebuild
```bash
code-crawler --input . --force-rebuild
```

### Issue: "Diagram rendering failed"
**Solution**: Install native renderers OR rely on fallback
```bash
# Option 1: Install renderers
npm install -g @mermaid-js/mermaid-cli
brew install plantuml graphviz

# Option 2: Use fallback (automatic)
# Code Crawler will use deterministic SVG/PNG generators
```

### Issue: "Bundle too large for LLM"
**Solution**: Adjust bundle settings
```bash
code-crawler --input . --preset api --include "src/core/**"
```

### Issue: "Quality gates failing"
**Solution**: Check the gates report
```bash
cat code_crawler_runs/latest/gates/report.json
# Fix issues, then re-run
```

## Next Steps

1. **Start Simple**: `code-crawler --input . --preset all`
2. **Explore Results**: Open `code_crawler_runs/latest/run_summary.md`
3. **Integrate CI/CD**: Add quality gates to your pipeline
4. **Customize**: Create a config file for your team's needs
5. **Automate**: Set up daily runs + dashboard updates

## Community & Resources

- 📖 [Full Documentation](../code_crawler/README.md)
- 🏗️ [Architecture Rules](../code_crawler/ARCHITECTURE_RULES.md)
- ✅ [Explain Card Review Checklist](../code_crawler/EXPLAIN_CARD_REVIEW_CHECKLIST.md)
- 🐛 [Report Issues](https://github.com/justinlietz93/Modular_Utilities/issues)

---

**Happy Crawling! 🕷️** Your codebase intelligence is now at your fingertips.
