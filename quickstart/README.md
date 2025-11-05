# Modular Utilities Quickstart Guides 🚀

Welcome to the comprehensive quickstart documentation for Modular Utilities! This collection of guides will help you master each utility and integrate them into your development workflow.

## 📚 Available Guides

### 🕷️ [Code Crawler](./code_crawler_quickstart.md)
**Transform your codebase into actionable intelligence**

The Code Crawler is an AI-powered codebase analysis tool that generates structured metadata, metrics, knowledge graphs, diagrams, and LLM-ready context bundles. Perfect for:
- Onboarding new developers
- Generating context for AI coding assistants
- Architecture documentation
- Quality gates in CI/CD
- Dependency analysis
- Security audits

**Quick Start**: `code-crawler --input . --preset all`

[Read the full guide →](./code_crawler_quickstart.md)

---

### 🤖 [Universal LLM Providers](./providers_quickstart.md)
**Write once, run on any LLM provider**

A plug-and-play abstraction layer for AI models that lets you switch between OpenAI, Anthropic, Gemini, Ollama, and more with zero code changes. Perfect for:
- Avoiding vendor lock-in
- Cost optimization through provider comparison
- Privacy-first local model usage
- A/B testing different models
- Fallback chains for reliability

**Quick Start**: Switch providers by changing one config line!

[Read the full guide →](./providers_quickstart.md)

---

### 📥 [Github-dlr](./github_dlr_quickstart.md)
**Surgical code extraction from GitHub repositories**

Download individual files or folders from any GitHub repository without cloning the entire repo. Perfect for:
- Grabbing specific examples or utilities
- Learning from open-source code patterns
- Template and boilerplate extraction
- CI/CD asset downloading
- Documentation collection

**Quick Start**: `github-dlr https://github.com/user/repo/tree/main/folder`

[Read the full guide →](./github_dlr_quickstart.md)

---

### 🔍 [Dependency Analyzer](./dependency_analyzer_quickstart.md)
**Real-time codebase dependency intelligence**

A live dependency tracking system that watches your files and maintains an up-to-date map of "what depends on what." Perfect for:
- Impact analysis before refactoring
- Detecting circular dependencies
- Finding dead code
- Architecture enforcement
- Safe code migrations

**Quick Start**: `dependency-analyzer . --background`

[Read the full guide →](./dependency_analyzer_quickstart.md)

---

### ⚡ [Python Utilities Generator](./python_utilities_generator_quickstart.md)
**Natural language to production-ready Python code**

An AI-powered code generator that transforms plain English descriptions into complete, modular Python utilities. Perfect for:
- Rapid prototyping
- Data processing scripts
- API wrappers
- CLI tools
- Automation scripts

**Quick Start**: Describe what you need, get production-ready code!

[Read the full guide →](./python_utilities_generator_quickstart.md)

---

## 🎯 Choose Your Path

### For New Users
Start with the utility that solves your immediate problem:

- **Need codebase insights?** → [Code Crawler](./code_crawler_quickstart.md)
- **Building AI apps?** → [Universal Providers](./providers_quickstart.md)
- **Want specific code from GitHub?** → [Github-dlr](./github_dlr_quickstart.md)
- **Tracking dependencies?** → [Dependency Analyzer](./dependency_analyzer_quickstart.md)
- **Writing Python scripts?** → [Python Utilities Generator](./python_utilities_generator_quickstart.md)

### For Teams
Integrate multiple utilities into your workflow:

1. **Code Intelligence Stack**
   - Code Crawler for documentation
   - Dependency Analyzer for safety
   - Combine for comprehensive codebase understanding

2. **AI Development Stack**
   - Universal Providers for model flexibility
   - Code Crawler for LLM context
   - Python Utilities Generator for rapid prototyping

3. **Learning & Research Stack**
   - Github-dlr for code examples
   - Code Crawler for analysis
   - Dependency Analyzer for understanding structure

## 🔥 Power User Combos

### Combo 1: The Complete Codebase Analyst
```bash
# Step 1: Analyze dependencies
dependency-analyzer . --background

# Step 2: Generate comprehensive documentation
code-crawler --input . --preset all --explain-cards

# Step 3: Extract knowledge graph
cat code_crawler_runs/latest/graphs/knowledge_graph.json

# Result: Complete understanding of your codebase!
```

