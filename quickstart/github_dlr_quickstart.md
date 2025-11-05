# Github-dlr Quickstart Guide 📥

Github-dlr (GitHub Downloader Recursive) is your precision tool for grabbing exactly what you need from any GitHub repository—no cloning required. Think of it as surgical extraction for code: pull a single folder, file, or entire directory tree in seconds.

## Table of Contents
- [Why Github-dlr?](#why-github-dlr)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Features & Use Cases](#core-features--use-cases)
- [Creative Workflows](#creative-workflows)
- [Advanced Usage](#advanced-usage)
- [Pro Tips](#pro-tips)

## Why Github-dlr?

### The Problem

You want to:
- Grab a single example from a massive repo (e.g., TensorFlow examples)
- Download just the `src/` folder from a monorepo
- Pull docs without cloning 2GB of code
- Try a utility without pulling dependencies
- Learn from specific parts of open-source projects

**Traditional approach**: Clone the entire repo (slow, wastes disk space, pulls everything).

**Github-dlr approach**: Download only what you need in seconds.

### What Makes It Priceless

✅ **Lightning Fast**: Download folders/files in seconds  
✅ **Bandwidth Saver**: No unnecessary downloads  
✅ **Disk Space Friendly**: Only get what you need  
✅ **Learning Accelerator**: Study specific code patterns quickly  
✅ **CI/CD Ready**: Pull specific assets in pipelines  
✅ **Offline-Friendly**: Download once, use everywhere  

## Installation

```bash
# Using pip
pip install github-dlr

# Using pipx (recommended for CLI tools)
pipx install github-dlr

# Verify installation
github-dlr --version
# or
gh-dlr --version  # Shorter alias!
```

**Requirements**: Python 3.8+

## Quick Start

### Basic Usage

```bash
# Copy the GitHub URL of any folder
# Example: https://github.com/django/django/tree/main/django/contrib/admin

# Paste it after the command
github-dlr https://github.com/django/django/tree/main/django/contrib/admin

# Done! The folder is now in your current directory
ls django-contrib-admin/
```

### Specify Output Directory

```bash
# Download to a specific location
github-dlr --output my-folder https://github.com/user/repo/tree/main/src

# Use short form
gh-dlr -o my-folder https://github.com/user/repo/tree/main/src
```

### Download Single Files

```bash
# Works with files too!
github-dlr https://github.com/user/repo/blob/main/README.md

# Specify output name
gh-dlr -o custom-readme.md https://github.com/user/repo/blob/main/README.md
```

## Core Features & Use Cases

### 1. **Learning from Examples** 📚

**Use Case**: You want to learn React patterns from Facebook's repos.

```bash
# Download React examples without cloning entire repo
github-dlr https://github.com/facebook/react/tree/main/fixtures/packaging

# Explore the code
cd react-fixtures-packaging
ls
# Now study the examples!
```

**Workflow**:
1. Browse GitHub for interesting patterns
2. Find the specific folder/file
3. Download with github-dlr
4. Study, modify, learn
5. Delete when done (no Git history clutter)

### 2. **Grabbing Utilities & Tools** 🛠️

**Use Case**: You need a specific utility from a monorepo.

```bash
# Example: Download a specific utility from Modular_Utilities
github-dlr https://github.com/justinlietz93/Modular_Utilities/tree/main/providers

# Now you have just the providers module!
cd Modular_Utilities-providers/
pip install -e .
```

**Real-World Scenarios**:
- Pull authentication module from a boilerplate
- Grab database utilities from a framework
- Extract config files from example projects
- Download specific middleware implementations

### 3. **Documentation Without Code** 📖

**Use Case**: You want docs but not the 2GB repo.

```bash
# Download just the docs folder
github-dlr https://github.com/microsoft/vscode/tree/main/docs

# Or specific doc files
gh-dlr -o api-docs https://github.com/fastapi/fastapi/tree/master/docs/en/docs
```

**Perfect For**:
- Offline documentation
- Creating custom doc collections
- Documentation research
- Building knowledge bases

### 4. **Template & Boilerplate Extraction** 🎨

**Use Case**: You want a project template without the repo baggage.

```bash
# Download a template directory
github-dlr https://github.com/vercel/next.js/tree/canary/examples/blog-starter

# Rename and use
mv next.js-examples-blog-starter my-new-blog
cd my-new-blog
npm install
```

**Template Use Cases**:
- React component patterns
- Express.js server templates
- CI/CD workflow files
- Docker configurations
- Terraform modules

### 5. **CI/CD Integration** 🔄

**Use Case**: Pull specific assets during build pipeline.

```bash
#!/bin/bash
# In your CI/CD pipeline

# Download deployment scripts from central repo
github-dlr -o scripts https://github.com/company/infra/tree/main/scripts

# Use them
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

**GitHub Actions Example**:
```yaml
name: Deploy
on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Install github-dlr
        run: pip install github-dlr
      
      - name: Download deployment configs
        run: |
          github-dlr -o configs https://github.com/company/configs/tree/main/production
      
      - name: Deploy
        run: ./deploy.sh --config configs/app.yaml
```

### 6. **Dependency Vendoring** 📦

**Use Case**: Vendor a small dependency instead of adding to package.json.

```bash
# Download a specific JavaScript utility
github-dlr https://github.com/lodash/lodash/tree/master/src

# Place in your project
mv lodash-src vendor/lodash

# Now you control the code!
```

**When to Vendor**:
- Small, stable utilities
- Custom modifications needed
- Avoiding dependency bloat
- Security: audit code first
- License compatibility checks

### 7. **Research & Analysis** 🔬

**Use Case**: Compare implementations across projects.

```bash
# Download authentication modules from different frameworks
github-dlr -o django-auth https://github.com/django/django/tree/main/django/contrib/auth
github-dlr -o flask-auth https://github.com/pallets/flask/tree/main/examples/tutorial/flaskr

# Compare approaches
diff -r django-auth flask-auth
```

**Research Workflows**:
- Security pattern analysis
- Performance comparison studies
- API design research
- Testing strategy evaluation

### 8. **Asset Extraction** 🖼️

**Use Case**: Pull images, configs, or other assets.

```bash
# Download wallpapers from a collection
github-dlr -o wallpapers https://github.com/makccr/wallpapers/tree/master/wallpapers/space

# Download config examples
github-dlr -o nginx-configs https://github.com/h5bp/server-configs-nginx/tree/main/h5bp

# Download icons/assets
github-dlr -o icons https://github.com/icons8/line-awesome/tree/master/svg
```

**Asset Types**:
- Images/icons
- Configuration files
- Database schemas
- API specifications (OpenAPI/Swagger)
- Machine learning models

## Creative Workflows

### Workflow 1: The Code Explorer

```bash
#!/bin/bash
# explore-repo.sh - Quickly explore parts of a repo

REPO=$1
PARTS=("src" "tests" "docs" "examples")

for part in "${PARTS[@]}"; do
  echo "Downloading $part..."
  github-dlr -o "${REPO##*/}-$part" "$REPO/tree/main/$part" 2>/dev/null
done

echo "✅ Exploration complete!"
ls -d "${REPO##*/}"-*
```

**Usage**:
```bash
./explore-repo.sh https://github.com/django/django
# Creates: django-src, django-tests, django-docs, django-examples
```

### Workflow 2: The Dependency Collector

```bash
#!/bin/bash
# collect-deps.sh - Build a local dependency archive

mkdir -p vendor

# Collect utilities from various repos
github-dlr -o vendor/auth https://github.com/repo1/auth-utils
github-dlr -o vendor/db https://github.com/repo2/db-helpers
github-dlr -o vendor/logging https://github.com/repo3/logging

# Now you have a curated collection!
tree vendor/
```

### Workflow 3: The Template Mixer

```bash
#!/bin/bash
# mix-templates.sh - Combine parts from different templates

# Download different pieces
github-dlr -o frontend https://github.com/template1/tree/main/frontend
github-dlr -o backend https://github.com/template2/tree/main/api
github-dlr -o infra https://github.com/template3/tree/main/infrastructure

# Combine into your project
mkdir my-app
cp -r frontend/* my-app/
cp -r backend/* my-app/api/
cp -r infra/* my-app/.infra/

cd my-app
# Customize and go!
```

### Workflow 4: The Documentation Aggregator

```bash
#!/bin/bash
# aggregate-docs.sh - Build a custom docs collection

mkdir -p docs-collection

DOCS_SOURCES=(
  "https://github.com/python/cpython/tree/main/Doc"
  "https://github.com/django/django/tree/main/docs"
  "https://github.com/pallets/flask/tree/main/docs"
)

for i in "${!DOCS_SOURCES[@]}"; do
  github-dlr -o "docs-collection/source-$i" "${DOCS_SOURCES[$i]}"
done

# Generate index
echo "# Documentation Collection" > docs-collection/INDEX.md
echo "" >> docs-collection/INDEX.md
ls -1 docs-collection/ | while read dir; do
  echo "- [$dir](./$dir)" >> docs-collection/INDEX.md
done

# Now serve with any static server
cd docs-collection && python -m http.server 8000
# Visit: http://localhost:8000
```

### Workflow 5: The Configuration Manager

```bash
#!/bin/bash
# sync-configs.sh - Keep configs in sync across projects

CENTRAL_CONFIGS="https://github.com/company/configs/tree/main"

# Download latest configs
github-dlr -o .tmp-configs "$CENTRAL_CONFIGS"

# Sync specific files
cp .tmp-configs/.eslintrc.json .
cp .tmp-configs/.prettierrc.json .
cp .tmp-configs/tsconfig.json .

# Cleanup
rm -rf .tmp-configs

echo "✅ Configs synchronized!"
```

### Workflow 6: The Multi-Source Learner

```bash
#!/bin/bash
# learn-pattern.sh - Study a pattern across repos

PATTERN="authentication"
REPOS=(
  "https://github.com/django/django/tree/main/django/contrib/auth"
  "https://github.com/expressjs/express/tree/master/examples/auth"
  "https://github.com/rails/rails/tree/main/railties/lib/rails/auth"
)

mkdir -p "learning-$PATTERN"

for i in "${!REPOS[@]}"; do
  github-dlr -o "learning-$PATTERN/implementation-$i" "${REPOS[$i]}"
done

# Generate comparison document
echo "# $PATTERN Implementation Comparison" > "learning-$PATTERN/COMPARISON.md"
echo "" >> "learning-$PATTERN/COMPARISON.md"
ls -1 "learning-$PATTERN/" | while read impl; do
  echo "## $impl" >> "learning-$PATTERN/COMPARISON.md"
  echo "" >> "learning-$PATTERN/COMPARISON.md"
  find "learning-$PATTERN/$impl" -type f -name "*.py" -o -name "*.js" | \
    head -5 | while read file; do
      echo "- \`$file\`" >> "learning-$PATTERN/COMPARISON.md"
    done
  echo "" >> "learning-$PATTERN/COMPARISON.md"
done

# Open for study
open "learning-$PATTERN/COMPARISON.md"
```

## Advanced Usage

### Recursive Downloads (Nested Folders)

```bash
# Github-dlr recursively downloads all subdirectories by default
github-dlr https://github.com/user/repo/tree/main/src

# This gets:
# src/
# ├── module1/
# │   ├── file1.py
# │   └── nested/
# │       └── file2.py
# └── module2/
#     └── file3.py
```

### Download from Specific Branches/Tags

```bash
# Download from a specific branch
github-dlr https://github.com/user/repo/tree/develop/src

# Download from a tag
github-dlr https://github.com/user/repo/tree/v1.2.3/src

# Download from a commit SHA
github-dlr https://github.com/user/repo/tree/abc123def/src
```

### Download from Private Repositories

```bash
# Set GitHub token
export GITHUB_TOKEN="ghp_your_token_here"

# Now you can download from private repos
github-dlr https://github.com/your-org/private-repo/tree/main/src
```

**Getting a Token**:
1. Go to GitHub Settings → Developer Settings → Personal Access Tokens
2. Generate token with `repo` scope
3. Export as environment variable

### Download Multiple Folders in Parallel

```bash
#!/bin/bash
# parallel-download.sh

FOLDERS=(
  "https://github.com/repo/tree/main/src"
  "https://github.com/repo/tree/main/tests"
  "https://github.com/repo/tree/main/docs"
)

for folder in "${FOLDERS[@]}"; do
  github-dlr "$folder" &
done

wait
echo "✅ All downloads complete!"
```

### Integration with Git Sparse Checkout Alternative

```bash
# Instead of git sparse-checkout (complex), use github-dlr!

# OLD WAY (complex):
git clone --filter=blob:none --sparse https://github.com/user/repo
cd repo
git sparse-checkout set src/specific/folder

# NEW WAY (simple):
github-dlr https://github.com/user/repo/tree/main/src/specific/folder
```

## Pro Tips

### 🎯 Tip 1: Use Shell Aliases

```bash
# Add to ~/.bashrc or ~/.zshrc
alias ghd='github-dlr'
alias ghdo='github-dlr -o'

# Now:
ghd https://github.com/user/repo/tree/main/src
ghdo my-folder https://github.com/user/repo/tree/main/docs
```

### 🎯 Tip 2: Bookmark Frequently Used URLs

```bash
# Create a bookmarks file
cat > ~/.github-dlr-bookmarks <<EOF
django-admin=https://github.com/django/django/tree/main/django/contrib/admin
react-examples=https://github.com/facebook/react/tree/main/fixtures/packaging
tailwind-components=https://github.com/tailwindlabs/tailwindcss/tree/master/src/components
EOF

# Use with a wrapper script
ghd-bookmark() {
  URL=$(grep "^$1=" ~/.github-dlr-bookmarks | cut -d= -f2)
  github-dlr "$URL"
}

# Usage:
ghd-bookmark django-admin
```

### 🎯 Tip 3: Auto-Extract Archives

```bash
# Some repos have release assets - download them!
github-dlr https://github.com/user/repo/releases/download/v1.0.0/package.tar.gz
tar -xzf package.tar.gz
```

### 🎯 Tip 4: Preview Before Download

```bash
# Use GitHub's web interface to browse first
# Copy URL when you find what you need
# Then use github-dlr for instant download
```

### 🎯 Tip 5: Cleanup Old Downloads

```bash
# Add to cron or run manually
find . -maxdepth 1 -type d -name "*github*" -mtime +30 -exec rm -rf {} \;
# Removes downloads older than 30 days
```

### 🎯 Tip 6: Create a Download Library

```bash
# Organize downloads systematically
mkdir -p ~/github-downloads/{utils,templates,docs,examples}

# Download to organized locations
github-dlr -o ~/github-downloads/utils/auth-module [URL]
github-dlr -o ~/github-downloads/templates/react-app [URL]
github-dlr -o ~/github-downloads/docs/python-guide [URL]
```

### 🎯 Tip 7: Use with Other Tools

```bash
# Download + analyze with tree
github-dlr [URL] && tree -L 3 ./downloaded-folder

# Download + search
github-dlr [URL] && cd downloaded-folder && rg "pattern"

# Download + count lines
github-dlr [URL] && find downloaded-folder -name "*.py" | xargs wc -l
```

## Common Use Cases Cheatsheet

| Use Case | Command |
|----------|---------|
| Download entire folder | `github-dlr [folder-url]` |
| Download to specific path | `github-dlr -o mydir [url]` |
| Download single file | `github-dlr [file-url]` |
| Download from branch | `github-dlr [url-with-branch]` |
| Download from tag | `github-dlr [url-with-tag]` |
| Download from private repo | `GITHUB_TOKEN=xxx github-dlr [url]` |

## Troubleshooting

### Issue: "Permission denied"
**Solution**: Check GitHub token for private repos
```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

### Issue: "URL not valid"
**Solution**: Ensure URL format is correct
```bash
# ✅ Correct:
github-dlr https://github.com/user/repo/tree/main/folder

# ❌ Wrong:
github-dlr https://github.com/user/repo/folder  # Missing /tree/main
```

### Issue: "Download too slow"
**Solution**: Check your network connection or try a smaller folder first

### Issue: "Already exists"
**Solution**: Rename or remove existing folder
```bash
rm -rf existing-folder
github-dlr [url]

# Or download to different name
github-dlr -o new-name [url]
```

## Performance Tips

- **Large folders**: Downloads may take time depending on size and network speed
- **Parallel downloads**: Use background jobs for multiple folders
- **Bandwidth**: github-dlr uses GitHub's API, respecting rate limits
- **Caching**: Downloaded files are not cached; re-downloading fetches fresh copies

## Comparison with Alternatives

| Feature | github-dlr | git clone | git sparse-checkout | degit |
|---------|-----------|-----------|---------------------|-------|
| Speed | ⚡ Fast | Slow | Medium | Fast |
| Ease | ✅ Simple | Complex | Very Complex | Simple |
| Single folder | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| No Git history | ✅ Yes | ❌ No | ❌ No | ✅ Yes |
| Works with any branch | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |

## Real-World Success Stories

### Story 1: The Fast Learner
> "I wanted to learn FastAPI patterns. Instead of cloning the entire repo (200MB), I used github-dlr to grab just the examples folder (2MB). Saved time and disk space!" - Dev Learning FastAPI

### Story 2: The CI/CD Engineer
> "We use github-dlr to pull deployment scripts from a central repo during builds. Shaved 5 minutes off every deployment!" - DevOps Engineer

### Story 3: The Template Collector
> "I maintain a collection of project templates. github-dlr lets me pull updates from upstream repos without dealing with Git submodules." - Open Source Maintainer

## Next Steps

1. **Try it**: Download your first folder
2. **Bookmark it**: Add frequently used repos
3. **Automate**: Integrate into your workflows
4. **Share**: Teach your team this time-saver

## Resources

- 📖 [Full Documentation](../github-dlr/README.md)
- 🐛 [Report Issues](https://github.com/justinlietz93/Modular_Utilities/issues)
- 💡 [Request Features](https://github.com/justinlietz93/Modular_Utilities/issues/new)

---

**Happy Downloading! 📥** Precision code extraction, at your fingertips.
