"""Tests for math converter domain models."""
import pytest
from math_converter.domain.syntax_types import SyntaxType, ConversionRequest


class TestSyntaxType:
    """Test SyntaxType enum."""
    
    def test_from_string_valid(self):
        """Test converting valid strings to SyntaxType."""
        assert SyntaxType.from_string("latex") == SyntaxType.LATEX
        assert SyntaxType.from_string("LATEX") == SyntaxType.LATEX
        assert SyntaxType.from_string("mathjax") == SyntaxType.MATHJAX
        assert SyntaxType.from_string("ascii") == SyntaxType.ASCII
        assert SyntaxType.from_string("unicode") == SyntaxType.UNICODE
    
    def test_from_string_invalid(self):
        """Test converting invalid string raises ValueError."""
        with pytest.raises(ValueError, match="Unknown syntax type"):
            SyntaxType.from_string("invalid")
    
    def test_all_types(self):
        """Test getting all syntax types."""
        all_types = SyntaxType.all_types()
        assert len(all_types) == 4
        assert SyntaxType.LATEX in all_types
        assert SyntaxType.MATHJAX in all_types
        assert SyntaxType.ASCII in all_types
        assert SyntaxType.UNICODE in all_types


class TestConversionRequest:
    """Test ConversionRequest dataclass."""
    
    def test_needs_from_prompt(self):
        """Test needs_from_prompt method."""
        request = ConversionRequest(
            from_syntax=None,
            to_syntax=SyntaxType.MATHJAX,
            input_paths=[],
            output_dir=None,
            in_place=True,
            auto_yes=False,
            auto_no=False
        )
        assert request.needs_from_prompt() is True
        
        request.from_syntax = SyntaxType.LATEX
        assert request.needs_from_prompt() is False
    
    def test_needs_to_prompt(self):
        """Test needs_to_prompt method."""
        request = ConversionRequest(
            from_syntax=SyntaxType.LATEX,
            to_syntax=None,
            input_paths=[],
            output_dir=None,
            in_place=True,
            auto_yes=False,
            auto_no=False
        )
        assert request.needs_to_prompt() is True
        
        request.to_syntax = SyntaxType.MATHJAX
        assert request.needs_to_prompt() is False