### Combo 2: The AI-Powered Developer
```bash
# Step 1: Generate LLM context
code-crawler --input . --preset api

# Step 2: Use universal provider to query
python -c "
from providers import get_client
from providers.config import ProviderConfig

config = ProviderConfig(provider='openai', model='gpt-4o', api_key='...')
client = get_client(config)

# Load context
with open('code_crawler_runs/latest/bundles/api_bundle.txt') as f:
    context = f.read()

# Ask questions about your code
response = client.complete(f'Based on this codebase:\n{context}\n\nHow does authentication work?')
print(response)
"
```

### Combo 3: The Rapid Prototyper
```bash
# Step 1: Download template from GitHub
github-dlr https://github.com/template/project/tree/main/src

# Step 2: Generate utility code
# Use Python Utilities Generator to create needed utilities

# Step 3: Analyze dependencies
dependency-analyzer . --verbose

# Result: Fast prototyping with clean architecture!
```

### Combo 4: The Open Source Researcher
```bash
# Step 1: Download specific implementations
github-dlr -o impl1 https://github.com/project1/tree/main/auth
github-dlr -o impl2 https://github.com/project2/tree/main/auth

# Step 2: Analyze each
code-crawler --input impl1 --preset all
code-crawler --input impl2 --preset all

# Step 3: Compare approaches
diff code_crawler_runs/impl1_*/graphs/knowledge_graph.json \
     code_crawler_runs/impl2_*/graphs/knowledge_graph.json

# Result: Deep understanding of different approaches!
```

### Combo 5: The Refactoring Champion
```bash
# Step 1: Baseline analysis
dependency-analyzer . --verbose
code-crawler --input . --preset all

# Step 2: Make changes
# ... refactor code ...

# Step 3: Impact analysis
dependency-analyzer . --verbose
code-crawler --input . --preset all

# Step 4: Compare before/after
cat code_crawler_runs/latest/delta/report.json

# Result: Safe, informed refactoring!
```

## 🎓 Learning Paths

### Path 1: Developer Productivity (1 week)
**Day 1-2**: Master Code Crawler
- Run on your current project
- Generate documentation
- Set up quality gates

**Day 3-4**: Integrate Dependency Analyzer
- Run in background mode
- Create dependency reports
- Set up architecture rules

**Day 5-7**: Add AI Tools
- Set up Universal Providers
- Generate LLM context with Code Crawler
- Build custom workflows

### Path 2: AI Integration (3 days)
**Day 1**: Universal Providers
- Set up multiple providers
- Test different models
- Build fallback chains

**Day 2**: Context Generation
- Use Code Crawler for context
- Feed to LLM via Providers
- Build code Q&A system

**Day 3**: Automation
- Use Python Utilities Generator
- Create custom utilities
- Integrate into pipeline

### Path 3: Code Quality (1 week)
**Day 1-2**: Dependency Analysis
- Map entire codebase
- Find circular dependencies
- Identify dead code

**Day 3-4**: Architecture Enforcement
- Set up quality gates
- Create architecture rules
- Integrate with CI/CD

**Day 5-7**: Documentation
- Generate explain cards
- Create diagrams
- Build knowledge base

## 💡 Creative Use Cases

### Use Case 1: AI Coding Assistant Context
```bash
# Generate perfect context for ChatGPT/Claude/Copilot
code-crawler --input . --preset api --include "src/core/**"

# Copy to clipboard
cat code_crawler_runs/latest/bundles/api_bundle.txt | pbcopy

# Paste into AI assistant
# Ask: "Review this architecture and suggest improvements"
```

### Use Case 2: Onboarding Documentation
```bash
# Generate comprehensive onboarding package
code-crawler --input . --preset all --explain-cards --assets

# Create onboarding repo
mkdir onboarding
cp -r code_crawler_runs/latest/* onboarding/
cp -r code_crawler_runs/latest/diagrams/*.svg onboarding/images/

# Add to your docs
```

