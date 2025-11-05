# Python Utilities Generator Quickstart Guide ⚡

The Python Utilities Generator is your AI-powered code assistant that transforms natural language into production-ready Python utilities. Describe what you need in plain English, and get a complete, modular, self-contained Python script or package—instantly.

## Table of Contents
- [Why Python Utilities Generator?](#why-python-utilities-generator)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Features & Use Cases](#core-features--use-cases)
- [Creative Workflows](#creative-workflows)
- [Example Generations](#example-generations)
- [Best Practices](#best-practices)

## Why Python Utilities Generator?

### The Problem

You need a Python utility for:
- Data processing scripts
- API wrappers
- CLI tools
- File converters
- Web scrapers
- Automation scripts

**Traditional approach**: Write from scratch, research libraries, handle edge cases, write tests.

**Python Utilities Generator approach**: Describe what you need, get production-ready code.

### What Makes It Priceless

✅ **Natural Language Interface**: No boilerplate coding  
✅ **Production-Ready**: Includes error handling, logging, tests  
✅ **Modular Design**: Clean, maintainable code structure  
✅ **Self-Contained**: Ready to run immediately  
✅ **Best Practices**: Follows Python conventions  
✅ **Time-Saver**: Minutes instead of hours  

## Installation

### Prerequisites

- Node.js (for the web interface)
- Gemini API key (for AI generation)

### Setup

```bash
# Navigate to the generator directory
cd python_utilities_generator

# Install dependencies
npm install

# Set up your API key
echo "GEMINI_API_KEY=your_api_key_here" > .env.local

# Start the application
npm run dev

# Open in browser
open http://localhost:3000  # macOS
xdg-open http://localhost:3000  # Linux
```

**Getting a Gemini API Key**:
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy it to `.env.local`

## Quick Start

### Generate Your First Utility

1. **Open the app** in your browser
2. **Describe your utility** in the text box:
   ```
   Create a utility that converts CSV files to JSON format
   ```
3. **Click "Generate"**
4. **Review the generated code**
5. **Download or copy** the utility

### Example Session

**Input**:
```
Create a CLI tool that monitors a directory for new files 
and automatically backs them up to a specified location
```

**Output**: Complete Python script with:
- Argument parsing (argparse)
- File watching (watchdog)
- Logging configuration
- Error handling
- Usage examples
- Tests

## Core Features & Use Cases

### 1. **Data Processing Utilities** 📊

**Use Case**: Transform data between formats quickly.

**Example Prompts**:

```
"Create a utility to convert JSON to CSV with nested object flattening"
```

```
"Build a script that merges multiple Excel files into one"
```

```
"Generate a tool to clean and validate email addresses in a CSV file"
```

**What You Get**:
- Input validation
- Error handling for malformed data
- Progress indicators
- Logging
- CLI interface

### 2. **API Wrappers** 🌐

**Use Case**: Quickly interact with third-party APIs.

**Example Prompts**:

```
"Create a wrapper for the GitHub API to list and clone repositories"
```

```
"Build a utility to fetch weather data from OpenWeatherMap API"
```

```
"Generate a tool to interact with Slack API for posting messages"
```

**What You Get**:
- Request handling with retries
- Authentication helpers
- Response parsing
- Rate limiting consideration
- Example usage

### 3. **File Operations** 📁

**Use Case**: Automate file system tasks.

**Example Prompts**:

```
"Create a utility to recursively find and remove duplicate files"
```

```
"Build a script to organize files by extension into subdirectories"
```

```
"Generate a tool to batch rename files based on patterns"
```

**What You Get**:
- Safe file operations (backups before changes)
- Progress tracking
- Dry-run mode
- Detailed logging
- Undo functionality

### 4. **Web Scraping** 🕷️

**Use Case**: Extract data from websites efficiently.

**Example Prompts**:

```
"Create a web scraper for product prices from an e-commerce site"
```

```
"Build a utility to extract article titles and summaries from a news site"
```

```
"Generate a tool to monitor website changes and send notifications"
```

**What You Get**:
- BeautifulSoup/Scrapy setup
- Respectful scraping (delays, robots.txt)
- Data export (JSON/CSV)
- Error handling for network issues
- Logging and debugging

### 5. **CLI Tools** 🖥️

**Use Case**: Build command-line interfaces quickly.

**Example Prompts**:

```
"Create a CLI tool for managing TODO lists stored in a JSON file"
```

```
"Build a password generator with configurable strength options"
```

```
"Generate a CLI for calculating various statistics on CSV data"
```

**What You Get**:
- Argparse configuration
- Subcommands support
- Help text generation
- Input validation
- Colorized output

### 6. **Automation Scripts** 🤖

**Use Case**: Automate repetitive tasks.

**Example Prompts**:

```
"Create a script to automatically backup databases and upload to S3"
```

```
"Build a utility to monitor system resources and send alerts"
```

```
"Generate a tool to automatically update documentation from code comments"
```

**What You Get**:
- Scheduling hooks (cron-compatible)
- Error notifications
- Retry logic
- Logging with rotation
- Configuration files

### 7. **Data Validation** ✅

**Use Case**: Ensure data quality and consistency.

**Example Prompts**:

```
"Create a validator for JSON data against a schema"
```

```
"Build a utility to check CSV files for data quality issues"
```

```
"Generate a tool to validate API responses"
```

**What You Get**:
- Schema validation
- Custom validation rules
- Detailed error reports
- Batch processing
- Summary statistics

### 8. **Testing Utilities** 🧪

**Use Case**: Generate test data and helpers.

**Example Prompts**:

```
"Create a utility to generate fake user data for testing"
```

```
"Build a tool to create realistic test datasets"
```

```
"Generate a mock API server for testing"
```

**What You Get**:
- Faker integration
- Configurable data generation
- Data export options
- Reproducible outputs (seeding)
- Documentation

## Creative Workflows

### Workflow 1: The Rapid Prototyper

```
Goal: Build a complete data pipeline in 30 minutes

Step 1: Generate data fetcher
Prompt: "Create a utility to fetch data from a REST API with pagination support"

Step 2: Generate data transformer
Prompt: "Build a script to transform JSON data and calculate aggregations"

Step 3: Generate data exporter
Prompt: "Create a utility to save processed data to PostgreSQL"

Step 4: Combine the utilities into a pipeline
- Copy generated code into single project
- Wire them together
- Add orchestration layer
- Done!
```

### Workflow 2: The Automation Engineer

```
Goal: Automate daily reporting

Step 1: Generate report generator
Prompt: "Create a utility to query database and generate HTML reports"

Step 2: Generate email sender
Prompt: "Build a script to send emails with attachments via SMTP"

Step 3: Generate scheduler wrapper
Prompt: "Create a utility to run scripts on schedule and log results"

Step 4: Deploy
- Combine utilities
- Set up cron job
- Monitor logs
```

### Workflow 3: The Data Scientist

```
Goal: Streamline data preprocessing

Step 1: Generate data cleaner
Prompt: "Create a utility to clean and normalize CSV data"

Step 2: Generate feature engineer
Prompt: "Build a script to extract features from text data"

Step 3: Generate train/test splitter
Prompt: "Create a utility to split datasets with stratification"

Step 4: Integration
- Chain utilities in notebook
- Create ML pipeline
- Iterate on results
```

### Workflow 4: The DevOps Engineer

```
Goal: Build deployment utilities

Step 1: Generate config manager
Prompt: "Create a utility to manage environment configurations across deployments"

Step 2: Generate health checker
Prompt: "Build a script to check service health and dependencies"

Step 3: Generate log analyzer
Prompt: "Create a utility to parse and analyze application logs"

Step 4: Dashboard
- Integrate utilities
- Add monitoring dashboard
- Set up alerts
```

### Workflow 5: The Integration Specialist

```
Goal: Connect multiple systems

Step 1: Generate API client A
Prompt: "Create a wrapper for System A's REST API"

Step 2: Generate API client B
Prompt: "Build a client for System B's GraphQL API"

Step 3: Generate data transformer
Prompt: "Create a utility to transform data between System A and B formats"

Step 4: Orchestration
- Build integration layer
- Add error handling
- Implement queue system
```

## Example Generations

### Example 1: CSV to JSON Converter

**Prompt**:
```
Create a utility that converts CSV files to JSON format with options 
for handling nested structures and type inference
```

**Generated Code** (simplified):
```python
#!/usr/bin/env python3
"""
CSV to JSON Converter
Converts CSV files to JSON with nested structure support and type inference.
"""

import csv
import json
import argparse
import logging
from pathlib import Path
from typing import Any, Dict, List

# ... (complete implementation with error handling, logging, tests)

def main():
    parser = argparse.ArgumentParser(description="Convert CSV to JSON")
    parser.add_argument("input", type=Path, help="Input CSV file")
    parser.add_argument("output", type=Path, help="Output JSON file")
    parser.add_argument("--infer-types", action="store_true")
    # ... more arguments
    
    args = parser.parse_args()
    convert_csv_to_json(args.input, args.output, infer_types=args.infer_types)

if __name__ == "__main__":
    main()
```

### Example 2: Directory Watcher

**Prompt**:
```
Build a CLI tool that watches a directory for new files and 
automatically processes them based on file type
```

**Generated Code** (simplified):
```python
#!/usr/bin/env python3
"""
Directory Watcher
Monitors directory for new files and processes them automatically.
"""

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import argparse
import logging
from pathlib import Path

class FileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            file_path = Path(event.src_path)
            self.process_file(file_path)
    
    def process_file(self, file_path: Path):
        """Process file based on extension"""
        # ... implementation

def main():
    parser = argparse.ArgumentParser(description="Watch directory for files")
    parser.add_argument("directory", type=Path)
    # ... setup and run
```

### Example 3: API Client Generator

**Prompt**:
```
Create a reusable API client wrapper with authentication, 
retry logic, and rate limiting
```

**Generated Code** (simplified):
```python
#!/usr/bin/env python3
"""
Generic API Client
Reusable API client with auth, retries, and rate limiting.
"""

import requests
import time
from typing import Dict, Optional
from functools import wraps

class APIClient:
    def __init__(self, base_url: str, api_key: str, rate_limit: int = 100):
        self.base_url = base_url
        self.api_key = api_key
        self.rate_limit = rate_limit
        # ... implementation
    
    def _request_with_retry(self, method: str, endpoint: str, **kwargs):
        """Make request with exponential backoff retry"""
        # ... implementation
    
    def get(self, endpoint: str, **kwargs) -> Dict:
        return self._request_with_retry("GET", endpoint, **kwargs)
    
    # ... other methods
```

## Best Practices

### ✅ DO: Be Specific in Prompts

```
❌ Bad: "Create a file utility"
✅ Good: "Create a utility to recursively find duplicate files by MD5 hash and move them to a backup directory"

❌ Bad: "Make an API wrapper"
✅ Good: "Build a Python wrapper for the GitHub REST API v3 with authentication, pagination, and rate limiting"
```

### ✅ DO: Specify Requirements

```
Include in your prompt:
- Input/output formats
- Error handling needs
- Performance requirements
- Dependencies to avoid/use
- Specific features
```

**Example**:
```
"Create a CSV processor that:
- Validates email addresses
- Removes duplicates
- Logs all errors to a file
- Uses pandas for performance
- Includes progress bar
- Has a --dry-run mode"
```

### ✅ DO: Request Tests

```
"Create a utility to... and include pytest tests for all main functions"
```

### ✅ DO: Ask for Documentation

```
"Create a utility to... with comprehensive docstrings and a README"
```

### ✅ DO: Iterate

```
Generate → Review → Refine prompt → Regenerate
```

### ❌ DON'T: Generate Complex Systems

The generator works best for:
- Single-purpose utilities (✅)
- Standalone scripts (✅)
- CLI tools (✅)
- Simple packages (✅)

Not ideal for:
- Full web applications (❌)
- Complex frameworks (❌)
- Multi-service architectures (❌)

**Instead**: Generate individual utilities and combine them.

## Advanced Usage

### Customizing Generation

Edit the generation parameters in the UI:
- **Temperature**: Lower = more deterministic
- **Max tokens**: Increase for longer utilities
- **Model**: Choose specific Gemini model

### Combining Generated Utilities

```bash
# Generate multiple utilities
# Then create a master script

# project/
# ├── utils/
# │   ├── data_fetcher.py (generated)
# │   ├── data_processor.py (generated)
# │   └── data_exporter.py (generated)
# └── main.py (you write this)

# main.py
from utils.data_fetcher import fetch_data
from utils.data_processor import process_data
from utils.data_exporter import export_data

def main():
    data = fetch_data()
    processed = process_data(data)
    export_data(processed)

if __name__ == "__main__":
    main()
```

### Version Control Strategy

```bash
# Initialize git
git init

# Generate utility
# Save to file: scripts/my_utility.py

# Commit generated code
git add scripts/my_utility.py
git commit -m "feat: add generated utility for X"

# Make manual modifications
# Edit scripts/my_utility.py

# Commit modifications separately
git add scripts/my_utility.py
git commit -m "refactor: customize generated utility"
```

## Prompt Templates

### Template: Data Transformer

```
Create a utility to transform [INPUT_FORMAT] to [OUTPUT_FORMAT] with:
- Validation of [FIELDS]
- Error handling for [EDGE_CASES]
- Logging to [LOG_DESTINATION]
- CLI interface with [OPTIONS]
- Progress indication
- Include tests
```

### Template: API Wrapper

```
Build a Python wrapper for [API_NAME] API that:
- Authenticates using [AUTH_METHOD]
- Implements [ENDPOINTS]
- Handles rate limiting at [RATE] requests per [TIME]
- Retries failed requests up to [N] times
- Returns data as [FORMAT]
- Includes usage examples
```

### Template: CLI Tool

```
Create a CLI tool for [PURPOSE] with:
- Subcommands: [COMMAND_LIST]
- Arguments: [ARG_LIST]
- Output formats: [FORMATS]
- Configuration file support
- Colorized output
- Help documentation
- Input validation
```

### Template: Automation Script

```
Generate a script to automatically:
- [ACTION_1]
- [ACTION_2]
- [ACTION_3]
With:
- Scheduling support
- Error notifications via [METHOD]
- Logging with rotation
- Dry-run mode
- Configuration via [CONFIG_METHOD]
```

## Troubleshooting

### Issue: "Generated code has errors"
**Solution**: Refine prompt with more specific requirements
```
Add to prompt: "Ensure the code handles [SPECIFIC_CASE]"
```

### Issue: "Code is too complex"
**Solution**: Request simpler implementation
```
Add to prompt: "Keep the implementation simple and minimal"
```

### Issue: "Missing features"
**Solution**: Be explicit about requirements
```
Add to prompt: "Must include [FEATURE_LIST]"
```

### Issue: "Dependencies not working"
**Solution**: Specify dependencies
```
Add to prompt: "Use only standard library" or "Use [SPECIFIC_LIBRARY]"
```

## Tips for Great Results

1. **Start Simple**: Generate basic version first, then iterate
2. **Be Explicit**: More details = better results
3. **Include Examples**: "Like this: [EXAMPLE]"
4. **Specify Style**: "Follow PEP 8", "Use type hints"
5. **Request Testing**: Always ask for tests
6. **Review Carefully**: Generated code needs human review
7. **Iterate**: Regenerate with refined prompts

## Use Case Library

### Quick Wins

- **File organizer**: Organize downloads by type
- **Log analyzer**: Parse and summarize log files
- **Backup script**: Automated backup with rotation
- **Data cleaner**: Clean CSV/JSON data
- **Config manager**: Manage app configurations

### Time-Savers

- **Report generator**: Auto-generate reports from data
- **Email sender**: Batch email sending utility
- **Image resizer**: Batch image processing
- **Database dumper**: Automated database backups
- **API monitor**: Health check for APIs

### Learning Tools

- **Code formatter**: Format code to standards
- **Docstring generator**: Auto-generate docstrings
- **Test generator**: Create test skeletons
- **Type hint adder**: Add type annotations
- **Import optimizer**: Organize imports

## Next Steps

1. **Start Generating**: Try the examples above
2. **Build a Library**: Create your utility collection
3. **Share Results**: Contribute back to the community
4. **Iterate**: Refine prompts based on results
5. **Combine**: Build complex systems from simple utilities

## Resources

- 📖 [Full Documentation](../python_utilities_generator/README.md)
- 🤖 [Gemini API Docs](https://ai.google.dev/docs)
- 🐛 [Report Issues](https://github.com/justinlietz93/Modular_Utilities/issues)

---

**Happy Generating! ⚡** Turn ideas into code in seconds.
