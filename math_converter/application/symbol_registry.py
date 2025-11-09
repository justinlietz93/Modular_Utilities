"""Symbol registry for tracking and naming mathematical symbols."""
import hashlib
import re
from typing import Dict, Set, Optional
from ..domain.codegen_types import SymbolInfo, NamingStrategy


class SymbolRegistry:
    """Registry for managing mathematical symbols and their canonical names."""
    
    # Python reserved keywords to avoid
    PYTHON_KEYWORDS = {
        'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
        'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
        'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
        'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try',
        'while', 'with', 'yield'
    }
    
    def __init__(self, naming_strategy: NamingStrategy = NamingStrategy.HASH):
        """
        Initialize the symbol registry.
        
        Args:
            naming_strategy: Strategy for generating names
        """
        self.naming_strategy = naming_strategy
        self._symbols: Dict[str, SymbolInfo] = {}
        self._name_counters: Dict[str, int] = {}
        self._used_names: Set[str] = set()
    
    def register_symbol(
        self,
        original_token: str,
        symbol_type: str = "scalar",
        source_info: Optional[Dict] = None
    ) -> str:
        """
        Register a symbol and get its canonical name.
        
        Args:
            original_token: Original symbol representation
            symbol_type: Type of symbol (scalar, indexed, function, constant)
            source_info: Optional source information
            
        Returns:
            Canonical name for the symbol
        """
        # Check if already registered
        if original_token in self._symbols:
            symbol = self._symbols[original_token]
            if source_info:
                symbol.occurrences.append(source_info)
            return symbol.canonical_name
        
        # Generate canonical name
        canonical = self._generate_canonical_name(original_token, symbol_type)
        
        # Create symbol info
        occurrences = [source_info] if source_info else []
        symbol = SymbolInfo(
            canonical_name=canonical,
            original_token=original_token,
            symbol_type=symbol_type,
            occurrences=occurrences
        )
        
        self._symbols[original_token] = symbol
        self._used_names.add(canonical)
        
        return canonical
    
    def _generate_canonical_name(self, original_token: str, symbol_type: str) -> str:
        """
        Generate a canonical name for a symbol.
        
        Args:
            original_token: Original symbol representation
            symbol_type: Type of symbol
            
        Returns:
            Canonical name
        """
        # Clean the token for use as a name
        base_name = self._clean_token(original_token)
        
        # Ensure it's a valid Python identifier
        if not base_name or base_name[0].isdigit():
            base_name = f"var_{base_name}"
        
        # Check for keyword collision
        if base_name in self.PYTHON_KEYWORDS:
            base_name = f"{base_name}_"
        
        # Apply naming strategy
        if self.naming_strategy == NamingStrategy.SEQUENTIAL:
            return self._sequential_name(base_name)
        elif self.naming_strategy == NamingStrategy.HASH:
            return self._hash_name(original_token, base_name)
        else:  # SEMANTIC
            return self._semantic_name(base_name)
    
    def _clean_token(self, token: str) -> str:
        """Clean a token to make it a valid Python identifier."""
        # Remove LaTeX commands
        token = re.sub(r'\\', '', token)
        
        # Replace special characters
        token = token.replace('{', '').replace('}', '')
        token = token.replace('^', '_pow_').replace('_', '_')
        
        # Keep only alphanumeric and underscore
        token = re.sub(r'[^a-zA-Z0-9_]', '', token)
        
        return token or "var"
    
    def _sequential_name(self, base_name: str) -> str:
        """Generate sequential name with counter."""
        # If base_name is not used, use it directly
        if base_name not in self._used_names:
            return base_name
        
        # Otherwise, add counter
        if base_name not in self._name_counters:
            self._name_counters[base_name] = 1
        
        counter = self._name_counters[base_name]
        new_name = f"{base_name}_{counter}"
        
        # Increment counter for next use
        self._name_counters[base_name] = counter + 1
        
        # Ensure uniqueness
        while new_name in self._used_names:
            counter += 1
            new_name = f"{base_name}_{counter}"
            self._name_counters[base_name] = counter + 1
        
        return new_name
    
    def _hash_name(self, original_token: str, base_name: str) -> str:
        """Generate hash-based name."""
        # Create short hash of original token
        hash_obj = hashlib.sha256(original_token.encode())
        short_hash = hash_obj.hexdigest()[:6]
        
        new_name = f"{base_name}_{short_hash}"
        
        # Ensure uniqueness (rare collision case)
        counter = 1
        while new_name in self._used_names:
            new_name = f"{base_name}_{short_hash}_{counter}"
            counter += 1
        
        return new_name
    
    def _semantic_name(self, base_name: str) -> str:
        """Generate semantic name (currently same as sequential)."""
        return self._sequential_name(base_name)
    
    def get_symbol(self, original_token: str) -> Optional[SymbolInfo]:
        """Get symbol info by original token."""
        return self._symbols.get(original_token)
    
    def get_all_symbols(self) -> Dict[str, SymbolInfo]:
        """Get all registered symbols."""
        return self._symbols.copy()
    
    def export_to_dict(self) -> Dict:
        """Export registry to dictionary format."""
        return {
            token: symbol.to_dict()
            for token, symbol in self._symbols.items()
        }
    
    def clear(self):
        """Clear the registry."""
        self._symbols.clear()
        self._name_counters.clear()
        self._used_names.clear()
