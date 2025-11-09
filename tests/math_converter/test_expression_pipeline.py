"""Tests for expression pipeline."""
import pytest
from math_converter.application.expression_pipeline import ExpressionPipeline


class TestExpressionPipeline:
    """Test expression pipeline."""
    
    def test_is_available(self):
        """Test checking if SymPy is available."""
        pipeline = ExpressionPipeline()
        # SymPy should be installed in test environment
        assert pipeline.is_available() is True
    
    def test_sanitize_latex_removes_delimiters(self):
        """Test sanitizing removes LaTeX delimiters."""
        pipeline = ExpressionPipeline()
        
        # Test various delimiter formats
        assert pipeline._sanitize_latex("\\[x + y\\]") == "x + y"
        assert pipeline._sanitize_latex("\\(x + y\\)") == "x + y"
        assert pipeline._sanitize_latex("$$x + y$$") == "x + y"
        assert pipeline._sanitize_latex("$x + y$") == "x + y"
    
    def test_sanitize_latex_removes_whitespace(self):
        """Test sanitizing removes excess whitespace."""
        pipeline = ExpressionPipeline()
        
        result = pipeline._sanitize_latex("x  +   y")
        assert result == "x + y"
    
    def test_process_simple_expression(self):
        """Test processing a simple expression."""
        pipeline = ExpressionPipeline()
        
        expr, metadata = pipeline.process_expression("x + y")
        
        assert expr is not None
        assert metadata.original_latex == "x + y"
        assert metadata.parse_error is None
    
    def test_process_expression_with_simplify(self):
        """Test processing with simplification."""
        pipeline = ExpressionPipeline(simplify=True)
        
        expr, metadata = pipeline.process_expression("x + x")
        
        assert expr is not None
        assert metadata.simplified_latex is not None
    
    def test_process_invalid_expression(self):
        """Test processing an invalid expression."""
        pipeline = ExpressionPipeline()
        
        expr, metadata = pipeline.process_expression("@#$%invalid")
        
        assert expr is None
        assert metadata.parse_error is not None
    
    def test_extract_variables_simple(self):
        """Test extracting variables from expression."""
        pipeline = ExpressionPipeline()
        
        expr, _ = pipeline.process_expression("x + y")
        variables = pipeline.extract_variables(expr)
        
        assert sorted(variables) == ["x", "y"]
    
    def test_extract_variables_with_constants(self):
        """Test extracting variables excludes numeric constants."""
        pipeline = ExpressionPipeline()
        
        expr, _ = pipeline.process_expression("x + 5")
        variables = pipeline.extract_variables(expr)
        
        assert variables == ["x"]
        assert "5" not in variables
    
    def test_extract_variables_none_expr(self):
        """Test extracting variables from None expression."""
        pipeline = ExpressionPipeline()
        
        variables = pipeline.extract_variables(None)
        assert variables == []
    
    def test_expression_to_python(self):
        """Test converting expression to Python code."""
        pipeline = ExpressionPipeline()
        
        # Use proper LaTeX notation
        expr, _ = pipeline.process_expression("x**2 + y**2")
        python_code = pipeline.expression_to_python(expr)
        
        assert "x" in python_code
        assert "y" in python_code
        # Check it's valid Python (uses ** for power)
        assert "**" in python_code or "pow" in python_code.lower()
    
    def test_expression_to_python_none_expr(self):
        """Test converting None expression to Python."""
        pipeline = ExpressionPipeline()
        
        python_code = pipeline.expression_to_python(None)
        assert python_code == "None"
    
    def test_attempt_repair_balances_braces(self):
        """Test repair attempts to balance braces."""
        pipeline = ExpressionPipeline()
        
        repaired = pipeline._attempt_repair("\\frac{x{y}")
        # Should add closing brace
        assert repaired.count("{") == repaired.count("}")
    
    def test_attempt_repair_replaces_cdot(self):
        """Test repair replaces \\cdot with *."""
        pipeline = ExpressionPipeline()
        
        repaired = pipeline._attempt_repair("x \\cdot y")
        assert "\\cdot" not in repaired
        assert "*" in repaired
    
    def test_process_expression_with_source_info(self):
        """Test processing expression with source information."""
        pipeline = ExpressionPipeline()
        
        source_info = {"file": "test.pdf", "page": 3}
        expr, metadata = pipeline.process_expression("a + b", source_info)
        
        assert metadata.source_file == "test.pdf"
        assert metadata.page_number == 3
    
    def test_process_quadratic_formula(self):
        """Test processing a more complex expression."""
        pipeline = ExpressionPipeline()
        
        latex = "\\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}"
        expr, metadata = pipeline.process_expression(latex)
        
        # May fail to parse, but should not crash
        assert metadata is not None
