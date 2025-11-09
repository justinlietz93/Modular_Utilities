"""Tests for function generator."""
import pytest
from math_converter.application.function_generator import FunctionGenerator
from math_converter.application.expression_pipeline import ExpressionPipeline
from math_converter.domain.codegen_types import ExpressionMetadata, NamingStrategy


class TestFunctionGenerator:
    """Test function generator."""
    
    def test_generate_function_sequential_naming(self):
        """Test generating function with sequential naming."""
        generator = FunctionGenerator(NamingStrategy.SEQUENTIAL)
        
        metadata = ExpressionMetadata(original_latex="x + y")
        func = generator.generate_function(
            expr=None,  # Not needed for this test
            variables=["x", "y"],
            metadata=metadata,
            expression_str="x + y"
        )
        
        assert func.name == "expr_0"
        assert func.parameters == ["x", "y"]
        assert func.expression_str == "x + y"
    
    def test_generate_function_hash_naming(self):
        """Test generating function with hash naming."""
        generator = FunctionGenerator(NamingStrategy.HASH)
        
        metadata = ExpressionMetadata(original_latex="a + b")
        func = generator.generate_function(
            expr=None,
            variables=["a", "b"],
            metadata=metadata,
            expression_str="a + b"
        )
        
        assert func.name.startswith("expr_")
        assert len(func.name) > 5  # expr_ + hash
    
    def test_generate_function_custom_name(self):
        """Test generating function with custom name."""
        generator = FunctionGenerator()
        
        metadata = ExpressionMetadata(original_latex="x^2")
        func = generator.generate_function(
            expr=None,
            variables=["x"],
            metadata=metadata,
            expression_str="x**2",
            function_name="square"
        )
        
        assert func.name == "square"
    
    def test_ensure_unique_names(self):
        """Test that function names are unique."""
        generator = FunctionGenerator(NamingStrategy.SEQUENTIAL)
        
        metadata = ExpressionMetadata(original_latex="x")
        
        func1 = generator.generate_function(None, [], metadata, "x")
        func2 = generator.generate_function(None, [], metadata, "x")
        func3 = generator.generate_function(None, [], metadata, "x")
        
        assert func1.name != func2.name
        assert func2.name != func3.name
        assert func1.name != func3.name
    
    def test_generate_docstring_basic(self):
        """Test generating basic docstring."""
        generator = FunctionGenerator()
        
        metadata = ExpressionMetadata(original_latex="x + y")
        docstring = generator._generate_docstring(metadata, ["x", "y"])
        
        assert "x + y" in docstring
        assert "Parameters:" in docstring
        assert "Returns:" in docstring
    
    def test_generate_docstring_with_source_info(self):
        """Test generating docstring with source information."""
        generator = FunctionGenerator()
        
        metadata = ExpressionMetadata(
            original_latex="E = mc^2",
            source_file="physics.pdf",
            page_number=42
        )
        docstring = generator._generate_docstring(metadata, ["m", "c"])
        
        assert "physics.pdf" in docstring
        assert "42" in docstring
    
    def test_generate_docstring_with_simplified(self):
        """Test generating docstring with simplified form."""
        generator = FunctionGenerator()
        
        metadata = ExpressionMetadata(
            original_latex="x + x",
            simplified_latex="2*x"
        )
        docstring = generator._generate_docstring(metadata, ["x"])
        
        assert "x + x" in docstring
        assert "2*x" in docstring
        assert "Simplified:" in docstring
    
    def test_function_to_python_code(self):
        """Test generating Python code from function."""
        generator = FunctionGenerator()
        
        metadata = ExpressionMetadata(original_latex="x * y")
        func = generator.generate_function(
            None,
            ["x", "y"],
            metadata,
            "x * y",
            function_name="multiply"
        )
        
        code = func.to_python_code()
        
        assert "def multiply(x, y):" in code
        assert "return x * y" in code
        assert '"""' in code  # Has docstring
    
    def test_function_with_no_parameters(self):
        """Test generating function with no parameters."""
        generator = FunctionGenerator()
        
        metadata = ExpressionMetadata(original_latex="\\pi")
        func = generator.generate_function(
            None,
            [],
            metadata,
            "pi",
            function_name="get_pi"
        )
        
        code = func.to_python_code()
        
        assert "def get_pi():" in code
        assert "return pi" in code
    
    def test_reset_generator(self):
        """Test resetting generator state."""
        generator = FunctionGenerator(NamingStrategy.SEQUENTIAL)
        
        metadata = ExpressionMetadata(original_latex="x")
        
        # Generate some functions
        func1 = generator.generate_function(None, [], metadata, "x")
        
        # Reset
        generator.reset()
        
        # Generate again - should start from 0
        func2 = generator.generate_function(None, [], metadata, "x")
        
        assert func1.name == "expr_0"
        assert func2.name == "expr_0"  # Counter was reset
    
    def test_integration_with_pipeline(self):
        """Test integration with expression pipeline."""
        pipeline = ExpressionPipeline()
        generator = FunctionGenerator()
        
        expr, metadata = pipeline.process_expression("x^2 + 2*x + 1")
        
        if expr is not None:
            variables = pipeline.extract_variables(expr)
            expr_str = pipeline.expression_to_python(expr)
            
            func = generator.generate_function(
                expr,
                variables,
                metadata,
                expr_str
            )
            
            assert func is not None
            assert "x" in func.parameters
            code = func.to_python_code()
            assert "def " in code
