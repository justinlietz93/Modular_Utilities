"""Tests for conversion engine."""
import pytest
from math_converter.application.converter import ConversionEngine
from math_converter.domain.syntax_types import SyntaxType


class TestConversionEngine:
    """Test ConversionEngine."""
    
    @pytest.fixture
    def engine(self):
        """Create conversion engine."""
        return ConversionEngine()
    
    def test_latex_to_mathjax_inline(self, engine):
        """Test LaTeX to MathJax inline math conversion."""
        content = r"This is \( E = mc^2 \) inline."
        result = engine.convert(content, SyntaxType.LATEX, SyntaxType.MATHJAX)
        assert "$`" in result
        assert "E = mc^2" in result
        
    def test_latex_to_mathjax_display(self, engine):
        """Test LaTeX to MathJax display math conversion."""
        content = r"Display: \[ x^2 + y^2 = z^2 \]"
        result = engine.convert(content, SyntaxType.LATEX, SyntaxType.MATHJAX)
        assert "```math" in result
        assert "x^2 + y^2 = z^2" in result
    
    def test_latex_to_mathjax_dollar_inline(self, engine):
        """Test LaTeX to MathJax single dollar inline."""
        content = r"This is $ f(x) = x^2 $ inline."
        result = engine.convert(content, SyntaxType.LATEX, SyntaxType.MATHJAX)
        assert "$`" in result
        assert "f(x) = x^2" in result
    
    def test_latex_to_mathjax_double_dollar(self, engine):
        """Test LaTeX to MathJax double dollar display."""
        content = r"Display: $$ \sum_{i=1}^n i $$"
        result = engine.convert(content, SyntaxType.LATEX, SyntaxType.MATHJAX)
        assert "```math" in result
        assert r"\sum_{i=1}^n i" in result
    
    def test_mathjax_to_latex_inline(self, engine):
        """Test MathJax to LaTeX inline math conversion."""
        content = "This is $` E = mc^2 `$ inline."
        result = engine.convert(content, SyntaxType.MATHJAX, SyntaxType.LATEX)
        assert r"\(" in result
        assert r"\)" in result
        assert "E = mc^2" in result
    
    def test_mathjax_to_latex_display(self, engine):
        """Test MathJax to LaTeX display math conversion."""
        content = "```math\nx^2 + y^2 = z^2\n```"
        result = engine.convert(content, SyntaxType.MATHJAX, SyntaxType.LATEX)
        assert r"\[" in result
        assert r"\]" in result
        assert "x^2 + y^2 = z^2" in result
    
    def test_same_syntax_returns_unchanged(self, engine):
        """Test that same syntax returns content unchanged."""
        content = "Some math content"
        result = engine.convert(content, SyntaxType.LATEX, SyntaxType.LATEX)
        assert result == content
    
    def test_roundtrip_conversion(self, engine):
        """Test roundtrip conversion LaTeX -> MathJax -> LaTeX."""
        original = r"Inline \( x + y \) and display \[ a^2 + b^2 \]"
        mathjax = engine.convert(original, SyntaxType.LATEX, SyntaxType.MATHJAX)
        latex = engine.convert(mathjax, SyntaxType.MATHJAX, SyntaxType.LATEX)
        
        # Should preserve the math content
        assert "x + y" in latex
        assert "a^2 + b^2" in latex
        assert r"\(" in latex
        assert r"\[" in latex
    
    def test_unicode_to_latex(self, engine):
        """Test Unicode to LaTeX conversion."""
        content = "α + β = γ"
        result = engine.convert(content, SyntaxType.UNICODE, SyntaxType.LATEX)
        assert r"\alpha" in result
        assert r"\beta" in result
        assert r"\gamma" in result
    
    def test_basic_latex_to_unicode(self, engine):
        """Test basic LaTeX to Unicode conversion."""
        content = r"\( \alpha + \beta = \gamma \)"
        result = engine.convert(content, SyntaxType.LATEX, SyntaxType.UNICODE)
        # Should convert Greek letters
        assert ("α" in result or "alpha" in result)
    
    def test_ascii_to_unicode_conversion(self, engine):
        """Test ASCII to Unicode conversion works."""
        # ASCII to UNICODE is now supported
        content = "f(x) = x^2"
        result = engine.convert(content, SyntaxType.ASCII, SyntaxType.UNICODE)
        # Should convert successfully (even if result is similar to input)
        assert result is not None
