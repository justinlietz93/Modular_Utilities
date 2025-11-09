"""Math syntax conversion engine using SymPy."""
from typing import Dict, Callable
import re

from ..domain.syntax_types import SyntaxType


class ConversionEngine:
    """Engine for converting between different math syntax formats."""
    
    def __init__(self):
        """Initialize the conversion engine."""
        self._converters: Dict[tuple, Callable[[str], str]] = {}
        self._register_converters()
    
    def _register_converters(self):
        """Register all conversion functions."""
        # LaTeX to MathJax (GitHub-friendly)
        self._converters[(SyntaxType.LATEX, SyntaxType.MATHJAX)] = self._latex_to_mathjax
        self._converters[(SyntaxType.MATHJAX, SyntaxType.LATEX)] = self._mathjax_to_latex
        
        # LaTeX to ASCII/Unicode
        self._converters[(SyntaxType.LATEX, SyntaxType.ASCII)] = self._latex_to_ascii
        self._converters[(SyntaxType.LATEX, SyntaxType.UNICODE)] = self._latex_to_unicode
        
        # ASCII/Unicode to LaTeX
        self._converters[(SyntaxType.ASCII, SyntaxType.LATEX)] = self._ascii_to_latex
        self._converters[(SyntaxType.UNICODE, SyntaxType.LATEX)] = self._unicode_to_latex
        
        # ASCII/Unicode cross-conversion
        self._converters[(SyntaxType.ASCII, SyntaxType.UNICODE)] = self._ascii_to_unicode
        self._converters[(SyntaxType.UNICODE, SyntaxType.ASCII)] = self._unicode_to_ascii
        
        # MathJax to ASCII/Unicode
        self._converters[(SyntaxType.MATHJAX, SyntaxType.ASCII)] = self._mathjax_to_ascii
        self._converters[(SyntaxType.MATHJAX, SyntaxType.UNICODE)] = self._mathjax_to_unicode
    
    def convert(self, content: str, from_syntax: SyntaxType, to_syntax: SyntaxType) -> str:
        """
        Convert math syntax from one format to another.
        
        Args:
            content: The content containing math expressions
            from_syntax: Source syntax type
            to_syntax: Target syntax type
            
        Returns:
            Converted content
        """
        if from_syntax == to_syntax:
            return content
        
        converter_key = (from_syntax, to_syntax)
        if converter_key not in self._converters:
            raise ValueError(f"Conversion from {from_syntax.value} to {to_syntax.value} not supported")
        
        return self._converters[converter_key](content)
    
    def _latex_to_mathjax(self, content: str) -> str:
        """Convert LaTeX to GitHub-friendly MathJax (wrapped in $ or $$)."""
        # Find display math first (to avoid conflicts with inline)
        # \[ ... \] -> ```math\n...\n```
        content = re.sub(r'\\\[(.*?)\\\]', r'```math\n\1\n```', content, flags=re.DOTALL)
        # $$ ... $$ -> ```math\n...\n```
        content = re.sub(r'\$\$(.*?)\$\$', r'```math\n\1\n```', content, flags=re.DOTALL)
        
        # Find inline math: \( ... \) -> $`...`$
        content = re.sub(r'\\\((.*?)\\\)', r'$`\1`$', content, flags=re.DOTALL)
        # Single $ ... $ (not already converted) -> $`...`$
        # This regex needs to NOT match $` patterns we just created
        def replace_single_dollar(match):
            inner = match.group(1)
            # Skip if this looks like our output format
            if inner.startswith('`') or inner.endswith('`'):
                return match.group(0)
            return f'$`{inner}`$'
        
        content = re.sub(r'(?<![\$`])\$(?!\$)([^\$]+?)\$(?![`\$])', replace_single_dollar, content)
        
        return content
    
    def _mathjax_to_latex(self, content: str) -> str:
        """Convert GitHub MathJax back to LaTeX."""
        # Convert inline: $`...`$ to \( ... \)
        content = re.sub(r'\$`(.*?)`\$', r'\\(\1\\)', content, flags=re.DOTALL)
        
        # Convert display: ```math\n...\n``` to \[ ... \]
        content = re.sub(r'```math\n(.*?)\n```', r'\\[\1\\]', content, flags=re.DOTALL)
        
        return content
    
    def _latex_to_ascii(self, content: str) -> str:
        """Convert LaTeX to ASCII representation."""
        try:
            from sympy.parsing.latex import parse_latex
            
            def convert_expr(match):
                latex_expr = match.group(1)
                try:
                    expr = parse_latex(latex_expr)
                    return str(expr)
                except Exception:
                    return match.group(0)
            
            # Convert inline and display math
            content = re.sub(r'\\\((.*?)\\\)', convert_expr, content, flags=re.DOTALL)
            content = re.sub(r'\\\[(.*?)\\\]', convert_expr, content, flags=re.DOTALL)
            
            return content
        except ImportError:
            # Fallback: basic conversion without SymPy
            return self._basic_latex_to_ascii(content)
    
    def _latex_to_unicode(self, content: str) -> str:
        """Convert LaTeX to Unicode representation."""
        try:
            from sympy.printing import pretty
            from sympy.parsing.latex import parse_latex
            
            def convert_expr(match):
                latex_expr = match.group(1)
                try:
                    expr = parse_latex(latex_expr)
                    return pretty(expr, use_unicode=True)
                except Exception:
                    return match.group(0)
            
            content = re.sub(r'\\\((.*?)\\\)', convert_expr, content, flags=re.DOTALL)
            content = re.sub(r'\\\[(.*?)\\\]', convert_expr, content, flags=re.DOTALL)
            
            return content
        except ImportError:
            return self._basic_latex_to_unicode(content)
    
    def _ascii_to_latex(self, content: str) -> str:
        """Convert ASCII math to LaTeX."""
        try:
            from sympy import sympify, latex
            
            def convert_expr(match):
                ascii_expr = match.group(0)
                try:
                    expr = sympify(ascii_expr)
                    return f"\\({latex(expr)}\\)"
                except Exception:
                    return match.group(0)
            
            # Simple pattern matching for common math expressions
            content = re.sub(r'[a-zA-Z]+\([^)]+\)', convert_expr, content)
            
            return content
        except ImportError:
            return content
    
    def _unicode_to_latex(self, content: str) -> str:
        """Convert Unicode math to LaTeX."""
        # Basic Unicode to LaTeX mappings
        unicode_map = {
            'α': r'\alpha', 'β': r'\beta', 'γ': r'\gamma', 'δ': r'\delta',
            'ε': r'\epsilon', 'π': r'\pi', 'σ': r'\sigma', 'θ': r'\theta',
            '∑': r'\sum', '∫': r'\int', '∂': r'\partial', '∇': r'\nabla',
            '√': r'\sqrt', '∞': r'\infty', '±': r'\pm', '≤': r'\leq', '≥': r'\geq',
            '≠': r'\neq', '≈': r'\approx', '×': r'\times', '÷': r'\div',
        }
        
        for unicode_char, latex_cmd in unicode_map.items():
            content = content.replace(unicode_char, latex_cmd)
        
        return content
    
    def _mathjax_to_ascii(self, content: str) -> str:
        """Convert MathJax to ASCII."""
        # First convert to LaTeX, then to ASCII
        latex_content = self._mathjax_to_latex(content)
        return self._latex_to_ascii(latex_content)
    
    def _mathjax_to_unicode(self, content: str) -> str:
        """Convert MathJax to Unicode."""
        latex_content = self._mathjax_to_latex(content)
        return self._latex_to_unicode(latex_content)
    
    def _basic_latex_to_ascii(self, content: str) -> str:
        """Basic LaTeX to ASCII without SymPy."""
        # Remove common LaTeX commands
        content = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', content)
        content = re.sub(r'\\sqrt\{([^}]+)\}', r'sqrt(\1)', content)
        content = re.sub(r'\\\((.*?)\\\)', r'\1', content, flags=re.DOTALL)
        content = re.sub(r'\\\[(.*?)\\\]', r'\1', content, flags=re.DOTALL)
        
        # Remove remaining backslashes from commands
        content = re.sub(r'\\([a-zA-Z]+)', r'\1', content)
        
        return content
    
    def _basic_latex_to_unicode(self, content: str) -> str:
        """Basic LaTeX to Unicode without SymPy."""
        # Map common LaTeX commands to Unicode
        latex_to_unicode = {
            r'\\alpha': 'α', r'\\beta': 'β', r'\\gamma': 'γ', r'\\delta': 'δ',
            r'\\epsilon': 'ε', r'\\pi': 'π', r'\\sigma': 'σ', r'\\theta': 'θ',
            r'\\sum': '∑', r'\\int': '∫', r'\\partial': '∂', r'\\nabla': '∇',
            r'\\sqrt': '√', r'\\infty': '∞', r'\\pm': '±', r'\\leq': '≤',
            r'\\geq': '≥', r'\\neq': '≠', r'\\approx': '≈', r'\\times': '×',
            r'\\div': '÷',
        }
        
        for latex_cmd, unicode_char in latex_to_unicode.items():
            content = content.replace(latex_cmd, unicode_char)
        
        # Handle fractions
        content = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', content)
        
        # Remove delimiters
        content = re.sub(r'\\\((.*?)\\\)', r'\1', content, flags=re.DOTALL)
        content = re.sub(r'\\\[(.*?)\\\]', r'\1', content, flags=re.DOTALL)
        
        return content
    
    def _ascii_to_unicode(self, content: str) -> str:
        """Convert ASCII math to Unicode representation."""
        # Convert via LaTeX as intermediate
        latex_content = self._ascii_to_latex(content)
        return self._latex_to_unicode(latex_content)
    
    def _unicode_to_ascii(self, content: str) -> str:
        """Convert Unicode math to ASCII representation."""
        # Convert via LaTeX as intermediate
        latex_content = self._unicode_to_latex(content)
        return self._latex_to_ascii(latex_content)
