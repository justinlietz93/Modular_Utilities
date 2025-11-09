"""Tests for code generation domain types."""
import pytest
from math_converter.domain.codegen_types import (
    NamingStrategy,
    ExpressionMetadata,
    GeneratedFunction,
    SymbolInfo,
    CodegenConfig
)


class TestNamingStrategy:
    """Test naming strategy enum."""
    
    def test_naming_strategies(self):
        """Test all naming strategies exist."""
        assert NamingStrategy.HASH.value == "hash"
        assert NamingStrategy.SEQUENTIAL.value == "sequential"
        assert NamingStrategy.SEMANTIC.value == "semantic"


class TestExpressionMetadata:
    """Test expression metadata."""
    
    def test_create_minimal(self):
        """Test creating minimal metadata."""
        meta = ExpressionMetadata(original_latex="x + y")
        assert meta.original_latex == "x + y"
        assert meta.simplified_latex is None
        assert meta.parse_error is None
    
    def test_create_full(self):
        """Test creating full metadata."""
        meta = ExpressionMetadata(
            original_latex="x^2 + y^2",
            simplified_latex="x**2 + y**2",
            source_file="test.pdf",
            page_number=5,
            expression_id="expr_1"
        )
        assert meta.original_latex == "x^2 + y^2"
        assert meta.simplified_latex == "x**2 + y**2"
        assert meta.source_file == "test.pdf"
        assert meta.page_number == 5
        assert meta.expression_id == "expr_1"
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        meta = ExpressionMetadata(
            original_latex="a + b",
            source_file="test.pdf"
        )
        d = meta.to_dict()
        assert d["original_latex"] == "a + b"
        assert d["source_file"] == "test.pdf"


class TestGeneratedFunction:
    """Test generated function."""
    
    def test_to_python_code_with_params(self):
        """Test generating Python code with parameters."""
        meta = ExpressionMetadata(original_latex="x + y")
        func = GeneratedFunction(
            name="add_xy",
            parameters=["x", "y"],
            expression_str="x + y",
            docstring="Add x and y",
            metadata=meta
        )
        
        code = func.to_python_code()
        assert "def add_xy(x, y):" in code
        assert "return x + y" in code
        assert '"""Add x and y"""' in code
    
    def test_to_python_code_no_params(self):
        """Test generating Python code without parameters."""
        meta = ExpressionMetadata(original_latex="42")
        func = GeneratedFunction(
            name="constant",
            parameters=[],
            expression_str="42",
            docstring="A constant",
            metadata=meta
        )
        
        code = func.to_python_code()
        assert "def constant():" in code
        assert "return 42" in code


class TestSymbolInfo:
    """Test symbol info."""
    
    def test_create_and_convert(self):
        """Test creating symbol info and converting to dict."""
        symbol = SymbolInfo(
            canonical_name="alpha",
            original_token="\\alpha",
            symbol_type="scalar",
            occurrences=[{"file": "test.pdf", "page": 1}],
            notes="Greek letter"
        )
        
        d = symbol.to_dict()
        assert d["canonical_name"] == "alpha"
        assert d["original_token"] == "\\alpha"
        assert d["symbol_type"] == "scalar"
        assert len(d["occurrences"]) == 1


class TestCodegenConfig:
    """Test codegen configuration."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = CodegenConfig()
        assert config.naming_strategy == NamingStrategy.HASH
        assert config.simplify is False
        assert config.target_language == "python"
        assert config.export_symbol_matrix is True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = CodegenConfig(
            naming_strategy=NamingStrategy.SEQUENTIAL,
            simplify=True,
            output_dir="custom_output"
        )
        assert config.naming_strategy == NamingStrategy.SEQUENTIAL
        assert config.simplify is True
        assert config.output_dir == "custom_output"
