"""
Tests for Parser Factory.
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.parser_factory import ParserFactory, ParserNotAvailableError
from src.parser_setup import GrammarSetupError, TreeSitterSetup


class TestParserFactory:
    """Tests for ParserFactory class."""
    
    def test_init_default_setup(self):
        """Test initialization with default setup."""
        with patch('taskmaster.parser_factory.TreeSitterSetup') as mock_setup_class:
            mock_instance = MagicMock()
            mock_setup_class.return_value = mock_instance
            
            factory = ParserFactory()
            
            # Should create a new TreeSitterSetup
            mock_setup_class.assert_called_once()
    
    def test_init_custom_setup(self):
        """Test initialization with custom setup."""
        mock_setup = MagicMock()
        factory = ParserFactory(setup=mock_setup)
        assert factory.setup == mock_setup
    
    def test_load_language_success(self):
        """Test loading a language successfully."""
        mock_setup = MagicMock()
        grammar_path = Path('/path/to/python.so')
        mock_setup.get_grammar_path.return_value = grammar_path
        
        factory = ParserFactory(setup=mock_setup)
        
        mock_language_class = MagicMock()
        mock_language = MagicMock()
        mock_language_class.return_value = mock_language
        
        with patch('tree_sitter.Language', mock_language_class):
            result = factory._load_language('python')
            
            assert result == mock_language
            mock_setup.get_grammar_path.assert_called_once_with('python')
            # Use str() to handle path conversion
            mock_language_class.assert_called_once_with(str(grammar_path), 'python')
    
    def test_load_language_cached(self):
        """Test that loaded languages are cached."""
        mock_setup = MagicMock()
        mock_language = MagicMock()
        
        factory = ParserFactory(setup=mock_setup)
        factory._languages['python'] = mock_language
        
        result = factory._load_language('python')
        
        assert result == mock_language
        # Should not call get_grammar_path if cached
        mock_setup.get_grammar_path.assert_not_called()
    
    def test_load_language_not_compiled(self):
        """Test loading language that hasn't been compiled."""
        mock_setup = MagicMock()
        mock_setup.get_grammar_path.side_effect = GrammarSetupError("Not compiled")
        
        factory = ParserFactory(setup=mock_setup)
        
        with pytest.raises(ParserNotAvailableError, match="Grammar for python not available"):
            factory._load_language('python')
    
    def test_load_language_loading_failure(self):
        """Test language loading failure."""
        mock_setup = MagicMock()
        mock_setup.get_grammar_path.return_value = Path('/path/to/python.so')
        
        factory = ParserFactory(setup=mock_setup)
        
        with patch('tree_sitter.Language', side_effect=Exception("Load failed")):
            with pytest.raises(ParserNotAvailableError, match="Failed to load language python"):
                factory._load_language('python')
    
    def test_create_parser_success(self):
        """Test creating a parser successfully."""
        mock_setup = MagicMock()
        factory = ParserFactory(setup=mock_setup)
        
        mock_language = MagicMock()
        mock_parser_class = MagicMock()
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        
        with patch.object(factory, '_load_language', return_value=mock_language):
            with patch('tree_sitter.Parser', mock_parser_class):
                result = factory._create_parser('python')
                
                assert result == mock_parser
                mock_parser.set_language.assert_called_once_with(mock_language)
    
    def test_create_parser_failure(self):
        """Test parser creation failure."""
        mock_setup = MagicMock()
        factory = ParserFactory(setup=mock_setup)
        
        with patch.object(factory, '_load_language', side_effect=Exception("Failed")):
            with pytest.raises(ParserNotAvailableError, match="Failed to create parser"):
                factory._create_parser('python')
    
    def test_get_parser_by_extension_success(self):
        """Test getting parser by file extension."""
        mock_setup = MagicMock()
        mock_setup.get_language_for_extension.return_value = 'python'
        
        factory = ParserFactory(setup=mock_setup)
        mock_parser = MagicMock()
        
        with patch.object(factory, '_create_parser', return_value=mock_parser):
            result = factory.get_parser('.py')
            
            assert result == mock_parser
            mock_setup.get_language_for_extension.assert_called_once_with('.py')
    
    def test_get_parser_by_extension_cached(self):
        """Test that parsers are cached by language."""
        mock_setup = MagicMock()
        mock_setup.get_language_for_extension.return_value = 'python'
        
        factory = ParserFactory(setup=mock_setup)
        mock_parser = MagicMock()
        factory._parsers['python'] = mock_parser
        
        result = factory.get_parser('.py')
        
        assert result == mock_parser
        # Should not create new parser if cached
        assert factory._parsers['python'] == mock_parser
    
    def test_get_parser_by_extension_unsupported(self):
        """Test getting parser for unsupported extension."""
        mock_setup = MagicMock()
        mock_setup.get_language_for_extension.return_value = None
        mock_setup.get_supported_extensions.return_value = ['.py', '.js']
        
        factory = ParserFactory(setup=mock_setup)
        
        with pytest.raises(ParserNotAvailableError, match="No parser available for extension"):
            factory.get_parser('.unknown')
    
    def test_get_parser_for_file_success(self):
        """Test getting parser for file path."""
        mock_setup = MagicMock()
        factory = ParserFactory(setup=mock_setup)
        mock_parser = MagicMock()
        
        file_path = Path('/path/to/script.py')
        
        with patch.object(factory, 'get_parser', return_value=mock_parser) as mock_get_parser:
            result = factory.get_parser_for_file(file_path)
            
            assert result == mock_parser
            mock_get_parser.assert_called_once_with('.py')
    
    def test_get_parser_for_language_success(self):
        """Test getting parser directly by language name."""
        mock_setup = MagicMock()
        mock_setup.LANGUAGE_REPOS = {'python': 'tree-sitter-python'}
        
        factory = ParserFactory(setup=mock_setup)
        mock_parser = MagicMock()
        
        with patch.object(factory, '_create_parser', return_value=mock_parser):
            result = factory.get_parser_for_language('python')
            
            assert result == mock_parser
    
    def test_get_parser_for_language_cached(self):
        """Test that language-based parser lookups use cache."""
        mock_setup = MagicMock()
        mock_setup.LANGUAGE_REPOS = {'python': 'tree-sitter-python'}
        
        factory = ParserFactory(setup=mock_setup)
        mock_parser = MagicMock()
        factory._parsers['python'] = mock_parser
        
        result = factory.get_parser_for_language('python')
        
        assert result == mock_parser
    
    def test_get_parser_for_language_unsupported(self):
        """Test getting parser for unsupported language."""
        mock_setup = MagicMock()
        mock_setup.LANGUAGE_REPOS = {'python': 'tree-sitter-python'}
        mock_setup.get_supported_languages.return_value = ['python', 'javascript']
        
        factory = ParserFactory(setup=mock_setup)
        
        with pytest.raises(ParserNotAvailableError, match="Language 'unknown' not supported"):
            factory.get_parser_for_language('unknown')
    
    def test_is_extension_supported_true(self):
        """Test checking if extension is supported (when it is)."""
        mock_setup = MagicMock()
        mock_setup.get_language_for_extension.return_value = 'python'
        
        factory = ParserFactory(setup=mock_setup)
        
        assert factory.is_extension_supported('.py') is True
    
    def test_is_extension_supported_false(self):
        """Test checking if extension is supported (when it's not)."""
        mock_setup = MagicMock()
        mock_setup.get_language_for_extension.return_value = None
        
        factory = ParserFactory(setup=mock_setup)
        
        assert factory.is_extension_supported('.unknown') is False
    
    def test_is_language_supported_true(self):
        """Test checking if language is supported (when it is)."""
        mock_setup = MagicMock()
        mock_setup.LANGUAGE_REPOS = {'python': 'tree-sitter-python'}
        
        factory = ParserFactory(setup=mock_setup)
        
        assert factory.is_language_supported('python') is True
    
    def test_is_language_supported_false(self):
        """Test checking if language is supported (when it's not)."""
        mock_setup = MagicMock()
        mock_setup.LANGUAGE_REPOS = {'python': 'tree-sitter-python'}
        
        factory = ParserFactory(setup=mock_setup)
        
        assert factory.is_language_supported('unknown') is False
    
    def test_get_supported_extensions(self):
        """Test getting list of supported extensions."""
        mock_setup = MagicMock()
        mock_setup.get_supported_extensions.return_value = ['.py', '.js', '.ts']
        
        factory = ParserFactory(setup=mock_setup)
        
        result = factory.get_supported_extensions()
        
        assert result == ['.py', '.js', '.ts']
        mock_setup.get_supported_extensions.assert_called_once()
    
    def test_get_supported_languages(self):
        """Test getting list of supported languages."""
        mock_setup = MagicMock()
        mock_setup.get_supported_languages.return_value = ['python', 'javascript', 'typescript']
        
        factory = ParserFactory(setup=mock_setup)
        
        result = factory.get_supported_languages()
        
        assert result == ['python', 'javascript', 'typescript']
        mock_setup.get_supported_languages.assert_called_once()
    
    def test_clear_cache(self):
        """Test clearing the parser and language cache."""
        mock_setup = MagicMock()
        factory = ParserFactory(setup=mock_setup)
        
        # Add some cached items
        factory._parsers['python'] = MagicMock()
        factory._languages['python'] = MagicMock()
        
        factory.clear_cache()
        
        assert len(factory._parsers) == 0
        assert len(factory._languages) == 0
    
    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        mock_setup = MagicMock()
        factory = ParserFactory(setup=mock_setup)
        
        # Add some cached items
        factory._parsers['python'] = MagicMock()
        factory._parsers['javascript'] = MagicMock()
        factory._languages['python'] = MagicMock()
        
        stats = factory.get_cache_stats()
        
        assert stats['parsers'] == 2
        assert stats['languages'] == 1
    
    def test_multiple_extensions_same_language(self):
        """Test that multiple extensions for same language share parser."""
        mock_setup = MagicMock()
        # Both .js and .jsx map to 'javascript'
        mock_setup.get_language_for_extension.side_effect = lambda ext: 'javascript' if ext in ['.js', '.jsx'] else None
        
        factory = ParserFactory(setup=mock_setup)
        mock_parser = MagicMock()
        
        with patch.object(factory, '_create_parser', return_value=mock_parser) as mock_create:
            parser1 = factory.get_parser('.js')
            parser2 = factory.get_parser('.jsx')
            
            # Should return same parser
            assert parser1 == parser2
            # Should only create parser once
            mock_create.assert_called_once()
