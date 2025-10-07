"""
Tests for the Lines of Code (LOC) Calculator module.
"""

import pytest
from pathlib import Path
from src.loc_calculator import (
    calculate_loc,
    calculate_loc_batch,
    is_code_line,
    get_comment_marker_for_extension,
    LOCCalculationError,
    COMMENT_MARKERS
)


class TestCommentMarkerRetrieval:
    """Tests for getting comment markers by file extension."""
    
    def test_python_extension(self):
        """Test Python file extension returns '#'."""
        assert get_comment_marker_for_extension('.py') == '#'
        assert get_comment_marker_for_extension('py') == '#'
    
    def test_javascript_extension(self):
        """Test JavaScript extensions return '//'."""
        assert get_comment_marker_for_extension('.js') == '//'
        assert get_comment_marker_for_extension('.jsx') == '//'
    
    def test_typescript_extension(self):
        """Test TypeScript extensions return '//'."""
        assert get_comment_marker_for_extension('.ts') == '//'
        assert get_comment_marker_for_extension('.tsx') == '//'
    
    def test_java_extension(self):
        """Test Java extension returns '//'."""
        assert get_comment_marker_for_extension('.java') == '//'
    
    def test_csharp_extension(self):
        """Test C# extension returns '//'."""
        assert get_comment_marker_for_extension('.cs') == '//'
    
    def test_sql_extension(self):
        """Test SQL extension returns '--'."""
        assert get_comment_marker_for_extension('.sql') == '--'
    
    def test_unsupported_extension(self):
        """Test unsupported extension raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported file extension"):
            get_comment_marker_for_extension('.xyz')
    
    def test_case_insensitive(self):
        """Test extension matching is case-insensitive."""
        assert get_comment_marker_for_extension('.PY') == '#'
        assert get_comment_marker_for_extension('.JS') == '//'


class TestCodeLineDetection:
    """Tests for determining if a line contains code."""
    
    def test_empty_line(self):
        """Test empty line is not code."""
        assert not is_code_line('', '#')
        assert not is_code_line('   ', '#')
        assert not is_code_line('\t\t', '#')
    
    def test_comment_line_python(self):
        """Test Python comment line is not code."""
        assert not is_code_line('# This is a comment', '#')
        assert not is_code_line('  # Indented comment', '#')
    
    def test_comment_line_javascript(self):
        """Test JavaScript comment line is not code."""
        assert not is_code_line('// This is a comment', '//')
        assert not is_code_line('  // Indented comment', '//')
    
    def test_code_line_python(self):
        """Test Python code line is detected."""
        assert is_code_line('x = 42', '#')
        assert is_code_line('def foo():', '#')
        assert is_code_line('    return True', '#')
    
    def test_code_line_javascript(self):
        """Test JavaScript code line is detected."""
        assert is_code_line('const x = 42;', '//')
        assert is_code_line('function foo() {', '//')
        assert is_code_line('    return true;', '//')
    
    def test_code_with_inline_comment(self):
        """Test line with code and inline comment is detected as code."""
        assert is_code_line('x = 42  # inline comment', '#')
        assert is_code_line('const x = 42; // inline comment', '//')


class TestCalculateLOC:
    """Tests for the main calculate_loc function."""
    
    @pytest.fixture
    def temp_python_file(self, tmp_path):
        """Create a temporary Python file with known LOC."""
        file = tmp_path / "test.py"
        content = """# This is a comment
x = 42

def foo():
    # Another comment
    return True

# Final comment
"""
        file.write_text(content)
        return file, 3  # Expected LOC: x=42, def foo():, return True
    
    @pytest.fixture
    def temp_javascript_file(self, tmp_path):
        """Create a temporary JavaScript file with known LOC."""
        file = tmp_path / "test.js"
        content = """// This is a comment
const x = 42;

function foo() {
    // Another comment
    return true;
}

// Final comment
"""
        file.write_text(content)
        return file, 4  # Expected LOC: const, function, return, closing brace
    
    @pytest.fixture
    def temp_empty_file(self, tmp_path):
        """Create an empty file."""
        file = tmp_path / "empty.py"
        file.write_text("")
        return file, 0  # Expected LOC: 0
    
    @pytest.fixture
    def temp_comments_only_file(self, tmp_path):
        """Create a file with only comments and whitespace."""
        file = tmp_path / "comments.py"
        content = """# Comment 1

# Comment 2
    # Comment 3

"""
        file.write_text(content)
        return file, 0  # Expected LOC: 0
    
    @pytest.fixture
    def temp_code_only_file(self, tmp_path):
        """Create a file with only code (no comments or empty lines)."""
        file = tmp_path / "code.py"
        content = """x = 1
