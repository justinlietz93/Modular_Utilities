"""Library assembler for generating complete module files."""
import json
from pathlib import Path
from typing import List, Dict
from ..domain.codegen_types import GeneratedFunction
from .symbol_registry import SymbolRegistry


class LibraryAssembler:
    """Assemble generated functions into a complete module."""
    
    def __init__(self):
        """Initialize library assembler."""
        pass
    
    def assemble_module(
        self,
        functions: List[GeneratedFunction],
        module_name: str = "generated_math_lib",
        export_symbol_matrix: bool = True,
        symbol_registry: SymbolRegistry = None
    ) -> str:
        """
        Assemble functions into a Python module.
        
        Args:
            functions: List of generated functions
            module_name: Name of the module
            export_symbol_matrix: Whether to export symbol registry
            symbol_registry: Optional symbol registry to export
            
        Returns:
            Complete Python module code
        """
        lines = []
        
        # Module docstring
        lines.append('"""')
        lines.append(f"Generated mathematical function library: {module_name}")
        lines.append("")
        lines.append("This module was automatically generated from LaTeX expressions.")
        lines.append(f"Contains {len(functions)} function(s).")
        lines.append('"""')
        lines.append("")
        
        # Imports
        lines.append("# Standard library imports")
        lines.append("from math import *  # noqa: F403,F401")
        lines.append("")
        
        # __all__ list
        function_names = [f.name for f in functions]
        lines.append("# Public API")
        lines.append("__all__ = [")
        for name in function_names:
            lines.append(f'    "{name}",')
        lines.append("]")
        lines.append("")
        lines.append("")
        
        # Functions
        lines.append("# Generated functions")
        lines.append("")
        for func in functions:
            lines.append(func.to_python_code())
            lines.append("")
            lines.append("")
        
        return "\n".join(lines)
    
    def save_module(
        self,
        functions: List[GeneratedFunction],
        output_path: Path,
        module_name: str = "generated_math_lib",
        export_symbol_matrix: bool = True,
        symbol_registry: SymbolRegistry = None
    ):
        """
        Save assembled module to file.
        
        Args:
            functions: List of generated functions
            output_path: Output file path
            module_name: Name of the module
            export_symbol_matrix: Whether to export symbol registry
            symbol_registry: Optional symbol registry to export
        """
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate module code
        module_code = self.assemble_module(
            functions,
            module_name,
            export_symbol_matrix,
            symbol_registry
        )
        
        # Write to file
        output_path.write_text(module_code, encoding='utf-8')
        
        # Export symbol matrix if requested
        if export_symbol_matrix and symbol_registry:
            matrix_path = output_path.with_suffix('.symbols.json')
            self._export_symbol_matrix(symbol_registry, matrix_path)
        
        # Export metadata
        metadata_path = output_path.with_suffix('.metadata.json')
        self._export_metadata(functions, metadata_path)
    
    def _export_symbol_matrix(
        self,
        symbol_registry: SymbolRegistry,
        output_path: Path
    ):
        """
        Export symbol matrix to JSON.
        
        Args:
            symbol_registry: Symbol registry to export
            output_path: Output file path
        """
        matrix = symbol_registry.export_to_dict()
        
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(matrix, f, indent=2)
    
    def _export_metadata(
        self,
        functions: List[GeneratedFunction],
        output_path: Path
    ):
        """
        Export function metadata to JSON.
        
        Args:
            functions: List of generated functions
            output_path: Output file path
        """
        metadata = {
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
