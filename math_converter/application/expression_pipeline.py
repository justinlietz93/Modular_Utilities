"""Pipeline for processing mathematical expressions."""
import re
from typing import Optional, Tuple, List
from ..domain.codegen_types import ExpressionMetadata


class ExpressionPipeline:
    """Pipeline for parsing and processing mathematical expressions."""
    
    def __init__(self, simplify: bool = False):
        """
        Initialize the expression pipeline.
        
        Args:
            simplify: Whether to simplify expressions
        """
        self.simplify = simplify
        self._sympy_available = False
        
        try:
            import sympy  # noqa: F401
            self._sympy_available = True
        except ImportError:
            pass
    
    def is_available(self) -> bool:
        """Check if SymPy is available."""
        return self._sympy_available
    
    def process_expression(
        self,
        latex_expr: str,
        source_info: Optional[dict] = None
    ) -> Tuple[Optional[object], ExpressionMetadata]:
        """
        Process a LaTeX expression into a SymPy expression.
        
        Args:
            latex_expr: LaTeX expression string
            source_info: Optional source information (file, page, etc.)
            
        Returns:
            Tuple of (SymPy expression or None, metadata)
        """
        # Clean the expression
        cleaned = self._sanitize_latex(latex_expr)
        
        # Create metadata
        metadata = ExpressionMetadata(
            original_latex=latex_expr,
            source_file=source_info.get('file') if source_info else None,
            page_number=source_info.get('page') if source_info else None,
            expression_id=source_info.get('id') if source_info else None
        )
        
        if not self._sympy_available:
            metadata.parse_error = "SymPy not available"
            return None, metadata
        
        # Try to parse
        try:
            from sympy.parsing.latex import parse_latex
            import sympy
            
            # parse_latex requires proper LaTeX, so we need to wrap simple expressions
            if not any(cmd in cleaned for cmd in ['\\frac', '\\sqrt', '\\sum', '\\int', '^', '_']):
                # Simple expression - try to parse as-is first
                try:
                    expr = sympy.sympify(cleaned)
                except Exception:
                    expr = parse_latex(cleaned)
            else:
                expr = parse_latex(cleaned)
            
            # Optionally simplify
            if self.simplify and expr is not None:
                expr = sympy.simplify(expr)
                metadata.simplified_latex = sympy.latex(expr)
            
            return expr, metadata
            
        except Exception as e:
            # Try basic repairs
            repaired = self._attempt_repair(cleaned)
            if repaired != cleaned:
                try:
                    from sympy.parsing.latex import parse_latex
                    import sympy
                    
                    expr = parse_latex(repaired)
                    
                    if self.simplify and expr is not None:
                        expr = sympy.simplify(expr)
                        metadata.simplified_latex = sympy.latex(expr)
                    
                    return expr, metadata
                except Exception:
                    pass
            
            metadata.parse_error = str(e)
            return None, metadata
    
    def _sanitize_latex(self, latex: str) -> str:
        """
        Sanitize LaTeX expression.
        
        Args:
            latex: Raw LaTeX string
            
        Returns:
            Sanitized LaTeX
        """
        # Remove common wrapper delimiters
        latex = re.sub(r'^\\\[', '', latex)
        latex = re.sub(r'\\\]$', '', latex)
        latex = re.sub(r'^\\\(', '', latex)
        latex = re.sub(r'\\\)$', '', latex)
        latex = re.sub(r'^\$\$', '', latex)
        latex = re.sub(r'\$\$$', '', latex)
        latex = re.sub(r'^\$', '', latex)
        latex = re.sub(r'\$$', '', latex)
        
        # Remove excess whitespace
        latex = ' '.join(latex.split())
        
        return latex.strip()
    
    def _attempt_repair(self, latex: str) -> str:
        """
        Attempt basic repairs on LaTeX expression.
        
        Args:
            latex: LaTeX string
            
        Returns:
            Repaired LaTeX (may be unchanged)
        """
        # Balance braces
        open_count = latex.count('{')
        close_count = latex.count('}')
        
        if open_count > close_count:
            latex += '}' * (open_count - close_count)
        elif close_count > open_count:
            latex = '{' * (close_count - open_count) + latex
        
        # Replace \cdot with *
        latex = latex.replace(r'\cdot', '*')
        
        # Replace \times with *
        latex = latex.replace(r'\times', '*')
        
        return latex
    
    def extract_variables(self, expr) -> List[str]:
        """
        Extract free variables from a SymPy expression.
        
        Args:
            expr: SymPy expression
            
        Returns:
            List of variable names (as strings)
        """
        if not self._sympy_available or expr is None:
            return []
        
        try:
            # Get free symbols
            free_symbols = expr.free_symbols
            
            # Sort for deterministic ordering
            var_names = sorted([str(sym) for sym in free_symbols])
            
            return var_names
        except Exception:
            return []
    
    def expression_to_python(self, expr) -> str:
        """
        Convert SymPy expression to Python code string.
        
        Args:
            expr: SymPy expression
            
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
