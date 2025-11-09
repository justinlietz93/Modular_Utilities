"""Integration tests for code generation."""
import pytest
from pathlib import Path
import tempfile
import shutil
from math_converter.domain.codegen_types import CodegenConfig, NamingStrategy
from math_converter.application.codegen_orchestrator import CodegenOrchestrator


class TestCodegenIntegration:
    """Integration tests for code generation."""
    
    def setup_method(self):
        """Setup temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup temporary directory."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_full_pipeline_simple_expressions(self):
        """Test full pipeline with simple expressions."""
        # Setup
        config = CodegenConfig(
            naming_strategy=NamingStrategy.SEQUENTIAL,
            simplify=False,
            export_symbol_matrix=True
        )
        orchestrator = CodegenOrchestrator(config)
        
        # Sample expressions (as would come from PDF extractor)
        expressions = [
            ("Page 1", "x + y"),
            ("Page 1", "a * b"),
            ("Page 2", "c / d"),
        ]
        
        output_path = self.temp_path / "test_lib.py"
        
        # Execute
        success = orchestrator.process_expressions(
            expressions,
            output_path,
            module_name="test_lib"
        )
        
        # Verify
        assert success is True
        assert output_path.exists()
        
        # Check generated file content
        content = output_path.read_text()
        assert "def expr_0(" in content
        assert "def expr_1(" in content
        assert "def expr_2(" in content
        
        # Check symbol matrix was created
        symbol_path = output_path.with_suffix('.symbols.json')
        assert symbol_path.exists()
        
        # Check metadata was created
        metadata_path = output_path.with_suffix('.metadata.json')
        assert metadata_path.exists()
    
    def test_full_pipeline_with_hash_naming(self):
        """Test full pipeline with hash naming strategy."""
        config = CodegenConfig(
            naming_strategy=NamingStrategy.HASH,
            simplify=False
        )
        orchestrator = CodegenOrchestrator(config)
        
        expressions = [
            ("Page 1", "x + y"),
        ]
        
        output_path = self.temp_path / "hash_lib.py"
        
        success = orchestrator.process_expressions(
            expressions,
            output_path,
            module_name="hash_lib"
        )
        
        assert success is True
        
        # Check content has hash-based names
        content = output_path.read_text()
        assert "def expr_" in content
        # Hash names should be longer
        assert len([line for line in content.split('\n') if 'def expr_' in line]) == 1
    
    def test_pipeline_handles_parse_failures(self):
        """Test pipeline handles expressions that fail to parse."""
        config = CodegenConfig(naming_strategy=NamingStrategy.SEQUENTIAL)
        orchestrator = CodegenOrchestrator(config)
        
        expressions = [
            ("Page 1", "x + y"),  # Valid
            ("Page 1", "@#$%invalid"),  # Invalid
            ("Page 2", "a * b"),  # Valid
        ]
        
        output_path = self.temp_path / "mixed_lib.py"
        
        success = orchestrator.process_expressions(
            expressions,
            output_path,
            module_name="mixed_lib"
        )
        
        # Should succeed overall even with some failures
        assert success is True
        
        # Should have 2 successful, 1 failed
        assert orchestrator.successful_count == 2
        assert orchestrator.failed_count == 1
        
        # Check failed expressions log
        failed_path = output_path.parent / "failed_expressions.txt"
        assert failed_path.exists()
        
        failed_content = failed_path.read_text()
        assert "@#$%invalid" in failed_content
    
    def test_pipeline_with_simplification(self):
        """Test pipeline with expression simplification."""
        config = CodegenConfig(
            naming_strategy=NamingStrategy.SEQUENTIAL,
            simplify=True
        )
        orchestrator = CodegenOrchestrator(config)
        
        expressions = [
            ("Page 1", "x + x"),  # Should simplify to 2*x
        ]
        
        output_path = self.temp_path / "simplified_lib.py"
        
        success = orchestrator.process_expressions(
            expressions,
            output_path,
            module_name="simplified_lib"
        )
        
        assert success is True
        
        # Check metadata has simplified form
        import json
        metadata_path = output_path.with_suffix('.metadata.json')
        with metadata_path.open() as f:
            metadata = json.load(f)
        
        # Should have simplified_latex field
        assert metadata["functions"][0]["metadata"]["simplified_latex"] is not None
    
    def test_generated_code_is_executable(self):
        """Test that generated code is valid Python and executable."""
        config = CodegenConfig(naming_strategy=NamingStrategy.SEQUENTIAL)
        orchestrator = CodegenOrchestrator(config)
        
        expressions = [
            ("Page 1", "x + y"),
            ("Page 1", "a**2 + b**2"),
        ]
        
        output_path = self.temp_path / "executable_lib.py"
        
        success = orchestrator.process_expressions(
            expressions,
            output_path,
            module_name="executable_lib"
        )
        
        assert success is True
        
        # Try to import and execute the generated module
        import sys
        sys.path.insert(0, str(self.temp_path))
        
        try:
            import executable_lib
            
            # Test calling the functions
            result1 = executable_lib.expr_0(2, 3)
            assert result1 == 5  # 2 + 3
            
            result2 = executable_lib.expr_1(3, 4)
            assert result2 == 25  # 3^2 + 4^2
            
        finally:
            # Cleanup
            sys.path.remove(str(self.temp_path))
            if 'executable_lib' in sys.modules:
                del sys.modules['executable_lib']
    
    def test_empty_expressions_list(self):
        """Test handling of empty expressions list."""
        config = CodegenConfig(naming_strategy=NamingStrategy.SEQUENTIAL)
        orchestrator = CodegenOrchestrator(config)
        
        expressions = []
        
        output_path = self.temp_path / "empty_lib.py"
        
        success = orchestrator.process_expressions(
            expressions,
            output_path,
            module_name="empty_lib"
        )
        
        # Should fail gracefully
        assert success is False
        assert not output_path.exists()
    
    def test_all_failed_expressions(self):
        """Test when all expressions fail to parse."""
        config = CodegenConfig(naming_strategy=NamingStrategy.SEQUENTIAL)
        orchestrator = CodegenOrchestrator(config)
        
        expressions = [
            ("Page 1", "@#$invalid1"),
            ("Page 1", "###invalid2"),
        ]
        
        output_path = self.temp_path / "allfailed_lib.py"
        
        success = orchestrator.process_expressions(
            expressions,
            output_path,
            module_name="allfailed_lib"
        )
        
        # Should fail because no valid expressions
        assert success is False
        assert orchestrator.failed_count == 2
