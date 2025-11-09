"""Tests for Rust code generation backend."""
import pytest
from pathlib import Path
import tempfile
import shutil
from math_converter.domain.codegen_types import CodegenConfig, NamingStrategy
from math_converter.application.codegen_orchestrator import CodegenOrchestrator
from math_converter.application.backends.rust_backend import RustBackend


class TestRustBackend:
    """Test Rust code generation backend."""
    
    def setup_method(self):
        """Setup temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.backend = RustBackend()
    
    def teardown_method(self):
        """Cleanup temporary directory."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_backend_initialization(self):
        """Test backend initializes correctly."""
        assert self.backend is not None
        assert self.backend._sympy_available is True
    
    def test_get_file_extension(self):
        """Test file extension for Rust."""
        assert self.backend.get_file_extension() == ".rs"
    
    def test_convert_simple_expression(self):
        """Test converting simple expression to Rust."""
        try:
            from sympy import symbols
            x, y = symbols('x y')
            expr = x + y
            
            rust_code = self.backend.convert_expression_to_code(expr, ['x', 'y'])
            
            assert rust_code is not None
            assert 'x' in rust_code
            assert 'y' in rust_code
            assert '+' in rust_code
        except ImportError:
            pytest.skip("SymPy not available")
    
    def test_convert_power_expression(self):
        """Test converting power expressions to Rust powi."""
        try:
            from sympy import symbols
            x = symbols('x')
            expr = x**2
            
            rust_code = self.backend.convert_expression_to_code(expr, ['x'])
            
            # Should use powi for integer powers
            assert 'powi' in rust_code or 'powf' in rust_code or '**' in str(rust_code)
        except ImportError:
            pytest.skip("SymPy not available")
    
    def test_convert_sqrt_expression(self):
        """Test converting sqrt to Rust method."""
        try:
            from sympy import symbols, sqrt
            x = symbols('x')
            expr = sqrt(x)
            
            rust_code = self.backend.convert_expression_to_code(expr, ['x'])
            
            # Should convert to .sqrt() method
            assert 'sqrt' in rust_code.lower()
        except ImportError:
            pytest.skip("SymPy not available")
    
    def test_convert_trig_functions(self):
        """Test converting trig functions to Rust methods."""
        try:
            from sympy import symbols, sin, cos
            x = symbols('x')
            expr = sin(x) + cos(x)
            
            rust_code = self.backend.convert_expression_to_code(expr, ['x'])
            
            # Should have sin and cos
            assert 'sin' in rust_code.lower()
            assert 'cos' in rust_code.lower()
        except ImportError:
            pytest.skip("SymPy not available")
    
    def test_generate_function_code(self):
        """Test generating complete Rust function."""
        from math_converter.domain.codegen_types import GeneratedFunction, ExpressionMetadata
        
        metadata = ExpressionMetadata(
            original_latex="x^2 + y^2",
            page_number=1
        )
        
        func = GeneratedFunction(
            name="test_func",
            parameters=["x", "y"],
            expression_str="x.powi(2) + y.powi(2)",
            docstring="Test function\nOriginal: x^2 + y^2",
            metadata=metadata,
            language="rust"
        )
        
        rust_code = self.backend.generate_function_code(func)
        
        assert "pub fn test_func" in rust_code
        assert "x: f64" in rust_code
        assert "y: f64" in rust_code
        assert "-> f64" in rust_code
        assert "x.powi(2) + y.powi(2)" in rust_code
        assert "///" in rust_code  # Rust doc comment
    
    def test_assemble_module(self):
        """Test assembling complete Rust module."""
        from math_converter.domain.codegen_types import GeneratedFunction, ExpressionMetadata
        
        metadata1 = ExpressionMetadata(original_latex="x + y")
        func1 = GeneratedFunction(
            name="add",
            parameters=["x", "y"],
            expression_str="x + y",
            docstring="Add two numbers",
            metadata=metadata1,
            language="rust"
        )
        
        metadata2 = ExpressionMetadata(original_latex="a * b")
        func2 = GeneratedFunction(
            name="multiply",
            parameters=["a", "b"],
            expression_str="a * b",
            docstring="Multiply two numbers",
            metadata=metadata2,
            language="rust"
        )
        
        module_code = self.backend.assemble_module([func1, func2], "test_module")
        
        # Check module structure
        assert "//!" in module_code  # Module doc comment
        assert "test_module" in module_code
        assert "pub fn add" in module_code
        assert "pub fn multiply" in module_code
        assert "2 function(s)" in module_code


