# Math Syntax Converter

A powerful CLI tool for converting math syntax between different formats: LaTeX, MathJax (GitHub-friendly), ASCII, and Unicode. Also extracts math equations from PDF files and generates executable code in Python or Rust from mathematical expressions.

## Features

- 🔄 Convert between LaTeX, MathJax, ASCII, and Unicode math syntaxes
- 📄 Extract math equations from PDF files (research papers, books, etc.)
- 🐍 Generate Python code libraries from extracted math expressions
- 🦀 **NEW:** Generate Rust code modules from extracted math expressions
- 📁 Process single files or entire directories
- 🎯 In-place conversion or output to separate directory
- 🤖 Smart interactive prompts when options are missing
- ⚡ Automatic mode with `-Y` and `-N` flags
- 🔧 Uses SymPy for accurate mathematical parsing

## Installation

From the Modular Utilities repository root:

```bash
pip install -e .
```

For PDF extraction support:

```bash
pip install -e ".[pdf]"
```

This installs the `convert-math` command globally.

## Usage

### Basic Usage

Convert from LaTeX to GitHub MathJax format:

```bash
convert-math --from latex --to mathjax
```

By default, this scans the current directory (non-recursively) and converts all eligible files in place.

### Specify Input

Convert specific files or directories:

```bash
# Single file
convert-math --from latex --to mathjax --input document.md

# Multiple files
convert-math --from latex --to mathjax --input doc1.md doc2.md

# Directory
convert-math --from latex --to mathjax --input math_writeups/
```

### Output to Different Directory

Keep original files and create converted copies:

```bash
convert-math --from latex --to mathjax --input math_writeups/ --output-dir converted/
```

### Interactive Prompts

If you omit the `--to` flag, the tool will prompt you to select a target syntax:

```bash
convert-math --from latex
# Prompts: "Select target syntax: 1. mathjax, 2. ascii, 3. unicode"
```

If you omit the `--from` flag, the tool asks if you want to specify a source syntax:

```bash
convert-math --to mathjax
# Shows: "All files with any of the following math types will be converted: latex, mathjax, ascii, unicode"
# Prompts: "Do you want to specify? (y/n)"
```

### Automation Flags

For scripts or automated workflows, use `-Y` (auto-yes) or `-N` (auto-no):

```bash
# Auto-yes: automatically accepts default options
convert-math --from latex --to mathjax -Y

# Auto-no: requires all parameters, no prompts
convert-math --from latex --to mathjax --input math_docs/ -N
```

### PDF Math Extraction

Extract math equations from PDF files (requires `pip install -e ".[pdf]"`):

```bash
# Extract to markdown (default)
convert-math --input research-paper.pdf --output research-equations.md

# Auto-generates output file (research-paper.md)
convert-math --input research-paper.pdf

# Append to existing file
convert-math --input another-paper.pdf --output research-equations.md
```

The tool intelligently detects PDF files and:
- Extracts LaTeX-style math expressions (`\(...\)`, `\[...\]`, `$...$`, `$$...$$`)
- Groups equations by page number
- Supports both markdown and text output formats
- Automatically appends if the output file already exists

**Note:** PDF extraction quality depends on how the PDF was created. PDFs with text-based math work best.

## Supported Formats

### LaTeX

Standard LaTeX math delimiters:
- Inline: `\( x + y \)` or `$ x + y $`
- Display: `\[ x + y \]` or `$$ x + y $$`

### MathJax (GitHub-friendly)

GitHub's preferred markdown math format:
- Inline: `` $` x + y `$ ``
- Display: `` ```math\n x + y \n``` ``

### ASCII

Plain text mathematical expressions:
- `f(x) = x^2 + 2*x + 1`
- Uses SymPy for parsing and rendering

### Unicode

Mathematical expressions using Unicode symbols:
- Greek letters: α, β, γ, π
- Math operators: ∑, ∫, ∂, ≤, ≥, ±
- Uses SymPy for conversion

## Supported File Types

The converter processes files with these extensions:
- `.md` - Markdown
- `.tex` - LaTeX
- `.txt` - Plain text
- `.rst` - reStructuredText
- `.html` - HTML
- `.pdf` - PDF (extraction mode, requires pymupdf)

## Examples

