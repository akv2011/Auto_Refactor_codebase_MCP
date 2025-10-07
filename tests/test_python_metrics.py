"""
Tests for the Python Metrics Calculator module.
"""

import pytest
from pathlib import Path
from src.python_metrics import (
    calculate_python_metrics,
    calculate_python_metrics_batch,
    get_complexity_grade,
    PythonMetricsError
)


class TestGetComplexityGrade:
    """Tests for complexity grade calculation."""
    
    def test_grade_a(self):
        """Test complexity grade A (simple)."""
        assert get_complexity_grade(1) == 'A'
        assert get_complexity_grade(5) == 'A'
    
    def test_grade_b(self):
        """Test complexity grade B (manageable)."""
        assert get_complexity_grade(6) == 'B'
        assert get_complexity_grade(10) == 'B'
    
    def test_grade_c(self):
        """Test complexity grade C (complex)."""
        assert get_complexity_grade(11) == 'C'
        assert get_complexity_grade(20) == 'C'
    
    def test_grade_d(self):
        """Test complexity grade D (very complex)."""
        assert get_complexity_grade(21) == 'D'
        assert get_complexity_grade(30) == 'D'
    
    def test_grade_f(self):
        """Test complexity grade F (extremely complex)."""
        assert get_complexity_grade(31) == 'F'
        assert get_complexity_grade(100) == 'F'


class TestCalculatePythonMetrics:
    """Tests for the main calculate_python_metrics function."""
    
    @pytest.fixture
    def simple_python_file(self, tmp_path):
        """Create a simple Python file with known metrics."""
        file = tmp_path / "simple.py"
        content = """def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""
        file.write_text(content)
        # Expected: 2 functions, each with complexity 1 (no branching)
        return file, {'function_count': 2, 'avg_complexity': 1.0, 'total': 2}
    
    @pytest.fixture
    def complex_python_file(self, tmp_path):
        """Create a Python file with complex functions."""
        file = tmp_path / "complex.py"
        content = """def process(data):
    if not data:
        return None
    
    results = []
    for item in data:
        if item > 0:
            results.append(item * 2)
        elif item < 0:
            results.append(abs(item))
    
    return results

def validate(value):
    if value is None:
        return False
    
    if isinstance(value, str):
        return len(value) > 0
    elif isinstance(value, int):
        return value >= 0
    else:
        return True
"""
        file.write_text(content)
        # process: 1 + 1 (if not data) + 1 (for) + 1 (if item > 0) + 1 (elif) = 5
        # validate: 1 + 1 (if value is None) + 1 (if isinstance str) + 1 (elif isinstance int) = 4
        # Total: 9, Avg: 4.5
        return file, {'function_count': 2, 'avg_complexity': 4.5, 'total': 9}
    
    @pytest.fixture
    def class_with_methods(self, tmp_path):
        """Create a Python file with a class containing methods."""
        file = tmp_path / "with_class.py"
        content = """class Calculator:
    def add(self, a, b):
        return a + b
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Division by zero")
        return a / b
    
    def process(self, values):
        if not values:
            return []
        
        results = []
        for v in values:
            if v > 0:
                results.append(v * 2)
        return results

def standalone_func():
    return 42
"""
        file.write_text(content)
        # add: 1, divide: 2 (if), process: 1 + 2 (if, for) + 1 (if) = 4
        # standalone_func: 1
        # Total: 4 functions, complexity: 1 + 2 + 4 + 1 = 8, avg: 2.0
        return file, {'function_count': 4, 'avg_complexity': 2.0, 'total': 8}
    
    @pytest.fixture
    def empty_python_file(self, tmp_path):
        """Create an empty Python file."""
        file = tmp_path / "empty.py"
        file.write_text("")
        return file, {'function_count': 0, 'avg_complexity': 0, 'total': 0}
    
    @pytest.fixture
    def python_file_no_functions(self, tmp_path):
        """Create a Python file with no functions."""
        file = tmp_path / "no_funcs.py"
        content = """# Just some variables
