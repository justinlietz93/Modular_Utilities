"""Domain models for code generation."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum


class NamingStrategy(Enum):
    """Strategy for generating function and variable names."""
    HASH = "hash"
    SEQUENTIAL = "sequential"
    SEMANTIC = "semantic"


class TargetLanguage(Enum):
    """Supported target languages for code generation."""
    PYTHON = "python"
    RUST = "rust"


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
    """Represents a generated function (language-agnostic)."""
    name: str
    parameters: List[str]
    expression_str: str
    docstring: str
    metadata: ExpressionMetadata
    language: str = "python"  # Target language
    
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
    
    def to_rust_code(self) -> str:
        """Generate Rust function code."""
        # Convert docstring to Rust doc comments
        doc_lines = self.docstring.split('\n')
        rust_docs = []
        for line in doc_lines:
            rust_docs.append(f"/// {line.strip()}")
        
        # Build parameter list with types
        if self.parameters:
            params_str = ", ".join([f"{p}: f64" for p in self.parameters])
        else:
            params_str = ""
        
        lines = rust_docs + [
            f"pub fn {self.name}({params_str}) -> f64 {{",
            f"    {self.expression_str}",
            "}"
        ]
        
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


class CodegenBackend(ABC):
    """Abstract base class for code generation backends."""
    
    @abstractmethod
    def convert_expression_to_code(self, expr, variables: List[str]) -> str:
        """
        Convert a SymPy expression to target language code.
        
        Args:
            expr: SymPy expression
            variables: List of variable names
            
        Returns:
            Code string in target language
        """
        pass
    
    @abstractmethod
    def generate_function_code(self, func: GeneratedFunction) -> str:
        """
        Generate function code in target language.
        
        Args:
            func: GeneratedFunction object
            
        Returns:
            Function code string
        """
        pass
    
    @abstractmethod
    def assemble_module(
        self,
        functions: List[GeneratedFunction],
        module_name: str,
        symbol_registry: Optional[Any] = None
    ) -> str:
        """
        Assemble functions into a complete module.
        
        Args:
            functions: List of generated functions
            module_name: Name of the module
            symbol_registry: Optional symbol registry
            
        Returns:
            Complete module code
        """
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """Get the file extension for this language."""
        pass
