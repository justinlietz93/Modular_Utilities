"""Python code generation backend."""
from typing import List, Optional, Any
from ...domain.codegen_types import CodegenBackend, GeneratedFunction


class PythonBackend(CodegenBackend):
    """Backend for generating Python code."""
    
    def __init__(self):
        """Initialize Python backend."""
        self._sympy_available = False
        try:
            import sympy  # noqa: F401
            self._sympy_available = True
        except ImportError:
            pass
    
    def convert_expression_to_code(self, expr, variables: List[str]) -> str:
        """
        Convert SymPy expression to Python code.
        
        Args:
            expr: SymPy expression
            variables: List of variable names
            
        Returns:
            Python code string
        """
        if not self._sympy_available or expr is None:
            return "None"
        
        try:
            from sympy import pycode
            return pycode(expr)
        except Exception:
            return str(expr)
    
    def generate_function_code(self, func: GeneratedFunction) -> str:
        """
        Generate Python function code.
        
        Args:
            func: GeneratedFunction object
            
        Returns:
            Python function code
        """
        return func.to_python_code()
    
    def assemble_module(
        self,
        functions: List[GeneratedFunction],
        module_name: str,
        symbol_registry: Optional[Any] = None
    ) -> str:
        """
        Assemble functions into a Python module.
        
        Args:
            functions: List of generated functions
            module_name: Name of the module
            symbol_registry: Optional symbol registry
            
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
            lines.append(self.generate_function_code(func))
            lines.append("")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_file_extension(self) -> str:
        """Get the file extension for Python."""
        return ".py"
