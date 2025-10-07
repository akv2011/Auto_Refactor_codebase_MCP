"""
Tree-sitter parser setup with modern API (0.25+).

This module handles the setup of Tree-sitter language parsers
for multi-language AST parsing support using pre-built language packages.
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from .config_errors import ConfigurationError


class GrammarSetupError(Exception):
    """Raised when language setup fails."""
    pass


class TreeSitterSetup:
    """
    Manages Tree-sitter parser setup using modern API (0.25+).
    
    Uses pre-built language packages instead of compiling grammars.
    Supported languages:
    - Python
    - JavaScript
    - TypeScript
    - Java
    - C#
    - SQL
    """
    
    # Language package mappings
    LANGUAGE_PACKAGES: Dict[str, str] = {
        'python': 'tree-sitter-python',
        'javascript': 'tree-sitter-javascript',
        'typescript': 'tree-sitter-typescript',
        'java': 'tree-sitter-java',
        'c_sharp': 'tree-sitter-c-sharp',
        'sql': 'tree-sitter-sql',
    }
    
    # File extensions mapping to languages
    EXTENSION_MAP: Dict[str, str] = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cs': 'c_sharp',
        '.sql': 'sql',
    }
    
    def __init__(self):
        """Initialize Tree-sitter setup."""
        pass
    
    def is_tree_sitter_installed(self) -> bool:
        """
        Check if tree-sitter Python package is installed.
        
        Returns:
            True if installed, False otherwise
        """
        try:
            import tree_sitter
            return True
        except ImportError:
            return False
    
    def is_language_installed(self, language: str) -> bool:
        """
        Check if language package is installed.
        
        Args:
            language: Language identifier (e.g., 'python', 'javascript')
        
        Returns:
            True if language package is installed
        """
        if language not in self.LANGUAGE_PACKAGES:
            return False
        
        package_name = self.LANGUAGE_PACKAGES[language].replace('-', '_')
        try:
            __import__(package_name)
            return True
        except ImportError:
            return False
    
    def install_language(self, language: str) -> None:
        """
        Install language package using pip.
        
        Args:
            language: Language identifier (e.g., 'python', 'javascript')
        
        Raises:
            GrammarSetupError: If installation fails
        """
        if language not in self.LANGUAGE_PACKAGES:
            raise GrammarSetupError(
                f"Unsupported language: {language}. "
                f"Supported: {', '.join(self.LANGUAGE_PACKAGES.keys())}"
            )
        
        package = self.LANGUAGE_PACKAGES[language]
        try:
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install', package],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError as e:
            raise GrammarSetupError(
                f"Failed to install {package}: {e}"
            ) from e
    
    def ensure_language_installed(self, language: str) -> None:
        """
        Ensure language package is installed, install if not.
        
        Args:
            language: Language identifier
        
        Raises:
            GrammarSetupError: If installation fails
        """
        if not self.is_tree_sitter_installed():
            self.install_tree_sitter()
        
        if not self.is_language_installed(language):
            self.install_language(language)
    
    def install_tree_sitter(self) -> None:
        """
        Install tree-sitter Python package using pip.
        
        Raises:
            GrammarSetupError: If installation fails
        """
        try:
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install', 'tree-sitter'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError as e:
            raise GrammarSetupError(
                f"Failed to install tree-sitter: {e}"
            ) from e
    
    def get_language(self, language: str):
        """
        Get Language object for the specified language.
        
        Args:
            language: Language identifier (e.g., 'python', 'javascript')
        
        Returns:
            Language object from tree_sitter
        
        Raises:
            GrammarSetupError: If language not supported or not installed
        """
        if language not in self.LANGUAGE_PACKAGES:
            raise GrammarSetupError(
                f"Unsupported language: {language}"
            )
        
        self.ensure_language_installed(language)
        
        from tree_sitter import Language
        
        # Import the language-specific module
        package_name = self.LANGUAGE_PACKAGES[language].replace('-', '_')
        
        try:
            if language == 'python':
                import tree_sitter_python as ts_lang
            elif language == 'javascript':
                import tree_sitter_javascript as ts_lang
            elif language == 'typescript':
                import tree_sitter_typescript as ts_lang
            elif language == 'java':
                import tree_sitter_java as ts_lang
            elif language == 'c_sharp':
                import tree_sitter_c_sharp as ts_lang
            elif language == 'sql':
                import tree_sitter_sql as ts_lang
            else:
                raise GrammarSetupError(f"Language {language} not implemented")
            
            return Language(ts_lang.language())
        except ImportError as e:
            raise GrammarSetupError(
                f"Failed to import {package_name}: {e}. "
                f"Try installing with: pip install {self.LANGUAGE_PACKAGES[language]}"
            ) from e
    
    def get_parser(self, language: str):
        """
        Get Parser configured for the specified language.
        
        Args:
            language: Language identifier (e.g., 'python', 'javascript')
        
        Returns:
            Configured Parser object
        
        Raises:
            GrammarSetupError: If language not supported or not installed
        """
        from tree_sitter import Parser
        
        lang_obj = self.get_language(language)
        parser = Parser(lang_obj)
        return parser
    
    @classmethod
    def get_language_for_extension(cls, extension: str) -> Optional[str]:
        """
        Get language identifier for file extension.
        
        Args:
            extension: File extension (e.g., '.py', '.js')
        
        Returns:
            Language identifier or None if not supported
        """
        return cls.EXTENSION_MAP.get(extension.lower())
    
    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """
        Get list of all supported file extensions.
        
        Returns:
            List of file extensions
        """
        return list(cls.EXTENSION_MAP.keys())
    
    @classmethod
    def get_supported_languages(cls) -> List[str]:
        """
        Get list of all supported languages.
        
        Returns:
            List of language identifiers
        """
        return list(cls.LANGUAGE_PACKAGES.keys())


def setup_tree_sitter(languages: Optional[List[str]] = None) -> TreeSitterSetup:
    """
    Convenience function to set up Tree-sitter with language packages.
    
    Args:
        languages: Languages to ensure installed. If None, does not pre-install any.
    
    Returns:
        TreeSitterSetup instance
    
    Raises:
        GrammarSetupError: If setup fails
    """
    setup = TreeSitterSetup()
    
    if languages:
        for lang in languages:
            setup.ensure_language_installed(lang)
    
    return setup
