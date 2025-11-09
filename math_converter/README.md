# Math Syntax Converter

A simple CLI tool for converting math syntax between different formats: LaTeX, MathJax (GitHub-friendly), ASCII, and Unicode.

## Features

- 🔄 Convert between LaTeX, MathJax, ASCII, and Unicode math syntaxes
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

## Architecture

The converter follows a clean architecture pattern:

```
math_converter/
├── domain/           # Core models and types
├── application/      # Business logic (conversion engine, file processor)
├── infrastructure/   # External integrations
└── presentation/     # CLI interface
```

## Dependencies

- **Python 3.10+**
- **SymPy**: For accurate mathematical parsing and conversion

## Development

### Running Tests

```bash
pytest tests/math_converter/ -v
```

### Adding New Syntax Types

1. Add new type to `SyntaxType` enum in `domain/syntax_types.py`
2. Implement converter methods in `application/converter.py`
3. Register converters in `_register_converters()`
4. Add tests

## Limitations

- Directory scanning is non-recursive by default
- Some complex LaTeX expressions may not convert perfectly
- ASCII conversion depends on SymPy's ability to parse the expression
- Not all Unicode symbols are supported

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
