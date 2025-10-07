"""
Custom exceptions and error handling for TaskMaster configuration.

This module provides custom exception classes and utilities for handling
configuration-related errors with clear, user-friendly messages.
"""

from typing import List, Any
from pathlib import Path
from pydantic import ValidationError


class ConfigurationError(Exception):
    """Base exception for configuration-related errors."""
    pass


class ConfigFileNotFoundError(ConfigurationError):
    """Raised when a required configuration file is not found."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        super().__init__(f"Configuration file not found: {file_path}")


class InvalidConfigJSONError(ConfigurationError):
    """Raised when configuration file contains invalid JSON."""
    
    def __init__(self, file_path: Path, error: str):
        self.file_path = file_path
        self.error = error
        super().__init__(
            f"Invalid JSON in configuration file '{file_path}': {error}"
        )


class ConfigValidationError(ConfigurationError):
    """Raised when configuration fails validation."""
    
    def __init__(self, errors: List[dict]):
        self.errors = errors
        message = self._format_validation_errors(errors)
        super().__init__(message)
    
    @staticmethod
    def _format_validation_errors(errors: List[dict]) -> str:
        """Format Pydantic validation errors into a readable message."""
        lines = ["Configuration validation failed:"]
        
        for error in errors:
            location = " -> ".join(str(loc) for loc in error.get('loc', []))
            msg = error.get('msg', 'Unknown error')
            error_type = error.get('type', 'unknown')
            
            lines.append(f"  • {location}: {msg} (type: {error_type})")
        
        return "\n".join(lines)
    
    @classmethod
    def from_pydantic_error(cls, pydantic_error: ValidationError) -> 'ConfigValidationError':
        """Create ConfigValidationError from Pydantic ValidationError."""
        return cls(pydantic_error.errors())


class ConfigPermissionError(ConfigurationError):
    """Raised when there are permission issues reading config files."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        super().__init__(
            f"Permission denied reading configuration file: {file_path}"
        )


def format_config_error(error: Exception, file_path: Path = None) -> str:
    """
    Format configuration errors into user-friendly messages.
    
    Args:
        error: The exception that occurred.
        file_path: The configuration file path (if applicable).
        
    Returns:
        Formatted error message string.
    """
    if isinstance(error, ConfigurationError):
        return str(error)
    
    if isinstance(error, ValidationError):
        return str(ConfigValidationError.from_pydantic_error(error))
    
    if isinstance(error, FileNotFoundError):
        if file_path:
            return str(ConfigFileNotFoundError(file_path))
        return f"File not found: {error}"
    
    if isinstance(error, PermissionError):
        if file_path:
            return str(ConfigPermissionError(file_path))
        return f"Permission denied: {error}"
    
    # Generic error
    return f"Configuration error: {error}"
