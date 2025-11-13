# Advanced Chunking Module

A sophisticated text chunking module with structural awareness, OCR integration, and flexible input/output options for the Modular Utilities project.

## Features

- **Multiple Chunking Strategies**: Support for sentence, line, paragraph, word count, character count, and token count based chunking
- **Structural Awareness**: Intelligently preserves code blocks and mathematical expressions
- **OCR Integration**: Process image-based text and scanned documents
- **Text Repair**: Automatic detection and repair of OCR artifacts and mojibake
- **Flexible I/O**: Process single files or entire directories recursively
- **Multiple Output Formats**: Per-file JSON, aggregated JSON, or plain text output
- **Rich Metadata**: Each chunk includes comprehensive metadata (position, counts, structure detection)

## Installation

The module is included with the Modular Utilities package. To use OCR features, install optional dependencies:

```bash
# For PDF support
pip install "modular-utilities[pdf]"

# For OCR/image support (requires Tesseract OCR system installation)
pip install "modular-utilities[image]"

# For both
pip install "modular-utilities[multimodal]"
```

For OCR functionality, you also need to install Tesseract OCR on your system:

- **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
- **macOS**: `brew install tesseract`
- **Windows**: Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)

## Quick Start

### Python API

```python
from pathlib import Path
from advanced_chunking import ChunkingService, ChunkingConfig, ChunkingStrategy

# Configure chunking
config = ChunkingConfig(
    strategy=ChunkingStrategy.SENTENCE,
    preserve_code_blocks=True,
    preserve_math_expressions=True,
)

# Create service and chunk text
service = ChunkingService(config)
chunks = service.chunk_text("Your text here.", Path("source.txt"))

# Access chunk data
for chunk in chunks:
    print(f"Chunk {chunk.metadata.chunk_number}: {chunk.text}")
    print(f"  Words: {chunk.metadata.word_count}, Tokens: {chunk.metadata.token_count}")
```

### Command Line Interface

```bash
# Chunk a file by sentences
python -m advanced_chunking --input document.txt --strategy sentence

# Chunk by word count (100 words per chunk)
python -m advanced_chunking --input document.txt --strategy word_count --word-count 100

# Process a directory recursively with token-based chunking
python -m advanced_chunking --input /path/to/docs --strategy token_count --token-count 500 --output chunks/

# Enable OCR for scanned documents
python -m advanced_chunking --input scanned.pdf --strategy paragraph --enable-ocr

# Create aggregated JSON output
python -m advanced_chunking --input docs/ --strategy sentence --aggregated
```

## Chunking Strategies

### 1. Sentence-Based Chunking
Splits text into individual sentences while respecting abbreviations and punctuation.

```python
config = ChunkingConfig(strategy=ChunkingStrategy.SENTENCE)
```

### 2. Line-Based Chunking
Splits text into individual lines (useful for code or structured data).

```python
config = ChunkingConfig(strategy=ChunkingStrategy.LINE)
```

### 3. Paragraph-Based Chunking
Splits text by paragraph boundaries (double newlines).

```python
config = ChunkingConfig(strategy=ChunkingStrategy.PARAGRAPH)
```

### 4. Word Count Chunking
Creates chunks of approximately N words.

```python
config = ChunkingConfig(
    strategy=ChunkingStrategy.WORD_COUNT,
    word_count=100
)
```

### 5. Character Count Chunking
Creates chunks of approximately N characters, breaking at sentence boundaries when possible.

```python
config = ChunkingConfig(
    strategy=ChunkingStrategy.CHARACTER_COUNT,
    character_count=500
)
```

### 6. Token Count Chunking
Creates chunks of approximately N tokens (useful for LLM context windows).

```python
config = ChunkingConfig(
    strategy=ChunkingStrategy.TOKEN_COUNT,
    token_count=500,
    tokenizer_model="gpt-3.5-turbo"
)
```

## Configuration Options

### Structural Preservation

```python
config = ChunkingConfig(
    strategy=ChunkingStrategy.PARAGRAPH,
    preserve_code_blocks=True,    # Keep code blocks intact
    preserve_math_expressions=True # Keep math equations intact
)
```

### OCR and Text Repair

```python
config = ChunkingConfig(
    strategy=ChunkingStrategy.SENTENCE,
    enable_ocr=True,              # Extract text from images
    repair_ocr_artifacts=True,    # Clean up OCR noise
    repair_mojibake=True          # Fix encoding issues
)
```

## Processing Files and Directories

### Single File Processing

```python
from advanced_chunking.application.input_handler import InputHandler

handler = InputHandler(config)
chunks = handler.process_file(Path("document.txt"))
```

### Directory Processing

```python
# Process all supported files recursively
file_chunks = handler.process_directory(Path("documents/"), recursive=True)

# file_chunks is a dict: {file_path: [chunks]}
for file_path, chunks in file_chunks.items():
    print(f"{file_path}: {len(chunks)} chunks")
```

## Output Formats

### Per-File JSON Output

```python
from advanced_chunking.application.output_formatter import OutputFormatter

formatter = OutputFormatter(Path("output/"))
output_files = formatter.write_per_file_json(file_chunks)
```

