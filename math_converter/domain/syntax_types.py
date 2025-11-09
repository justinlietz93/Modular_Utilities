"""Domain models for math syntax types."""
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional


class SyntaxType(Enum):
    """Supported math syntax types."""
    LATEX = "latex"
    MATHJAX = "mathjax"
    ASCII = "ascii"
    UNICODE = "unicode"
    
    @classmethod
    def from_string(cls, value: str) -> "SyntaxType":
        """Convert string to SyntaxType."""
        value_lower = value.lower()
        for syntax_type in cls:
            if syntax_type.value == value_lower:
                return syntax_type
        raise ValueError(f"Unknown syntax type: {value}")
    
    @classmethod
    def all_types(cls) -> List["SyntaxType"]:
        """Get all syntax types."""
        return list(cls)


@dataclass
class ConversionRequest:
    """Request for math syntax conversion."""
    from_syntax: Optional[SyntaxType]
    to_syntax: Optional[SyntaxType]
    input_paths: List[str]
    output_dir: Optional[str]
    in_place: bool
    auto_yes: bool
    auto_no: bool
    
    def needs_from_prompt(self) -> bool:
        """Check if from_syntax needs to be prompted."""
        return self.from_syntax is None
    
    def needs_to_prompt(self) -> bool:
        """Check if to_syntax needs to be prompted."""
        return self.to_syntax is None
