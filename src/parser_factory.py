"""
Parser Factory for loading and configuring tree-sitter parsers.

This module provides a factory class for creating tree-sitter parser instances
configured for specific programming languages based on file extensions.
"""

from pathlib import Path
from typing import Dict, Optional

from .parser_setup import TreeSitterSetup, GrammarSetupError


class ParserNotAvailableError(Exception):
    """Raised when a parser for a language is not available."""
    pass


class ParserFactory:
    """
    Factory for creating and managing tree-sitter parser instances.
    
    The factory loads compiled language grammars and provides configured
    parser instances based on file extensions.
    """
    
    def __init__(self, setup: Optional[TreeSitterSetup] = None):
        """
        Initialize the parser factory.
        
        Args:
            setup: TreeSitterSetup instance. If None, creates a new one with defaults.
        """
        self.setup = setup if setup is not None else TreeSitterSetup()
        self._parsers: Dict[str, 'Parser'] = {}
        self._languages: Dict[str, 'Language'] = {}
    
    def _load_language(self, language: str) -> 'Language':
        """
        Load a compiled language grammar.
        
        Args:
            language: Language identifier (e.g., 'python', 'javascript')
        
        Returns:
            tree_sitter.Language object
        
        Raises:
            ParserNotAvailableError: If grammar not compiled or loading fails
        """
        if language in self._languages:
            return self._languages[language]
        
        try:
            from tree_sitter import Language
            
            grammar_path = self.setup.get_grammar_path(language)
            
            # Language.load() expects the library path and language name
            lang = Language(str(grammar_path), language)
            self._languages[language] = lang
            return lang
            
        except GrammarSetupError as e:
            raise ParserNotAvailableError(
                f"Grammar for {language} not available. "
                f"Run TreeSitterSetup.compile_grammar('{language}') first. "
                f"Error: {e}"
            ) from e
        except Exception as e:
            raise ParserNotAvailableError(
                f"Failed to load language {language}: {e}"
            ) from e
    
    def _create_parser(self, language: str) -> 'Parser':
        """
        Create a new parser instance for a language.
        
        Args:
            language: Language identifier
        
        Returns:
            tree_sitter.Parser configured for the language
        
        Raises:
            ParserNotAvailableError: If parser creation fails
        """
        try:
            from tree_sitter import Parser
            
            lang = self._load_language(language)
            parser = Parser()
            parser.set_language(lang)
            return parser
            
        except Exception as e:
            raise ParserNotAvailableError(
                f"Failed to create parser for {language}: {e}"
            ) from e
    
    def get_parser(self, file_extension: str) -> 'Parser':
        """
        Get a parser instance for a file extension.
        
        Args:
            file_extension: File extension (e.g., '.py', '.js')
        
        Returns:
            tree_sitter.Parser configured for the language
        
        Raises:
            ParserNotAvailableError: If extension not supported or parser unavailable
        """
        # Get language for extension
        language = self.setup.get_language_for_extension(file_extension)
        
        if language is None:
            supported = ', '.join(self.setup.get_supported_extensions())
            raise ParserNotAvailableError(
                f"No parser available for extension '{file_extension}'. "
                f"Supported extensions: {supported}"
            )
        
        # Check cache
        if language in self._parsers:
            return self._parsers[language]
        
        # Create and cache parser
        parser = self._create_parser(language)
        self._parsers[language] = parser
        return parser
    
    def get_parser_for_file(self, file_path: Path) -> 'Parser':
        """
        Get a parser instance for a file path.
        
        Args:
            file_path: Path to file
        
        Returns:
            tree_sitter.Parser configured for the file's language
        
        Raises:
            ParserNotAvailableError: If file extension not supported
        """
        extension = file_path.suffix
        return self.get_parser(extension)
    
    def get_parser_for_language(self, language: str) -> 'Parser':
        """
        Get a parser instance directly by language name.
        
        Args:
            language: Language identifier (e.g., 'python', 'javascript')
        
        Returns:
            tree_sitter.Parser configured for the language
        
        Raises:
            ParserNotAvailableError: If language not supported or parser unavailable
        """
        if language not in self.setup.LANGUAGE_REPOS:
            supported = ', '.join(self.setup.get_supported_languages())
            raise ParserNotAvailableError(
                f"Language '{language}' not supported. "
                f"Supported languages: {supported}"
            )
        
        # Check cache
        if language in self._parsers:
            return self._parsers[language]
        
        # Create and cache parser
        parser = self._create_parser(language)
        self._parsers[language] = parser
        return parser
    
    def is_extension_supported(self, extension: str) -> bool:
        """
        Check if a file extension is supported.
        
        Args:
            extension: File extension (e.g., '.py')
        
        Returns:
            True if supported, False otherwise
        """
        return self.setup.get_language_for_extension(extension) is not None
    
    def is_language_supported(self, language: str) -> bool:
        """
        Check if a language is supported.
        
        Args:
            language: Language identifier
        
        Returns:
            True if supported, False otherwise
        """
        return language in self.setup.LANGUAGE_REPOS
    
    def get_supported_extensions(self) -> list[str]:
        """
        Get list of all supported file extensions.
        
        Returns:
            List of file extensions
        """
        return self.setup.get_supported_extensions()
    
    def get_supported_languages(self) -> list[str]:
        """
        Get list of all supported languages.
        
        Returns:
            List of language identifiers
        """
        return self.setup.get_supported_languages()
    
    def clear_cache(self) -> None:
        """
        Clear cached parsers and languages.
        
        Useful for testing or when grammars are recompiled.
        """
        self._parsers.clear()
        self._languages.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get statistics about cached parsers and languages.
        
        Returns:
            Dictionary with cache counts
        """
        return {
            'parsers': len(self._parsers),
            'languages': len(self._languages)
        }