Output structure:
```json
{
  "source_file": "/path/to/source.txt",
  "chunk_count": 10,
  "chunks": [
    {
      "text": "First chunk text...",
      "metadata": {
        "chunk_number": 1,
        "start_position": 0,
        "end_position": 100,
        "strategy": "sentence",
        "source_file": "/path/to/source.txt",
        "word_count": 15,
        "character_count": 100,
        "token_count": 20,
        "contains_code": false,
        "contains_math": false
      }
    }
  ]
}
```

### Aggregated JSON Output

```python
output_file = formatter.write_aggregated_json(file_chunks)
```

Combines all chunks from all files into a single JSON file.

### Plain Text Output

```python
output_file = formatter.write_text_output(file_chunks)
```

Human-readable text format with chunk metadata.

## Supported File Formats

- **Text files**: .txt, .md, .py, .js, .java, .cpp, .c, .h, .cs, .go, .rs, .rb, .php, .html, .css, .json, .xml, .yaml, .toml, .sh, .bat, and more
- **PDF files**: Requires `pymupdf` (included with `[pdf]` extra)
- **DOCX files**: Requires `python-docx` (install separately if needed)
- **Images**: .png, .jpg, .jpeg, .tiff, .bmp (requires `pytesseract` and Tesseract OCR)

## Use Cases

### 1. LLM Context Preparation
```python
# Chunk documents for feeding to LLMs
config = ChunkingConfig(
    strategy=ChunkingStrategy.TOKEN_COUNT,
    token_count=1000,  # Fit within context window
    preserve_code_blocks=True
)
```

### 2. Knowledge Graph Ingestion
```python
# Create semantic chunks for knowledge graph nodes
config = ChunkingConfig(
    strategy=ChunkingStrategy.PARAGRAPH,
    preserve_math_expressions=True
)
```

### 3. Document Search Indexing
```python
# Create searchable chunks with metadata
config = ChunkingConfig(
    strategy=ChunkingStrategy.SENTENCE,
    repair_ocr_artifacts=True
)
```

### 4. Content Mining
```python
# Extract and analyze content from diverse sources
handler = InputHandler(config)
results = handler.process_directory(Path("corpus/"), recursive=True)

# Analyze chunks
for file_path, chunks in results.items():
    code_chunks = [c for c in chunks if c.metadata.contains_code]
    math_chunks = [c for c in chunks if c.metadata.contains_math]
    print(f"{file_path}: {len(code_chunks)} code, {len(math_chunks)} math")
```

## Architecture

The module follows clean architecture principles:

```
advanced_chunking/
├── domain/           # Core models and entities
│   └── models.py     # ChunkingStrategy, Chunk, ChunkMetadata, ChunkingConfig
├── application/      # Business logic
│   ├── chunking_service.py    # Main chunking implementation
│   ├── structure_detector.py  # Code/math detection
│   ├── input_handler.py       # File/directory processing
│   └── output_formatter.py    # Output generation
├── infrastructure/   # External dependencies
│   ├── tokenizers.py          # Token counting
│   ├── text_processors.py    # Text repair and normalization
│   ├── file_readers.py        # File I/O
│   └── ocr_processor.py       # OCR integration
└── presentation/     # User interfaces
    └── cli/          # Command-line interface
```

## API Reference

### Core Classes

#### `ChunkingConfig`
Configuration for chunking operations.

**Parameters:**
- `strategy`: ChunkingStrategy enum
- `word_count`: int (optional) - For WORD_COUNT strategy
- `character_count`: int (optional) - For CHARACTER_COUNT strategy
- `token_count`: int (optional) - For TOKEN_COUNT strategy
- `tokenizer_model`: str - Default "gpt-3.5-turbo"
- `preserve_code_blocks`: bool - Default True
- `preserve_math_expressions`: bool - Default True
- `enable_ocr`: bool - Default False
- `repair_ocr_artifacts`: bool - Default True
- `repair_mojibake`: bool - Default True

#### `ChunkingService`
Main service for chunking operations.

**Methods:**
- `chunk_text(text: str, source_file: Path) -> List[Chunk]`
- `chunk_file(file_path: Path) -> List[Chunk]`

#### `Chunk`
Represents a text chunk with metadata.

**Attributes:**
- `text`: str - The chunk content
- `metadata`: ChunkMetadata - Chunk metadata

**Methods:**
- `to_dict() -> dict` - Convert to dictionary for JSON serialization

## Performance Considerations

- **Large Files**: The chunker processes entire files in memory. For very large files (>100MB), consider pre-splitting.
- **Token Counting**: Token counting is approximate. For exact counts, integrate with tiktoken or similar libraries.
- **OCR**: Image processing can be slow. Consider batch processing and caching results.
- **Directory Processing**: Processes files sequentially. For massive directories, consider parallelization.

## Extending the Module

### Adding a New Chunking Strategy

1. Add strategy to `ChunkingStrategy` enum
2. Implement chunking method in `ChunkingService`
3. Add configuration validation
4. Add tests

### Custom Text Processors

```python
from advanced_chunking.infrastructure.text_processors import TextProcessor

class CustomProcessor(TextProcessor):
    def process(self, text: str) -> str:
        text = super().process(text)
        # Add custom processing
        return text
```

## Testing

Run the test suite:

```bash
pytest tests/advanced_chunking/ -v
```

## Contributing

Contributions are welcome! Please:
1. Follow the existing code structure and patterns
2. Add tests for new functionality
3. Update documentation
4. Ensure `ruff check` passes

## License

Part of the Modular Utilities project. See LICENSE for details.