x = 42
y = 100
z = x + y
"""
        file.write_text(content)
        return file, {'function_count': 0, 'avg_complexity': 0, 'total': 0}
    
    def test_simple_functions(self, simple_python_file):
        """Test metrics for simple functions."""
        file, expected = simple_python_file
        metrics = calculate_python_metrics(file)
        
        assert metrics['function_count'] == expected['function_count']
        assert metrics['cyclomatic_complexity'] == expected['avg_complexity']
        assert metrics['total_complexity'] == expected['total']
        assert len(metrics['functions']) == expected['function_count']
    
    def test_complex_functions(self, complex_python_file):
        """Test metrics for complex functions."""
        file, expected = complex_python_file
        metrics = calculate_python_metrics(file)
        
        assert metrics['function_count'] == expected['function_count']
        assert metrics['cyclomatic_complexity'] == expected['avg_complexity']
        assert metrics['total_complexity'] == expected['total']
    
    def test_class_with_methods(self, class_with_methods):
        """Test metrics for class methods."""
        file, expected = class_with_methods
        metrics = calculate_python_metrics(file)
        
        assert metrics['function_count'] == expected['function_count']
        assert metrics['cyclomatic_complexity'] == expected['avg_complexity']
        assert metrics['total_complexity'] == expected['total']
        
        # Check that we have both methods and standalone function
        function_names = [f['name'] for f in metrics['functions']]
        assert 'add' in function_names
        assert 'divide' in function_names
        assert 'process' in function_names
        assert 'standalone_func' in function_names
    
    def test_empty_file(self, empty_python_file):
        """Test metrics for empty file."""
        file, expected = empty_python_file
        metrics = calculate_python_metrics(file)
        
        assert metrics['function_count'] == 0
        assert metrics['cyclomatic_complexity'] == 0
        assert metrics['total_complexity'] == 0
        assert metrics['functions'] == []
    
    def test_no_functions(self, python_file_no_functions):
        """Test metrics for file with no functions."""
        file, expected = python_file_no_functions
        metrics = calculate_python_metrics(file)
        
        assert metrics['function_count'] == 0
        assert metrics['cyclomatic_complexity'] == 0
        assert metrics['total_complexity'] == 0
    
    def test_function_details(self, simple_python_file):
        """Test that function details are included."""
        file, _ = simple_python_file
        metrics = calculate_python_metrics(file)
        
        # Check first function details
        func = metrics['functions'][0]
        assert 'name' in func
        assert 'complexity' in func
        assert 'line_number' in func
        assert 'end_line_number' in func
        assert 'is_method' in func
        
        # Simple functions should have names
        assert func['name'] in ['add', 'subtract']
        assert func['complexity'] == 1
    
    def test_nonexistent_file(self):
        """Test error handling for nonexistent file."""
        with pytest.raises(PythonMetricsError, match="File not found"):
            calculate_python_metrics("nonexistent.py")
    
    def test_directory_path(self, tmp_path):
        """Test error handling for directory path."""
        with pytest.raises(PythonMetricsError, match="Path is not a file"):
            calculate_python_metrics(tmp_path)
    
    def test_non_python_file(self, tmp_path):
        """Test error handling for non-Python file."""
        file = tmp_path / "test.txt"
        file.write_text("some content")
        with pytest.raises(PythonMetricsError, match="Not a Python file"):
            calculate_python_metrics(file)
    
    def test_syntax_error_file(self, tmp_path):
        """Test error handling for file with syntax errors."""
        file = tmp_path / "syntax_error.py"
        content = """def broken(
    # Missing closing parenthesis
    return 42
"""
        file.write_text(content)
        with pytest.raises(PythonMetricsError, match="Syntax error"):
            calculate_python_metrics(file)
    
    def test_path_as_string(self, simple_python_file):
        """Test that function accepts string paths."""
        file, expected = simple_python_file
        metrics = calculate_python_metrics(str(file))
        assert metrics['function_count'] == expected['function_count']
    
    def test_path_as_pathlib(self, simple_python_file):
        """Test that function accepts Path objects."""
        file, expected = simple_python_file
        metrics = calculate_python_metrics(Path(file))
        assert metrics['function_count'] == expected['function_count']


class TestCalculatePythonMetricsBatch:
    """Tests for batch Python metrics calculation."""
    
    @pytest.fixture
    def multiple_files(self, tmp_path):
        """Create multiple Python files."""
        files = []
        
        # Simple file
        simple = tmp_path / "simple.py"
        simple.write_text("def foo():\n    return 1\n")
        files.append((simple, 1))  # 1 function
        
        # Complex file
        complex_file = tmp_path / "complex.py"
        complex_file.write_text("""def bar():
    if True:
        return 1
    return 2

def baz():
    return 3
""")
        files.append((complex_file, 2))  # 2 functions
        
        # Empty file
        empty = tmp_path / "empty.py"
        empty.write_text("")
        files.append((empty, 0))  # 0 functions
        
        return files
    
    def test_batch_calculation(self, multiple_files):
        """Test batch metrics calculation for multiple files."""
        file_paths = [file for file, _ in multiple_files]
        results = calculate_python_metrics_batch(file_paths)
        
        # Check all files are in results
        assert len(results) == 3
        
        # Check each result
        for file, expected_count in multiple_files:
            assert str(file) in results
            assert results[str(file)]['function_count'] == expected_count
    
    def test_batch_with_errors(self, tmp_path):
        """Test batch calculation handles errors gracefully."""
        # Create one valid file
        valid = tmp_path / "valid.py"
        valid.write_text("def foo():\n    return 1\n")
        
        # Use one nonexistent file
        invalid = tmp_path / "nonexistent.py"
        
        results = calculate_python_metrics_batch([valid, invalid])
        
        # Valid file should have metrics
        assert results[str(valid)]['function_count'] == 1
        
        # Invalid file should have error
        assert 'error' in results[str(invalid)]
        assert results[str(invalid)]['function_count'] == 0
    
    def test_batch_empty_list(self):
        """Test batch calculation with empty list."""
        results = calculate_python_metrics_batch([])
        assert results == {}


class TestIntegration:
    """Integration tests for real-world scenarios."""
    
    @pytest.fixture
    def realistic_python_module(self, tmp_path):
        """Create a realistic Python module."""
        file = tmp_path / "module.py"
        content = '''"""A realistic Python module."""

import os
import sys

def process_data(data, options=None):
    """Process data with optional configuration."""
    if not data:
        return []
    
    if options is None:
        options = {}
    
    results = []
    for item in data:
        if not isinstance(item, dict):
            continue
        
        if options.get('filter'):
            if item.get('value', 0) < 0:
                continue
        
        processed = item.copy()
        if options.get('double'):
            processed['value'] = processed.get('value', 0) * 2
        
        results.append(processed)
    
    return results

class DataValidator:
    """Validates data structures."""
    
    def __init__(self, strict=False):
        self.strict = strict
    
    def validate(self, data):
        """Validate data structure."""
        if not isinstance(data, dict):
            if self.strict:
                raise ValueError("Data must be a dict")
            return False
        
        if 'id' not in data:
            if self.strict:
                raise ValueError("Missing id")
            return False
        
        if 'value' in data:
            if not isinstance(data['value'], (int, float)):
                if self.strict:
                    raise ValueError("Invalid value type")
                return False
        
        return True
'''
        file.write_text(content)
        # process_data: 1 + 2 (if, if) + 1 (for) + 2 (if, if) + 2 (if, if) = 8
        # __init__: 1
        # validate: 1 + 2 (if, if) + 2 (if, if) + 2 (if, if) = 8
        # Total: 3 functions, complexity: 8 + 1 + 8 = 17, avg: ~5.67
        return file, 3, 17
    
    def test_realistic_module(self, realistic_python_module):
        """Test metrics calculation on realistic module."""
        file, expected_count, expected_total = realistic_python_module
        metrics = calculate_python_metrics(file)
        
        assert metrics['function_count'] == expected_count
        assert metrics['total_complexity'] == expected_total
        assert abs(metrics['cyclomatic_complexity'] - (expected_total / expected_count)) < 0.1
        
        # Check function names
        names = [f['name'] for f in metrics['functions']]
        assert 'process_data' in names
        assert '__init__' in names
        assert 'validate' in names