class TestRustCodegenIntegration:
    """Integration tests for Rust code generation."""
    
    def setup_method(self):
        """Setup temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup temporary directory."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_full_pipeline_rust_simple_expressions(self):
        """Test full pipeline with Rust backend and simple expressions."""
        config = CodegenConfig(
            naming_strategy=NamingStrategy.SEQUENTIAL,
            target_language="rust",
            simplify=False,
            export_symbol_matrix=True
        )
        orchestrator = CodegenOrchestrator(config)
        
        expressions = [
            ("Page 1", "x + y"),
            ("Page 1", "a * b"),
            ("Page 2", "c / d"),
        ]
        
        output_path = self.temp_path / "test_lib.rs"
        
        success = orchestrator.process_expressions(
            expressions,
            output_path,
            module_name="test_lib"
        )
        
        assert success is True
        assert output_path.exists()
        
        # Check generated Rust file content
        content = output_path.read_text()
        assert "pub fn expr_0" in content
        assert "pub fn expr_1" in content
        assert "pub fn expr_2" in content
        assert "-> f64" in content
        assert "//!" in content  # Module doc comments
        
        # Check symbol matrix was created
        symbol_path = self.temp_path / "test_lib.symbols.json"
        assert symbol_path.exists()
        
        # Check metadata was created
        metadata_path = self.temp_path / "test_lib.metadata.json"
        assert metadata_path.exists()
        
        # Verify metadata has language field
        import json
        with metadata_path.open() as f:
            metadata = json.load(f)
        assert metadata["language"] == "rust"
    
    def test_rust_with_power_expressions(self):
        """Test Rust generation with power expressions."""
        config = CodegenConfig(
            naming_strategy=NamingStrategy.SEQUENTIAL,
            target_language="rust"
        )
        orchestrator = CodegenOrchestrator(config)
        
        expressions = [
            ("Page 1", r"x^{2}"),
            ("Page 1", r"a^{2} + b^{2}"),
        ]
        
        output_path = self.temp_path / "powers_lib.rs"
        
        success = orchestrator.process_expressions(
            expressions,
            output_path,
            module_name="powers_lib"
        )
        
        assert success is True
        
        content = output_path.read_text()
        # Should have power operations (either powi or powf)
        assert "pow" in content.lower()
    
    def test_rust_with_trig_functions(self):
        """Test Rust generation with trigonometric functions."""
        config = CodegenConfig(
            naming_strategy=NamingStrategy.SEQUENTIAL,
            target_language="rust"
        )
        orchestrator = CodegenOrchestrator(config)
        
        expressions = [
            ("Page 1", r"\sin{x}"),
            ("Page 1", r"\cos{y}"),
        ]
        
        output_path = self.temp_path / "trig_lib.rs"
        
        success = orchestrator.process_expressions(
            expressions,
            output_path,
            module_name="trig_lib"
        )
        
        assert success is True
        
        content = output_path.read_text()
        # Should have trig functions
        assert "sin" in content.lower()
        assert "cos" in content.lower()
    
    def test_rust_with_hash_naming(self):
        """Test Rust generation with hash naming strategy."""
        config = CodegenConfig(
            naming_strategy=NamingStrategy.HASH,
            target_language="rust"
        )
        orchestrator = CodegenOrchestrator(config)
        
        expressions = [
            ("Page 1", "x + y"),
        ]
        
        output_path = self.temp_path / "hash_lib.rs"
        
        success = orchestrator.process_expressions(
            expressions,
            output_path,
            module_name="hash_lib"
        )
        
        assert success is True
        
        content = output_path.read_text()
        assert "pub fn expr_" in content
    
    def test_rust_handles_parse_failures(self):
        """Test Rust generation handles parse failures gracefully."""
        config = CodegenConfig(
            naming_strategy=NamingStrategy.SEQUENTIAL,
            target_language="rust"
        )
        orchestrator = CodegenOrchestrator(config)
        
        expressions = [
            ("Page 1", "x + y"),  # Valid
            ("Page 1", "@#$%invalid"),  # Invalid
            ("Page 2", "a * b"),  # Valid
        ]
        
        output_path = self.temp_path / "mixed_lib.rs"
        
        success = orchestrator.process_expressions(
            expressions,
            output_path,
            module_name="mixed_lib"
        )
        
        assert success is True
        assert orchestrator.successful_count == 2
        assert orchestrator.failed_count == 1
        
        # Check failed expressions log
        failed_path = output_path.parent / "failed_expressions.txt"
        assert failed_path.exists()
    
    def test_rust_module_structure(self):
        """Test that generated Rust module has proper structure."""
        config = CodegenConfig(
            naming_strategy=NamingStrategy.SEQUENTIAL,
            target_language="rust"
        )
        orchestrator = CodegenOrchestrator(config)
        
        expressions = [
            ("Page 1", "x + y"),
        ]
        
        output_path = self.temp_path / "structure_lib.rs"
        
        success = orchestrator.process_expressions(
            expressions,
            output_path,
            module_name="structure_lib"
        )
        
        assert success is True
        
        content = output_path.read_text()
        
        # Check module structure
        assert "//! Generated mathematical function library" in content
        assert "//! Module: structure_lib" in content
        assert "//! ## Usage" in content
        assert "pub fn expr_0" in content
        assert "-> f64" in content
        
        # Check function has proper signature
        lines = content.split('\n')
        func_lines = [l for l in lines if 'pub fn expr_0' in l]
        assert len(func_lines) > 0
        assert '-> f64' in func_lines[0]
    
    def test_rust_with_no_parameters(self):
        """Test Rust generation with constant expressions (no parameters)."""
        config = CodegenConfig(
            naming_strategy=NamingStrategy.SEQUENTIAL,
            target_language="rust"
        )
        orchestrator = CodegenOrchestrator(config)
        
        expressions = [
            ("Page 1", "42"),
            ("Page 1", "3.14159"),
        ]
        
        output_path = self.temp_path / "constants_lib.rs"
        
        success = orchestrator.process_expressions(
            expressions,
            output_path,
            module_name="constants_lib"
        )
        
        assert success is True
        
        content = output_path.read_text()
        # Functions with no parameters
        assert "pub fn expr_0() -> f64" in content
        assert "pub fn expr_1() -> f64" in content
