# ==============================================================================
# Code Crawler: Ignore Patterns (`config.py`)
# ==============================================================================
#
# This file defines the `ignore_patterns` list, which controls which files and
# directories are excluded from the analysis.
#
# HOW IT WORKS:
# The list is imported by `analyzer.py` and used to filter the file paths
# during the directory walk. The patterns are simple glob-style strings that
# are matched against paths relative to the project root (where the crawler
# is executed).
#
# ==============================================================================
# Crawler Configuration
# ==============================================================================
# This file specifies directories and files to be ignored by the code crawler.
# The matching logic is inspired by how `.gitignore` works.
#
# HOW TO USE:
# - Add glob patterns to the `ignore_patterns` list.
# - Patterns are matched against paths relative to the project root.
#
# PATTERN RULES:
#
# 1. To ignore a directory and all its contents, add a trailing slash.
#    - `'my_dir/'` ignores the entire directory.
#
# 2. To ignore files by a pattern everywhere, do not use a slash.
#    - `'*.log'` ignores all log files.
#    - `'__pycache__'` ignores all __pycache__ directories.
#
# 3. To ignore a specific file or path, use the full relative path.
#    - `'AdvancedMath/main.py'` ignores only that specific file.
#
# IMPORTANT: The recursive wildcard `**` is NOT supported. Blank lines and
# lines starting with '#' are ignored.
# ==============================================================================

# config.py
ignore_patterns = [
    # General file patterns (no slash)
    '*.pyc',
    '*.DS_Store',
    '*.png',
    '*.jpg',
    '*.jpeg',
    '*.gif',
    '*.log',
    'ENHANCEMENTS.md',
    'FUM_Novelty_Memo.md',
    'MESSAGE_TO_ROO.txt',

    # General directory patterns (no slash)
    '.git',
    '__pycache__',
    
    # Path-specific directory patterns (must end with /)
    'ignore/',
    '.vscode/',
    'venv/',
    'code_crawler/',
    #'FullyUnifiedModel/',
    'CURRENT_PLAN/',
    '_FUM_Training/',
    'mathematical_frameworks/',
    'planning_outlines/',
    'code_crawler_results/',
    'runs/',

    # # Path-specific file patterns
    'AdvancedMath/calculate_descriptive_stats.py',
]