"""
Tests for the JavaScript/TypeScript Cyclomatic Complexity Calculator module.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from src.js_complexity import (
    calculate_complexity_ast,
    calculate_complexity_in_file,
    calculate_complexity_batch,
    calculate_per_function_complexity,
    get_complexity_grade,
    JSComplexityError
)
from src.ast_wrapper import ASTWrapper
from src.code_node import CodeNode


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


class TestCalculateComplexityAST:
    """Tests for AST-based complexity calculation."""
    
    def create_mock_node(self, node_type, children=None, text=b''):
        """Helper to create mock tree-sitter nodes."""
        node = Mock()
        node.type = node_type
        node.children = children or []
        node.text = text
        node.is_named = True
        return node
    
    def test_base_complexity(self):
        """Test base complexity for simple code."""
        mock_wrapper = Mock(spec=ASTWrapper)
        mock_wrapper.language = 'javascript'
        
        # Create a simple root node with no decision points
        root = self.create_mock_node('program', [
            self.create_mock_node('expression_statement')
        ])
        mock_wrapper.root_node = root
        
        complexity = calculate_complexity_ast(mock_wrapper)
        assert complexity == 1  # Base complexity
    
    def test_if_statement(self):
        """Test complexity with if statement."""
        mock_wrapper = Mock(spec=ASTWrapper)
        mock_wrapper.language = 'javascript'
        
        # Root with one if statement
        root = self.create_mock_node('program', [
            self.create_mock_node('if_statement')
        ])
        mock_wrapper.root_node = root
        
        complexity = calculate_complexity_ast(mock_wrapper)
        assert complexity == 2  # Base (1) + if (1)
    
    def test_multiple_decision_points(self):
        """Test complexity with multiple decision points."""
        mock_wrapper = Mock(spec=ASTWrapper)
        mock_wrapper.language = 'javascript'
        
        # Multiple decision points
        root = self.create_mock_node('program', [
            self.create_mock_node('if_statement'),
            self.create_mock_node('for_statement'),
            self.create_mock_node('while_statement'),
        ])
        mock_wrapper.root_node = root
        
        complexity = calculate_complexity_ast(mock_wrapper)
        assert complexity == 4  # Base (1) + if (1) + for (1) + while (1)
    
    def test_invalid_input_type(self):
        """Test error handling for invalid input type."""
        with pytest.raises(JSComplexityError, match="must be an ASTWrapper instance"):
            calculate_complexity_ast("not a wrapper")
    
    def test_unsupported_language(self):
        """Test error handling for unsupported language."""
        mock_wrapper = Mock(spec=ASTWrapper)
        mock_wrapper.language = 'python'
        
        with pytest.raises(JSComplexityError, match="Unsupported language"):
            calculate_complexity_ast(mock_wrapper)


class TestCalculateComplexityInFile:
    """Tests for file-based complexity calculation."""
    
    @pytest.fixture
    def simple_js_file(self, tmp_path):
        """Create a simple JavaScript file."""
        file = tmp_path / "simple.js"
        content = """function add(a, b) {
    return a + b;
}
"""
        file.write_text(content)
        return file, 1  # Base complexity only
    
    @pytest.fixture
    def complex_js_file(self, tmp_path):
        """Create a JavaScript file with decision points."""
        file = tmp_path / "complex.js"
        content = """function process(data) {
    if (!data) {
        return null;
    }
    
    for (let item of data) {
        if (item > 0) {
            console.log(item);
        }
    }
    
    return true;
}
"""
        file.write_text(content)
        # Base (1) + if (!data) (1) + for (1) + if (item > 0) (1) = 4
        return file, 4
    
    @pytest.fixture
    def empty_js_file(self, tmp_path):
        """Create an empty JavaScript file."""
        file = tmp_path / "empty.js"
        file.write_text("")
        return file, 1  # Base complexity
    
    @pytest.mark.skipif(
        True,
        reason="Requires compiled tree-sitter grammars"
    )
    def test_simple_file(self, simple_js_file):
        """Test complexity calculation for simple file."""
        file, expected = simple_js_file
        complexity = calculate_complexity_in_file(file)
        assert complexity == expected
    
    @pytest.mark.skipif(
        True,
        reason="Requires compiled tree-sitter grammars"
    )
    def test_complex_file(self, complex_js_file):
        """Test complexity calculation for complex file."""
        file, expected = complex_js_file
        complexity = calculate_complexity_in_file(file)
        assert complexity == expected
    
    @pytest.mark.skipif(
        True,
        reason="Requires compiled tree-sitter grammars"
    )
    def test_empty_file(self, empty_js_file):
        """Test complexity for empty file."""
        file, expected = empty_js_file
        complexity = calculate_complexity_in_file(file)
        assert complexity == expected
    
    def test_nonexistent_file(self):
        """Test error handling for nonexistent file."""
        with pytest.raises(JSComplexityError, match="File not found"):
            calculate_complexity_in_file("nonexistent.js")
    
    def test_directory_path(self, tmp_path):
        """Test error handling for directory path."""
        with pytest.raises(JSComplexityError, match="Path is not a file"):
            calculate_complexity_in_file(tmp_path)
    
    def test_non_js_ts_file(self, tmp_path):
        """Test error handling for non-JS/TS file."""
        file = tmp_path / "test.py"
        file.write_text("def foo(): pass")
        with pytest.raises(JSComplexityError, match="Not a JavaScript/TypeScript file"):
            calculate_complexity_in_file(file)


class TestCalculateComplexityBatch:
    """Tests for batch complexity calculation."""
    
    @pytest.fixture
    def multiple_files(self, tmp_path):
        """Create multiple JS files."""
        files = []
        
        # Simple file
        simple = tmp_path / "simple.js"
        simple.write_text("const x = 42;")
        files.append(simple)
        
        # File with if
        with_if = tmp_path / "with_if.js"
        with_if.write_text("if (true) { console.log('yes'); }")
        files.append(with_if)
        
        # Empty file
        empty = tmp_path / "empty.js"
        empty.write_text("")
        files.append(empty)
        
        return files
    
    @pytest.mark.skipif(
        True,
        reason="Requires compiled tree-sitter grammars"
    )
    def test_batch_calculation(self, multiple_files):
        """Test batch complexity calculation."""
        results = calculate_complexity_batch(multiple_files)
        
        assert len(results) == 3
        # All files should have entries
        for file in multiple_files:
            assert str(file) in results
    
    def test_batch_with_errors(self, tmp_path):
        """Test batch calculation handles errors gracefully."""
        # Create one valid file (but will fail without tree-sitter)
        valid = tmp_path / "valid.js"
        valid.write_text("const x = 1;")
        
        # Use one nonexistent file
        invalid = tmp_path / "nonexistent.js"
        
        results = calculate_complexity_batch([valid, invalid])
        
        # Both should have entries
        assert str(valid) in results
        assert str(invalid) in results
        
        # Invalid file should have error
        assert "Error" in str(results[str(invalid)])
    
    def test_batch_empty_list(self):
        """Test batch calculation with empty list."""
        results = calculate_complexity_batch([])
        assert results == {}


class TestCalculatePerFunctionComplexity:
    """Tests for per-function complexity calculation."""
    
    def test_per_function_complexity(self):
        """Test calculating complexity for each function."""
        mock_wrapper = Mock(spec=ASTWrapper)
        mock_wrapper.language = 'javascript'
        
        # Create mock function nodes
        func1_node = Mock()
        func1_node.type = 'function_declaration'
        func1_node.children = []  # Simple function, no decision points
        
        func2_node = Mock()
        func2_node.type = 'function_declaration'
        func2_child = Mock()
        func2_child.type = 'if_statement'
        func2_child.children = []
        func2_node.children = [func2_child]  # Function with if statement
        
        # Create CodeNode objects
        func1 = CodeNode(
            type='function',
            name='simple',
            start_line=1,
            end_line=3,
            source_text='function simple() { return 1; }',
            node=func1_node
        )
        
        func2 = CodeNode(
            type='function',
            name='complex',
            start_line=5,
            end_line=10,
            source_text='function complex(x) { if (x) return 1; }',
            node=func2_node
        )
        
        # Mock find_function_definitions
        from code_node import CodeNodeCollection
        mock_wrapper.find_function_definitions.return_value = CodeNodeCollection([func1, func2])
        
        results = calculate_per_function_complexity(mock_wrapper)
        
        assert len(results) == 2
        assert results[0]['name'] == 'simple'
        assert results[0]['complexity'] == 1  # Base only
        assert results[1]['name'] == 'complex'
        assert results[1]['complexity'] == 2  # Base + if
    
    def test_per_function_no_functions(self):
        """Test per-function complexity when no functions exist."""
        mock_wrapper = Mock(spec=ASTWrapper)
        mock_wrapper.language = 'javascript'
        
        from code_node import CodeNodeCollection
        mock_wrapper.find_function_definitions.return_value = CodeNodeCollection([])
        
        results = calculate_per_function_complexity(mock_wrapper)
        assert results == []
    
    def test_invalid_input(self):
        """Test error handling for invalid input."""
        with pytest.raises(JSComplexityError, match="must be an ASTWrapper instance"):
            calculate_per_function_complexity("not a wrapper")


class TestIntegration:
    """Integration tests with real code."""
    
    @pytest.fixture
    def complex_js_file(self, tmp_path):
        """Create a complex JavaScript file."""
        file = tmp_path / "complex.js"
        content = '''function complexFunction(data) {
    // Base: 1
    if (!data) {  // +1
        return null;
    }
    
    const results = [];
    for (let i = 0; i < data.length; i++) {  // +1
        const item = data[i];
        
        if (item.active && item.value > 0) {  // +1 for if, +1 for &&
            results.push(item.value * 2);
        } else if (item.value < 0) {  // +1 for else if
            results.push(0);
        }
    }
    
    return results.length > 0 ? results : null;  // +1 for ternary
}

function simpleFunction() {
    return 42;  // Base: 1
}
'''
        file.write_text(content)
        # complexFunction: 1 + 1 + 1 + 1 + 1 + 1 + 1 = 7
        # simpleFunction: 1
        # Total: 8
        return file, 8, 7, 1
    
    @pytest.mark.skipif(
        True,
        reason="Requires compiled tree-sitter grammars"
    )
    def test_complex_file_total(self, complex_js_file):
        """Test total complexity calculation."""
        file, expected_total, _, _ = complex_js_file
        complexity = calculate_complexity_in_file(file)
        assert complexity == expected_total
    
    @pytest.mark.skipif(
        True,
        reason="Requires compiled tree-sitter grammars"
    )
    def test_complex_file_per_function(self, complex_js_file):
        """Test per-function complexity calculation."""
        file, _, expected_complex, expected_simple = complex_js_file
        
        # Parse file
        with open(file, 'r') as f:
            code = f.read()
        wrapper = ASTWrapper(code, file)
        
        results = calculate_per_function_complexity(wrapper)
        
        assert len(results) == 2
        # Find each function and check its complexity
        complex_func = next(f for f in results if f['name'] == 'complexFunction')
        simple_func = next(f for f in results if f['name'] == 'simpleFunction')
        
        assert complex_func['complexity'] == expected_complex
        assert simple_func['complexity'] == expected_simple