### Example 1: Convert LaTeX Document to GitHub

You have a LaTeX document with math you want to use in GitHub README:

```bash
convert-math --from latex --to mathjax --input research_notes.md
```

Before:
```markdown
The equation \( E = mc^2 \) shows the relationship.

Display form:
\[ \int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2} \]
```

After:
```markdown
The equation $` E = mc^2 `$ shows the relationship.

Display form:
```math
 \int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2} 
```

### Example 2: Batch Convert Directory

Convert all markdown files in a directory:

```bash
convert-math --from latex --to mathjax --input math_writeups/ --output-dir github_ready/
```

This preserves your original files and creates converted copies in `github_ready/`.

### Example 3: Unicode to LaTeX

Convert Unicode symbols back to LaTeX:

```bash
convert-math --from unicode --to latex --input unicode_notes.md
```

Before: `α + β = γ`
After: `\alpha + \beta = \gamma`

### Example 4: Extract Math from PDF

Extract all math equations from a research paper:

```bash
convert-math --input research-paper.pdf --output equations.md
```

Sample output (`equations.md`):
```markdown
# Extracted Math Expressions

## Page 1

\[e^{i\pi} + 1 = 0\]

\(a^2 + b^2 = c^2\)

$$\sum_{i=1}^n i = \frac{n(n+1)}{2}$$
```

**Append mode**: If you run the same command again or extract from another PDF to the same file, it automatically appends with a separator.

### Code Generation from PDFs

**NEW:** Generate executable code (Python or Rust) from mathematical expressions in PDFs:

#### Python Code Generation

```bash
# Extract math from PDF and generate Python functions
convert-math --input research-paper.pdf --codegen python --codegen-output generated/

# Use sequential naming for functions
convert-math --input paper.pdf --codegen python --naming-strategy sequential

# Simplify expressions before generating code
convert-math --input paper.pdf --codegen python --simplify
```

#### Rust Code Generation

```bash
# Extract math from PDF and generate Rust functions
convert-math --input research-paper.pdf --codegen rust --codegen-output generated/

# Use sequential naming for functions
convert-math --input paper.pdf --codegen rust --naming-strategy sequential

# Simplify expressions before generating code
convert-math --input paper.pdf --codegen rust --simplify
```

The code generator:
- Extracts LaTeX expressions from PDF
- Parses them using SymPy
- Generates callable functions with proper parameters
- Creates a module with all functions, documentation, and metadata
- Exports a symbol matrix (JSON) tracking all variables
- Logs any expressions that failed to parse

**Generated files:**
- `{name}_lib.py` or `{name}_lib.rs` - The module with generated functions
- `{name}_lib.symbols.json` - Symbol registry with variable tracking
- `{name}_lib.metadata.json` - Metadata about all generated functions
- `failed_expressions.txt` - Log of expressions that couldn't be parsed

**Example Python output:**

Given a PDF with expressions like `x + y` and `a^2 + b^2`, generates:

```python
def expr_0(x, y):
    """Generated mathematical function.
    
    Original: x + y
    Page: 1
    
    Parameters:
        x: numeric value
        y: numeric value
    
    Returns:
        Evaluated expression result"""
    return x + y

def expr_1(a, b):
    """Generated mathematical function.
    
    Original: a^2 + b^2
    Page: 2
    
    Parameters:
        a: numeric value
        b: numeric value
    
    Returns:
        Evaluated expression result"""
    return a**2 + b**2
```

You can then import and use the generated module:

```python
from generated.paper_lib import expr_0, expr_1

result = expr_0(2, 3)  # Returns 5
result = expr_1(3, 4)  # Returns 25
```

**Example Rust output:**

The same expressions generate idiomatic Rust code:

```rust
/// Generated mathematical function.
/// 
/// Original: x + y
/// Page: 1
/// 
/// Parameters:
/// x: numeric value
/// y: numeric value
/// 
/// Returns:
/// Evaluated expression result
pub fn expr_0(x: f64, y: f64) -> f64 {
    x + y
}

