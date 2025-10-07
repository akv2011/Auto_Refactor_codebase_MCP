"""
Python Metrics Calculator Module

This module provides specialized metrics calculation for Python files using the radon library.
It calculates cyclomatic complexity and function counts for Python code.
"""

from pathlib import Path
from typing import Union, Dict, Any
from radon.complexity import ComplexityVisitor
from radon.visitors import Function


class PythonMetricsError(Exception):
    """Raised when Python metrics calculation fails."""
    pass


def calculate_python_metrics(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Calculate cyclomatic complexity and function count for a Python file.
    
    Uses the radon library to analyze Python source code and extract:
    - Total number of functions/methods
    - Average cyclomatic complexity across all functions
    - Total cyclomatic complexity (sum of all functions)
    - Individual complexity for each function
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Dictionary containing:
            - 'function_count': Total number of functions/methods
            - 'cyclomatic_complexity': Average cyclomatic complexity
            - 'total_complexity': Sum of all function complexities
            - 'functions': List of dicts with per-function details
            
    Raises:
        PythonMetricsError: If file cannot be read or analyzed
        
    Example:
        >>> metrics = calculate_python_metrics('my_module.py')
        >>> print(f"Functions: {metrics['function_count']}")
        >>> print(f"Avg Complexity: {metrics['cyclomatic_complexity']:.2f}")
    """
    try:
        path = Path(file_path)
        
        # Validate file exists
        if not path.exists():
            raise PythonMetricsError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise PythonMetricsError(f"Path is not a file: {file_path}")
        
        # Validate it's a Python file
        if path.suffix.lower() != '.py':
            raise PythonMetricsError(f"Not a Python file: {file_path}")
        
        # Read file content
        try:
            with open(path, 'r', encoding='utf-8') as f:
                code = f.read()
        except UnicodeDecodeError:
            # Try with error ignore if UTF-8 fails
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
        
        # Handle empty file
        if not code.strip():
            return {
                'function_count': 0,
                'cyclomatic_complexity': 0,
                'total_complexity': 0,
                'functions': []
            }
        
        # Analyze with radon
        try:
            visitor = ComplexityVisitor.from_code(code)
        except SyntaxError as e:
            raise PythonMetricsError(f"Syntax error in {file_path}: {e}") from e
        
        # Extract all functions (including methods)
        all_functions = []
        
        # Add top-level functions
        all_functions.extend(visitor.functions)
        
        # Add methods from classes
        for cls in visitor.classes:
            all_functions.extend(cls.methods)
        
        # Calculate metrics
        function_count = len(all_functions)
        
        if function_count == 0:
            return {
                'function_count': 0,
                'cyclomatic_complexity': 0,
                'total_complexity': 0,
                'functions': []
            }
        
        # Extract complexity values
        complexities = [func.complexity for func in all_functions]
        total_complexity = sum(complexities)
        avg_complexity = total_complexity / function_count
        
        # Build function details list
        function_details = []
        for func in all_functions:
            function_details.append({
                'name': func.name,
                'complexity': func.complexity,
                'line_number': func.lineno,
                'end_line_number': func.endline,
                'is_method': func.is_method
            })
        
        return {
            'function_count': function_count,
            'cyclomatic_complexity': avg_complexity,
            'total_complexity': total_complexity,
            'functions': function_details
        }
        
    except PythonMetricsError:
        # Re-raise our custom errors
        raise
    except Exception as e:
        # Wrap any other errors
        raise PythonMetricsError(
            f"Error calculating Python metrics for {file_path}: {e}"
        ) from e


def calculate_python_metrics_batch(
    file_paths: list[Union[str, Path]]
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate Python metrics for multiple files.
    
    Args:
        file_paths: List of Python file paths
        
    Returns:
        Dictionary mapping file paths to their metrics
        
    Example:
        >>> results = calculate_python_metrics_batch(['file1.py', 'file2.py'])
        >>> for path, metrics in results.items():
        ...     print(f"{path}: {metrics['function_count']} functions")
    """
    results = {}
    
    for file_path in file_paths:
        try:
            path_str = str(file_path)
            results[path_str] = calculate_python_metrics(file_path)
        except PythonMetricsError as e:
            # Store error message instead of metrics
            results[str(file_path)] = {
                'error': str(e),
                'function_count': 0,
                'cyclomatic_complexity': 0,
                'total_complexity': 0,
                'functions': []
            }
    
    return results


def get_complexity_grade(complexity: float) -> str:
    """
    Get a letter grade for cyclomatic complexity.
    
    Based on common thresholds:
    - A: 1-5 (simple)
    - B: 6-10 (manageable)
    - C: 11-20 (complex)
    - D: 21-30 (very complex)
    - F: 31+ (extremely complex, needs refactoring)
    
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
