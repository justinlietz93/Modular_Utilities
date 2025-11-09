# Knowledge Graph Utility

A CLI utility for building, querying, and managing knowledge graphs based on conceptual and semantic similarity.

## Features

- **Create and manage** multiple knowledge graphs
- **Ingest content** from files and directories (with optional recursive parsing)
- **Multi-format support**: Text files, Markdown, PDF documents, and images (with OCR)
- **Semantic querying** using natural language queries
- **Subgraph extraction** with configurable hop distance
- **Metadata tracking** and statistics
- **Graph pruning** to maintain optimal graph size
- **Query tracking** with SQLite database
- **Configurable verbosity** levels
- **Random exploration** for discovering connections

## Installation

### Basic Installation

```bash
pip install -e .
```

### With PDF Support

```bash
pip install -e ".[pdf]"
```

### With Image Support (OCR)

```bash
pip install -e ".[image]"
```

Note: Image OCR requires tesseract to be installed on your system:
- Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
- macOS: `brew install tesseract`
- Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### With Both PDF and Image Support

```bash
pip install -e ".[multimodal]"
```

## Quick Start

### Create a Graph

```bash
knowledge-graph --create --graph-id my-research
```

### Ingest Content

Ingest from a directory:
```bash
knowledge-graph --input research-papers/ --graph-id my-research
```

Ingest recursively (includes PDFs and images if dependencies are installed):
```bash
knowledge-graph --input whole-folder/ --graph-id my-research --recursive
```

### Supported File Formats

The utility automatically detects and processes:
- **Text files**: `.txt`, `.md`, `.markdown`, `.rst`, `.log`
- **Code files**: `.py`, `.js`, `.java`, `.cpp`, `.c`, `.h`, `.sh`, `.bash`
- **Data files**: `.json`, `.xml`, `.yaml`, `.yml`, `.csv`
- **Documentation**: `.html`, `.css`, `.tex`, `.org`
- **PDF documents**: `.pdf` (requires `pymupdf`)
- **Images**: `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`, `.webp` (requires `pillow` and `pytesseract`)

### Query the Graph

Basic query:
```bash
knowledge-graph --query "machine learning neural networks" --graph-id my-research
```

Save results to file:
```bash
knowledge-graph --query "quantum computing" --output results.md
```

Query without specifying graph (uses last accessed graph):
```bash
knowledge-graph --query "artificial intelligence"
```

Random query for exploration:
```bash
knowledge-graph --query --random
```

### Extract Subgraph

Extract a subgraph centered on query results:
```bash
knowledge-graph --query "black hole entropy" --subgraph blackhole-graph.json --hops 4
```

### Metadata

View metadata in terminal:
```bash
knowledge-graph --metadata --graph-id my-research
```

Save metadata to file:
```bash
knowledge-graph --metadata graph-stats.md --graph-id my-research
```

Query-specific metadata:
```bash
knowledge-graph --query "quantum entanglement" --metadata
```

### Graph Management

Dump entire graph:
```bash
knowledge-graph --dump --graph-id my-research
```

Delete a graph (with confirmation):
```bash
knowledge-graph --delete --graph-id my-research
```

Delete without confirmation:
```bash
knowledge-graph --delete --graph-id my-research -Y
```

### Pruning

Prune bottom 10% (default) based on retrieval frequency and uniqueness:
```bash
knowledge-graph --prune -Y
```

Prune bottom 25%:
```bash
knowledge-graph --prune --bottom 25
```

Prune top 25% (to thin noise):
```bash
knowledge-graph --prune --top 25
```

### Settings

Set verbosity level:
```bash
knowledge-graph --settings --verbosity high
```

Verbosity levels:
- `off`: Only errors
- `low`: Minimal output (prompts and confirmations)
- `medium`: Results and basic info (default)
- `high`: Results with metrics
- `max`: Everything including detailed internal state

Enable/disable query tracking database:
```bash
knowledge-graph --settings --db off
knowledge-graph --settings --db on
```

## Architecture

The knowledge graph utility follows a layered architecture:

- **Domain**: Core models (GraphNode, KnowledgeGraph, QueryResult, etc.)
- **Infrastructure**: Storage, similarity calculation, text extraction (PDF, OCR), and database management
- **Application**: Business logic services (GraphService, QueryService, PruningService, IngestionService, etc.)
- **Presentation**: CLI interface

## How It Works

1. **Ingestion**: Files are detected by type (text, PDF, image) and content is extracted accordingly
   - Text files: Direct reading
   - PDFs: Text extraction using PyMuPDF
   - Images: OCR using Tesseract via pytesseract
2. **Content Processing**: Extracted content is split into semantic chunks (paragraphs/sections)
3. **Node Creation**: Each chunk becomes a node in the graph
4. **Edge Creation**: Edges are created between similar nodes using TF-IDF and cosine similarity
5. **Querying**: Queries use semantic similarity to rank and retrieve relevant nodes
6. **Tracking**: Retrieval frequency and uniqueness are tracked for each node
7. **Pruning**: Low-value nodes can be removed based on usage patterns

## Storage

Graphs are stored as JSON files in the `.knowledge_graphs` directory:
- Graph data: `.knowledge_graphs/<graph-id>.json`
- Query database: `.knowledge_graphs/queries.db` (SQLite)
- Settings: `.knowledge_graphs/settings.json`
- Last graph tracker: `.knowledge_graphs/.last_graph`

## Examples

### Research Paper Management (with PDFs)

```bash
# Create graph
knowledge-graph --create --graph-id physics-research

# Ingest papers (including PDFs)
knowledge-graph --input papers/ --graph-id physics-research --recursive

# Query specific topic
knowledge-graph --query "accretion disk hawking radiation black hole entropy" \
  --graph-id physics-research --output black-hole-notes.md

# Extract related concepts
knowledge-graph --query "dark matter" --subgraph dark-matter.json --hops 3

# Get statistics
knowledge-graph --metadata --graph-id physics-research
```

### Scanned Documents with OCR

```bash
# Create graph
knowledge-graph --create --graph-id scanned-docs

# Ingest scanned images and PDFs
knowledge-graph --input scans/ --graph-id scanned-docs --recursive

# Query extracted text
knowledge-graph --query "invoice payment terms" --graph-id scanned-docs
```

### Code Documentation

```bash
# Create graph
knowledge-graph --create --graph-id codebase-docs

# Ingest documentation
knowledge-graph --input docs/ --graph-id codebase-docs --recursive

# Find information
knowledge-graph --query "authentication middleware" --graph-id codebase-docs

# Explore randomly
knowledge-graph --query --random --graph-id codebase-docs
```

## Future Features

- RAG (Retrieval-Augmented Generation) integration
- Graph visualization
- Export formats (GraphML, Gephi, etc.)
- Advanced query syntax
- Enhanced multi-modal support (audio transcription, video frames)
- Clustering and community detection
- Time-based analysis

## License

Part of Modular Utilities - MIT License
