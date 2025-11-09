"""Code generation orchestrator."""
from pathlib import Path
from typing import List, Tuple
from ..domain.codegen_types import CodegenConfig
from .expression_pipeline import ExpressionPipeline
from .symbol_registry import SymbolRegistry
from .function_generator import FunctionGenerator
from .backends.registry import get_backend, is_supported


class CodegenOrchestrator:
    """Orchestrate the code generation pipeline."""
    
    def __init__(self, config: CodegenConfig):
        """
        Initialize orchestrator.
        
        Args:
            config: Code generation configuration
        """
        self.config = config
        self.pipeline = ExpressionPipeline(simplify=config.simplify)
        self.symbol_registry = SymbolRegistry(naming_strategy=config.naming_strategy)
        self.function_generator = FunctionGenerator(naming_strategy=config.naming_strategy)
        
        # Get the appropriate backend
        self.backend = get_backend(config.target_language)
        if self.backend is None:
            raise ValueError(f"Unsupported target language: {config.target_language}")
        
        self.successful_count = 0
        self.failed_count = 0
        self.failed_expressions: List[Tuple[str, str]] = []
    
    def is_available(self) -> bool:
        """Check if code generation is available (requires SymPy)."""
        return self.pipeline.is_available()
    
    def process_expressions(
        self,
        expressions: List[Tuple[str, str]],
        output_path: Path,
        module_name: str = "generated_math_lib"
    ) -> bool:
        """
        Process expressions and generate code library.
        
        Args:
            expressions: List of (page_ref, latex_expression) tuples
            output_path: Output file path for generated module
            module_name: Name of the generated module
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            print("Error: Code generation requires SymPy.")
            print("Install with: pip install sympy")
            return False
        
        print(f"Processing {len(expressions)} expression(s)...")
        
        functions = []
        
        for page_ref, latex_expr in expressions:
            # Extract page number if available
            page_num = None
            if "Page " in page_ref:
                try:
                    page_num = int(page_ref.replace("Page ", ""))
                except ValueError:
                    pass
            
            source_info = {
                'page': page_num,
                'id': f"expr_{len(functions)}"
            }
            
            # Process expression
            expr, metadata = self.pipeline.process_expression(latex_expr, source_info)
            
            if expr is None:
                # Failed to parse
                self.failed_count += 1
                self.failed_expressions.append((latex_expr, metadata.parse_error or "Unknown error"))
                continue
            
            # Extract variables
            variables = self.pipeline.extract_variables(expr)
            
            # Register symbols
            for var in variables:
                self.symbol_registry.register_symbol(
                    var,
                    symbol_type="scalar",
                    source_info={'expression_id': source_info['id']}
                )
            
            # Convert to target language code
            expr_str = self.backend.convert_expression_to_code(expr, variables)
            
            # Generate function
            func = self.function_generator.generate_function(
                expr,
                variables,
                metadata,
                expr_str,
                language=self.config.target_language
            )
            
            functions.append(func)
            self.successful_count += 1
        
        if not functions:
            print("Error: No expressions could be successfully parsed.")
            return False
        
        # Assemble and save module using backend
        print(f"Generating {self.config.target_language} module: {output_path}")
        self._save_module(functions, output_path, module_name)
        
        # Report results
        print("\n✓ Code generation complete!")
        print(f"  Language: {self.config.target_language}")
        print(f"  Module: {output_path}")
        print(f"  Functions generated: {len(functions)}")
        print(f"  Successful: {self.successful_count}")
        print(f"  Failed: {self.failed_count}")
        
        if self.config.export_symbol_matrix:
            symbol_path = self._get_symbol_path(output_path)
            print(f"  Symbol matrix: {symbol_path}")
        
        metadata_path = self._get_metadata_path(output_path)
        print(f"  Metadata: {metadata_path}")
        
        # Report failures if any
        if self.failed_expressions:
            failed_path = output_path.parent / "failed_expressions.txt"
            self._save_failed_expressions(failed_path)
            print(f"\n  Failed expressions logged to: {failed_path}")
        
        return True
    
    def _save_module(self, functions: List, output_path: Path, module_name: str):
        """Save module using backend."""
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate module code
        module_code = self.backend.assemble_module(
            functions,
            module_name,
            self.symbol_registry
        )
        
        # Write to file
        output_path.write_text(module_code, encoding='utf-8')
        
        # Export symbol matrix if requested
        if self.config.export_symbol_matrix:
            symbol_path = self._get_symbol_path(output_path)
            self._export_symbol_matrix(symbol_path)
        
        # Export metadata
        metadata_path = self._get_metadata_path(output_path)
        self._export_metadata(functions, metadata_path)
    
    def _get_symbol_path(self, output_path: Path) -> Path:
        """Get symbol matrix file path."""
        return output_path.with_name(f"{output_path.stem}.symbols.json")
    
    def _get_metadata_path(self, output_path: Path) -> Path:
        """Get metadata file path."""
        return output_path.with_name(f"{output_path.stem}.metadata.json")
    
    def _export_symbol_matrix(self, output_path: Path):
        """Export symbol matrix to JSON."""
        import json
        matrix = self.symbol_registry.export_to_dict()
        
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(matrix, f, indent=2)
    
    def _export_metadata(self, functions: List, output_path: Path):
        """Export function metadata to JSON."""
        import json
        metadata = {
            "language": self.config.target_language,
            "function_count": len(functions),
            "functions": [
                {
                    "name": func.name,
                    "parameters": func.parameters,
                    "metadata": func.metadata.to_dict()
                }
                for func in functions
            ]
        }
        
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        # Report failures if any
        if self.failed_expressions:
            failed_path = output_path.parent / "failed_expressions.txt"
            self._save_failed_expressions(failed_path)
            print(f"\n  Failed expressions logged to: {failed_path}")
        
        return True
    
    def _save_failed_expressions(self, output_path: Path):
        """Save failed expressions to a log file."""
        with output_path.open('w', encoding='utf-8') as f:
            f.write("FAILED EXPRESSIONS\n")
            f.write("=" * 60 + "\n\n")
            
            for i, (expr, error) in enumerate(self.failed_expressions, 1):
                f.write(f"Expression {i}:\n")
                f.write(f"  {expr}\n")
                f.write(f"  Error: {error}\n\n")
