"""
Tests for AST Wrapper class.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from src.ast_wrapper import ASTWrapper, ASTParsingError
from src.parser_factory import ParserFactory, ParserNotAvailableError


class TestASTWrapperInitialization:
    """Test AST wrapper initialization and parsing."""
    
    def test_initialization_with_string_source(self):
        """Test initialization with string source code."""
        source = "def hello():\n    pass"
        file_path = "test.py"
        
        with patch.object(ASTWrapper, '_parse') as mock_parse:
            wrapper = ASTWrapper(source, file_path)
            
            assert wrapper.source_code == source
            assert wrapper.file_path == Path(file_path)
            assert wrapper._parser_factory is not None
            mock_parse.assert_called_once()
    
    def test_initialization_with_bytes_source(self):
        """Test initialization with bytes source code."""
        source = b"def hello():\n    pass"
        file_path = Path("test.py")
        
        with patch.object(ASTWrapper, '_parse') as mock_parse:
            wrapper = ASTWrapper(source, file_path)
            
            assert wrapper.source_code == source
            assert wrapper.file_path == file_path
            mock_parse.assert_called_once()
    
    def test_initialization_with_custom_parser_factory(self):
        """Test initialization with custom parser factory."""
        source = "console.log('hello');"
        file_path = "test.js"
        factory = Mock(spec=ParserFactory)
        
        with patch.object(ASTWrapper, '_parse') as mock_parse:
            wrapper = ASTWrapper(source, file_path, parser_factory=factory)
            
            assert wrapper._parser_factory is factory
            mock_parse.assert_called_once()
    
    def test_initialization_creates_default_factory(self):
        """Test that default factory is created if none provided."""
        source = "test code"
        file_path = "test.py"
        
        with patch.object(ASTWrapper, '_parse'):
            with patch('taskmaster.ast_wrapper.ParserFactory') as mock_factory_class:
                wrapper = ASTWrapper(source, file_path)
                
                mock_factory_class.assert_called_once()


class TestASTWrapperParsing:
    """Test parsing functionality."""
    
    def test_parse_success_with_string_source(self):
        """Test successful parsing with string source."""
        source = "def hello():\n    pass"
        file_path = "test.py"
        
        # Create mock tree and node
        mock_node = Mock()
        mock_node.has_error = False
        mock_tree = Mock()
        mock_tree.root_node = mock_node
        
        # Create mock parser
        mock_parser = Mock()
        mock_parser.parse.return_value = mock_tree
        
        # Create mock factory
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.get_parser_for_file.return_value = mock_parser
        
        wrapper = ASTWrapper(source, file_path, parser_factory=mock_factory)
        
        # Verify parsing occurred
        mock_factory.get_parser_for_file.assert_called_once_with(Path(file_path))
        mock_parser.parse.assert_called_once()
        
        # Verify tree and node are set
        assert wrapper._tree is mock_tree
        assert wrapper._root_node is mock_node
    
    def test_parse_success_with_bytes_source(self):
        """Test successful parsing with bytes source."""
        source = b"console.log('test');"
        file_path = "test.js"
        
        # Create mock tree and node
        mock_node = Mock()
        mock_node.has_error = False
        mock_tree = Mock()
        mock_tree.root_node = mock_node
        
        # Create mock parser
        mock_parser = Mock()
        mock_parser.parse.return_value = mock_tree
        
        # Create mock factory
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.get_parser_for_file.return_value = mock_parser
        
        wrapper = ASTWrapper(source, file_path, parser_factory=mock_factory)
        
        # Verify bytes were passed directly
        mock_parser.parse.assert_called_once_with(source)
    
    def test_parse_converts_string_to_bytes(self):
        """Test that string source is converted to bytes for parsing."""
        source = "test code"
        file_path = "test.py"
        
        mock_node = Mock()
        mock_node.has_error = False
        mock_tree = Mock()
        mock_tree.root_node = mock_node
        mock_parser = Mock()
        mock_parser.parse.return_value = mock_tree
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.get_parser_for_file.return_value = mock_parser
        
        wrapper = ASTWrapper(source, file_path, parser_factory=mock_factory)
        
        # Verify bytes were passed to parser
        call_args = mock_parser.parse.call_args[0][0]
        assert isinstance(call_args, bytes)
        assert call_args == source.encode('utf-8')
    
    def test_parse_raises_error_when_tree_is_none(self):
        """Test that ASTParsingError is raised when parser returns None."""
        source = "test code"
        file_path = "test.py"
        
        mock_parser = Mock()
        mock_parser.parse.return_value = None
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.get_parser_for_file.return_value = mock_parser
        
        with pytest.raises(ASTParsingError, match="Parser returned None"):
            ASTWrapper(source, file_path, parser_factory=mock_factory)
    
    def test_parse_raises_error_when_root_node_is_none(self):
        """Test that ASTParsingError is raised when root node is None."""
        source = "test code"
        file_path = "test.py"
        
        mock_tree = Mock()
        mock_tree.root_node = None
        mock_parser = Mock()
        mock_parser.parse.return_value = mock_tree
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.get_parser_for_file.return_value = mock_parser
        
        with pytest.raises(ASTParsingError, match="No root node"):
            ASTWrapper(source, file_path, parser_factory=mock_factory)
    
    def test_parse_raises_error_when_has_error(self):
        """Test that ASTParsingError is raised when tree has errors."""
        source = "def invalid syntax"
        file_path = "test.py"
        
        mock_node = Mock()
        mock_node.has_error = True
        mock_tree = Mock()
        mock_tree.root_node = mock_node
        mock_parser = Mock()
        mock_parser.parse.return_value = mock_tree
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.get_parser_for_file.return_value = mock_parser
        
        with pytest.raises(ASTParsingError, match="Parse errors detected"):
            ASTWrapper(source, file_path, parser_factory=mock_factory)
    
    def test_parse_reraises_parser_not_available_error(self):
        """Test that ParserNotAvailableError is re-raised."""
        source = "test code"
        file_path = "test.unknown"
        
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.get_parser_for_file.side_effect = ParserNotAvailableError("Unsupported")
        
        with pytest.raises(ParserNotAvailableError, match="Unsupported"):
            ASTWrapper(source, file_path, parser_factory=mock_factory)
    
    def test_parse_wraps_unexpected_exceptions(self):
        """Test that unexpected exceptions are wrapped in ASTParsingError."""
        source = "test code"
        file_path = "test.py"
        
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.get_parser_for_file.side_effect = RuntimeError("Unexpected error")
        
        with pytest.raises(ASTParsingError, match="Unexpected error parsing"):
            ASTWrapper(source, file_path, parser_factory=mock_factory)


class TestASTWrapperProperties:
    """Test property accessors."""
    
    def test_root_node_property(self):
        """Test root_node property."""
        source = "test"
        file_path = "test.py"
        
        mock_node = Mock()
        mock_node.has_error = False
        mock_tree = Mock()
        mock_tree.root_node = mock_node
        mock_parser = Mock()
        mock_parser.parse.return_value = mock_tree
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.get_parser_for_file.return_value = mock_parser
        
        wrapper = ASTWrapper(source, file_path, parser_factory=mock_factory)
        
        assert wrapper.root_node is mock_node
    
    def test_tree_property(self):
        """Test tree property."""
        source = "test"
        file_path = "test.py"
        
        mock_node = Mock()
        mock_node.has_error = False
        mock_tree = Mock()
        mock_tree.root_node = mock_node
        mock_parser = Mock()
        mock_parser.parse.return_value = mock_tree
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.get_parser_for_file.return_value = mock_parser
        
        wrapper = ASTWrapper(source, file_path, parser_factory=mock_factory)
        
        assert wrapper.tree is mock_tree
    
    def test_source_code_property(self):
        """Test source_code property."""
        source = "test code"
        file_path = "test.py"
        
        with patch.object(ASTWrapper, '_parse'):
            wrapper = ASTWrapper(source, file_path)
            
            assert wrapper.source_code == source
    
    def test_file_path_property(self):
        """Test file_path property."""
        source = "test"
        file_path = "test.py"
        
        with patch.object(ASTWrapper, '_parse'):
            wrapper = ASTWrapper(source, file_path)
            
            assert wrapper.file_path == Path(file_path)
    
    def test_language_property(self):
        """Test language property."""
        source = "test"
        file_path = "test.py"
        
        mock_setup = Mock()
        mock_setup.get_language_for_extension.return_value = "python"
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.setup = mock_setup
        
        with patch.object(ASTWrapper, '_parse'):
            wrapper = ASTWrapper(source, file_path, parser_factory=mock_factory)
            
            language = wrapper.language
            
            assert language == "python"
            mock_setup.get_language_for_extension.assert_called_once_with(".py")


class TestASTWrapperMethods:
    """Test utility methods."""
    
    def test_has_errors_returns_true_when_errors_exist(self):
        """Test has_errors returns True when parse errors exist."""
        source = "test"
        file_path = "test.py"
        
        mock_node = Mock()
        mock_node.has_error = False
        mock_tree = Mock()
        mock_tree.root_node = mock_node
        mock_parser = Mock()
        mock_parser.parse.return_value = mock_tree
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.get_parser_for_file.return_value = mock_parser
        
        wrapper = ASTWrapper(source, file_path, parser_factory=mock_factory)
        wrapper._root_node.has_error = True
        
        assert wrapper.has_errors() is True
    
    def test_has_errors_returns_false_when_no_errors(self):
        """Test has_errors returns False when no errors."""
        source = "test"
        file_path = "test.py"
        
        mock_node = Mock()
        mock_node.has_error = False
        mock_tree = Mock()
        mock_tree.root_node = mock_node
        mock_parser = Mock()
        mock_parser.parse.return_value = mock_tree
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.get_parser_for_file.return_value = mock_parser
        
        wrapper = ASTWrapper(source, file_path, parser_factory=mock_factory)
        
        assert wrapper.has_errors() is False
    
    def test_has_errors_returns_true_when_no_root_node(self):
        """Test has_errors returns True when root node is None."""
        source = "test"
        file_path = "test.py"
        
        with patch.object(ASTWrapper, '_parse'):
            wrapper = ASTWrapper(source, file_path)
            wrapper._root_node = None
            
            assert wrapper.has_errors() is True
    
    def test_get_node_text_with_string_source(self):
        """Test get_node_text with string source."""
        source = "def hello():\n    pass"
        file_path = "test.py"
        
        mock_node = Mock()
        mock_node.start_byte = 0
        mock_node.end_byte = 3
        
        with patch.object(ASTWrapper, '_parse'):
            wrapper = ASTWrapper(source, file_path)
            
            text = wrapper.get_node_text(mock_node)
            
            assert text == "def"
    
    def test_get_node_text_with_bytes_source(self):
        """Test get_node_text with bytes source."""
        source = b"def hello():\n    pass"
        file_path = "test.py"
        
        mock_node = Mock()
        mock_node.start_byte = 4
        mock_node.end_byte = 9
        
        with patch.object(ASTWrapper, '_parse'):
            wrapper = ASTWrapper(source, file_path)
            
            text = wrapper.get_node_text(mock_node)
            
            assert text == "hello"
    
    def test_get_node_text_with_none_node(self):
        """Test get_node_text returns empty string for None."""
        source = "test"
        file_path = "test.py"
        
        with patch.object(ASTWrapper, '_parse'):
            wrapper = ASTWrapper(source, file_path)
            
            text = wrapper.get_node_text(None)
            
            assert text == ""
    
    def test_repr(self):
        """Test string representation."""
        source = "test"
        file_path = "test.py"
        
        mock_node = Mock()
        mock_node.has_error = False
        mock_tree = Mock()
        mock_tree.root_node = mock_node
        mock_parser = Mock()
        mock_parser.parse.return_value = mock_tree
        
        mock_setup = Mock()
        mock_setup.get_language_for_extension.return_value = "python"
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.setup = mock_setup
        mock_factory.get_parser_for_file.return_value = mock_parser
        
        wrapper = ASTWrapper(source, file_path, parser_factory=mock_factory)
        
        repr_str = repr(wrapper)
        
        assert "test.py" in repr_str
        assert "python" in repr_str
        assert "parsed" in repr_str
    
    def test_repr_with_errors(self):
        """Test string representation when errors exist."""
        source = "test"
        file_path = "test.py"
        
        mock_node = Mock()
        mock_node.has_error = True
        mock_tree = Mock()
        mock_tree.root_node = mock_node
        mock_parser = Mock()
        mock_parser.parse.return_value = mock_tree
        
        mock_setup = Mock()
        mock_setup.get_language_for_extension.return_value = "python"
        mock_factory = Mock(spec=ParserFactory)
        mock_factory.setup = mock_setup
        mock_factory.get_parser_for_file.return_value = mock_parser
        
        # Bypass error checking in constructor
        with patch.object(ASTWrapper, '_parse'):
            wrapper = ASTWrapper(source, file_path, parser_factory=mock_factory)
            wrapper._root_node = mock_node
            wrapper._tree = mock_tree
        
        repr_str = repr(wrapper)
        
        assert "error" in repr_str


class TestASTWrapperIntegration:
    """Integration tests with real parsers (if available)."""
    
    def test_parse_simple_python_code(self):
        """Test parsing simple Python code."""
        source = "def hello():\n    pass"
        file_path = "test.py"
        
        # Try to create wrapper with real parsing
        # This will fail if tree-sitter is not set up, which is expected
        try:
            wrapper = ASTWrapper(source, file_path)
            
            # If parsing succeeds, verify basic properties
            assert wrapper.root_node is not None
            assert wrapper.source_code == source
            assert wrapper.language == "python"
            assert not wrapper.has_errors()
            
        except (ParserNotAvailableError, ImportError):
            # Expected when tree-sitter not fully set up
            pytest.skip("Tree-sitter not available for integration test")
    
    def test_parse_simple_javascript_code(self):
        """Test parsing simple JavaScript code."""
        source = "function hello() {\n  return 'world';\n}"
        file_path = "test.js"
        
        try:
            wrapper = ASTWrapper(source, file_path)
            
            assert wrapper.root_node is not None
            assert wrapper.source_code == source
            assert wrapper.language == "javascript"
            assert not wrapper.has_errors()
            
        except (ParserNotAvailableError, ImportError):
            pytest.skip("Tree-sitter not available for integration test")