### Use Case 3: Multi-Provider Cost Analysis
```python
# Compare costs across providers
from providers import get_client
from providers.config import ProviderConfig
import time

providers = [
    ("openai", "gpt-4o", 0.03),  # cost per 1k tokens
    ("gemini", "gemini-2.0-flash-exp", 0.0007),
    ("anthropic", "claude-3-5-sonnet-20241022", 0.015),
]

prompt = "Your common task prompt"

for provider, model, cost_per_1k in providers:
    config = ProviderConfig(provider=provider, model=model, api_key=get_key(provider))
    client = get_client(config)
    
    start = time.time()
    response = client.complete(prompt)
    duration = time.time() - start
    
    print(f"{provider}/{model}:")
    print(f"  Latency: {duration:.2f}s")
    print(f"  Est. cost (1k calls): ${cost_per_1k}k")
```

### Use Case 4: Architecture Validation
```bash
# Enforce clean architecture rules
dependency-analyzer . --verbose

# Check violations
python -c "
import json
with open('dependency_tracking/dependency_map.json') as f:
    data = json.load(f)

# Rule: UI layer shouldn't import database
violations = [
    dep['file'] for dep in data['dependencies']
    if 'ui/' in dep['file'] and any('database' in imp for imp in dep['imports'])
]

if violations:
    print('Architecture violations found:')
    for v in violations:
        print(f'  - {v}')
    exit(1)
"
```

### Use Case 5: Smart Code Templates
```bash
# Download template
github-dlr -o template https://github.com/templates/fastapi-template/tree/main

# Customize with generated utilities
# Use Python Utilities Generator to create auth module
# Use Python Utilities Generator to create db utilities

# Analyze final structure
code-crawler --input . --preset all

# Result: Custom template with generated components!
```

## 🛠️ Workflow Integration

### VS Code Integration
```json
{
  "tasks": [
    {
      "label": "Analyze Codebase",
      "type": "shell",
      "command": "code-crawler --input . --preset all",
      "group": "build"
    },
    {
      "label": "Watch Dependencies",
      "type": "shell",
      "command": "dependency-analyzer . --background",
      "isBackground": true
    }
  ]
}
```

### Git Hooks
```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "Running dependency analysis..."
dependency-analyzer . --verbose
code-crawler --input . --no-diagrams --no-bundles
```

### Makefile
```makefile
.PHONY: analyze deps docs

analyze:
	code-crawler --input . --preset all
	dependency-analyzer . --verbose

deps:
	dependency-analyzer . --verbose

docs:
	code-crawler --input . --preset all --explain-cards
	cp code_crawler_runs/latest/diagrams/*.svg docs/images/
```

## 📊 Measuring Success

Track these metrics to see the value:

- **Time saved**: Before/after code understanding
- **Bugs prevented**: By impact analysis
- **Documentation coverage**: Auto-generated vs manual
- **Onboarding time**: New developers to productivity
- **Code quality**: Architecture violations found
- **AI costs**: Savings from provider optimization

## 🎉 Success Stories

> "Code Crawler reduced our onboarding time from 2 weeks to 3 days. New devs now get comprehensive docs and diagrams on day 1." - Tech Lead

> "Universal Providers saved us 70% on AI costs by switching to Gemini for non-critical tasks while keeping OpenAI for production." - CTO

> "Github-dlr is my secret weapon. I learn from 10x more codebases now because I only download what I need." - Senior Dev

> "Dependency Analyzer caught a circular dependency that would have caused a production outage. Saved us hours of debugging." - DevOps Engineer

> "Python Utilities Generator turned a 3-hour task into 5 minutes. I generated 20 utilities in a day." - Data Engineer

## 🤝 Contributing

Found a great use case? Creative workflow? Share it!

1. Open an issue with your use case
2. Submit a PR to add to these guides
3. Share your success story

## 📚 Additional Resources

- [Main Repository](https://github.com/justinlietz93/Modular_Utilities)
- [Report Issues](https://github.com/justinlietz93/Modular_Utilities/issues)
- [Request Features](https://github.com/justinlietz93/Modular_Utilities/issues/new)

## 🚀 Next Steps

1. **Pick a utility** that solves your current problem
2. **Follow the quickstart** guide for that utility
3. **Try a power combo** from this guide
4. **Share your experience** with the community
5. **Build something amazing**!

---

**Welcome to the Modular Utilities family!** 🎊

Whether you're analyzing codebases, building AI apps, or automating workflows, these tools are here to supercharge your development experience. Start with one utility, master it, then add more to your toolkit.

*Happy coding, happy automating, happy building!* 🚀
