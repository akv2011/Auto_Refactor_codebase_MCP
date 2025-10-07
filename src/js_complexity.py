"""
JavaScript/TypeScript Cyclomatic Complexity Calculator Module

This module provides utilities for calculating cyclomatic complexity in JavaScript
and TypeScript files using tree-sitter AST traversal.
"""

from pathlib import Path
from typing import Union, Dict, Any
from .ast_wrapper import ASTWrapper


class JSComplexityError(Exception):
    """Raised when JS/TS complexity calculation fails."""
    pass


# Node types that represent decision points in JS/TS
DECISION_POINT_NODES = {
    'if_statement',           # if (...) { }
    'for_statement',          # for (...) { }
    'for_in_statement',       # for (x in y) { }
    'while_statement',        # while (...) { }
    'do_statement',           # do { } while (...)
    'switch_case',            # case x: (each case adds complexity)
    'ternary_expression',     # a ? b : c
    'catch_clause',           # catch (e) { }
}

# Binary operators that add complexity
LOGICAL_OPERATORS = {'&&', '||', '??'}  # AND, OR, nullish coalescing


def _traverse_and_count(node, complexity_counter: list[int]) -> None:
    """
    Recursively traverse AST node and count decision points.
    
    Args:
        node: tree-sitter Node to traverse
        complexity_counter: List containing single integer (mutable counter)
    """
    # Check if this node is a decision point
    if node.type in DECISION_POINT_NODES:
        complexity_counter[0] += 1
    
    # Check for logical operators in binary expressions
    elif node.type == 'binary_expression':
        # Get the operator
        operator_node = None
        for child in node.children:
            if child.type in LOGICAL_OPERATORS or child.is_named is False:
                # Check if it's one of our target operators
                operator_text = child.text.decode('utf-8') if hasattr(child, 'text') else ''
                if operator_text in LOGICAL_OPERATORS:
                    complexity_counter[0] += 1
                    break
    
    # Recursively traverse children
    for child in node.children:
        _traverse_and_count(child, complexity_counter)


def calculate_complexity_ast(ast_wrapper: ASTWrapper) -> int:
    """
    Calculate cyclomatic complexity for a JavaScript/TypeScript AST.
    
    Cyclomatic complexity is calculated as:
    - Base complexity: 1
    - +1 for each: if, for, while, do-while, case, catch, ternary
    - +1 for each logical operator: &&, ||, ??
    
    Args:
        ast_wrapper: ASTWrapper instance with parsed JS/TS code
        
    Returns:
        Total cyclomatic complexity
        
    Raises:
        JSComplexityError: If calculation fails
        
    Example:
        >>> wrapper = ASTWrapper(js_code, 'example.js')
        >>> complexity = calculate_complexity_ast(wrapper)
        >>> print(f"Complexity: {complexity}")
    """
    try:
        # Validate input
        if not isinstance(ast_wrapper, ASTWrapper):
            raise JSComplexityError("Input must be an ASTWrapper instance")
        
        # Validate language
        language = ast_wrapper.language
        if language not in ['javascript', 'typescript']:
            raise JSComplexityError(
                f"Unsupported language: {language}. Only JavaScript and TypeScript are supported."
            )
        
        # Initialize complexity to 1 (base complexity)
        complexity_counter = [1]
        
        # Traverse AST and count decision points
        _traverse_and_count(ast_wrapper.root_node, complexity_counter)
        
        return complexity_counter[0]
        
    except Exception as e:
        if isinstance(e, JSComplexityError):
            raise
        raise JSComplexityError(
            f"Error calculating complexity: {e}"
        ) from e


