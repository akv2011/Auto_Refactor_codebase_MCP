"""
Unified Metrics Engine Module

This module provides a unified interface for calculating code metrics across multiple
programming languages. It integrates LOC calculation, cyclomatic complexity, and
function counting into a single cohesive service.
"""

from pathlib import Path
from typing import Union, Dict, Any
from .loc_calculator import calculate_loc, LOCCalculationError
from .python_metrics import calculate_python_metrics, PythonMetricsError
from .js_function_counter import count_functions_in_file, JSFunctionCountError
from .js_complexity import calculate_complexity_in_file, JSComplexityError


class MetricsEngineError(Exception):
    """Raised when metrics calculation fails."""
    pass


class MetricsEngine:
    """
    Unified engine for calculating code metrics across multiple languages.
    
    Supports:
    - Python: LOC, cyclomatic complexity (via radon), function count
    - JavaScript/TypeScript: LOC, cyclomatic complexity (AST-based), function count
    
    Example:
        >>> engine = MetricsEngine()
        >>> metrics = engine.calculate('my_module.py')
        >>> print(f"LOC: {metrics['metrics']['loc']}")
        >>> print(f"Complexity: {metrics['metrics']['cyclomatic_complexity']}")
    """
    
    # Supported language mappings
    PYTHON_EXTENSIONS = {'.py'}
    JS_TS_EXTENSIONS = {'.js', '.jsx', '.ts', '.tsx'}
    SUPPORTED_EXTENSIONS = PYTHON_EXTENSIONS | JS_TS_EXTENSIONS
    
    def __init__(self):
        """Initialize the MetricsEngine."""
        pass
    
    def _detect_language(self, file_path: Path) -> str:
        """
        Detect the programming language from file extension.
        
        Args:
            file_path: Path object for the file
            
        Returns:
            Language identifier: 'python', 'javascript', or 'typescript'
            
        Raises:
            MetricsEngineError: If language is not supported
        """
        ext = file_path.suffix.lower()
        
        if ext in self.PYTHON_EXTENSIONS:
            return 'python'
        elif ext in {'.js', '.jsx'}:
            return 'javascript'
        elif ext in {'.ts', '.tsx'}:
            return 'typescript'
        else:
            raise MetricsEngineError(
                f"Unsupported file extension: {ext}. "
                f"Supported: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )
    
    def calculate(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Calculate all available metrics for a source file.
        
        Returns a standardized report containing:
        - file_path: Absolute path to the file
        - language: Detected programming language
        - metrics: Dictionary with LOC, complexity, function count, etc.
        - status: 'success' or 'error'
        - error: Error message if status is 'error'
        
        Args:
            file_path: Path to the source file
            
        Returns:
            Dictionary with metrics report
            
        Raises:
            MetricsEngineError: If calculation fails
            
        Example:
            >>> engine = MetricsEngine()
            >>> report = engine.calculate('example.py')
            >>> print(report)
            {
                'file_path': '/path/to/example.py',
                'language': 'python',
                'metrics': {
                    'loc': 42,
                    'cyclomatic_complexity': 5.5,
                    'function_count': 3,
                    'total_complexity': 11
                },
                'status': 'success'
            }
        """
        try:
            path = Path(file_path).resolve()
            
            # Validate file exists
            if not path.exists():
                raise MetricsEngineError(f"File not found: {file_path}")
            
            if not path.is_file():
                raise MetricsEngineError(f"Path is not a file: {file_path}")
            
            # Detect language
            language = self._detect_language(path)
            
            # Initialize metrics dictionary
            metrics = {}
            
            # Calculate LOC (works for all languages)
            try:
                metrics['loc'] = calculate_loc(path)
            except LOCCalculationError as e:
                # LOC calculation failed, but continue with other metrics
                metrics['loc'] = None
                metrics['loc_error'] = str(e)
            
            # Calculate language-specific metrics
            if language == 'python':
                metrics.update(self._calculate_python_metrics(path))
            else:  # javascript or typescript
                metrics.update(self._calculate_js_ts_metrics(path))
            
            return {
                'file_path': str(path),
                'language': language,
                'metrics': metrics,
                'status': 'success'
            }
            
        except MetricsEngineError:
            raise
        except Exception as e:
            raise MetricsEngineError(
                f"Error calculating metrics for {file_path}: {e}"
            ) from e
    
    def _calculate_python_metrics(self, file_path: Path) -> Dict[str, Any]:
        """
        Calculate Python-specific metrics using radon.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Dictionary with Python metrics
        """
        try:
            python_metrics = calculate_python_metrics(file_path)
            return {
                'function_count': python_metrics['function_count'],
                'cyclomatic_complexity': python_metrics['cyclomatic_complexity'],
                'total_complexity': python_metrics['total_complexity'],
                'functions': python_metrics['functions']
            }
        except PythonMetricsError as e:
            # Return partial metrics with error
            return {
                'function_count': None,
                'cyclomatic_complexity': None,
                'total_complexity': None,
                'functions': [],
                'python_metrics_error': str(e)
            }
    
    def _calculate_js_ts_metrics(self, file_path: Path) -> Dict[str, Any]:
        """
        Calculate JavaScript/TypeScript metrics using AST traversal.
        
        Args:
            file_path: Path to JS/TS file
            
        Returns:
            Dictionary with JS/TS metrics
        """
        metrics = {}
        
        # Function count
        try:
            metrics['function_count'] = count_functions_in_file(file_path)
        except JSFunctionCountError as e:
            metrics['function_count'] = None
            metrics['function_count_error'] = str(e)
        
        # Cyclomatic complexity
        try:
            metrics['cyclomatic_complexity'] = calculate_complexity_in_file(file_path)
            metrics['total_complexity'] = metrics['cyclomatic_complexity']
        except JSComplexityError as e:
            metrics['cyclomatic_complexity'] = None
            metrics['total_complexity'] = None
            metrics['complexity_error'] = str(e)
        
        return metrics
    
    def calculate_batch(
        self,
        file_paths: list[Union[str, Path]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate metrics for multiple files.
        
        Args:
            file_paths: List of file paths
            
        Returns:
            Dictionary mapping file paths to their metric reports
            
        Example:
            >>> engine = MetricsEngine()
            >>> results = engine.calculate_batch(['file1.py', 'file2.js'])
            >>> for path, report in results.items():
            ...     print(f"{path}: {report['metrics']['loc']} LOC")
        """
        results = {}
        
        for file_path in file_paths:
            try:
                report = self.calculate(file_path)
                results[str(file_path)] = report
            except MetricsEngineError as e:
                # Store error report
                results[str(file_path)] = {
                    'file_path': str(file_path),
                    'language': None,
                    'metrics': {},
                    'status': 'error',
                    'error': str(e)
                }
        
        return results
    
    def get_supported_extensions(self) -> set[str]:
        """
        Get the set of supported file extensions.
        
        Returns:
            Set of supported extensions (e.g., {'.py', '.js', '.ts'})
        """
        return self.SUPPORTED_EXTENSIONS.copy()
    
    def is_supported(self, file_path: Union[str, Path]) -> bool:
        """
        Check if a file is supported by the metrics engine.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file extension is supported, False otherwise
        """
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_EXTENSIONS


# Convenience function for single-file calculation
def calculate_file_metrics(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Convenience function to calculate metrics for a single file.
    
    This is equivalent to:
        engine = MetricsEngine()
        return engine.calculate(file_path)
    
    Args:
        file_path: Path to the source file
        
    Returns:
        Dictionary with metrics report
        
    Example:
        >>> metrics = calculate_file_metrics('example.py')
        >>> print(f"LOC: {metrics['metrics']['loc']}")
    """
    engine = MetricsEngine()
    return engine.calculate(file_path)
