# Contributing to GitHub-dlr

Thank you for your interest in contributing to GitHub-dlr! This guide will help you set up your local development environment and understand the development workflow.

## Prerequisites

- Python 3.8 or higher
- [uv](https://docs.astral.sh/uv/) package manager

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/rocktimsaikia/github-dlr.git
cd github-dlr
```

### 2. Create a Virtual Environment

Use the commands

Create a virtual environment using uv
```bash
uv venv
```

Activate the virtual environment
```bash
source .venv/bin/activate
```

And you can deactivate the virtual environment with:
```bash
deactivate
```

### 3. Install Dependencies

Install all dependencies including development dependencies:
```bash
uv sync
```

### 4. Verify Installation

Test that the installation works by running the CLI:
```bash
uv run github-dlr --help
```

## Development Workflow

### Running Tests

Run all tests:
```bash
uv run pytest
```

### Testing the CLI

Test the CLI locally with a GitHub URL:
```bash
uv run github-dlr https://github.com/example/repo/tree/main/folder
```

Test with custom output directory:
```bash
uv run github-dlr -o output_dir https://github.com/example/repo/tree/main/folder
```

### Building the Package

Build the package for distribution:
```bash
uv build
```

Check the build without creating files:
```bash
uv build --check
```

## Code Structure

- `github_dlr/console.py` - CLI entry point and argument parsing
- `github_dlr/source.py` - Core download logic and GitHub API integration
- `github_dlr/loader.py` - Loading animation utilities
- `tests/` - Test suite with async HTTP mocking

## Contributing Guidelines

1. **Fork the repository** and create a feature branch
2. **Write tests** for any new functionality
3. **Ensure all tests pass** before submitting
4. **Follow the existing code style** and patterns
5. **Update documentation** if needed
6. **Create a pull request** with a clear description

## Development Tips

- The project uses async/await heavily for HTTP requests
- Tests use `pytest-asyncio` and `pytest-aiohttp` for async testing
- Progress bars are implemented with `alive-progress`
- All HTTP requests use `aiohttp` for better performance

## Getting Help

If you have questions or need help:
- Check existing issues on GitHub
- Create a new issue for bugs or feature requests
- Review the code documentation and tests for examples

Thank you for contributing! 🎉
