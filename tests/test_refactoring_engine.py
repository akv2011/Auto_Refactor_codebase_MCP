"""
Tests for the RefactoringEngine class.
"""

import pytest
import tempfile
from pathlib import Path
from src.refactoring_engine import (
    RefactoringEngine,
    RefactoringError,
    UnsupportedOperationError,
    RefactoringValidationError,
    ParsingError,
    CodeGenerationError
)
from src.parser_setup import TreeSitterSetup


@pytest.fixture(scope="session", autouse=True)
def setup_tree_sitter_grammars():
    """
    Set up tree-sitter language packages once for all tests.
    This is a session-scoped fixture that runs before any tests.
    """
    setup = TreeSitterSetup()
    
    # Ensure language packages are installed
    try:
        # Ensure Python and JavaScript language packages are installed
        setup.ensure_language_installed('python')
        setup.ensure_language_installed('javascript')
    except Exception as e:
        pytest.skip(f"Could not install tree-sitter language packages: {e}")


class TestRefactoringEngineInit:
    """Tests for RefactoringEngine initialization."""
    
    def test_initialization(self):
        """Test RefactoringEngine initialization."""
        engine = RefactoringEngine()
        assert engine is not None
    
    def test_has_operation_handlers(self):
        """Test that operation handlers are configured."""
        engine = RefactoringEngine()
        assert hasattr(engine, '_operation_handlers')
        assert isinstance(engine._operation_handlers, dict)
        assert len(engine._operation_handlers) > 0


class TestSupportedOperations:
    """Tests for checking supported operations."""
    
    def test_get_supported_operations(self):
        """Test getting list of supported operations."""
        engine = RefactoringEngine()
        operations = engine.get_supported_operations()
        
        assert isinstance(operations, list)
        assert len(operations) > 0
        assert 'extract_function' in operations
        assert 'split_file' in operations
        assert 'apply_diff' in operations
    
    def test_is_operation_supported_true(self):
        """Test checking if supported operation exists."""
        engine = RefactoringEngine()
        
        assert engine.is_operation_supported('extract_function') is True
        assert engine.is_operation_supported('split_file') is True
        assert engine.is_operation_supported('apply_diff') is True
    
    def test_is_operation_supported_false(self):
        """Test checking if unsupported operation exists."""
        engine = RefactoringEngine()
        
        assert engine.is_operation_supported('nonexistent') is False
        assert engine.is_operation_supported('invalid_op') is False


class TestOperationDispatcher:
    """Tests for the operation dispatcher."""
    
    def test_apply_requires_dict(self):
        """Test that apply requires a dictionary."""
        engine = RefactoringEngine()
        
        with pytest.raises(RefactoringValidationError, match="must be a dictionary"):
            engine.apply("not a dict")
        
        with pytest.raises(RefactoringValidationError, match="must be a dictionary"):
            engine.apply(None)
    
    def test_apply_requires_type_field(self):
        """Test that operation_details must have 'type' field."""
        engine = RefactoringEngine()
        
        with pytest.raises(RefactoringValidationError, match="must include 'type' field"):
            engine.apply({})
        
        with pytest.raises(RefactoringValidationError, match="must include 'type' field"):
            engine.apply({'source_file': 'test.py'})
    
    def test_apply_unsupported_operation(self):
        """Test error for unsupported operation type."""
        engine = RefactoringEngine()
        
        with pytest.raises(UnsupportedOperationError, match="Unsupported operation type"):
            engine.apply({'type': 'nonexistent_operation'})
        
        with pytest.raises(UnsupportedOperationError, match="Unsupported operation type"):
            engine.apply({'type': 'invalid'})
    
    def test_dispatcher_calls_extract_function(self):
        """Test that extract_function operation is dispatched correctly."""
        engine = RefactoringEngine()
        
        operation = {
            'type': 'extract_function',
            'source_file': 'nonexistent.py',
            'target_file': 'helpers.py',
            'function_name': 'helper'
        }
        
        # Should call the handler (which will fail due to nonexistent file)
        result = engine.apply(operation)
        
        # Should return error result (file not found)
        assert result['status'] == 'error'
        assert 'Failed to extract function' in result['error']
    
    def test_dispatcher_calls_split_file(self):
        """Test that split_file operation is dispatched correctly."""
        engine = RefactoringEngine()
        
        operation = {
            'type': 'split_file',
            'source_file': 'large.py'
        }
        
        result = engine.apply(operation)
        assert result['status'] == 'error'
        assert 'not yet implemented' in result['error']
    
    def test_dispatcher_calls_apply_diff(self):
        """Test that apply_diff operation is dispatched correctly."""
        engine = RefactoringEngine()
        
        operation = {
            'type': 'apply_diff',
            'file': 'test.py',
            'diff': 'some diff content'
        }
        
        result = engine.apply(operation)
        assert result['status'] == 'error'
        assert 'not yet implemented' in result['error']
    
    def test_dispatcher_calls_rename_symbol(self):
        """Test that rename_symbol operation is dispatched correctly."""
        engine = RefactoringEngine()
        
        operation = {
            'type': 'rename_symbol',
            'file': 'test.py',
            'old_name': 'old_func',
            'new_name': 'new_func'
        }
        
        result = engine.apply(operation)
        assert result['status'] == 'error'
        assert 'not yet implemented' in result['error']
    
    def test_dispatcher_calls_inline_function(self):
        """Test that inline_function operation is dispatched correctly."""
        engine = RefactoringEngine()
        
        operation = {
            'type': 'inline_function',
            'file': 'test.py',
            'function_name': 'helper'
        }
        
        result = engine.apply(operation)
        assert result['status'] == 'error'
        assert 'not yet implemented' in result['error']


