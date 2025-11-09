"""Tests for symbol registry."""
import pytest
from math_converter.application.symbol_registry import SymbolRegistry
from math_converter.domain.codegen_types import NamingStrategy


class TestSymbolRegistry:
    """Test symbol registry."""
    
    def test_register_simple_symbol(self):
        """Test registering a simple symbol."""
        registry = SymbolRegistry(NamingStrategy.SEQUENTIAL)
        
        name = registry.register_symbol("x", "scalar")
        assert name == "x"
        
        # Check it's tracked
        symbol = registry.get_symbol("x")
        assert symbol is not None
        assert symbol.canonical_name == "x"
        assert symbol.original_token == "x"
    
    def test_register_duplicate_symbol(self):
        """Test registering duplicate symbol returns same name."""
        registry = SymbolRegistry(NamingStrategy.SEQUENTIAL)
        
        name1 = registry.register_symbol("alpha", "scalar")
        name2 = registry.register_symbol("alpha", "scalar")
        
        assert name1 == name2
    
    def test_sequential_naming_with_collision(self):
        """Test sequential naming strategy with name collisions."""
        registry = SymbolRegistry(NamingStrategy.SEQUENTIAL)
        
        # Register same base name multiple times
        name1 = registry.register_symbol("x", "scalar")
        name2 = registry.register_symbol("x1", "scalar")  # Different token
        
        assert name1 == "x"
        assert name2 == "x1"
        
        # Now force a collision by pre-registering "y"
        registry._used_names.add("y")
        name3 = registry.register_symbol("y", "scalar")
        
        # Should get y_1 because y is already used
        assert name3 == "y_1"
    
    def test_hash_naming_strategy(self):
        """Test hash-based naming strategy."""
        registry = SymbolRegistry(NamingStrategy.HASH)
        
        name = registry.register_symbol("alpha", "scalar")
        
        # Should include base name and hash
        assert name.startswith("alpha_")
        assert len(name) > 6  # alpha + _ + hash
    
    def test_clean_latex_token(self):
        """Test cleaning LaTeX tokens."""
        registry = SymbolRegistry(NamingStrategy.SEQUENTIAL)
        
        # Test LaTeX command
        name = registry.register_symbol("\\alpha", "scalar")
        assert "\\" not in name
        assert name == "alpha"
    
    def test_avoid_python_keywords(self):
        """Test avoiding Python keywords."""
        registry = SymbolRegistry(NamingStrategy.SEQUENTIAL)
        
        # Try to register a Python keyword
        name = registry.register_symbol("lambda", "scalar")
        
        # Should have been modified to avoid keyword
        assert name == "lambda_"
    
    def test_handle_numeric_start(self):
        """Test handling tokens that start with numbers."""
        registry = SymbolRegistry(NamingStrategy.SEQUENTIAL)
        
        name = registry.register_symbol("1x", "scalar")
        
        # Should be prefixed to make valid identifier
        assert name.startswith("var_")
    
    def test_export_to_dict(self):
        """Test exporting registry to dictionary."""
        registry = SymbolRegistry(NamingStrategy.SEQUENTIAL)
        
        registry.register_symbol("x", "scalar")
        registry.register_symbol("y", "scalar")
        
        exported = registry.export_to_dict()
        
        assert "x" in exported
        assert "y" in exported
        assert exported["x"]["canonical_name"] == "x"
    
    def test_clear_registry(self):
        """Test clearing the registry."""
        registry = SymbolRegistry(NamingStrategy.SEQUENTIAL)
        
        registry.register_symbol("x", "scalar")
        registry.register_symbol("y", "scalar")
        
        assert len(registry.get_all_symbols()) == 2
        
        registry.clear()
        
        assert len(registry.get_all_symbols()) == 0
    
    def test_register_with_source_info(self):
        """Test registering symbol with source information."""
        registry = SymbolRegistry(NamingStrategy.SEQUENTIAL)
        
        source_info = {"file": "test.pdf", "page": 5}
        name = registry.register_symbol("theta", "scalar", source_info)
        
        symbol = registry.get_symbol("theta")
        assert len(symbol.occurrences) == 1
        assert symbol.occurrences[0]["file"] == "test.pdf"
    
    def test_multiple_occurrences(self):
        """Test tracking multiple occurrences of same symbol."""
        registry = SymbolRegistry(NamingStrategy.SEQUENTIAL)
        
        registry.register_symbol("x", "scalar", {"page": 1})
        registry.register_symbol("x", "scalar", {"page": 2})
        
        symbol = registry.get_symbol("x")
        assert len(symbol.occurrences) == 2
