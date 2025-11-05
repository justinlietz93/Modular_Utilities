# Modular Utilities

Welcome! Modular Utilities is the start of a library of developer-experience tools designed to help you keep the gears on your workflow oiled. 
It currently focuses on:
- A high-precision codebase meta-file generator for building LLM context (think: codebase indexing, meta-data headers, different flag options, diagrams, and structure for your codebase).
- A universal, plug-and-play LLM providers layer (swap models/providers with minimal changes and a universal API contract).
- More utilities are planned and on the way.

If you’re a developer looking to improve your workflow, or a curious reader exploring modern tooling patterns, you’re in the right place.

---

## Why this project?

- Developer-first ergonomics: Practical, minimal ceremony, and composable. Sometimes a single basic tool can provide huge value and time savings to your workflow.
- Batteries-included, but optional: Use what you need. The [Github-dlr](https://github.com/justinlietz93/Modular_Utilities/tree/main/github-dlr) tool lets you pull individual folders from the repo.
- Future-friendly: Interfaces and adapters to help you pivot across providers and tools without rewrites.

---

## Contents

- Codebase Meta-File Generator
  - Generates structured metadata (indexes, summaries, references) for your repo.
  - Useful for code navigation, documentation, code search, embeddings pipelines, and LLM-augmented tooling.

- Universal LLM Providers (Plug-and-Play)
  - Unified interface to talk to different LLM providers and models.
  - Swap providers via configuration rather than code changes.

- More utilities to come
  - Modular building blocks oriented around DX and AI-assisted development.

---

## Project status

- Early stage / alpha / experimental
- These are best seen as quick cheap tools, unstable and not production ready
- APIs and module boundaries may evolve as features stabilize
- Feedback, ideas, and contributions are very welcome

---

## Quick start

🚀 **NEW: [Comprehensive Quickstart Guides](./quickstart/README.md)** - Detailed guides for every utility with examples, workflows, and best practices!

Because this project is evolving, the most reliable way to try it is to clone and run locally.

1) Clone the repository
- git clone https://github.com/justinlietz93/Modular_Utilities.git
- cd Modular_Utilities

2) Python setup (recommended today)
- Ensure you have Python 3.10+ installed.
- - Create and activate a virtual environment, then install in editable mode:
  - python -m venv .venv
  - source .venv/bin/activate  # on Windows: .venv\Scripts\activate
  - pip install -U pip setuptools wheel
  - pip install -e .  # add [dev] if a dev extra is provided in the future

3) Explore the utilities
- [Code Crawler](./quickstart/code_crawler_quickstart.md) - Transform your codebase into actionable intelligence
- [Universal LLM Providers](./quickstart/providers_quickstart.md) - Write once, run on any AI provider
- [Github-dlr](./quickstart/github_dlr_quickstart.md) - Download specific files/folders from GitHub
- [Dependency Analyzer](./quickstart/dependency_analyzer_quickstart.md) - Real-time dependency tracking
- [Python Utilities Generator](./quickstart/python_utilities_generator_quickstart.md) - Natural language to code

Note: If/when TypeScript packages are published to npm, we’ll add npm/pnpm/yarn install instructions here.

---

## Examples (lightweight, conceptual)

Below are high-level examples to convey the spirit of the utilities. Names and APIs may differ as the project iterates—consult the source for the current interfaces.

- Codebase meta-file generation (conceptual Python sketch)
  - from modular_utilities.meta import CodebaseIndexer
  - index = CodebaseIndexer(path=".", include=["src", "app"]).build()
  - index.to_json("codebase.index.json")

- Universal LLM provider abstraction (conceptual Python sketch)
  - from modular_utilities.llm import LLM, ProviderConfig
  - llm = LLM.from_config(ProviderConfig(provider="openai", model="gpt-4o-mini", api_key="..."))
  - response = llm.complete("Summarize this repository in two sentences.")
  - print(response.text)

As stable APIs land, we’ll include fully runnable examples and notebooks.

---

## Roadmap

- [ ] Solidify stable interfaces for meta-file generation and LLM abstraction
- [ ] Add provider adapters (OpenAI, Anthropic, etc.) behind a unified API
- [ ] Expand TypeScript utilities to parity where it makes sense
- [ ] Example scripts and notebooks
- [ ] Documentation website (guides, patterns, recipes)
- [ ] Benchmarks and integration tests

If there’s a feature you want, please open an issue with details about your use case.

---

## Contributing

Contributions of all sizes are welcome:
- Suggest features or improvements via issues
- Submit PRs for bug fixes, docs, or new utilities
- Share patterns and examples that helped you

Suggested flow:
1) Open an issue to discuss your idea (optional but helpful).
2) Fork, create a feature branch, and make changes.
3) Write a concise PR explaining the “why” and the “how.”

Please keep code modular and well-documented—this project values clarity and composability.

---

## Community & support

- Have questions or feedback? Open an issue and we’ll triage quickly.
- Curious about direction? Check the Roadmap section above and join the discussion in issues.

If you find Modular Utilities useful, consider starring the repo—it helps others discover it!

---

## License

This project will include a license file if it hasn’t already. If you need clarification on usage before then, feel free to open an issue.

---

Made with a focus on developer experience by @justinlietz93.
