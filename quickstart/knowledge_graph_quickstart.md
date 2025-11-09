# Knowledge Graph Utility - Quick Start Guide

## What is the Knowledge Graph Utility?

The Knowledge Graph utility helps you organize, search, and explore your documents using semantic similarity. It automatically extracts concepts from your files, builds connections between related ideas, and lets you query your knowledge base using natural language.

Perfect for:
- Research paper management
- Documentation search
- Code knowledge base
- Note-taking and idea organization
- Content discovery and exploration

## Installation

Make sure you have the modular-utilities package installed:

```bash
cd Modular_Utilities
pip install -e .
```

Verify installation:
```bash
knowledge-graph --help
```

## Quick Start in 5 Minutes

### 1. Create Your First Graph

```bash
knowledge-graph --create --graph-id research-notes
```

This creates a new, empty knowledge graph called "research-notes".

### 2. Add Content

Point the utility to a directory with text files:

```bash
knowledge-graph --input ~/Documents/research-papers/ --graph-id research-notes
```

For recursive scanning of subdirectories:
```bash
knowledge-graph --input ~/Documents/research-papers/ --graph-id research-notes --recursive
```

Supported file types: `.txt`, `.md`, `.py`, `.js`, `.java`, `.cpp`, `.html`, `.json`, `.yaml`, and more.

### 3. Query Your Knowledge

Search using natural language:
```bash
knowledge-graph --query "machine learning neural networks" --graph-id research-notes
```

The utility will:
1. Find semantically similar content
2. Rank results by relevance
3. Display the top matches with scores

### 4. Save Results

Export query results to a file:
```bash
knowledge-graph --query "quantum computing" --output quantum-notes.md
```

Results are saved in markdown format with scores and source attribution.

## Common Workflows

### Research Paper Management

```bash
# Create a graph for your research
knowledge-graph --create --graph-id physics-research

# Ingest all papers
knowledge-graph --input ~/Papers/ --recursive --graph-id physics-research

# Query specific topics
knowledge-graph --query "black hole entropy" --output entropy-notes.md

# View statistics
knowledge-graph --metadata --graph-id physics-research
```

### Code Documentation Search

```bash
# Create a documentation graph
knowledge-graph --create --graph-id project-docs

# Ingest markdown docs
knowledge-graph --input ./docs/ --recursive --graph-id project-docs

# Find relevant documentation
knowledge-graph --query "authentication middleware" --graph-id project-docs

# Extract related concepts
knowledge-graph --query "API endpoints" --subgraph api-subgraph.json --hops 2
```

### Exploratory Research

```bash
# Random query for serendipitous discovery
knowledge-graph --query --random --graph-id research-notes

# Extract a subgraph around interesting concepts
knowledge-graph --query "emergence complexity" --subgraph emergence.json --hops 3
```

## Advanced Features

### Subgraph Extraction

Extract a focused subgraph around a query:
```bash
knowledge-graph --query "neural architecture search" \
  --subgraph nas-graph.json \
  --hops 3 \
  --graph-id ml-papers
```

The `--hops` parameter controls how many "degrees of separation" to include from the best match.

### Metadata and Statistics

View graph statistics:
```bash
knowledge-graph --metadata --graph-id research-notes
```

Query-specific metadata:
```bash
knowledge-graph --query "deep learning" --metadata metrics.md
```

Save metadata to a file:
```bash
knowledge-graph --metadata stats.md --graph-id research-notes
```

### Graph Maintenance (Pruning)

Remove rarely-used nodes:
```bash
knowledge-graph --prune --bottom 10 -Y --graph-id research-notes
```

Remove frequently-queried nodes (to reduce noise):
```bash
knowledge-graph --prune --top 5 -Y --graph-id research-notes
```

### Settings Management

Control verbosity:
```bash
knowledge-graph --settings --verbosity high
```

Verbosity levels:
- `off`: Errors only
- `low`: Minimal output, prompts only
- `medium`: Standard output (default)
- `high`: Include metrics
- `max`: Full debug output

Disable query tracking:
```bash
knowledge-graph --settings --db off
```

### Graph Operations

Dump graph to file:
```bash
knowledge-graph --dump --graph-id research-notes
```

Delete a graph:
```bash
knowledge-graph --delete --graph-id old-graph -Y
```

## Using Without Graph ID

The utility remembers the last graph you worked with:

```bash
# Create and use a graph
knowledge-graph --create --graph-id notes

# Later, you can omit --graph-id
knowledge-graph --query "important concept"
knowledge-graph --metadata
knowledge-graph --prune --bottom 15 -Y
```

## Tips and Best Practices

### 1. Organize by Project
Create separate graphs for different projects or research areas:
```bash
knowledge-graph --create --graph-id project-alpha
knowledge-graph --create --graph-id project-beta
knowledge-graph --create --graph-id personal-notes
```

### 2. Regular Pruning
Prune graphs periodically to maintain quality:
```bash
# Remove bottom 10% every few months
knowledge-graph --prune --bottom 10 -Y
```

### 3. Export Important Queries
Save frequently-used queries:
```bash
knowledge-graph --query "core concepts" --output core-concepts.md
knowledge-graph --query "key findings" --output findings.md
```

### 4. Use Subgraphs for Focus
Extract subgraphs for specific topics:
```bash
knowledge-graph --query "topic X" --subgraph topic-x.json --hops 2
```

### 5. High Verbosity for Learning
Start with high verbosity to understand the system:
```bash
knowledge-graph --settings --verbosity high
knowledge-graph --query "test query"
```

## Troubleshooting

### Graph not found
Make sure you created the graph first:
```bash
knowledge-graph --create --graph-id my-graph
```

### No results from query
- Try broader search terms
- Check if content was successfully ingested
- View metadata to ensure nodes exist

### Poor query results
- The similarity algorithm works best with substantial content
- Try different phrasings
- Check that your query matches the vocabulary in your documents

## File Storage

All graphs are stored in `.knowledge_graphs/`:
- `<graph-id>.json`: Graph data
- `queries.db`: Query history (SQLite)
- `settings.json`: User preferences
- `.last_graph`: Last accessed graph

You can back up this directory to preserve your graphs.

## Next Steps

- Explore the [full README](../knowledge_graph/README.md) for complete documentation
- Check out example workflows in this guide
- Experiment with different pruning strategies
- Try combining with other utilities in the Modular Utilities suite

## Example: Complete Workflow

```bash
# 1. Create a research graph
knowledge-graph --create --graph-id ai-research

# 2. Ingest papers
knowledge-graph --input ~/Research/AI-Papers/ --recursive --graph-id ai-research

# 3. Enable high verbosity
knowledge-graph --settings --verbosity high

# 4. Query and explore
knowledge-graph --query "transformer architectures attention mechanism"

# 5. Save important findings
knowledge-graph --query "transformer" --output transformers-overview.md

# 6. Extract a subgraph for detailed study
knowledge-graph --query "attention mechanism" --subgraph attention.json --hops 3

# 7. View statistics
knowledge-graph --metadata

# 8. Random exploration
knowledge-graph --query --random

# 9. Prune after a month
knowledge-graph --prune --bottom 15 -Y

# 10. Export the full graph
knowledge-graph --dump
```

Happy knowledge graphing! 🧠📊