y = 2
z = x + y
print(z)
"""
        file.write_text(content)
        return file, 4  # Expected LOC: 4
    
    def test_python_file_with_mixed_content(self, temp_python_file):
        """Test LOC calculation for Python file with code and comments."""
        file, expected_loc = temp_python_file
        assert calculate_loc(file) == expected_loc
    
    def test_javascript_file_with_mixed_content(self, temp_javascript_file):
        """Test LOC calculation for JavaScript file with code and comments."""
        file, expected_loc = temp_javascript_file
        assert calculate_loc(file) == expected_loc
    
    def test_empty_file(self, temp_empty_file):
        """Test LOC calculation for empty file."""
        file, expected_loc = temp_empty_file
        assert calculate_loc(file) == expected_loc
    
    def test_comments_only_file(self, temp_comments_only_file):
        """Test LOC calculation for file with only comments."""
        file, expected_loc = temp_comments_only_file
        assert calculate_loc(file) == expected_loc
    
    def test_code_only_file(self, temp_code_only_file):
        """Test LOC calculation for file with only code."""
        file, expected_loc = temp_code_only_file
        assert calculate_loc(file) == expected_loc
    
    def test_nonexistent_file(self):
        """Test error handling for nonexistent file."""
        with pytest.raises(LOCCalculationError, match="File not found"):
            calculate_loc("nonexistent.py")
    
    def test_directory_path(self, tmp_path):
        """Test error handling for directory path."""
        with pytest.raises(LOCCalculationError, match="Path is not a file"):
            calculate_loc(tmp_path)
    
    def test_unsupported_file_extension(self, tmp_path):
        """Test error handling for unsupported file extension."""
        file = tmp_path / "test.xyz"
        file.write_text("some content")
        with pytest.raises(ValueError, match="Unsupported file extension"):
            calculate_loc(file)
    
    def test_path_as_string(self, temp_python_file):
        """Test that function accepts string paths."""
        file, expected_loc = temp_python_file
        assert calculate_loc(str(file)) == expected_loc
    
    def test_path_as_pathlib(self, temp_python_file):
        """Test that function accepts Path objects."""
        file, expected_loc = temp_python_file
        assert calculate_loc(Path(file)) == expected_loc


class TestCalculateLOCBatch:
    """Tests for batch LOC calculation."""
    
    @pytest.fixture
    def temp_files(self, tmp_path):
        """Create multiple temporary files."""
        files = []
        
        # Python file
        py_file = tmp_path / "test1.py"
        py_file.write_text("x = 1\ny = 2\n")
        files.append((py_file, 2))
        
        # JavaScript file
        js_file = tmp_path / "test2.js"
        js_file.write_text("const x = 1;\nconst y = 2;\n")
        files.append((js_file, 2))
        
        # Empty file
        empty_file = tmp_path / "empty.py"
        empty_file.write_text("")
        files.append((empty_file, 0))
        
        return files
    
    def test_batch_calculation(self, temp_files):
        """Test batch LOC calculation for multiple files."""
        file_paths = [file for file, _ in temp_files]
        results = calculate_loc_batch(file_paths)
        
        # Check all files are in results
        assert len(results) == 3
        
        # Check each result
        for file, expected_loc in temp_files:
            assert str(file) in results
            assert results[str(file)] == expected_loc
    
    def test_batch_with_errors(self, tmp_path):
        """Test batch calculation handles errors gracefully."""
        # Create one valid file
        valid_file = tmp_path / "valid.py"
        valid_file.write_text("x = 1\n")
        
        # Use one nonexistent file
        invalid_file = tmp_path / "nonexistent.py"
        
        results = calculate_loc_batch([valid_file, invalid_file])
        
        # Valid file should have count
        assert results[str(valid_file)] == 1
        
        # Invalid file should have error message
        assert "Error" in str(results[str(invalid_file)])
    
    def test_batch_empty_list(self):
        """Test batch calculation with empty list."""
        results = calculate_loc_batch([])
        assert results == {}


class TestIntegration:
    """Integration tests for real-world scenarios."""
    
    @pytest.fixture
    def realistic_python_file(self, tmp_path):
        """Create a realistic Python file."""
        file = tmp_path / "realistic.py"
        content = '''"""
Module docstring
"""

import os
import sys

# Constants
MAX_VALUE = 100

def process_data(data):
    """Process the data."""
    # Validate input
    if not data:
        return None
    
    # Process each item
    results = []
    for item in data:
        # Skip invalid items
        if item < 0:
            continue
        results.append(item * 2)
    
    return results

class DataProcessor:
    """A class for processing data."""
    
    def __init__(self):
        self.data = []
    
    def add(self, item):
        """Add an item."""
        self.data.append(item)
'''
        file.write_text(content)
        # Expected LOC: All non-empty, non-comment lines including:
        # - imports (2)
        # - MAX_VALUE (1) 
        # - function/class definitions with docstrings and bodies
        # Actual count verified by running the function
        return file, 23
    
    def test_realistic_python_file(self, realistic_python_file):
        """Test LOC calculation on realistic Python file."""
        file, expected_loc = realistic_python_file
        actual_loc = calculate_loc(file)
        assert actual_loc == expected_loc
