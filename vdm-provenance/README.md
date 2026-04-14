# vdm-provenance

**VDM Provenance Manifest Generator** — Create immutable, machine-verifiable manifests of any repository or directory.

Generates:
- Per-file SHA-256 hashes
- File sizes
- Deterministic tree hash over the entire set
- Git commit + dirty flag (if inside a git repo)
- UTC timestamp
- Structured JSON (schema `vdm.provenance.manifest.v1`)

Optionally packs a reproducible `tar.gz` archive containing the manifest and all files.

---

## Installation (one-time, global CLI)

This tool is designed to be installed once and used from anywhere on your system.

```bash
# Clone into your modular_utilities collection (or anywhere stable)
git clone https://github.com/justinlietz03/modular_utilities.git
cd modular_utilities/vdm-provenance   # or wherever you placed the folder

# Install globally via pipx (recommended — isolated, no system pollution)
pipx install -e .

# Add to PATH (run once)
pipx ensurepath
```

> **Important**: Close and reopen your terminal (or run `exec bash -l` / `source ~/.bashrc`) so the new `build_provenance` command is visible.

---

## Usage

From any directory on your machine:

```bash
# Generate manifest in the current directory
build_provenance --target .

# Or point at any absolute/relative path
build_provenance --target /path/to/your/project
build_provenance --target ~/Downloads/my-dataset

# With optional release archive
build_provenance --target . --archive VDM_RELEASE.tar.gz

# Verbose progress
build_provenance --target . --verbose

# Full help
build_provenance --help
```

**Output**  
After execution you will see a summary on stdout:

```json
{
  "manifest": "/path/to/PROVENANCE_manifest.json",
  "archive": null,
  "files": 1427,
  "bytes": 8743921
}
```

`PROVENANCE_manifest.json` is created **inside the target folder** (never elsewhere).

---

## Command-line Options

| Flag              | Description                                      | Default                  |
|-------------------|--------------------------------------------------|--------------------------|
| `--target ROOT`   | Directory to scan (required for manifest)        | `.`                      |
| `--output FILE`   | Manifest filename/path                           | `PROVENANCE_manifest.json` |
| `--archive FILE`  | Create tar.gz containing manifest + all files    | (none)                   |
| `--exclude PATH`  | Extra path prefix to exclude (repeatable)        | (none)                   |
| `--verbose`       | Show progress on stderr                          | false                    |

---

## Features & Guarantees

- **Deterministic**: Same input directory → identical manifest (tree hash is canonical).
- **Git-aware**: Uses `git ls-files` when possible (respects `.gitignore` automatically).
- **Safe**: Skips build caches, binaries, and the manifest/archive itself.
- **No external services**: Pure stdlib; no network calls.
- **Reproducible builds**: After generation, submit the manifest + archive to a TSA (RFC3161) or OpenTimestamps for independent time-stamping.

---

## For Developers / Contributors

1. Clone the repo.
2. Make changes in `src/vdm_provenance/cli.py`.
3. Test with `pipx install -e .` (changes take effect immediately).
4. Bump version in `pyproject.toml` before releasing.

Pull requests welcome for bug fixes, additional excludes, or platform improvements.

---

**License**  
MIT

**Copyright © 2025 Justin K. Lietz, Neuroca, Inc.**  
