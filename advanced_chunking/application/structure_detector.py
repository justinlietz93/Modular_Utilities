"""Structure detection for code blocks and mathematical expressions."""

import re
from typing import Tuple


class StructureDetector:
    """Detects and analyzes structural elements in text like code and math."""

    # Code patterns for various languages
    CODE_PATTERNS = {
        "function_def": [
            r"def\s+\w+\s*\([^)]*\)\s*:",  # Python
            r"function\s+\w+\s*\([^)]*\)\s*\{",  # JavaScript
            r"(public|private|protected)?\s*(static\s+)?[\w<>]+\s+\w+\s*\([^)]*\)\s*\{",  # Java/C#
            r"fn\s+\w+\s*\([^)]*\)\s*->",  # Rust
            r"func\s+\w+\s*\([^)]*\)",  # Go
        ],
        "class_def": [
            r"class\s+\w+(\([^)]*\))?\s*:",  # Python
            r"class\s+\w+(\s+extends\s+\w+)?(\s+implements\s+[\w,\s]+)?\s*\{",  # Java/JS
            r"struct\s+\w+\s*\{",  # C/Rust
        ],
        "loop": [
            r"for\s*\([^)]*\)\s*\{",  # C-style
            r"for\s+\w+\s+in\s+",  # Python/Ruby
            r"while\s*\([^)]*\)\s*\{",  # C-style
            r"while\s+[^:]+:",  # Python
        ],
        "conditional": [
            r"if\s*\([^)]*\)\s*\{",  # C-style
            r"if\s+[^:]+:",  # Python
        ],
    }

    # Math patterns
    MATH_PATTERNS = {
        "latex_inline": r"\$[^\$]+\$",
        "latex_display": r"\$\$[^\$]+\$\$",
        "latex_env": r"\\begin\{(equation|align|array|matrix)[*]?\}.*?\\end\{\1[*]?\}",
        "equation": r"[a-zA-Z0-9_]+\s*=\s*[^=\n]+",  # Simple equations
        "summation": r"∑|\\sum",
        "integral": r"∫|\\int",
        "fraction": r"\\frac\{[^}]+\}\{[^}]+\}",
        "greek": r"[α-ωΑ-Ω]|\\(alpha|beta|gamma|delta|epsilon|theta|lambda|mu|pi|sigma|omega)",
    }

    def detect_code_blocks(self, text: str) -> list[Tuple[int, int]]:
        """Detect code blocks in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of tuples (start_pos, end_pos) for each code block
        """
        code_blocks = []

        # Detect fenced code blocks (markdown style)
        fenced_pattern = r"```[\s\S]*?```|~~~[\s\S]*?~~~"
        for match in re.finditer(fenced_pattern, text):
            code_blocks.append((match.start(), match.end()))

        # Detect indented code blocks (4+ spaces at line start)
        lines = text.split("\n")
        in_code_block = False
        block_start = 0

        for i, line in enumerate(lines):
            is_code_line = len(line) > 0 and (
                line.startswith("    ") or line.startswith("\t")
            )

            if is_code_line and not in_code_block:
                in_code_block = True
                block_start = sum(len(line) + 1 for line in lines[:i])
            elif not is_code_line and in_code_block:
                in_code_block = False
                block_end = sum(len(line) + 1 for line in lines[:i])
                code_blocks.append((block_start, block_end))

        if in_code_block:
            code_blocks.append((block_start, len(text)))

        return code_blocks

    def detect_mathematical_expressions(self, text: str) -> list[Tuple[int, int]]:
        """Detect mathematical expressions in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of tuples (start_pos, end_pos) for each math expression
        """
        math_regions = []

        for pattern_name, pattern in self.MATH_PATTERNS.items():
            for match in re.finditer(pattern, text, re.DOTALL):
                math_regions.append((match.start(), match.end()))

        # Merge overlapping regions
        if math_regions:
            math_regions.sort()
            merged = [math_regions[0]]

            for start, end in math_regions[1:]:
                last_start, last_end = merged[-1]
                if start <= last_end:
                    # Overlapping or adjacent - merge
                    merged[-1] = (last_start, max(end, last_end))
                else:
                    merged.append((start, end))

            return merged

        return []

    def has_code_structure(self, text: str) -> bool:
        """Check if text contains code structures.
        
        Args:
            text: Text to check
            
        Returns:
            True if code structures are detected
        """
        # Check for code blocks
        if self.detect_code_blocks(text):
            return True

        # Check for common code patterns
        for pattern_type, patterns in self.CODE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return True

        return False

    def has_mathematical_content(self, text: str) -> bool:
        """Check if text contains mathematical expressions.
        
        Args:
            text: Text to check
            
        Returns:
            True if math expressions are detected
        """
        return len(self.detect_mathematical_expressions(text)) > 0

    def find_safe_break_points(
        self, text: str, prefer_positions: list[int]
    ) -> list[int]:
        """Find safe positions to break text that don't split structures.
        
        Args:
            text: Text to analyze
            prefer_positions: Preferred break positions
            
        Returns:
            Adjusted break positions that preserve structures
        """
        code_blocks = self.detect_code_blocks(text)
        math_regions = self.detect_mathematical_expressions(text)

        protected_regions = code_blocks + math_regions
        protected_regions.sort()

        safe_positions = []

        for pos in prefer_positions:
            # Check if position is inside a protected region
            for start, end in protected_regions:
                if start < pos < end:
                    # Move to end of protected region
                    pos = end
                    break

            safe_positions.append(pos)

        return safe_positions

    def extract_structure_info(self, text: str) -> dict:
        """Extract comprehensive structure information from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with structure information
        """
        code_blocks = self.detect_code_blocks(text)
        math_regions = self.detect_mathematical_expressions(text)

        return {
            "has_code": len(code_blocks) > 0,
            "code_blocks": code_blocks,
            "code_block_count": len(code_blocks),
            "has_math": len(math_regions) > 0,
            "math_regions": math_regions,
            "math_region_count": len(math_regions),
            "total_protected_chars": sum(
                end - start
                for start, end in code_blocks + math_regions
            ),
        }
