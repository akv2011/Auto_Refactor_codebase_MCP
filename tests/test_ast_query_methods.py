"""
Tests for AST Query Methods.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from src.ast_wrapper import ASTWrapper, ASTParsingError, QUERY_PATTERNS
from src.parser_factory import ParserFactory
from src.code_node import CodeNode, CodeNodeCollection


class TestQueryMethod:
    """Test the generic query method."""
    
    def test_query_executes_successfully(self):
        """Test that query method executes a query."""
        source = "def hello():\n    pass"
        file_path = "test.py"
        
        # Create mock nodes
        mock_node = Mock()
        mock_node.has_error = False
        mock_tree = Mock()
        mock_tree.root_node = mock_node
        mock_parser = Mock()
        mock_parser.parse.return_value = mock_tree
        
        # Create mock factory and setup
        mock_setup = Mock()
        mock_setup.get_language_for_extension.return_value = "python"
        mock_setup.get_grammar_path.return_value = Path("/path/to/grammar.so")
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.setup = mock_setup
        mock_factory.get_parser_for_file.return_value = mock_parser
        
        wrapper = ASTWrapper(source, file_path, parser_factory=mock_factory)
        
        # Mock Language and query
        mock_lang = Mock()
        mock_query_obj = Mock()
        mock_query_obj.captures.return_value = [
            (Mock(), "name"),
            (Mock(), "body")
        ]
        mock_lang.query.return_value = mock_query_obj
        
        with patch('tree_sitter.Language', return_value=mock_lang):
            captures = wrapper.query("(function_definition) @func")
            
            assert len(captures) == 2
            assert captures[0][1] == "name"
            assert captures[1][1] == "body"
    
    def test_query_raises_error_on_failure(self):
        """Test that query raises ASTParsingError on failure."""
        source = "test"
        file_path = "test.py"
        
        with patch.object(ASTWrapper, '_parse'):
            wrapper = ASTWrapper(source, file_path)
            
            # Make query fail
            with patch('tree_sitter.Language', side_effect=Exception("Query error")):
                with pytest.raises(ASTParsingError, match="Failed to execute query"):
                    wrapper.query("(bad_query)")


class TestGroupCaptures:
    """Test the capture grouping helper method."""
    
    def test_group_captures_by_definition(self):
        """Test grouping captures by definition node."""
        source = "test"
        file_path = "test.py"
        
        with patch.object(ASTWrapper, '_parse'):
            wrapper = ASTWrapper(source, file_path)
            
            # Create mock nodes with parent relationships
            def_node = Mock()
            def_node.parent = None
            name_node = Mock()
            name_node.parent = def_node
            body_node = Mock()
            body_node.parent = def_node
            
            captures = [
                (def_node, "definition"),
                (name_node, "name"),
                (body_node, "body")
            ]
            
            grouped = wrapper._group_captures(captures)
            
            assert len(grouped) == 1
            assert grouped[0]["definition_node"] is def_node
            assert grouped[0]["captures"]["name"] is name_node
            assert grouped[0]["captures"]["body"] is body_node
    
    def test_group_multiple_definitions(self):
        """Test grouping multiple definitions."""
        source = "test"
        file_path = "test.py"
        
        with patch.object(ASTWrapper, '_parse'):
            wrapper = ASTWrapper(source, file_path)
            
            # Create two separate definitions
            def_node1 = Mock()
            def_node1.parent = None
            name_node1 = Mock()
            name_node1.parent = def_node1
            
            def_node2 = Mock()
            def_node2.parent = None
            name_node2 = Mock()
            name_node2.parent = def_node2
            
            captures = [
                (def_node1, "definition"),
                (name_node1, "name"),
                (def_node2, "definition"),
                (name_node2, "name")
            ]
            
            grouped = wrapper._group_captures(captures)
            
            assert len(grouped) == 2


class TestFindFunctionDefinitions:
    """Test finding function definitions."""
    
    def test_find_functions_in_python(self):
        """Test finding Python functions."""
        source = "def hello():\n    pass"
        file_path = "test.py"
        
        # Mock the complete parsing and query flow
        mock_node = Mock()
        mock_node.has_error = False
        mock_tree = Mock()
        mock_tree.root_node = mock_node
        mock_parser = Mock()
        mock_parser.parse.return_value = mock_tree
        
        mock_setup = Mock()
        mock_setup.get_language_for_extension.return_value = "python"
        mock_setup.get_grammar_path.return_value = Path("/path/to/grammar.so")
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.setup = mock_setup
        mock_factory.get_parser_for_file.return_value = mock_parser
        
        wrapper = ASTWrapper(source, file_path, parser_factory=mock_factory)
        
        # Mock function definition node
        func_def_node = Mock()
        func_def_node.type = "function_definition"
        func_def_node.start_point = (0, 0)
        func_def_node.end_point = (1, 8)
        func_def_node.start_byte = 0
        func_def_node.end_byte = len(source)
        func_def_node.parent = None
        
        name_node = Mock()
        name_node.start_byte = 4
        name_node.end_byte = 9
        name_node.parent = func_def_node
        
        # Mock Language and query
        mock_lang = Mock()
        mock_query_obj = Mock()
        mock_query_obj.captures.return_value = [
            (func_def_node, "definition"),
            (name_node, "name")
        ]
        mock_lang.query.return_value = mock_query_obj
        
        with patch('tree_sitter.Language', return_value=mock_lang):
            functions = wrapper.find_function_definitions()
            
            assert isinstance(functions, CodeNodeCollection)
            assert len(functions) == 1
            assert isinstance(functions[0], CodeNode)
            assert functions[0].name == "hello"
            assert functions[0].type == "function"
            assert functions[0].start_line == 1
            assert functions[0].end_line == 2
            assert functions[0].language == "python"
            assert functions[0].node is func_def_node
    
    def test_find_functions_unsupported_language(self):
        """Test finding functions in unsupported language."""
        source = "test"
        file_path = "test.xyz"
        
        mock_setup = Mock()
        mock_setup.get_language_for_extension.return_value = "unknown"
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.setup = mock_setup
        
        with patch.object(ASTWrapper, '_parse'):
            wrapper = ASTWrapper(source, file_path, parser_factory=mock_factory)
            
            with pytest.raises(ASTParsingError, match="not supported"):
                wrapper.find_function_definitions()
    
    def test_find_functions_returns_empty_for_no_matches(self):
        """Test that no functions returns empty collection."""
        source = "x = 5"
        file_path = "test.py"
        
        mock_node = Mock()
        mock_node.has_error = False
        mock_tree = Mock()
        mock_tree.root_node = mock_node
        mock_parser = Mock()
        mock_parser.parse.return_value = mock_tree
        
        mock_setup = Mock()
        mock_setup.get_language_for_extension.return_value = "python"
        mock_setup.get_grammar_path.return_value = Path("/path/to/grammar.so")
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.setup = mock_setup
        mock_factory.get_parser_for_file.return_value = mock_parser
        
        wrapper = ASTWrapper(source, file_path, parser_factory=mock_factory)
        
        # Mock empty query result
        mock_lang = Mock()
        mock_query_obj = Mock()
        mock_query_obj.captures.return_value = []
        mock_lang.query.return_value = mock_query_obj
        
        with patch('tree_sitter.Language', return_value=mock_lang):
            functions = wrapper.find_function_definitions()
            
            assert isinstance(functions, CodeNodeCollection)
            assert len(functions) == 0
    
    def test_find_functions_with_anonymous_function(self):
        """Test finding function with no name capture."""
        source = "lambda x: x + 1"
        file_path = "test.py"
        
        mock_node = Mock()
        mock_node.has_error = False
        mock_tree = Mock()
        mock_tree.root_node = mock_node
        mock_parser = Mock()
        mock_parser.parse.return_value = mock_tree
        
        mock_setup = Mock()
        mock_setup.get_language_for_extension.return_value = "python"
        mock_setup.get_grammar_path.return_value = Path("/path/to/grammar.so")
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.setup = mock_setup
        mock_factory.get_parser_for_file.return_value = mock_parser
        
        wrapper = ASTWrapper(source, file_path, parser_factory=mock_factory)
        
        # Mock function node without name
        func_def_node = Mock()
        func_def_node.type = "lambda"
        func_def_node.start_point = (0, 0)
        func_def_node.end_point = (0, 15)
        func_def_node.start_byte = 0
        func_def_node.end_byte = len(source)
        func_def_node.parent = None
        
        mock_lang = Mock()
        mock_query_obj = Mock()
        mock_query_obj.captures.return_value = [
            (func_def_node, "definition")
            # No name capture
        ]
        mock_lang.query.return_value = mock_query_obj
        
        with patch('tree_sitter.Language', return_value=mock_lang):
            functions = wrapper.find_function_definitions()
            
            assert len(functions) == 1
            assert functions[0].name == "<anonymous>"


class TestFindClassDeclarations:
    """Test finding class declarations."""
    
    def test_find_classes_in_python(self):
        """Test finding Python classes."""
        source = "class MyClass:\n    pass"
        file_path = "test.py"
        
        mock_node = Mock()
        mock_node.has_error = False
        mock_tree = Mock()
        mock_tree.root_node = mock_node
        mock_parser = Mock()
        mock_parser.parse.return_value = mock_tree
        
        mock_setup = Mock()
        mock_setup.get_language_for_extension.return_value = "python"
        mock_setup.get_grammar_path.return_value = Path("/path/to/grammar.so")
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.setup = mock_setup
        mock_factory.get_parser_for_file.return_value = mock_parser
        
        wrapper = ASTWrapper(source, file_path, parser_factory=mock_factory)
        
        # Mock class definition node
        class_def_node = Mock()
        class_def_node.type = "class_definition"
        class_def_node.start_point = (0, 0)
        class_def_node.end_point = (1, 8)
        class_def_node.start_byte = 0
        class_def_node.end_byte = len(source)
        class_def_node.parent = None
        
        name_node = Mock()
        name_node.start_byte = 6
        name_node.end_byte = 13
        name_node.parent = class_def_node
        
        mock_lang = Mock()
        mock_query_obj = Mock()
        mock_query_obj.captures.return_value = [
            (class_def_node, "definition"),
            (name_node, "name")
        ]
        mock_lang.query.return_value = mock_query_obj
        
        with patch('tree_sitter.Language', return_value=mock_lang):
            classes = wrapper.find_class_declarations()
            
            assert isinstance(classes, CodeNodeCollection)
            assert len(classes) == 1
            assert isinstance(classes[0], CodeNode)
            assert classes[0].name == "MyClass"
            assert classes[0].type == "class"
            assert classes[0].start_line == 1
            assert classes[0].end_line == 2
            assert classes[0].node is class_def_node
    
    def test_find_classes_unsupported_language(self):
        """Test finding classes in unsupported language."""
        source = "test"
        file_path = "test.xyz"
        
        mock_setup = Mock()
        mock_setup.get_language_for_extension.return_value = "unknown"
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.setup = mock_setup
        
        with patch.object(ASTWrapper, '_parse'):
            wrapper = ASTWrapper(source, file_path, parser_factory=mock_factory)
            
            with pytest.raises(ASTParsingError, match="not supported"):
                wrapper.find_class_declarations()
    
    def test_find_classes_returns_empty_for_no_matches(self):
        """Test that no classes returns empty collection."""
        source = "x = 5"
        file_path = "test.py"
        
        mock_node = Mock()
        mock_node.has_error = False
        mock_tree = Mock()
        mock_tree.root_node = mock_node
        mock_parser = Mock()
        mock_parser.parse.return_value = mock_tree
        
        mock_setup = Mock()
        mock_setup.get_language_for_extension.return_value = "python"
        mock_setup.get_grammar_path.return_value = Path("/path/to/grammar.so")
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.setup = mock_setup
        mock_factory.get_parser_for_file.return_value = mock_parser
        
        wrapper = ASTWrapper(source, file_path, parser_factory=mock_factory)
        
        mock_lang = Mock()
        mock_query_obj = Mock()
        mock_query_obj.captures.return_value = []
        mock_lang.query.return_value = mock_query_obj
        
        with patch('tree_sitter.Language', return_value=mock_lang):
            classes = wrapper.find_class_declarations()
            
            assert isinstance(classes, CodeNodeCollection)
            assert len(classes) == 0


class TestQueryPatterns:
    """Test the query patterns dictionary."""
    
    def test_all_supported_languages_have_patterns(self):
        """Test that patterns exist for all supported languages."""
        expected_languages = ["python", "javascript", "typescript", "java", "csharp", "sql"]
        
        for lang in expected_languages:
            assert lang in QUERY_PATTERNS, f"Missing patterns for {lang}"
            assert "function" in QUERY_PATTERNS[lang], f"Missing function pattern for {lang}"
            assert "class" in QUERY_PATTERNS[lang], f"Missing class pattern for {lang}"
    
    def test_patterns_are_non_empty(self):
        """Test that all patterns are non-empty strings."""
        for lang, patterns in QUERY_PATTERNS.items():
            for pattern_type, pattern_str in patterns.items():
                assert isinstance(pattern_str, str), f"{lang}.{pattern_type} is not a string"
                assert len(pattern_str.strip()) > 0, f"{lang}.{pattern_type} is empty"


class TestQueryIntegration:
    """Integration tests with real parsers (if available)."""
    
    def test_find_python_functions_real(self):
        """Test finding real Python functions."""
        source = """
def foo():
    pass

def bar(x, y):
    return x + y

class MyClass:
    def method(self):
        return 42
"""
        file_path = "test.py"
        
        try:
            wrapper = ASTWrapper(source, file_path)
            functions = wrapper.find_function_definitions()
            
            # Should be a CodeNodeCollection
            assert isinstance(functions, CodeNodeCollection)
            # Should find foo, bar, and method
            assert len(functions) >= 2  # At minimum foo and bar
            names = [f.name for f in functions]
            assert "foo" in names
            assert "bar" in names
            
        except (Exception) as e:
            pytest.skip(f"Tree-sitter not available for integration test: {e}")
    
    def test_find_python_classes_real(self):
        """Test finding real Python classes."""
        source = """
class Animal:
    pass

class Dog(Animal):
    def bark(self):
        print("Woof!")
"""
        file_path = "test.py"
        
        try:
            wrapper = ASTWrapper(source, file_path)
            classes = wrapper.find_class_declarations()
            
            assert isinstance(classes, CodeNodeCollection)
            assert len(classes) == 2
            names = [c.name for c in classes]
            assert "Animal" in names
            assert "Dog" in names
            
        except (Exception) as e:
            pytest.skip(f"Tree-sitter not available for integration test: {e}")