class TestErrorHandling:
    """Tests for error handling in the refactoring engine."""
    
    def test_error_result_structure(self):
        """Test that error results have correct structure."""
        engine = RefactoringEngine()
        
        operation = {
            'type': 'extract_function',
            'source_file': 'test.py'
        }
        
        result = engine.apply(operation)
        
        # Check result structure
        assert 'status' in result
        assert 'error' in result
        assert 'modified_files' in result
        assert 'created_files' in result
        assert 'message' in result
        
        # Check values
        assert result['status'] == 'error'
        assert isinstance(result['error'], str)
        assert isinstance(result['modified_files'], list)
        assert isinstance(result['created_files'], list)
        assert isinstance(result['message'], str)
    
    def test_unsupported_operation_error_message(self):
        """Test that unsupported operation error includes helpful message."""
        engine = RefactoringEngine()
        
        try:
            engine.apply({'type': 'invalid_op'})
        except UnsupportedOperationError as e:
            error_msg = str(e)
            assert 'Unsupported operation type' in error_msg
            assert 'invalid_op' in error_msg
            assert 'Supported operations:' in error_msg
            # Should list at least some supported operations
            assert 'extract_function' in error_msg


class TestOperationHandlers:
    """Tests for individual operation handler methods."""
    
    def test_extract_function_handler_requires_valid_files(self, tmp_path):
        """Test that extract_function handler requires valid files."""
        engine = RefactoringEngine()
        
        operation = {
            'type': 'extract_function',
            'source_file': 'nonexistent.py',
            'target_file': 'helpers.py',
            'function_name': 'helper'
        }
        
        # Should raise RefactoringError for nonexistent file
        with pytest.raises(RefactoringError, match="Failed to extract function"):
            engine._handle_extract_function(operation)
    
    def test_split_file_handler_not_implemented(self):
        """Test that split_file handler raises NotImplementedError."""
        engine = RefactoringEngine()
        
        with pytest.raises(NotImplementedError):
            engine._handle_split_file({})
    
    def test_apply_diff_handler_not_implemented(self):
        """Test that apply_diff handler raises NotImplementedError."""
        engine = RefactoringEngine()
        
        with pytest.raises(NotImplementedError):
            engine._handle_apply_diff({})
    
    def test_rename_symbol_handler_not_implemented(self):
        """Test that rename_symbol handler raises NotImplementedError."""
        engine = RefactoringEngine()
        
        with pytest.raises(NotImplementedError):
            engine._handle_rename_symbol({})
    
    def test_inline_function_handler_not_implemented(self):
        """Test that inline_function handler raises NotImplementedError."""
        engine = RefactoringEngine()
        
        with pytest.raises(NotImplementedError):
            engine._handle_inline_function({})


