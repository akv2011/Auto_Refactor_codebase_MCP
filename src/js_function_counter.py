"""
JavaScript/TypeScript Function Counter Module

This module provides utilities for counting functions in JavaScript and TypeScript files
using tree-sitter AST traversal.
"""

from pathlib import Path
from typing import Union
from .ast_wrapper import ASTWrapper


class JSFunctionCountError(Exception):
    """Raised when JS/TS function counting fails."""
    pass


def count_functions_ast(ast_wrapper: ASTWrapper) -> int:
    """
    Count the number of functions in a parsed JavaScript/TypeScript AST.
    
    Counts all function types:
    - Function declarations (function foo() {})
    - Arrow functions (const foo = () => {})
    - Method definitions (class methods)
    - Function expressions (const foo = function() {})
    - Generator functions
    - Async functions
    
    Args:
        ast_wrapper: ASTWrapper instance with parsed JS/TS code
        
    Returns:
        Total number of functions found
        
    Raises:
        JSFunctionCountError: If counting fails
        
    Example:
        >>> wrapper = ASTWrapper(js_code, 'example.js')
        >>> count = count_functions_ast(wrapper)
        >>> print(f"Found {count} functions")
    """
    try:
        # Validate input
        if not isinstance(ast_wrapper, ASTWrapper):
            raise JSFunctionCountError("Input must be an ASTWrapper instance")
        
        # Validate language
        language = ast_wrapper.language
        if language not in ['javascript', 'typescript']:
            raise JSFunctionCountError(
                f"Unsupported language: {language}. Only JavaScript and TypeScript are supported."
            )
        
        # Use the existing find_function_definitions method
        functions = ast_wrapper.find_function_definitions()
        
        return len(functions)
        
    except Exception as e:
        if isinstance(e, JSFunctionCountError):
            raise
        raise JSFunctionCountError(
            f"Error counting functions: {e}"
        ) from e


def count_functions_in_file(file_path: Union[str, Path]) -> int:
    """
    Count functions in a JavaScript or TypeScript file.
    
    This is a convenience function that handles parsing and counting in one step.
    
    Args:
        file_path: Path to the JS/TS file
        
    Returns:
        Total number of functions found
        
    Raises:
        JSFunctionCountError: If file cannot be read or parsed
        
    Example:
        >>> count = count_functions_in_file('app.js')
        >>> print(f"Found {count} functions")
    """
    try:
        path = Path(file_path)
        
        # Validate file exists
        if not path.exists():
            raise JSFunctionCountError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise JSFunctionCountError(f"Path is not a file: {file_path}")
        
        # Validate extension
        ext = path.suffix.lower()
        if ext not in ['.js', '.jsx', '.ts', '.tsx']:
            raise JSFunctionCountError(
                f"Not a JavaScript/TypeScript file: {file_path} (extension: {ext})"
            )
        
        # Read file
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        # Handle empty file
        if not code.strip():
            return 0
        
        # Parse and count
        wrapper = ASTWrapper(code, path)
        return count_functions_ast(wrapper)
        
    except Exception as e:
        if isinstance(e, JSFunctionCountError):
            raise
        raise JSFunctionCountError(
            f"Error counting functions in {file_path}: {e}"
        ) from e


def count_functions_batch(file_paths: list[Union[str, Path]]) -> dict[str, int]:
    """
    Count functions in multiple JavaScript/TypeScript files.
    
    Args:
        file_paths: List of JS/TS file paths
        
    Returns:
        Dictionary mapping file paths to function counts
        
    Example:
        >>> results = count_functions_batch(['app.js', 'utils.ts'])
        >>> for path, count in results.items():
        ...     print(f"{path}: {count} functions")
    """
    results = {}
    
    for file_path in file_paths:
        try:
            path_str = str(file_path)
            results[path_str] = count_functions_in_file(file_path)
        except JSFunctionCountError as e:
            # Store error message instead of count
            results[str(file_path)] = f"Error: {e}"
    
    return results


def get_function_details_from_ast(ast_wrapper: ASTWrapper) -> list[dict]:
    """
    Get detailed information about all functions in a JS/TS AST.
    
    Returns a list of dictionaries with function details:
    - name: Function name
    - type: Function type (function, method, constructor, etc.)
    - line_number: Starting line number
    - end_line: Ending line number
    - is_async: Whether function is async
    - is_generator: Whether function is a generator
    
    Args:
        ast_wrapper: ASTWrapper instance with parsed JS/TS code
        
    Returns:
        List of function detail dictionaries
        
    Example:
        >>> wrapper = ASTWrapper(js_code, 'example.js')
        >>> details = get_function_details_from_ast(wrapper)
        >>> for func in details:
        ...     print(f"{func['name']}: lines {func['line_number']}-{func['end_line']}")
    """
    try:
        # Validate input
        if not isinstance(ast_wrapper, ASTWrapper):
            raise JSFunctionCountError("Input must be an ASTWrapper instance")
        
        # Use the existing find_function_definitions method
        functions = ast_wrapper.find_function_definitions()
        
        # Convert CodeNode objects to dictionaries
        details = []
        for func in functions:
            details.append({
                'name': func.name,
                'type': func.type,
                'line_number': func.start_line,
                'end_line': func.end_line,
                'metadata': func.metadata
            })
        
        return details
        
    except Exception as e:
        if isinstance(e, JSFunctionCountError):
            raise
        raise JSFunctionCountError(
            f"Error getting function details: {e}"
        ) from e
