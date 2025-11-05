# Dependency Analyzer Quickstart Guide 🔍

The Dependency Analyzer is your real-time codebase intelligence engine. It watches your files, tracks dependencies as they change, and keeps a living map of "what depends on what" in your project. Think of it as a GPS for your codebase—always knows the territory, always up-to-date.

## Table of Contents
- [Why Dependency Analyzer?](#why-dependency-analyzer)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Features & Use Cases](#core-features--use-cases)
- [Real-World Workflows](#real-world-workflows)
- [Advanced Usage](#advanced-usage)
- [Integration Patterns](#integration-patterns)

## Why Dependency Analyzer?

### The Problem

You're working on a codebase and need to answer:
- "If I change this file, what breaks?"
- "Where is this function imported?"
- "What are the hidden dependencies of this module?"
- "Which files haven't been updated in months?"
- "How coupled is our architecture?"

**Traditional approach**: Grep, manual inspection, or outdated documentation.

**Dependency Analyzer approach**: Automated, real-time, always-accurate dependency mapping.

### What Makes It Priceless

✅ **Live Updates**: Auto-refreshes as files change  
✅ **Multi-Language**: Python, JavaScript/TypeScript/JSX, HTML  
✅ **Background Mode**: Runs as daemon—zero developer friction  
✅ **Detailed Tracking**: Metadata includes sizes, lines, timestamps  
✅ **Graph Visualization**: See your dependencies visually  
✅ **Impact Analysis**: Know what breaks before you break it  
✅ **Refactoring Safety**: Trace all consumers before changes  

## Installation

### Option 1: Use Pre-built Executable

```bash
# Download from releases
wget https://github.com/justinlietz93/Modular_Utilities/releases/download/v1.0/dependency-analyzer

# Make executable
chmod +x dependency-analyzer

# Run
./dependency-analyzer /path/to/your/project
```

### Option 2: Build from Source

```bash
# Clone the repository
git clone https://github.com/justinlietz93/Modular_Utilities.git
cd Modular_Utilities/dependency_analyzer

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (for JavaScript parsing)
# Download Node.js v20.17.0 and extract to dependency_analyzer/nodejs
wget https://nodejs.org/dist/v20.17.0/node-v20.17.0-linux-x64.tar.xz
tar -xf node-v20.17.0-linux-x64.tar.xz
mv node-v20.17.0-linux-x64 nodejs

# Install @babel/parser for JS parsing
nodejs/bin/npm install @babel/parser

# Build executable (optional)
pyinstaller --add-data "src/dependency_analyzer/scripts;dependency_analyzer/scripts" \
            --add-data "nodejs;nodejs" \
            --onefile src/dependency_analyzer/cli.py \
            -n dependency-analyzer

# Run
dist/dependency-analyzer /path/to/your/project
```

### Option 3: Run from Source

```bash
cd Modular_Utilities/dependency_analyzer
python -m dependency_analyzer.cli /path/to/your/project
```

## Quick Start

### Basic Analysis

```bash
# Analyze your project (foreground mode)
dependency-analyzer /path/to/your/project --verbose

# Output files created:
# - dependency_tracking/dependency_map.json
# - dependency_tracking/dependency_metadata.csv
# - dependency_tracking/analyzer.log
```

### Background Mode (Recommended)

```bash
# Run as background daemon
dependency-analyzer /path/to/your/project --background

# Work on your code normally
# Analyzer updates dependencies automatically as you save files!

# Check status
ps aux | grep dependency-analyzer

# View live updates
tail -f dependency_tracking/analyzer.log
```

### Quick Look at Results

```bash
# View dependency map
cat dependency_tracking/dependency_map.json | jq

# View metadata
cat dependency_tracking/dependency_metadata.csv

# Check log for recent changes
tail -n 50 dependency_tracking/analyzer.log
```

## Core Features & Use Cases

### 1. **Impact Analysis** 💥

**Use Case**: "If I change this file, what breaks?"

```bash
# Run analyzer
dependency-analyzer . --verbose

# Query dependency map
jq '.dependencies[] | select(.file | contains("auth.py"))' dependency_tracking/dependency_map.json

# See all files that import auth.py
```

**Example Output**:
```json
{
  "file": "src/auth.py",
  "imported_by": [
    "src/api/users.py",
    "src/api/sessions.py",
    "tests/test_auth.py"
  ],
  "imports": [
    "bcrypt",
    "jwt",
    "src/database.py"
  ]
}
```

**Workflow**:
1. Plan to modify `auth.py`
2. Check dependency map
3. See 3 files depend on it
4. Update those files accordingly
5. Run tests for all dependents

### 2. **Refactoring Safety** 🛡️

**Use Case**: Safely rename/move files without breaking imports.

```bash
# Before refactoring: analyze dependencies
dependency-analyzer . --verbose

# Find all files that import the module you want to rename
jq '.dependencies[] | select(.imports[] | contains("old_name.py"))' \
   dependency_tracking/dependency_map.json

# List of files found:
# - src/module_a.py
# - src/module_b.py
# - tests/test_old.py

# Now refactor with confidence:
# 1. Rename/move the file
# 2. Update all found files
# 3. Re-run analyzer to verify
dependency-analyzer . --verbose

# Check if any broken imports remain
grep "ERROR" dependency_tracking/analyzer.log
```

### 3. **Architecture Visualization** 📊

**Use Case**: Understand your codebase structure visually.

```bash
# Generate dependency map
dependency-analyzer . --verbose

# Convert to DOT format for Graphviz
python -c "
import json
with open('dependency_tracking/dependency_map.json') as f:
    data = json.load(f)

print('digraph Dependencies {')
for dep in data.get('dependencies', []):
    file = dep['file']
    for imp in dep.get('imports', []):
        if not imp.startswith('src/'):
            continue  # Skip external imports
        print(f'  \"{file}\" -> \"{imp}\";')
print('}')
" > dependencies.dot

# Render as image
dot -Tpng dependencies.dot -o dependencies.png

# Open image
open dependencies.png  # macOS
xdg-open dependencies.png  # Linux
```

**Visual Output**: Graph showing all file relationships!

### 4. **Dead Code Detection** 💀

**Use Case**: Find files that nothing imports.

```bash
# Run analyzer
dependency-analyzer . --verbose

# Find orphaned files (not imported by anything)
python -c "
import json
with open('dependency_tracking/dependency_map.json') as f:
    data = json.load(f)

all_files = {dep['file'] for dep in data.get('dependencies', [])}
imported_files = set()
for dep in data.get('dependencies', []):
    imported_files.update(dep.get('imports', []))

orphans = all_files - imported_files
print('Potential dead code:')
for orphan in sorted(orphans):
    print(f'  - {orphan}')
"
```

**Result**: List of files that may be safe to delete.

### 5. **Circular Dependency Detection** 🔄

**Use Case**: Find and fix circular imports.

```bash
# Run analyzer
dependency-analyzer . --verbose

# Check for circular dependencies
python -c "
import json
from collections import defaultdict, deque

with open('dependency_tracking/dependency_map.json') as f:
    data = json.load(f)

# Build graph
graph = defaultdict(list)
for dep in data.get('dependencies', []):
    file = dep['file']
    for imp in dep.get('imports', []):
        graph[file].append(imp)

# Detect cycles (simplified DFS)
def has_cycle(node, visited, rec_stack):
    visited.add(node)
    rec_stack.add(node)
    
    for neighbor in graph.get(node, []):
        if neighbor not in visited:
            if has_cycle(neighbor, visited, rec_stack):
                return True
        elif neighbor in rec_stack:
            print(f'Circular dependency: {node} -> {neighbor}')
            return True
    
    rec_stack.remove(node)
    return False

visited = set()
for node in graph:
    if node not in visited:
        has_cycle(node, set(), set())
"
```

### 6. **Dependency Audit** 📋

**Use Case**: Generate report of all external dependencies.

```bash
# Run analyzer
dependency-analyzer . --verbose

# List all external dependencies
jq -r '.dependencies[].imports[]' dependency_tracking/dependency_map.json | \
  grep -v '^src/' | \
  sort -u > external_deps.txt

# Count usage
cat external_deps.txt | while read dep; do
  count=$(jq -r --arg dep "$dep" '.dependencies[].imports[] | select(. == $dep)' \
          dependency_tracking/dependency_map.json | wc -l)
  echo "$count $dep"
done | sort -rn

# Output:
# 15 requests
# 12 pytest
# 8 flask
# 3 sqlalchemy
```

### 7. **Change Tracking** 📈

**Use Case**: Monitor which files are actively being developed.

```bash
# Run in background mode
dependency-analyzer . --background

# Watch log for changes
tail -f dependency_tracking/analyzer.log

# See recent modifications
grep "Modified:" dependency_tracking/analyzer.log | tail -20

# Count modifications per file
grep "Modified:" dependency_tracking/analyzer.log | \
  awk '{print $3}' | sort | uniq -c | sort -rn

# Output shows hotspot files:
# 47 src/api/users.py
# 23 src/database.py
# 15 tests/test_users.py
```

### 8. **Documentation Auto-Generation** 📝

**Use Case**: Keep dependency docs up-to-date automatically.

```bash
# Run analyzer
dependency-analyzer . --verbose

# Generate markdown documentation
python -c "
import json
with open('dependency_tracking/dependency_map.json') as f:
    data = json.load(f)

print('# Project Dependencies\n')
for dep in sorted(data.get('dependencies', []), key=lambda x: x['file']):
    file = dep['file']
    imports = dep.get('imports', [])
    imported_by = dep.get('imported_by', [])
    
    print(f'## {file}\n')
    
    if imports:
        print('**Imports:**')
        for imp in imports:
            print(f'- \`{imp}\`')
        print()
    
    if imported_by:
        print('**Used by:**')
        for usage in imported_by:
            print(f'- \`{usage}\`')
        print()
" > DEPENDENCIES.md

# Add to docs
mv DEPENDENCIES.md docs/
```

## Real-World Workflows

### Workflow 1: The Safe Refactorer

```bash
#!/bin/bash
# safe-refactor.sh - Refactor with dependency awareness

set -e

FILE_TO_REFACTOR=$1
NEW_NAME=$2

echo "🔍 Step 1: Analyzing dependencies..."
dependency-analyzer . --verbose

echo "📋 Step 2: Finding all usages..."
jq -r --arg file "$FILE_TO_REFACTOR" \
  '.dependencies[] | select(.imports[] | contains($file)) | .file' \
  dependency_tracking/dependency_map.json > usages.txt

echo "Found $(wc -l < usages.txt) files that import $FILE_TO_REFACTOR"
cat usages.txt

echo "🔧 Step 3: Refactoring..."
# Rename the file
git mv "$FILE_TO_REFACTOR" "$NEW_NAME"

# Update all imports
cat usages.txt | while read file; do
  sed -i "s|$FILE_TO_REFACTOR|$NEW_NAME|g" "$file"
done

echo "✅ Step 4: Re-analyzing..."
dependency-analyzer . --verbose

echo "🧪 Step 5: Running tests..."
pytest

echo "✅ Refactoring complete!"
```

### Workflow 2: The Dependency Dashboard

```bash
#!/bin/bash
# dependency-dashboard.sh - Generate live dependency metrics

while true; do
  clear
  echo "============================================"
  echo "        DEPENDENCY DASHBOARD"
  echo "============================================"
  echo ""
  
  # Run analyzer
  dependency-analyzer . --verbose > /dev/null 2>&1
  
  # Total files
  total=$(jq '.dependencies | length' dependency_tracking/dependency_map.json)
  echo "📁 Total files analyzed: $total"
  
  # Average imports per file
  avg_imports=$(jq '.dependencies | map(.imports | length) | add / length' \
                dependency_tracking/dependency_map.json)
  echo "📦 Average imports per file: $(printf "%.1f" $avg_imports)"
  
  # Most coupled file
  most_coupled=$(jq -r '.dependencies | max_by(.imports | length) | "\(.file) (\(.imports | length) imports)"' \
                 dependency_tracking/dependency_map.json)
  echo "🔗 Most coupled file: $most_coupled"
  
  # Recently modified
  echo ""
  echo "🕒 Recently modified files:"
  grep "Modified:" dependency_tracking/analyzer.log | tail -5 | \
    awk '{print "   - " $3 " at " $5 " " $6}'
  
  echo ""
  echo "Refreshing in 30 seconds... (Ctrl+C to exit)"
  sleep 30
done
```

### Workflow 3: The PR Analyzer

```bash
#!/bin/bash
# pr-analyzer.sh - Analyze impact of PR changes

# Get changed files in PR
git diff --name-only origin/main...HEAD > changed_files.txt

echo "📋 Changed files:"
cat changed_files.txt

echo ""
echo "🔍 Analyzing impact..."
dependency-analyzer . --verbose > /dev/null

echo ""
echo "⚠️  Files affected by this PR:"

cat changed_files.txt | while read changed_file; do
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Changes to: $changed_file"
  echo ""
  
  # Find files that import this one
  affected=$(jq -r --arg file "$changed_file" \
    '.dependencies[] | select(.imports[] | contains($file)) | .file' \
    dependency_tracking/dependency_map.json)
  
  if [ -n "$affected" ]; then
    echo "Will impact:"
    echo "$affected" | sed 's/^/  - /'
  else
    echo "No direct dependents found."
  fi
  echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Impact analysis complete!"
```

### Workflow 4: The Architecture Enforcer

```bash
#!/bin/bash
# enforce-architecture.sh - Ensure clean architecture rules

dependency-analyzer . --verbose > /dev/null

echo "🏗️  Checking architecture rules..."

# Rule 1: Controllers should not import models directly
violations_1=$(jq -r '.dependencies[] | 
  select(.file | contains("controllers/")) | 
  select(.imports[] | contains("models/")) | 
  .file' dependency_tracking/dependency_map.json)

if [ -n "$violations_1" ]; then
  echo "❌ Rule 1 violated: Controllers importing models directly:"
  echo "$violations_1" | sed 's/^/   - /'
  exit 1
fi

# Rule 2: Utils should not import application code
violations_2=$(jq -r '.dependencies[] | 
  select(.file | contains("utils/")) | 
  select(.imports[] | contains("src/app")) | 
  .file' dependency_tracking/dependency_map.json)

if [ -n "$violations_2" ]; then
  echo "❌ Rule 2 violated: Utils importing application code:"
  echo "$violations_2" | sed 's/^/   - /'
  exit 1
fi

# Rule 3: No circular dependencies between modules
# (Simplified check)
echo "✅ All architecture rules passed!"
```

## Advanced Usage

### Metadata Analysis

```bash
# The CSV contains rich metadata
head -5 dependency_tracking/dependency_metadata.csv

# Example output:
# file,size_bytes,lines,last_modified,dependencies_count
# src/main.py,1024,45,2025-01-15T10:30:00,5
# src/utils.py,512,23,2025-01-14T14:20:00,2

# Find largest files
sort -t',' -k2 -rn dependency_tracking/dependency_metadata.csv | head -10

# Find most complex files (by dependency count)
sort -t',' -k5 -rn dependency_tracking/dependency_metadata.csv | head -10

# Find oldest files
sort -t',' -k4 dependency_tracking/dependency_metadata.csv | head -10
```

### Header Injection (Auto-Documentation)

The analyzer can inject dependency headers into source files:

```python
# src/example.py
# DEPENDENCIES: datetime, logging, src.utils, src.database
# LAST_ANALYZED: 2025-01-15T10:30:00

import datetime
import logging
from src import utils
from src.database import connect

# ... rest of file
```

**Enable header injection** (modify analyzer config):
```python
# In analyzer source, set:
config = {
    "inject_headers": True,
    "header_format": "# DEPENDENCIES: {deps}\n# LAST_ANALYZED: {timestamp}\n"
}
```

### Integration with CI/CD

```yaml
# .github/workflows/dependency-check.yml
name: Dependency Analysis

on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Download Dependency Analyzer
      run: |
        wget https://github.com/.../dependency-analyzer
        chmod +x dependency-analyzer
    
    - name: Run Analysis
      run: ./dependency-analyzer . --verbose
    
    - name: Check for Circular Dependencies
      run: |
        # Add your circular dependency check script
        python scripts/check_circular.py
    
    - name: Upload Dependency Map
      uses: actions/upload-artifact@v3
      with:
        name: dependency-map
        path: dependency_tracking/
    
    - name: Comment PR
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          const map = JSON.parse(fs.readFileSync('dependency_tracking/dependency_map.json'));
          const summary = `## Dependency Analysis\n\nTotal files: ${map.dependencies.length}`;
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: summary
          });
```

### Custom Queries with jq

```bash
# Find files with no imports
jq '.dependencies[] | select(.imports | length == 0) | .file' \
   dependency_tracking/dependency_map.json

# Find files imported by everyone
jq -r '.dependencies[].imports[]' dependency_tracking/dependency_map.json | \
   sort | uniq -c | sort -rn | head -10

# Find test files
jq '.dependencies[] | select(.file | contains("test")) | .file' \
   dependency_tracking/dependency_map.json

# Export to CSV for analysis in Excel
jq -r '.dependencies[] | [.file, (.imports | length), (.imported_by | length)] | @csv' \
   dependency_tracking/dependency_map.json > deps.csv
```

## Integration Patterns

### Pattern 1: Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "🔍 Analyzing dependencies..."
dependency-analyzer . --verbose > /dev/null

# Check for issues
if grep -q "ERROR" dependency_tracking/analyzer.log; then
  echo "❌ Dependency errors found!"
  grep "ERROR" dependency_tracking/analyzer.log
  exit 1
fi

echo "✅ Dependency analysis passed!"
```

### Pattern 2: IDE Integration

```json
// VSCode tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Analyze Dependencies",
      "type": "shell",
      "command": "dependency-analyzer . --verbose",
      "problemMatcher": [],
      "group": {
        "kind": "build",
        "isDefault": true
      }
    },
    {
      "label": "Watch Dependencies",
      "type": "shell",
      "command": "dependency-analyzer . --background",
      "isBackground": true,
      "problemMatcher": []
    }
  ]
}
```

### Pattern 3: Makefile Integration

```makefile
.PHONY: deps deps-watch deps-clean deps-report

deps:
	dependency-analyzer . --verbose
	@echo "Dependency analysis complete!"

deps-watch:
	dependency-analyzer . --background

deps-clean:
	rm -rf dependency_tracking/

deps-report:
	@echo "Dependency Report"
	@echo "================="
	@jq '.dependencies | length' dependency_tracking/dependency_map.json | \
	  xargs echo "Total files:"
	@jq '.dependencies | map(.imports | length) | add' dependency_tracking/dependency_map.json | \
	  xargs echo "Total imports:"
```

## Troubleshooting

### Issue: "Analyzer not detecting changes"
**Solution**: Check if running in background mode
```bash
ps aux | grep dependency-analyzer
# If not running: dependency-analyzer . --background
```

### Issue: "JavaScript files not parsed"
**Solution**: Ensure Node.js and @babel/parser are installed
```bash
nodejs/bin/node --version
nodejs/bin/npm list @babel/parser
```

### Issue: "Permission denied on analyzer.log"
**Solution**: Check file permissions
```bash
chmod 644 dependency_tracking/analyzer.log
```

### Issue: "Large projects are slow"
**Solution**: Exclude directories
```python
# Modify analyzer config to ignore:
# - node_modules/
# - .venv/
# - build/
# - dist/
```

## Best Practices

✅ **Run in background mode during development**  
✅ **Add dependency_tracking/ to .gitignore**  
✅ **Review dependency map before major refactors**  
✅ **Set up CI/CD checks for architecture rules**  
✅ **Generate reports periodically**  
✅ **Clean up old logs regularly**  

## Next Steps

1. **Install**: Get the analyzer running on your project
2. **Explore**: Review the dependency map
3. **Automate**: Add to CI/CD pipeline
4. **Monitor**: Use background mode during development
5. **Enforce**: Create architecture rules

## Resources

- 📖 [Full Documentation](../dependency_analyzer/dependency_analyzer/README.md)
- 🐛 [Report Issues](https://github.com/justinlietz93/Modular_Utilities/issues)

---

**Happy Analyzing! 🔍** Know your dependencies, control your codebase.
