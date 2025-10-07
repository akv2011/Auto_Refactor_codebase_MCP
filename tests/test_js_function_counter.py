"""
Tests for the JavaScript/TypeScript Function Counter module.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from src.js_function_counter import (
    count_functions_ast,
    count_functions_in_file,
    count_functions_batch,
    get_function_details_from_ast,
    JSFunctionCountError
)
from src.ast_wrapper import ASTWrapper
from src.code_node import CodeNode, CodeNodeCollection


class TestCountFunctionsAST:
    """Tests for counting functions from AST."""
    
    def test_valid_javascript_wrapper(self):
        """Test counting functions with valid JavaScript wrapper."""
        # Create mock wrapper
        mock_wrapper = Mock(spec=ASTWrapper)
        mock_wrapper.language = 'javascript'
        
        # Create mock CodeNode objects
        func1 = CodeNode(
            type='function',
            name='foo',
            start_line=1,
            end_line=3,
            source_text='function foo() { return 1; }'
        )
        func2 = CodeNode(
            type='function',
            name='bar',
            start_line=5,
            end_line=7,
            source_text='function bar() { return 2; }'
        )
        
        # Mock find_function_definitions to return CodeNodeCollection
        mock_wrapper.find_function_definitions.return_value = CodeNodeCollection([func1, func2])
        
        count = count_functions_ast(mock_wrapper)
        assert count == 2
    
    def test_valid_typescript_wrapper(self):
        """Test counting functions with valid TypeScript wrapper."""
        mock_wrapper = Mock(spec=ASTWrapper)
        mock_wrapper.language = 'typescript'
        
        func1 = CodeNode(
            type='function',
            name='foo',
            start_line=1,
            end_line=3,
            source_text='function foo(): number { return 1; }'
        )
        
        mock_wrapper.find_function_definitions.return_value = CodeNodeCollection([func1])
        
        count = count_functions_ast(mock_wrapper)
        assert count == 1
    
    def test_no_functions(self):
        """Test counting when no functions are found."""
        mock_wrapper = Mock(spec=ASTWrapper)
        mock_wrapper.language = 'javascript'
        mock_wrapper.find_function_definitions.return_value = CodeNodeCollection([])
        
        count = count_functions_ast(mock_wrapper)
        assert count == 0
    
    def test_invalid_input_type(self):
        """Test error handling for invalid input type."""
        with pytest.raises(JSFunctionCountError, match="must be an ASTWrapper instance"):
            count_functions_ast("not a wrapper")
    
    def test_unsupported_language(self):
        """Test error handling for unsupported language."""
        mock_wrapper = Mock(spec=ASTWrapper)
        mock_wrapper.language = 'python'
        
        with pytest.raises(JSFunctionCountError, match="Unsupported language"):
            count_functions_ast(mock_wrapper)


class TestCountFunctionsInFile:
    """Tests for counting functions from files."""
    
    @pytest.fixture
    def simple_js_file(self, tmp_path):
        """Create a simple JavaScript file."""
        file = tmp_path / "simple.js"
        content = """function add(a, b) {
    return a + b;
}

function subtract(a, b) {
    return a - b;
}

const multiply = (a, b) => a * b;
"""
        file.write_text(content)
        return file, 3  # 2 regular functions + 1 arrow function
    
    @pytest.fixture
    def typescript_file(self, tmp_path):
        """Create a TypeScript file with various function types."""
        file = tmp_path / "example.ts"
        content = """function regularFunc(): number {
    return 42;
}

const arrowFunc = (): string => 'hello';

class MyClass {
    method1(): void {
        console.log('method1');
    }
    
    method2(): number {
        return 100;
    }
}

async function asyncFunc(): Promise<void> {
    await Promise.resolve();
}
"""
        file.write_text(content)
        # 1 regular + 1 arrow + 2 methods + 1 async = 5
        return file, 5
    
    @pytest.fixture
    def empty_js_file(self, tmp_path):
        """Create an empty JavaScript file."""
        file = tmp_path / "empty.js"
        file.write_text("")
        return file, 0
    
    @pytest.fixture
    def js_file_no_functions(self, tmp_path):
        """Create a JavaScript file with no functions."""
        file = tmp_path / "no_funcs.js"
        content = """// Just some variables