class TestIntegration:
    """Integration tests for RefactoringEngine."""
    
    def test_multiple_operations_on_same_engine(self):
        """Test that the same engine can handle multiple operations."""
        engine = RefactoringEngine()
        
        # Try different operations
        ops = [
            {'type': 'extract_function', 'source_file': 'a.py'},  # Missing params
            {'type': 'split_file', 'source_file': 'b.py'},  # Not implemented
            {'type': 'apply_diff', 'file': 'c.py'}  # Not implemented
        ]
        
        for op in ops:
            result = engine.apply(op)
            # All should fail gracefully
            assert result['status'] == 'error'
            # Different error messages depending on the operation
            assert 'error' in result
    
    def test_operation_type_case_sensitive(self):
        """Test that operation types are case-sensitive."""
        engine = RefactoringEngine()
        
        # Correct case
        assert engine.is_operation_supported('extract_function')
        
        # Wrong case
        assert not engine.is_operation_supported('Extract_Function')
        assert not engine.is_operation_supported('EXTRACT_FUNCTION')


class TestASTParsingAndGeneration:
    """Tests for AST parsing and code generation methods."""
    
    def test_parse_file_to_ast_python(self):
        """Test parsing a Python file to AST."""
        engine = RefactoringEngine()
        
        # Create temporary Python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def hello():
    print("Hello, World!")
    
def goodbye():
    print("Goodbye!")
""")
            temp_file = f.name
        
        try:
            # Parse the file
            ast = engine._parse_file_to_ast(temp_file)
            
            # Verify AST is not None
            assert ast is not None
            
            # Verify it has a root node
            assert hasattr(ast, 'root_node')
            assert ast.root_node is not None
            
            # Verify root node type for Python is 'module'
            assert ast.root_node.type == 'module'
            
            # Verify no parsing errors
            assert not ast.root_node.has_error
            
        finally:
            # Clean up
            Path(temp_file).unlink()
    
    def test_parse_file_to_ast_javascript(self):
        """Test parsing a JavaScript file to AST."""
        engine = RefactoringEngine()
        
        # Create temporary JavaScript file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write("""
function hello() {
    console.log("Hello, World!");
}

const goodbye = () => {
    console.log("Goodbye!");
};
""")
            temp_file = f.name
        
        try:
            # Parse the file
            ast = engine._parse_file_to_ast(temp_file)
            
            # Verify AST is not None
            assert ast is not None
            assert ast.root_node is not None
            
            # Verify root node type for JavaScript is 'program'
            assert ast.root_node.type == 'program'
            
            # Verify no parsing errors
            assert not ast.root_node.has_error
            
        finally:
            # Clean up
            Path(temp_file).unlink()
    
    def test_parse_file_to_ast_file_not_found(self):
        """Test parsing a non-existent file raises ParsingError."""
        engine = RefactoringEngine()
        
        with pytest.raises(ParsingError, match="File not found"):
            engine._parse_file_to_ast('/nonexistent/file.py')
    
    def test_parse_file_to_ast_directory_not_file(self):
        """Test parsing a directory raises ParsingError."""
        engine = RefactoringEngine()
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ParsingError, match="Path is not a file"):
                engine._parse_file_to_ast(temp_dir)
    
    def test_parse_file_to_ast_unsupported_extension(self):
        """Test parsing unsupported file type raises ParsingError."""
        engine = RefactoringEngine()
        
        # Create temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write("some content")
            temp_file = f.name
        
        try:
            with pytest.raises(ParsingError, match="Cannot parse"):
                engine._parse_file_to_ast(temp_file)
        finally:
            Path(temp_file).unlink()
    
    def test_parse_file_to_ast_syntax_error(self):
        """Test parsing file with syntax errors raises ParsingError."""
        engine = RefactoringEngine()
        
        # Create temporary Python file with syntax errors
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def invalid syntax here
    print("This is broken")
""")
            temp_file = f.name
        
        try:
            with pytest.raises(ParsingError, match="Syntax errors detected"):
                engine._parse_file_to_ast(temp_file)
        finally:
            Path(temp_file).unlink()
    
    def test_generate_code_from_ast_with_source(self):
        """Test generating code from AST with original source."""
        engine = RefactoringEngine()
        
        # Create sample Python file
        source_code = """def hello():
    print("Hello, World!")
    
def goodbye():
    print("Goodbye!")
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source_code)
            temp_file = f.name
        
        try:
            # Parse the file
            with open(temp_file, 'rb') as f:
                original_bytes = f.read()
            
            ast = engine._parse_file_to_ast(temp_file)
            
            # Generate code from AST
            generated_code = engine._generate_code_from_ast(ast, original_bytes)
            
            # Verify generated code is not None
            assert generated_code is not None
            assert isinstance(generated_code, str)
            
            # Verify it's semantically identical (same content)
            # Normalize line endings for comparison (Windows vs Unix)
            generated_normalized = generated_code.replace('\r\n', '\n').strip()
            source_normalized = source_code.replace('\r\n', '\n').strip()
            assert generated_normalized == source_normalized
            
        finally:
            Path(temp_file).unlink()
    
    def test_generate_code_from_ast_without_source_fails(self):
        """Test that generating code without original source raises error."""
        engine = RefactoringEngine()
        
        # Create sample Python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def hello():\n    pass\n")
            temp_file = f.name
        
        try:
            # Parse the file
            ast = engine._parse_file_to_ast(temp_file)
            
            # Try to generate code without original source
            with pytest.raises(CodeGenerationError, match="Cannot generate code without original source"):
                engine._generate_code_from_ast(ast, None)
            
        finally:
            Path(temp_file).unlink()
    
    def test_generate_code_from_ast_none_ast(self):
        """Test that generating code from None AST raises error."""
        engine = RefactoringEngine()
        
        with pytest.raises(CodeGenerationError, match="AST is None"):
            engine._generate_code_from_ast(None)
    
    def test_generate_code_from_ast_with_string_source(self):
        """Test generating code with source as string (converts to bytes)."""
        engine = RefactoringEngine()
        
        source_code = "def test():\n    pass\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source_code)
            temp_file = f.name
        
        try:
            ast = engine._parse_file_to_ast(temp_file)
            
            # Pass source as string
            generated_code = engine._generate_code_from_ast(ast, source_code)
            
            assert generated_code.strip() == source_code.strip()
            
        finally:
            Path(temp_file).unlink()
    
    def test_roundtrip_parse_and_generate(self):
        """Test roundtrip: parse -> generate -> parse produces same AST structure."""
        engine = RefactoringEngine()
        
        source_code = """class MyClass:
    def __init__(self, name):
        self.name = name
    
    def greet(self):
        print(f"Hello, {self.name}!")

