"""Tests for PDF extraction functionality."""
import pytest
from pathlib import Path
import tempfile
import shutil

from math_converter.application.pdf_extractor import PDFExtractor


class TestPDFExtractor:
    """Test PDF extraction."""
    
    @pytest.fixture
    def extractor(self):
        """Create PDF extractor."""
        return PDFExtractor()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_is_available(self, extractor):
        """Test checking if PDF extraction is available."""
        # Should be available if PyMuPDF is installed
        available = extractor.is_available()
        assert isinstance(available, bool)
    
    def test_extract_math_patterns_display_bracket(self, extractor):
        """Test extracting display math with brackets."""
        text = r"Some text \[ x^2 + y^2 = z^2 \] more text"
        expressions = extractor._extract_math_patterns(text, 1)
        
        assert len(expressions) > 0
        assert any("x^2 + y^2 = z^2" in expr for _, expr in expressions)
    
    def test_extract_math_patterns_inline_paren(self, extractor):
        """Test extracting inline math with parentheses."""
        text = r"Inline \( E = mc^2 \) equation"
        expressions = extractor._extract_math_patterns(text, 1)
        
        assert len(expressions) > 0
        assert any("E = mc^2" in expr for _, expr in expressions)
    
    def test_extract_math_patterns_double_dollar(self, extractor):
        """Test extracting display math with double dollars."""
        text = r"Display $$ \sum_{i=1}^n i $$ equation"
        expressions = extractor._extract_math_patterns(text, 1)
        
        assert len(expressions) > 0
        assert any(r"\sum_{i=1}^n i" in expr for _, expr in expressions)
    
    def test_extract_math_patterns_single_dollar(self, extractor):
        """Test extracting inline math with single dollars."""
        text = "Inline $f(x) = x^2$ equation"
        expressions = extractor._extract_math_patterns(text, 1)
        
        assert len(expressions) > 0
        assert any("f(x) = x^2" in expr for _, expr in expressions)
    
    def test_extract_math_patterns_filters_currency(self, extractor):
        """Test that currency amounts are filtered out."""
        text = "The cost is $50 dollars"
        expressions = extractor._extract_math_patterns(text, 1)
        
        # Should not extract "$50" as math
        assert not any("50" in expr and "$" in expr for _, expr in expressions)
    
    def test_save_to_markdown(self, extractor, temp_dir):
        """Test saving expressions to markdown."""
        expressions = [
            ("Page 1", r"\( x + y \)"),
            ("Page 1", r"\[ a^2 + b^2 \]"),
            ("Page 2", r"$$ \sum i $$"),
        ]
        
        output_path = temp_dir / "output.md"
        extractor.save_to_markdown(expressions, output_path, append=False)
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "# Extracted Math Expressions" in content
        assert "## Page 1" in content
        assert "## Page 2" in content
        assert r"\( x + y \)" in content
    
    def test_save_to_markdown_append(self, extractor, temp_dir):
        """Test appending to existing markdown file."""
        output_path = temp_dir / "output.md"
        output_path.write_text("# Existing Content\n")
        
        expressions = [("Page 1", r"\( x \)")]
        extractor.save_to_markdown(expressions, output_path, append=True)
        
        content = output_path.read_text()
        assert "# Existing Content" in content
        assert "---" in content
        assert "# Extracted Math Expressions" in content
    
    def test_save_to_text(self, extractor, temp_dir):
        """Test saving expressions to text file."""
        expressions = [
            ("Page 1", r"\( x + y \)"),
            ("Page 2", r"\[ a^2 \]"),
        ]
        
        output_path = temp_dir / "output.txt"
        extractor.save_to_text(expressions, output_path, append=False)
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "EXTRACTED MATH EXPRESSIONS" in content
        assert "[Page 1]" in content
        assert "[Page 2]" in content
    
    def test_save_empty_expressions(self, extractor, temp_dir):
        """Test saving when no expressions found."""
        expressions = []
        output_path = temp_dir / "output.md"
        
        extractor.save_to_markdown(expressions, output_path, append=False)
        
        content = output_path.read_text()
        assert "no math expressions found" in content.lower()
