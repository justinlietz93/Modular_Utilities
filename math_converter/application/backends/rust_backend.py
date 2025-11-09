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
        
        # Replace pow(x, n) with x.powi(n) for integer powers or x.powf(y) for float powers
        # We need to check if second arg is an integer
        def replace_pow(args):
            if len(args) >= 2:
                # Check if second arg is a simple integer
                if args[1].strip().isdigit():
                    return f'{args[0]}.powi({args[1]})'
                else:
                    return f'{args[0]}.powf({args[1]})'
            return f'{args[0]}.powf(1.0)'  # Fallback
        
        rust_code = self._replace_function_calls(rust_code, 'pow', replace_pow)
        
        # Replace sqrt - use careful matching
        rust_code = self._replace_function_calls(rust_code, 'sqrt', lambda args: f'({args[0]}).sqrt()')
        
        # Replace sin, cos, tan, etc. with method calls
        for func in ['sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh']:
            rust_code = self._replace_function_calls(rust_code, func, lambda args, f=func: f'({args[0]}).{f}()')
        
        # Replace exp(x) with x.exp()
        rust_code = self._replace_function_calls(rust_code, 'exp', lambda args: f'({args[0]}).exp()')
        
        # Replace log(x) with x.ln()
        rust_code = self._replace_function_calls(rust_code, 'log', lambda args: f'({args[0]}).ln()')
        
        # Replace abs(x) with x.abs()
        rust_code = self._replace_function_calls(rust_code, 'abs', lambda args: f'({args[0]}).abs()')
        
        # Replace floor(x) with x.floor()
        rust_code = self._replace_function_calls(rust_code, 'floor', lambda args: f'({args[0]}).floor()')
        
        # Replace ceil(x) with x.ceil()
        rust_code = self._replace_function_calls(rust_code, 'ceil', lambda args: f'({args[0]}).ceil()')
        
        # Note: We don't clean up double parentheses as they may be intentional
        # For example: (x.powi(2) + y.powi(2)).sqrt() is correct
        
        return rust_code
    
    def _replace_function_calls(self, code: str, func_name: str, replacement_func) -> str:
        """
        Replace function calls handling nested parentheses.
        
        Args:
            code: Code string
            func_name: Function name to replace
            replacement_func: Function that takes args list and returns replacement
            
        Returns:
            Modified code string
        """
        result = []
        i = 0
        while i < len(code):
            # Look for function name followed by (
            if code[i:i+len(func_name)] == func_name and i + len(func_name) < len(code) and code[i+len(func_name)] == '(':
                # Found function call, extract arguments
                start = i + len(func_name) + 1
                paren_count = 1
                j = start
                args_start = []
                current_arg_start = start
                
                while j < len(code) and paren_count > 0:
                    if code[j] == '(':
                        paren_count += 1
                    elif code[j] == ')':
                        paren_count -= 1
                        if paren_count == 0:
                            # End of function call
                            break
                    elif code[j] == ',' and paren_count == 1:
                        # Argument separator at top level
                        args_start.append(code[current_arg_start:j].strip())
                        current_arg_start = j + 1
                    j += 1
                
                # Get last argument
                if current_arg_start < j:
                    args_start.append(code[current_arg_start:j].strip())
                
                # Apply replacement
                replacement = replacement_func(args_start)
                result.append(replacement)
                i = j + 1
            else:
                result.append(code[i])
                i += 1
        
        return ''.join(result)
        
        # Replace ceil(x) with x.ceil()
        rust_code = self._replace_function_calls(rust_code, 'ceil', lambda args: f'({args[0]}).ceil()')
        
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