def main():
    obj = MyClass("World")
    obj.greet()

if __name__ == "__main__":
    main()
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source_code)
            temp_file = f.name
        
        try:
            # First parse
            with open(temp_file, 'rb') as f:
                original_bytes = f.read()
            
            ast1 = engine._parse_file_to_ast(temp_file)
            
            # Generate code
            generated_code = engine._generate_code_from_ast(ast1, original_bytes)
            
            # Write generated code to new file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(generated_code)
                temp_file2 = f.name
            
            try:
                # Parse again
                ast2 = engine._parse_file_to_ast(temp_file2)
                
                # Verify both ASTs have same root type
                assert ast1.root_node.type == ast2.root_node.type
                
                # Verify both have no errors
                assert not ast1.root_node.has_error
                assert not ast2.root_node.has_error
                
            finally:
                Path(temp_file2).unlink()
            
        finally:
            Path(temp_file).unlink()
    
    def test_parser_factory_initialization(self):
        """Test that RefactoringEngine initializes parser factory."""
        engine = RefactoringEngine()
        
        assert hasattr(engine, '_parser_factory')
        assert engine._parser_factory is not None
    
    def test_parse_multiple_files_different_languages(self):
        """Test parsing multiple files with different languages."""
        engine = RefactoringEngine()
        
        # Python file
        py_code = "def test():\n    pass\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(py_code)
            py_file = f.name
        
        # JavaScript file
        js_code = "function test() {\n    console.log('test');\n}\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(js_code)
            js_file = f.name
        
        try:
            # Parse both
            py_ast = engine._parse_file_to_ast(py_file)
            js_ast = engine._parse_file_to_ast(js_file)
            
            # Verify different root types
            assert py_ast.root_node.type == 'module'  # Python
            assert js_ast.root_node.type == 'program'  # JavaScript
            
            # Both should be valid
            assert not py_ast.root_node.has_error
            assert not js_ast.root_node.has_error
            
        finally:
            Path(py_file).unlink()
            Path(js_file).unlink()
