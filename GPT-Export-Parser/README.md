# GPT Export Parser

A Python utility to parse and organize ChatGPT conversation exports into readable text files, organized by month and year.

**NEW:** ML Memory Trainer - Build a "permanent memory" from your conversations! See [ml_trainer/README.md](ml_trainer/README.md) for details.

## Overview

This tool processes ChatGPT conversation export data (from the `conversations.json` file) and:

- Extracts all messages from conversations
- Organizes conversations into monthly directories
- Saves each conversation as a plain text file
- Generates a pruned JSON file with structured conversation data
- **NEW:** Train ML models for semantic search, prompt assistance, and thread detection

## Components

### 1. Extract Messages (`extract_messages.py`)
Parses and organizes your ChatGPT conversation exports.

### 2. ML Memory Trainer (`ml_trainer/`)
**NEW!** Build an intelligent "permanent memory" system:
- **Semantic Search**: Find relevant past conversations
- **Prompt Assistance**: Get context-aware suggestions
- **Thread Detection**: Identify open threads and action items
- **Incremental Training**: Daily updates with only new conversations
- **Privacy-First**: 100% local execution, no cloud dependencies

See [ml_trainer/README.md](ml_trainer/README.md) for complete documentation.

## Prerequisites

- Python 3.10+
- ChatGPT conversation export data (`conversations.json`)

## How to Get Your ChatGPT Data

1. Go to ChatGPT settings
2. Navigate to "Data controls"
3. Click "Export data"
4. Wait for the email with your data export
5. Download and extract the ZIP file
6. Locate the `conversations.json` file

## Installation

No external dependencies required - uses only Python standard library modules.

```bash
git clone <repository-url>
cd GPT-Export-Parser
```

## Usage

### Setup

1. Create a `data` directory in the same location as the script and place your `conversations.json` file there:

   ```bash
   mkdir -p data
   cp /path/to/your/conversations.json data/
   ```

2. Run the script (incremental by default):

   ```bash
   python3 extract_messages.py
   ```

### Advanced usage

- Full rebuild (ignore previous runs and reprocess everything):

   ```bash
   python3 extract_messages.py --full
   ```

- Only ingest conversations updated on/after a date (still incremental against prior runs):

   ```bash
   python3 extract_messages.py --since 2025-11-01
   ```

- Show per-month counts and exit (no file writes):

   ```bash
   python3 extract_messages.py --stats
   ```

- Export a CSV summary of metadata (id, title, times, month, output file, message_count):

   ```bash
   python3 extract_messages.py --csv-out data/summary.csv
   ```

- Verbose or quiet logging:

   ```bash
   python3 extract_messages.py --verbose
   python3 extract_messages.py --quiet
   ```

- Use a custom data directory (contains conversations.json and receives outputs):

   ```bash
   python3 extract_messages.py --data-dir /path/to/data
   ```

### Output

The script creates all output in the `data/` directory relative to the script location:

#### 1. Monthly Directories

Conversations are organized into directories by month and year:

```text
data/
├── January_2024/
├── February_2024/
├── March_2024/
└── ...
```

#### 2. Individual Conversation Files

Each conversation is saved as a text file with format:

```text
<sanitized_title>_<dd_mm_yyyy_HH_MM_SS>.txt
```

Example: `Python_debugging_help_15_03_2024_14_30_45.txt`

**File contents format:**

```text
user
<user message text>
ChatGPT
<assistant response text>
user
<next user message>
...
```

#### 3. Pruned JSON File

A `pruned.json` file is created at `data/pruned.json` containing:

- All conversations organized by month
- Conversation metadata (title, create time, update time)
- All messages with author and text

## Customization

### Changing Output Directory

The script uses a relative path to the `data/` directory. If you want to change this, edit the `DATA_DIR` variable in `extract_messages.py`:

```python
# Change this line:
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')

# To your preferred relative path:
DATA_DIR = os.path.join(SCRIPT_DIR, 'your_custom_directory')

# Or to an absolute path:
DATA_DIR = '/your/absolute/path'
```

### Title Sanitization

File names are automatically sanitized:

- Special characters replaced with underscores
- Truncated to 120 characters
- Timestamp appended for uniqueness

## Features

### Extract Messages
- **Message extraction**: Parses the conversation tree structure to extract messages in chronological order
- **Author identification**: Distinguishes between user, ChatGPT, and custom system messages
- **Date-based organization**: Groups conversations by month and year
- **Sanitized filenames**: Ensures filesystem compatibility
- **JSON export**: Creates a structured JSON file for programmatic access
- **UTF-8 support**: Handles international characters correctly
- **Relative paths**: Uses relative paths for easy portability
- **Incremental ingestion**: Tracks processed conversations in `data/metadata.db` and only adds new data on subsequent runs
- **Date filter**: `--since YYYY-MM-DD` filters new ingestion to recent updates
- **Stats and CSV**: `--stats` for a quick overview, `--csv-out` for downstream analysis

### ML Memory Trainer (NEW!)
- **Semantic Search**: Find relevant conversations using meaning, not just keywords
- **Prompt Assistance**: Get context-aware suggestions from your conversation history
- **Thread Detection**: Automatically identify open threads and unresolved questions
- **Action Item Tracking**: Find pending tasks and follow-ups
- **Incremental Training**: Efficient daily updates with only new/changed conversations
- **Privacy-Preserving**: 100% local execution, no cloud dependencies
- **Flexible Architecture**: Works with sentence-transformers + FAISS, or falls back to TF-IDF + numpy

See [ml_trainer/README.md](ml_trainer/README.md) for complete ML features documentation.

## Quick Start with ML Memory

```bash
# 1. Extract your conversations
python extract_messages.py

# 2. Train the ML model
python ml_trainer/cli.py train

# 3. Query your memory
python ml_trainer/cli.py query "How did I solve that async error?"

# 4. Check open threads
python ml_trainer/cli.py threads --summary

# 5. Get prompt assistance
python ml_trainer/cli.py prompt-assist "debugging React hooks" --enhanced
```

## Limitations

### Extract Messages
- Skips conversations without an update timestamp
- Only processes text content (ignores images, code outputs, etc.)
- System messages are filtered out (except custom user system messages)

### ML Memory Trainer
- Semantic search requires sentence-transformers or falls back to TF-IDF
- Vector search requires FAISS or falls back to numpy (slower for large datasets)
- Initial training time scales with number of conversations (~100/min on CPU)

## Notes on Search

**Basic Search**: Use your text editor to search across the generated `.txt` files or `pruned.json`.

**Semantic Search**: Use the new ML Memory Trainer! It provides meaning-based search, not just keyword matching. See [ml_trainer/README.md](ml_trainer/README.md) for details.

## Troubleshooting

**File not found error:**

- Ensure `conversations.json` exists in the `data/` directory
- Check file permissions

**Permission denied:**

- Ensure write permissions for the `data/` directory
- Run with appropriate user permissions

**Empty output:**

- Verify `conversations.json` is valid JSON
- Check if conversations have text content

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
