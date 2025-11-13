# GPT Export Parser

A Python utility to parse and organize ChatGPT conversation exports into readable text files, organized by month and year.

## Overview

This tool processes ChatGPT conversation export data (from the `conversations.json` file) and:

- Extracts all messages from conversations
- Organizes conversations into monthly directories
- Saves each conversation as a plain text file
- Generates a pruned JSON file with structured conversation data

## Prerequisites

- Python 3.x
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

## Limitations

- Skips conversations without an update timestamp
- Only processes text content (ignores images, code outputs, etc.)
- System messages are filtered out (except custom user system messages)

## Notes on search

Basic exact-text search is best done with your editor across the generated `.txt` files or `pruned.json`. If you want semantic search (meaning-based), that requires additional tooling (embedding models + vector index). If you want, we can add a minimal semantic search utility as a separate command in the future.

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