def calculate_complexity_in_file(file_path: Union[str, Path]) -> int:
    """
    Calculate cyclomatic complexity for a JavaScript or TypeScript file.
    
    This is a convenience function that handles parsing and calculation in one step.
    
    Args:
        file_path: Path to the JS/TS file
        
    Returns:
        Total cyclomatic complexity
        
    Raises:
        JSComplexityError: If file cannot be read or parsed
        
    Example:
        >>> complexity = calculate_complexity_in_file('app.js')
        >>> print(f"Complexity: {complexity}")
    """
    try:
        path = Path(file_path)
        
        # Validate file exists
        if not path.exists():
            raise JSComplexityError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise JSComplexityError(f"Path is not a file: {file_path}")
        
        # Validate extension
        ext = path.suffix.lower()
        if ext not in ['.js', '.jsx', '.ts', '.tsx']:
            raise JSComplexityError(
                f"Not a JavaScript/TypeScript file: {file_path} (extension: {ext})"
            )
        
        # Read file
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        # Handle empty file
        if not code.strip():
            return 1  # Base complexity even for empty file
        
        # Parse and calculate
        wrapper = ASTWrapper(code, path)
        return calculate_complexity_ast(wrapper)
        
    except Exception as e:
        if isinstance(e, JSComplexityError):
            raise
        raise JSComplexityError(
            f"Error calculating complexity in {file_path}: {e}"
        ) from e


def calculate_complexity_batch(file_paths: list[Union[str, Path]]) -> Dict[str, int]:
    """
    Calculate cyclomatic complexity for multiple JavaScript/TypeScript files.
    
    Args:
        file_paths: List of JS/TS file paths
        
    Returns:
        Dictionary mapping file paths to complexity values
        
    Example:
        >>> results = calculate_complexity_batch(['app.js', 'utils.ts'])
        >>> for path, complexity in results.items():
        ...     print(f"{path}: complexity {complexity}")
    """
    results = {}
    
    for file_path in file_paths:
        try:
            path_str = str(file_path)
            results[path_str] = calculate_complexity_in_file(file_path)
        except JSComplexityError as e:
            # Store error message instead of complexity
            results[str(file_path)] = f"Error: {e}"
    
    return results


def calculate_per_function_complexity(ast_wrapper: ASTWrapper) -> list[Dict[str, Any]]:
    """
    Calculate cyclomatic complexity for each function in a JS/TS file.
    
    Returns a list of dictionaries with per-function complexity:
    - name: Function name
    - complexity: Cyclomatic complexity of that function
    - line_number: Starting line number
    - end_line: Ending line number
    
    Args:
        ast_wrapper: ASTWrapper instance with parsed JS/TS code
        
    Returns:
        List of function complexity dictionaries
        
    Example:
        >>> wrapper = ASTWrapper(js_code, 'example.js')
        >>> complexities = calculate_per_function_complexity(wrapper)
        >>> for func in complexities:
        ...     print(f"{func['name']}: complexity {func['complexity']}")
    """
    try:
        # Validate input
        if not isinstance(ast_wrapper, ASTWrapper):
            raise JSComplexityError("Input must be an ASTWrapper instance")
        
        # Get all functions
        functions = ast_wrapper.find_function_definitions()
        
        # Calculate complexity for each function
        results = []
        for func in functions:
            # Create a temporary wrapper for just this function's node
            # We'll traverse just the function's subtree
            complexity_counter = [1]  # Base complexity
            _traverse_and_count(func.node, complexity_counter)
            
            results.append({
                'name': func.name,
                'complexity': complexity_counter[0],
                'line_number': func.start_line,
                'end_line': func.end_line,
                'type': func.type
            })
        
        return results
        
    except Exception as e:
        if isinstance(e, JSComplexityError):
            raise
        raise JSComplexityError(
            f"Error calculating per-function complexity: {e}"
        ) from e


def get_complexity_grade(complexity: int) -> str:
    """
    Get a letter grade for cyclomatic complexity.
    
    Based on common thresholds:
    - A: 1-5 (simple, low risk)
    - B: 6-10 (manageable, low-moderate risk)
    - C: 11-20 (complex, moderate risk)
    - D: 21-30 (very complex, high risk)
    - F: 31+ (extremely complex, very high risk, needs refactoring)
    
    Args:
        complexity: Cyclomatic complexity value
        
    Returns:
        Letter grade (A, B, C, D, or F)
    """
    if complexity <= 5:
        return 'A'
    elif complexity <= 10:
        return 'B'
    elif complexity <= 20:
        return 'C'
    elif complexity <= 30:
        return 'D'
    else:
        return 'F'
