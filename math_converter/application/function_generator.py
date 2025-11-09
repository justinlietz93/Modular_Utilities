"""Function code generator."""
import hashlib
from typing import List, Optional
from ..domain.codegen_types import GeneratedFunction, ExpressionMetadata, NamingStrategy


class FunctionGenerator:
    """Generate function code from expressions."""
    
    def __init__(self, naming_strategy: NamingStrategy = NamingStrategy.HASH):
        """
        Initialize function generator.
        
        Args:
            naming_strategy: Strategy for naming functions
        """
        self.naming_strategy = naming_strategy
        self._function_counter = 0
        self._used_names = set()
    
    def generate_function(
        self,
        expr,
        variables: List[str],
        metadata: ExpressionMetadata,
        expression_str: str,
        function_name: Optional[str] = None
    ) -> GeneratedFunction:
        """
        Generate a function from expression.
        
        Args:
            expr: SymPy expression (or None if parse failed)
            variables: List of parameter names
            metadata: Expression metadata
            expression_str: Python code string for expression
            function_name: Optional custom function name
            
        Returns:
            GeneratedFunction object
        """
        # Generate function name if not provided
        if function_name is None:
            function_name = self._generate_function_name(metadata.original_latex)
        else:
            function_name = self._ensure_unique_name(function_name)
        
        # Generate docstring
        docstring = self._generate_docstring(metadata, variables)
        
        # Create function
        func = GeneratedFunction(
            name=function_name,
            parameters=variables,
            expression_str=expression_str,
            docstring=docstring,
            metadata=metadata
        )
        
        return func
    
    def _generate_function_name(self, latex_expr: str) -> str:
        """
        Generate a function name based on naming strategy.
        
        Args:
            latex_expr: LaTeX expression
            
        Returns:
            Function name
        """
        if self.naming_strategy == NamingStrategy.SEQUENTIAL:
            name = f"expr_{self._function_counter}"
            self._function_counter += 1
            return self._ensure_unique_name(name)
        
        elif self.naming_strategy == NamingStrategy.HASH:
            # Generate hash-based name
            hash_obj = hashlib.sha256(latex_expr.encode())
            short_hash = hash_obj.hexdigest()[:8]
            name = f"expr_{short_hash}"
            return self._ensure_unique_name(name)
        
        else:  # SEMANTIC - try to extract meaningful name
            # For now, use hash as fallback
            hash_obj = hashlib.sha256(latex_expr.encode())
            short_hash = hash_obj.hexdigest()[:8]
            name = f"expr_{short_hash}"
            return self._ensure_unique_name(name)
    
    def _ensure_unique_name(self, name: str) -> str:
        """Ensure function name is unique."""
        if name not in self._used_names:
            self._used_names.add(name)
            return name
        
        # Add counter suffix
        counter = 1
        while f"{name}_{counter}" in self._used_names:
            counter += 1
        
        unique_name = f"{name}_{counter}"
        self._used_names.add(unique_name)
        return unique_name
    
    def _generate_docstring(
        self,
        metadata: ExpressionMetadata,
        variables: List[str]
    ) -> str:
        """
        Generate docstring for function.
        
        Args:
            metadata: Expression metadata
            variables: List of parameters
            
        Returns:
            Docstring text
        """
        lines = []
        
        # Add original expression
        lines.append("Generated mathematical function.")
        lines.append("")
        lines.append(f"Original: {metadata.original_latex}")
        
        # Add simplified form if available
        if metadata.simplified_latex:
            lines.append(f"Simplified: {metadata.simplified_latex}")
        
        # Add source info if available
        if metadata.source_file:
            lines.append(f"Source: {metadata.source_file}")
        if metadata.page_number:
            lines.append(f"Page: {metadata.page_number}")
        
        # Add parameters
        if variables:
            lines.append("")
            lines.append("Parameters:")
            for var in variables:
                lines.append(f"    {var}: numeric value")
        
        # Add return info
        lines.append("")
        lines.append("Returns:")
        lines.append("    Evaluated expression result")
        
        return "\n    ".join(lines)
    
    def reset(self):
        """Reset generator state."""
        self._function_counter = 0
        self._used_names.clear()