const x = 42;
const y = 100;
const z = x + y;
"""
        file.write_text(content)
        return file, 0
    
    @pytest.mark.skipif(
        True,  # Skip by default as it requires compiled tree-sitter grammars
        reason="Requires compiled tree-sitter grammars"
    )
    def test_simple_javascript_file(self, simple_js_file):
        """Test counting functions in simple JavaScript file."""
        file, expected_count = simple_js_file
        count = count_functions_in_file(file)
        assert count == expected_count
    
    @pytest.mark.skipif(
        True,
        reason="Requires compiled tree-sitter grammars"
    )
    def test_typescript_file(self, typescript_file):
        """Test counting functions in TypeScript file."""
        file, expected_count = typescript_file
        count = count_functions_in_file(file)
        assert count == expected_count
    
    @pytest.mark.skipif(
        True,
        reason="Requires compiled tree-sitter grammars"
    )
    def test_empty_file(self, empty_js_file):
        """Test counting functions in empty file."""
        file, expected_count = empty_js_file
        count = count_functions_in_file(file)
        assert count == expected_count
    
    @pytest.mark.skipif(
        True,
        reason="Requires compiled tree-sitter grammars"
    )
    def test_file_no_functions(self, js_file_no_functions):
        """Test counting when file has no functions."""
        file, expected_count = js_file_no_functions
        count = count_functions_in_file(file)
        assert count == expected_count
    
    def test_nonexistent_file(self):
        """Test error handling for nonexistent file."""
        with pytest.raises(JSFunctionCountError, match="File not found"):
            count_functions_in_file("nonexistent.js")
    
    def test_directory_path(self, tmp_path):
        """Test error handling for directory path."""
        with pytest.raises(JSFunctionCountError, match="Path is not a file"):
            count_functions_in_file(tmp_path)
    
    def test_non_js_ts_file(self, tmp_path):
        """Test error handling for non-JS/TS file."""
        file = tmp_path / "test.py"
        file.write_text("def foo(): pass")
        with pytest.raises(JSFunctionCountError, match="Not a JavaScript/TypeScript file"):
            count_functions_in_file(file)


class TestCountFunctionsBatch:
    """Tests for batch function counting."""
    
    @pytest.fixture
    def multiple_files(self, tmp_path):
        """Create multiple JS files."""
        files = []
        
        # Simple file
        simple = tmp_path / "simple.js"
        simple.write_text("function foo() { return 1; }")
        files.append(simple)
        
        # File with arrow function
        arrow = tmp_path / "arrow.js"
        arrow.write_text("const bar = () => 2;")
        files.append(arrow)
        
        # Empty file
        empty = tmp_path / "empty.js"
        empty.write_text("")
        files.append(empty)
        
        return files
    
    @pytest.mark.skipif(
        True,
        reason="Requires compiled tree-sitter grammars"
    )
    def test_batch_counting(self, multiple_files):
        """Test batch counting for multiple files."""
        results = count_functions_batch(multiple_files)
        
        assert len(results) == 3
        # Check that all files are present
        for file in multiple_files:
            assert str(file) in results
    
    def test_batch_with_errors(self, tmp_path):
        """Test batch counting handles errors gracefully."""
        # Create one valid file (but will fail without tree-sitter)
        valid = tmp_path / "valid.js"
        valid.write_text("function foo() {}")
        
        # Use one nonexistent file
        invalid = tmp_path / "nonexistent.js"
        
        results = count_functions_batch([valid, invalid])
        
        # Both should have entries
        assert str(valid) in results
        assert str(invalid) in results
        
        # Invalid file should have error
        assert "Error" in str(results[str(invalid)])
    
    def test_batch_empty_list(self):
        """Test batch counting with empty list."""
        results = count_functions_batch([])
        assert results == {}


class TestGetFunctionDetailsFromAST:
    """Tests for getting function details."""
    
    def test_get_function_details(self):
        """Test getting detailed function information."""
        mock_wrapper = Mock(spec=ASTWrapper)
        mock_wrapper.language = 'javascript'
        
        # Create mock CodeNode objects with metadata
        func1 = CodeNode(
            type='function',
            name='foo',
            start_line=1,
            end_line=3,
            source_text='function foo() { return 1; }',
            metadata={'parameters': '', 'async': False}
        )
        func2 = CodeNode(
            type='method',
            name='bar',
            start_line=5,
            end_line=7,
            source_text='bar() { return 2; }',
            metadata={'parameters': '', 'async': False}
        )
        
        mock_wrapper.find_function_definitions.return_value = CodeNodeCollection([func1, func2])
        
        details = get_function_details_from_ast(mock_wrapper)
        
        assert len(details) == 2
        assert details[0]['name'] == 'foo'
        assert details[0]['type'] == 'function'
        assert details[0]['line_number'] == 1
        assert details[0]['end_line'] == 3
        assert details[1]['name'] == 'bar'
        assert details[1]['type'] == 'method'
    
    def test_get_details_no_functions(self):
        """Test getting details when no functions exist."""
        mock_wrapper = Mock(spec=ASTWrapper)
        mock_wrapper.language = 'javascript'
        mock_wrapper.find_function_definitions.return_value = CodeNodeCollection([])
        
        details = get_function_details_from_ast(mock_wrapper)
        assert details == []
    
    def test_invalid_input(self):
        """Test error handling for invalid input."""
        with pytest.raises(JSFunctionCountError, match="must be an ASTWrapper instance"):
            get_function_details_from_ast("not a wrapper")


class TestIntegration:
    """Integration tests with real code."""
    
    @pytest.fixture
    def complex_js_file(self, tmp_path):
        """Create a complex JavaScript file."""
        file = tmp_path / "complex.js"
        content = '''// Complex JavaScript module
function regularFunction(x, y) {
    return x + y;
}

const arrowFunction = (a, b) => {
    return a * b;
};

class Calculator {
    add(x, y) {
        return x + y;
    }
    
    subtract(x, y) {
        return x - y;
    }
    
    static multiply(x, y) {
        return x * y;
    }
}

async function fetchData(url) {
    const response = await fetch(url);
    return response.json();
}

const anonymousFunc = function(value) {
    return value * 2;
};

export default {
    regularFunction,
    arrowFunction,
    Calculator
};
'''
        file.write_text(content)
        # 1 regular + 1 arrow + 3 methods (add, subtract, multiply) + 1 async + 1 anonymous = 7
        return file, 7
    
    @pytest.mark.skipif(
        True,
        reason="Requires compiled tree-sitter grammars"
    )
    def test_complex_javascript_file(self, complex_js_file):
        """Test counting in complex JavaScript file."""
        file, expected_count = complex_js_file
        count = count_functions_in_file(file)
        assert count == expected_count
