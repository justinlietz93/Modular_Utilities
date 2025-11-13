"""Pytest configuration for all tests."""

import sys
from pathlib import Path

# Add GPT-Export-Parser to Python path for ml_trainer tests
gpt_parser_path = Path(__file__).parent.parent / 'GPT-Export-Parser'
if gpt_parser_path.exists():
    sys.path.insert(0, str(gpt_parser_path))
