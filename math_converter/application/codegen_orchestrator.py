"""Code generation orchestrator."""
from pathlib import Path
from typing import List, Optional, Tuple
from ..domain.codegen_types import CodegenConfig, GeneratedFunction, ExpressionMetadata
from .expression_pipeline import ExpressionPipeline
from .symbol_registry import SymbolRegistry
from .function_generator import FunctionGenerator
from .library_assembler import LibraryAssembler


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
        self.assembler = LibraryAssembler()
        
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
            
            # Convert to Python code
            expr_str = self.pipeline.expression_to_python(expr)
            
            # Generate function
            func = self.function_generator.generate_function(
                expr,
                variables,
                metadata,
                expr_str
            )
            
            functions.append(func)
            self.successful_count += 1
        
        if not functions:
            print("Error: No expressions could be successfully parsed.")
            return False
        
        # Assemble and save module
        print(f"Generating module: {output_path}")
        self.assembler.save_module(
            functions,
            output_path,
            module_name=module_name,
            export_symbol_matrix=self.config.export_symbol_matrix,
            symbol_registry=self.symbol_registry
        )
        
        # Report results
        print(f"\n✓ Code generation complete!")
        print(f"  Module: {output_path}")
        print(f"  Functions generated: {len(functions)}")
        print(f"  Successful: {self.successful_count}")
        print(f"  Failed: {self.failed_count}")
        
        if self.config.export_symbol_matrix:
            symbol_path = output_path.with_suffix('.symbols.json')
            print(f"  Symbol matrix: {symbol_path}")
        
        metadata_path = output_path.with_suffix('.metadata.json')
        print(f"  Metadata: {metadata_path}")
        
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
