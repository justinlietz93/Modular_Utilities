"""PDF extraction service for math content."""
import re
from pathlib import Path
from typing import List, Tuple


class PDFExtractor:
    """Extract math content from PDF files."""
    
    def __init__(self):
        """Initialize PDF extractor."""
        self._pymupdf_available = False
        try:
            import fitz  # PyMuPDF  # noqa: F401
            self._pymupdf_available = True
        except ImportError:
            pass
    
    def is_available(self) -> bool:
        """Check if PDF extraction is available."""
        return self._pymupdf_available
    
    def extract_math_from_pdf(self, pdf_path: Path) -> List[Tuple[str, str]]:
        """
        Extract math expressions from a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of tuples (page_number, math_expression)
        """
        if not self._pymupdf_available:
            raise RuntimeError(
                "PDF extraction requires PyMuPDF. Install with: pip install pymupdf"
            )
        
        import fitz
        
        math_expressions = []
        
        try:
            doc = fitz.open(str(pdf_path))
            
            for page_num, page in enumerate(doc, 1):
                text = page.get_text()
                
                # Extract LaTeX-style math expressions
                # Look for common patterns: $...$, $$...$$, \(...\), \[...\]
                expressions = self._extract_math_patterns(text, page_num)
                math_expressions.extend(expressions)
            
            doc.close()
            
        except Exception as e:
            raise RuntimeError(f"Failed to extract from PDF: {e}")
        
        return math_expressions
    
    def _extract_math_patterns(self, text: str, page_num: int) -> List[Tuple[str, str]]:
        """
        Extract math patterns from text.
        
        Args:
            text: Text to search
            page_num: Page number for reference
            
        Returns:
            List of tuples (page_ref, math_expression)
        """
        expressions = []
        
        # Pattern 1: Display math \[ ... \]
        display_bracket = re.finditer(r'\\\[(.*?)\\\]', text, re.DOTALL)
        for match in display_bracket:
            expr = match.group(1).strip()
            if expr:
                expressions.append((f"Page {page_num}", f"\\[{expr}\\]"))
        
        # Pattern 2: Inline math \( ... \)
        inline_paren = re.finditer(r'\\\((.*?)\\\)', text, re.DOTALL)
        for match in inline_paren:
            expr = match.group(1).strip()
            if expr and len(expr) > 1:  # Avoid single chars
                expressions.append((f"Page {page_num}", f"\\({expr}\\)"))
        
        # Pattern 3: Display math $$ ... $$
        display_dollar = re.finditer(r'\$\$(.*?)\$\$', text, re.DOTALL)
        for match in display_dollar:
            expr = match.group(1).strip()
            if expr:
                expressions.append((f"Page {page_num}", f"$${expr}$$"))
        
        # Pattern 4: Inline math $ ... $ (be careful not to match currency)
        # Use negative lookbehind/lookahead to avoid common false positives
        inline_dollar = re.finditer(
            r'(?<![0-9])\$(?!\$)([^\$\n]+?)\$(?![0-9])', 
            text
        )
        for match in inline_dollar:
            expr = match.group(1).strip()
            # Filter: must contain math-like characters
            if expr and (
                any(c in expr for c in r'\^_{}\=+−×÷∫∑∏√') or
                re.search(r'[a-zA-Z]+\([^)]*\)', expr)  # Functions like sin(x)
            ):
                expressions.append((f"Page {page_num}", f"${expr}$"))
        
        return expressions
    
    def save_to_markdown(
        self, 
        expressions: List[Tuple[str, str]], 
        output_path: Path,
        append: bool = False
    ):
        """
        Save extracted math expressions to a markdown file.
        
        Args:
            expressions: List of (page_ref, expression) tuples
            output_path: Output file path
            append: Whether to append to existing file
        """
        mode = 'a' if append else 'w'
        
        with output_path.open(mode, encoding='utf-8') as f:
            if append:
                f.write("\n\n---\n\n")
            
            f.write("# Extracted Math Expressions\n\n")
            
            if not expressions:
                f.write("*No math expressions found.*\n")
                return
            
            # Group by page
            by_page = {}
            for page_ref, expr in expressions:
                if page_ref not in by_page:
                    by_page[page_ref] = []
                by_page[page_ref].append(expr)
            
            # Write grouped by page
            for page_ref in sorted(by_page.keys()):
                f.write(f"## {page_ref}\n\n")
                for expr in by_page[page_ref]:
                    f.write(f"{expr}\n\n")
    
    def save_to_text(
        self, 
        expressions: List[Tuple[str, str]], 
        output_path: Path,
        append: bool = False
    ):
        """
        Save extracted math expressions to a text file.
        
        Args:
            expressions: List of (page_ref, expression) tuples
            output_path: Output file path
            append: Whether to append to existing file
        """
        mode = 'a' if append else 'w'
        
        with output_path.open(mode, encoding='utf-8') as f:
            if append:
                f.write("\n\n" + "="*60 + "\n\n")
            
            f.write("EXTRACTED MATH EXPRESSIONS\n")
            f.write("="*60 + "\n\n")
            
            if not expressions:
                f.write("No math expressions found.\n")
                return
            
            for page_ref, expr in expressions:
                f.write(f"[{page_ref}] {expr}\n")
