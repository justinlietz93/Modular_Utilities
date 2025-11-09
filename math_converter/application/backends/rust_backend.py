"""Rust code generation backend."""
import re
from typing import List, Optional, Any
from ...domain.codegen_types import CodegenBackend, GeneratedFunction


class RustBackend(CodegenBackend):
    """Backend for generating Rust code."""
    
    def __init__(self):
        """Initialize Rust backend."""
        self._sympy_available = False
        try:
            import sympy  # noqa: F401
            self._sympy_available = True
        except ImportError:
            pass
    
    def convert_expression_to_code(self, expr, variables: List[str]) -> str:
        """
        Convert SymPy expression to Rust code.
        
        Args:
            expr: SymPy expression
            variables: List of variable names
            
        Returns:
            Rust code string
        """
        if not self._sympy_available or expr is None:
            return "0.0"
        
        try:
            # Get C code representation which is close to Rust
            from sympy import ccode
            c_code = ccode(expr)
            
            # Convert C patterns to Rust patterns
            rust_code = self._convert_c_to_rust(c_code)
            
            return rust_code
        except Exception:
            # Fallback to string representation
            return str(expr)
    
    def _convert_c_to_rust(self, c_code: str) -> str:
        """
        Convert C code patterns to Rust.
        
        Args:
            c_code: C code string
            
        Returns:
            Rust code string
        """
        rust_code = c_code
        
        # Replace pow(x, 2) with x.powi(2) for integer powers
        rust_code = re.sub(r'pow\(([^,]+),\s*(\d+)\)', r'\1.powi(\2)', rust_code)
        
        # Replace pow(x, y) with x.powf(y) for float powers
        rust_code = re.sub(r'pow\(([^,]+),\s*([^)]+)\)', r'\1.powf(\2)', rust_code)
        
        # Replace sqrt(x) with x.sqrt()
        rust_code = re.sub(r'sqrt\(([^)]+)\)', r'(\1).sqrt()', rust_code)
        
        # Replace sin, cos, tan, etc. with method calls
        for func in ['sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh']:
            rust_code = re.sub(rf'{func}\(([^)]+)\)', rf'(\1).{func}()', rust_code)
        
        # Replace exp(x) with x.exp()
        rust_code = re.sub(r'exp\(([^)]+)\)', r'(\1).exp()', rust_code)
        
        # Replace log(x) with x.ln()
        rust_code = re.sub(r'log\(([^)]+)\)', r'(\1).ln()', rust_code)
        
        # Replace abs(x) with x.abs()
        rust_code = re.sub(r'abs\(([^)]+)\)', r'(\1).abs()', rust_code)
        
        # Replace floor(x) with x.floor()
        rust_code = re.sub(r'floor\(([^)]+)\)', r'(\1).floor()', rust_code)
        
        # Replace ceil(x) with x.ceil()
        rust_code = re.sub(r'ceil\(([^)]+)\)', r'(\1).ceil()', rust_code)
        
        # Clean up any double parentheses
        rust_code = rust_code.replace('((', '(').replace('))', ')')
        
        return rust_code
    
    def generate_function_code(self, func: GeneratedFunction) -> str:
        """
        Generate Rust function code.
        
        Args:
            func: GeneratedFunction object
            
        Returns:
            Rust function code
        """
        return func.to_rust_code()
    
    def assemble_module(
        self,
        functions: List[GeneratedFunction],
        module_name: str,
        symbol_registry: Optional[Any] = None
    ) -> str:
        """
        Assemble functions into a Rust module.
        
        Args:
            functions: List of generated functions
            module_name: Name of the module
            symbol_registry: Optional symbol registry
            
        Returns:
            Complete Rust module code
        """
        lines = []
        
        # Module header comment
        lines.append("//! Generated mathematical function library")
        lines.append(f"//! Module: {module_name}")
        lines.append("//!")
        lines.append("//! This module was automatically generated from LaTeX expressions.")
        lines.append(f"//! Contains {len(functions)} function(s).")
        lines.append("")
        
        # Add documentation about usage
        lines.append("//! ## Usage")
        lines.append("//!")
        lines.append("//! ```rust")
        if functions:
            example_func = functions[0]
            if example_func.parameters:
                params_example = ", ".join(["1.0"] * len(example_func.parameters))
                lines.append(f"//! let result = {example_func.name}({params_example});")
            else:
                lines.append(f"//! let result = {example_func.name}();")
        lines.append("//! ```")
        lines.append("")
        
        # Add any necessary imports
        lines.append("// Note: This module uses f64 arithmetic")
        lines.append("// For ndarray support, add ndarray dependency to your Cargo.toml")
        lines.append("")
        
        # Functions
        for i, func in enumerate(functions):
            lines.append(self.generate_function_code(func))
            if i < len(functions) - 1:
                lines.append("")
        
        return "\n".join(lines)
    
    def get_file_extension(self) -> str:
        """Get the file extension for Rust."""
        return ".rs"
