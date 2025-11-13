"""Pytest configuration for ml_trainer tests."""

import sys
from pathlib import Path

# Add GPT-Export-Parser to Python path
gpt_parser_path = Path(__file__).parent.parent.parent / 'GPT-Export-Parser'
sys.path.insert(0, str(gpt_parser_path))
