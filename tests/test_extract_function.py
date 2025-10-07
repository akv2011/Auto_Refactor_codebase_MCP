"""
Tests for extract_function operation in RefactoringEngine.
"""

import tempfile
from pathlib import Path
import pytest

from src.refactoring_engine import (
    RefactoringEngine,
    RefactoringError,
    RefactoringValidationError,
)


class TestExtractFunction:
    """Tests for the extract_function refactoring operation."""
    
    def test_extract_function_basic(self):
        """Test basic function extraction."""
        engine = RefactoringEngine()
        
        # Create source file with multiple functions
        source_code = """def hello():
    print("Hello, World!")

def goodbye():
    print("Goodbye!")

def main():
    hello()
    goodbye()
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source_code)
            source_file = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            target_file = f.name
        
        try:
            # Extract the 'goodbye' function
            result = engine.apply({
                'type': 'extract_function',
                'source_file': source_file,
                'target_file': target_file,
                'function_name': 'goodbye'
            })
            
            # Verify result
            assert result['status'] == 'success'
            assert source_file in result['affected_files']
            assert target_file in result['affected_files']
            
            # Read modified source
            with open(source_file, 'r') as f:
                modified_source = f.read()
            
            # Verify function was removed from source
            assert 'def goodbye():' not in modified_source
            assert 'def hello():' in modified_source  # Other functions remain
            assert 'def main():' in modified_source
            
            # Read target file
            with open(target_file, 'r') as f:
                target_content = f.read()
            
            # Verify function was added to target
            assert 'def goodbye():' in target_content
            assert 'print("Goodbye!")' in target_content
            
        finally:
            Path(source_file).unlink()
            Path(target_file).unlink()
    
    def test_extract_function_not_found(self):
        """Test extraction of non-existent function."""
        engine = RefactoringEngine()
        
        source_code = """def hello():
    print("Hello")
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source_code)
            source_file = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            target_file = f.name
        
        try:
            result = engine.apply({
                'type': 'extract_function',
                'source_file': source_file,
                'target_file': target_file,
                'function_name': 'nonexistent'
            })
            
            # Should return error status
            assert result['status'] == 'error'
            assert 'not found' in result['error']
        finally:
            Path(source_file).unlink()
            Path(target_file).unlink()
    
    def test_extract_function_missing_params(self):
        """Test extraction with missing parameters."""
        engine = RefactoringEngine()
        
        # Missing function_name - should return error
        result = engine.apply({
            'type': 'extract_function',
            'source_file': 'test.py',
            'target_file': 'target.py'
        })
        assert result['status'] == 'error'
        assert 'Missing required parameter' in result['error']
        
        # Missing target_file - should return error
        result = engine.apply({
            'type': 'extract_function',
            'source_file': 'test.py',
            'function_name': 'hello'
        })
        assert result['status'] == 'error'
        assert 'Missing required parameter' in result['error']
    
    def test_extract_function_preserves_other_code(self):
        """Test that extraction preserves other code in source file."""
        engine = RefactoringEngine()
        
        source_code = """# Module docstring
'''This is a test module.'''

CONSTANT = 42

def function_a():
    return 1

def function_b():
    return 2

def function_c():
    return 3

# End of file
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source_code)
            source_file = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            target_file = f.name
        
        try:
            # Extract function_b
            engine.apply({
                'type': 'extract_function',
                'source_file': source_file,
                'target_file': target_file,
                'function_name': 'function_b'
            })
            
            # Read modified source
            with open(source_file, 'r') as f:
                modified_source = f.read()
            
            # Verify other code is preserved
            assert 'CONSTANT = 42' in modified_source
            assert 'def function_a():' in modified_source
            assert 'def function_c():' in modified_source
            assert '# Module docstring' in modified_source
            assert '# End of file' in modified_source
            
            # Verify extracted function is not in source
            assert 'def function_b():' not in modified_source
            
        finally:
            Path(source_file).unlink()
            Path(target_file).unlink()

    def test_extract_function_with_import_management(self):
        """Test that extraction properly manages imports and exports."""
        engine = RefactoringEngine()
        
        # Source file with imports and a function that uses them
        source_code = """import os
from pathlib import Path

def process_file(filename):
    '''Process a file using os and Path.'''
    p = Path(filename)
    if os.path.exists(p):
        return str(p.absolute())
    return None

def main():
    result = process_file('test.txt')
    print(result)
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source_code)
            source_file = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            target_file = f.name
        
        try:
            # Extract process_file
            result = engine.apply({
                'type': 'extract_function',
                'source_file': source_file,
                'target_file': target_file,
                'function_name': 'process_file'
            })
            
            assert result['status'] == 'success'
            
            # Read modified source
            with open(source_file, 'r') as f:
                modified_source = f.read()
            
            # Source should have import for the extracted function
            assert 'process_file' in modified_source
            # Import statement should be added
            assert 'import' in modified_source
            
            # Read target file
            with open(target_file, 'r') as f:
                target_content = f.read()
            
            # Target should have the function
            assert 'def process_file(filename):' in target_content
            
            # Target should have __all__ with the function
            assert '__all__' in target_content
            
            # Target should have necessary imports (os and Path from pathlib)
            assert 'os' in target_content
            assert 'Path' in target_content
            
            # Verify target file is valid Python
            compile(target_content, target_file, 'exec')
            
        finally:
            Path(source_file).unlink()
            Path(target_file).unlink()
