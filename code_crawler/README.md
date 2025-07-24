# code_crawler

This package crawls the current directory recursively, ignoring files/directories matching patterns in config.py, and outputs an XML file with metadata report, ASCII directory tree, and wrapped file contents.

To run:

```powershell
python main.py --input /path/to/directory --output output.xml
```

--input: Directory to crawl (defaults to current directory).
--output: Output XML file (defaults to output.xml).
Edit config.py to customize ignore patterns. Ensure Python 3+ is installed; no external dependencies beyond standard library.