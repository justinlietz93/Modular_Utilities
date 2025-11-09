"""Domain models for code generation."""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum


class NamingStrategy(Enum):
    """Strategy for generating function and variable names."""
    HASH = "hash"
    SEQUENTIAL = "sequential"
    SEMANTIC = "semantic"


@dataclass
class ExpressionMetadata:
    """Metadata about a mathematical expression."""
    original_latex: str
    simplified_latex: Optional[str] = None
    source_file: Optional[str] = None
    page_number: Optional[int] = None
    expression_id: Optional[str] = None
    parse_error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_latex": self.original_latex,
            "simplified_latex": self.simplified_latex,
            "source_file": self.source_file,
            "page_number": self.page_number,
            "expression_id": self.expression_id,
            "parse_error": self.parse_error,
        }


@dataclass
class GeneratedFunction:
    """Represents a generated function."""
    name: str
    parameters: List[str]
    expression_str: str
    docstring: str
    metadata: ExpressionMetadata
    
    def to_python_code(self) -> str:
        """Generate Python function code."""
        params_str = ", ".join(self.parameters) if self.parameters else ""
        
        lines = [
            f"def {self.name}({params_str}):",
            f'    """{self.docstring}"""',
        ]
        
        if not self.parameters:
            lines.append(f"    return {self.expression_str}")
        else:
            lines.append(f"    return {self.expression_str}")
        
        return "\n".join(lines)


@dataclass
class SymbolInfo:
    """Information about a mathematical symbol."""
    canonical_name: str
    original_token: str
    symbol_type: str  # "scalar", "indexed", "function", "constant"
    occurrences: List[Dict[str, Any]] = field(default_factory=list)
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "canonical_name": self.canonical_name,
            "original_token": self.original_token,
            "symbol_type": self.symbol_type,
            "occurrences": self.occurrences,
            "notes": self.notes,
        }


@dataclass
class CodegenConfig:
    """Configuration for code generation."""
    naming_strategy: NamingStrategy = NamingStrategy.HASH
    simplify: bool = False
    target_language: str = "python"
    docstring_style: str = "short"  # short, full, none
    export_symbol_matrix: bool = True
    output_dir: str = "generated"