/// Generated mathematical function.
/// 
/// Original: a^2 + b^2
/// Page: 2
/// 
/// Parameters:
/// a: numeric value
/// b: numeric value
/// 
/// Returns:
/// Evaluated expression result
pub fn expr_1(a: f64, b: f64) -> f64 {
    a.powi(2) + b.powi(2)
}
```

Rust code features:
- Uses `f64` for numeric values (high precision)
- Idiomatic Rust methods (`.powi()`, `.sqrt()`, `.sin()`, etc.)
- Full documentation comments (`///`)
- Module-level documentation (`//!`)
- Memory-safe, zero-cost abstractions
- Ready for high-performance numerical computing

**Naming Strategies:**
- `hash` (default): Generates function names with hash-based suffixes (e.g., `expr_a1b2c3d4`)
- `sequential`: Simple sequential numbering (e.g., `expr_0`, `expr_1`, ...)
- `semantic`: Attempts to derive meaningful names from expressions (future enhancement)

## Architecture

The converter follows a clean architecture pattern:

```
math_converter/
├── domain/           # Core models and types
│   ├── syntax_types.py     # Syntax conversion types
│   └── codegen_types.py    # Code generation types, backend abstractions
├── application/      # Business logic
│   ├── converter.py          # Syntax conversion engine
│   ├── file_processor.py    # File processing
│   ├── pdf_extractor.py     # PDF math extraction
│   ├── expression_pipeline.py  # LaTeX parsing pipeline
│   ├── symbol_registry.py      # Variable name management
│   ├── function_generator.py   # Function code generation
│   ├── codegen_orchestrator.py # Code generation orchestration
│   └── backends/             # Language-specific code generators
│       ├── python_backend.py # Python code generation
│       ├── rust_backend.py   # Rust code generation
│       └── registry.py       # Backend registry
├── infrastructure/   # External integrations
└── presentation/     # CLI interface
```

## Dependencies

- **Python 3.10+**
- **SymPy**: For accurate mathematical parsing, conversion, and code generation
- **PyMuPDF** (optional): For PDF extraction (`pip install -e ".[pdf]"`)

## Development

### Running Tests

```bash
pytest tests/math_converter/ -v
```

All 101 tests should pass, including:
- 33 tests for syntax conversion
- 9 tests for codegen types
- 11 tests for symbol registry
- 16 tests for expression pipeline
- 11 tests for function generator
- 7 tests for Python codegen integration
- 15 tests for Rust backend

### Adding New Syntax Types

1. Add new type to `SyntaxType` enum in `domain/syntax_types.py`
2. Implement converter methods in `application/converter.py`
3. Register converters in `_register_converters()`
4. Add tests

### Adding Code Generation Features

1. Core pipeline: `expression_pipeline.py` handles LaTeX → SymPy parsing
2. Symbol naming: `symbol_registry.py` manages variable name generation
3. Function creation: `function_generator.py` generates language-agnostic function metadata
4. Backend implementation: Language-specific backends handle code generation
5. Orchestration: `codegen_orchestrator.py` coordinates the full pipeline

### Adding New Code Generation Backends

1. Create a new backend class in `application/backends/` inheriting from `CodegenBackend`
2. Implement required methods:
   - `convert_expression_to_code()` - Convert SymPy to target language
   - `generate_function_code()` - Generate function in target language
   - `assemble_module()` - Assemble complete module
   - `get_file_extension()` - Return file extension
3. Register the backend in `backends/registry.py`
4. Add CLI support in `presentation/cli/main.py`
5. Add comprehensive tests
5. Orchestration: `codegen_orchestrator.py` coordinates the full pipeline

## Limitations

- Directory scanning is non-recursive by default
- Some complex LaTeX expressions may not convert perfectly
- ASCII conversion depends on SymPy's ability to parse the expression
- Not all Unicode symbols are supported
- Code generation currently supports Python and Rust (Go/C++ support planned)
- Generated Rust code uses f64 scalar types (ndarray support for multi-dimensional arrays coming soon)
- Expression simplification is optional and may change expression semantics

## Contributing

This is part of the Modular Utilities project. Contributions are welcome!

1. Follow the existing clean architecture pattern
2. Keep modules under 500 lines (AMOS guideline)
3. Add tests for new functionality
4. Update this README

## License

Part of Modular Utilities - MIT License

## Support

For issues, questions, or feature requests, please open an issue in the [Modular Utilities repository](https://github.com/justinlietz93/Modular_Utilities).
