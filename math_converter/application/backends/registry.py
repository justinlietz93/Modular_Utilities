"""Backend registry for code generation."""
from typing import Dict, Optional
from ...domain.codegen_types import CodegenBackend


class BackendRegistry:
    """Registry for code generation backends."""
    
    def __init__(self):
        """Initialize the backend registry."""
        self._backends: Dict[str, CodegenBackend] = {}
        self._register_default_backends()
    
    def _register_default_backends(self):
        """Register default backends."""
        from .python_backend import PythonBackend
        from .rust_backend import RustBackend
        
        self.register("python", PythonBackend())
        self.register("rust", RustBackend())
    
    def register(self, language: str, backend: CodegenBackend):
        """
        Register a backend for a language.
        
        Args:
            language: Language name (e.g., 'python', 'rust')
            backend: Backend instance
        """
        self._backends[language.lower()] = backend
    
    def get_backend(self, language: str) -> Optional[CodegenBackend]:
        """
        Get backend for a language.
        
        Args:
            language: Language name
            
        Returns:
            Backend instance or None if not found
        """
        return self._backends.get(language.lower())
    
    def list_backends(self) -> list:
        """
        List available backends.
        
        Returns:
            List of supported language names
        """
        return list(self._backends.keys())
    
    def is_supported(self, language: str) -> bool:
        """
        Check if a language is supported.
        
        Args:
            language: Language name
            
        Returns:
            True if supported, False otherwise
        """
        return language.lower() in self._backends


# Global registry instance
_global_registry = BackendRegistry()


def get_backend(language: str) -> Optional[CodegenBackend]:
    """
    Get backend from global registry.
    
    Args:
        language: Language name
        
    Returns:
        Backend instance or None if not found
    """
    return _global_registry.get_backend(language)


def list_backends() -> list:
    """
    List available backends from global registry.
    
    Returns:
        List of supported language names
    """
    return _global_registry.list_backends()


def is_supported(language: str) -> bool:
    """
    Check if a language is supported.
    
    Args:
        language: Language name
        
    Returns:
        True if supported, False otherwise
    """
    return _global_registry.is_supported(language)
