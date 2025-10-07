"""
Tests for Tree-sitter parser setup and grammar compilation.
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.parser_setup import (
    GrammarSetupError,
    TreeSitterSetup,
    setup_tree_sitter,
)


class TestTreeSitterSetup:
    """Tests for TreeSitterSetup class."""
    
    def test_init_default_build_dir(self):
        """Test initialization with default build directory."""
        setup = TreeSitterSetup()
        expected_dir = Path.home() / '.tree-sitter' / 'grammars'
        assert setup.build_dir == expected_dir
    
    def test_init_custom_build_dir(self, tmp_path):
        """Test initialization with custom build directory."""
        custom_dir = tmp_path / 'custom_grammars'
        setup = TreeSitterSetup(build_dir=custom_dir)
        assert setup.build_dir == custom_dir
        assert custom_dir.exists()
    
    def test_build_dir_created(self, tmp_path):
        """Test that build directory is created if it doesn't exist."""
        build_dir = tmp_path / 'non_existent' / 'grammars'
        setup = TreeSitterSetup(build_dir=build_dir)
        assert build_dir.exists()
    
    def test_is_tree_sitter_installed_true(self):
        """Test checking if tree-sitter is installed (when it is)."""
        setup = TreeSitterSetup()
        # Mock the import by adding tree_sitter to sys.modules
        with patch.dict('sys.modules', {'tree_sitter': MagicMock()}):
            assert setup.is_tree_sitter_installed() is True
    
    def test_is_tree_sitter_installed_false(self):
        """Test checking if tree-sitter is not installed."""
        setup = TreeSitterSetup()
        with patch('builtins.__import__', side_effect=ImportError):
            assert setup.is_tree_sitter_installed() is False
    
    def test_install_tree_sitter_success(self):
        """Test successful tree-sitter installation."""
        setup = TreeSitterSetup()
        with patch('subprocess.check_call') as mock_check_call:
            setup.install_tree_sitter()
            mock_check_call.assert_called_once_with(
                [sys.executable, '-m', 'pip', 'install', 'tree-sitter'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
    
    def test_install_tree_sitter_failure(self):
        """Test tree-sitter installation failure."""
        setup = TreeSitterSetup()
        with patch('subprocess.check_call', side_effect=subprocess.CalledProcessError(1, 'pip')):
            with pytest.raises(GrammarSetupError, match="Failed to install tree-sitter"):
                setup.install_tree_sitter()
    
    def test_ensure_tree_sitter_installed_already_installed(self):
        """Test ensuring tree-sitter when already installed."""
        setup = TreeSitterSetup()
        with patch.object(setup, 'is_tree_sitter_installed', return_value=True):
            with patch.object(setup, 'install_tree_sitter') as mock_install:
                setup.ensure_tree_sitter_installed()
                mock_install.assert_not_called()
    
    def test_ensure_tree_sitter_installed_not_installed(self):
        """Test ensuring tree-sitter when not installed."""
        setup = TreeSitterSetup()
        with patch.object(setup, 'is_tree_sitter_installed', return_value=False):
            with patch.object(setup, 'install_tree_sitter') as mock_install:
                setup.ensure_tree_sitter_installed()
                mock_install.assert_called_once()
    
    def test_clone_grammar_repo_unsupported_language(self, tmp_path):
        """Test cloning grammar for unsupported language."""
        setup = TreeSitterSetup(build_dir=tmp_path)
        with pytest.raises(GrammarSetupError, match="Unsupported language: unknown"):
            setup.clone_grammar_repo('unknown')
    
    def test_clone_grammar_repo_success(self, tmp_path):
        """Test successful grammar repository cloning."""
        setup = TreeSitterSetup(build_dir=tmp_path)
        expected_path = tmp_path / 'tree-sitter-python'
        
        with patch('subprocess.check_call') as mock_check_call:
            result = setup.clone_grammar_repo('python')
            
            assert result == expected_path
            mock_check_call.assert_called_once()
            args = mock_check_call.call_args[0][0]
            assert args[0] == 'git'
            assert args[1] == 'clone'
            assert 'tree-sitter-python' in args[-2]
    
    def test_clone_grammar_repo_already_exists(self, tmp_path):
        """Test cloning when repository already exists."""
        setup = TreeSitterSetup(build_dir=tmp_path)
        repo_path = tmp_path / 'tree-sitter-python'
        repo_path.mkdir()
        
        with patch('subprocess.check_call') as mock_check_call:
            result = setup.clone_grammar_repo('python')
            assert result == repo_path
            mock_check_call.assert_not_called()
    
    def test_clone_grammar_repo_failure(self, tmp_path):
        """Test grammar repository cloning failure."""
        setup = TreeSitterSetup(build_dir=tmp_path)
        
        with patch('subprocess.check_call', side_effect=subprocess.CalledProcessError(1, 'git')):
            with pytest.raises(GrammarSetupError, match="Failed to clone"):
                setup.clone_grammar_repo('python')
    
    def test_compile_grammar_python(self, tmp_path):
        """Test compiling Python grammar."""
        setup = TreeSitterSetup(build_dir=tmp_path)
        repo_path = tmp_path / 'tree-sitter-python'
        
        mock_language = MagicMock()
        
        with patch.object(setup, 'clone_grammar_repo', return_value=repo_path):
            with patch('tree_sitter.Language', mock_language):
                result = setup.compile_grammar('python')
                
                expected_lib = tmp_path / 'python.so'
                assert result == expected_lib
                
                mock_language.build_library.assert_called_once_with(
                    str(expected_lib),
                    [str(repo_path)]
                )
    
    def test_compile_grammar_typescript_special_handling(self, tmp_path):
        """Test compiling TypeScript grammar with subdirectory handling."""
        setup = TreeSitterSetup(build_dir=tmp_path)
        repo_path = tmp_path / 'tree-sitter-typescript'
        
        mock_language = MagicMock()
        
        with patch.object(setup, 'clone_grammar_repo', return_value=repo_path):
            with patch('tree_sitter.Language', mock_language):
                result = setup.compile_grammar('typescript')
                
                expected_lib = tmp_path / 'typescript.so'
                assert result == expected_lib
                
                # Should include both typescript and tsx subdirectories
                call_args = mock_language.build_library.call_args[0]
                assert len(call_args[1]) == 2
                assert str(repo_path / 'typescript') in call_args[1]
                assert str(repo_path / 'tsx') in call_args[1]
    
    def test_compile_grammar_failure(self, tmp_path):
        """Test grammar compilation failure."""
        setup = TreeSitterSetup(build_dir=tmp_path)
        repo_path = tmp_path / 'tree-sitter-python'
        
        with patch.object(setup, 'clone_grammar_repo', return_value=repo_path):
            with patch('tree_sitter.Language') as mock_language:
                mock_language.build_library.side_effect = Exception("Build failed")
                
                with pytest.raises(GrammarSetupError, match="Failed to compile python grammar"):
                    setup.compile_grammar('python')
    
    def test_compile_all_grammars_default(self, tmp_path):
        """Test compiling all supported grammars."""
        setup = TreeSitterSetup(build_dir=tmp_path)
        
        with patch.object(setup, 'compile_grammar') as mock_compile:
            mock_compile.return_value = tmp_path / 'test.so'
            
            result = setup.compile_all_grammars()
            
            # Should compile all supported languages
            assert len(result) == len(setup.LANGUAGE_REPOS)
            assert mock_compile.call_count == len(setup.LANGUAGE_REPOS)
    
    def test_compile_all_grammars_specific_languages(self, tmp_path):
        """Test compiling specific languages only."""
        setup = TreeSitterSetup(build_dir=tmp_path)
        languages = ['python', 'javascript']
        
        with patch.object(setup, 'compile_grammar') as mock_compile:
            mock_compile.return_value = tmp_path / 'test.so'
            
            result = setup.compile_all_grammars(languages=languages)
            
            assert len(result) == 2
            assert mock_compile.call_count == 2
    
    def test_compile_all_grammars_partial_failure(self, tmp_path):
        """Test compiling when some grammars fail."""
        setup = TreeSitterSetup(build_dir=tmp_path)
        
        def mock_compile_side_effect(lang):
            if lang == 'python':
                raise GrammarSetupError("Python failed")
            return tmp_path / f'{lang}.so'
        
        with patch.object(setup, 'compile_grammar', side_effect=mock_compile_side_effect):
            with pytest.raises(GrammarSetupError, match="Failed to compile some grammars"):
                setup.compile_all_grammars(languages=['python', 'javascript'])
    
    def test_is_grammar_compiled_true(self, tmp_path):
        """Test checking if grammar is compiled (when it is)."""
        setup = TreeSitterSetup(build_dir=tmp_path)
        lib_path = tmp_path / 'python.so'
        lib_path.touch()
        
        assert setup.is_grammar_compiled('python') is True
    
    def test_is_grammar_compiled_false(self, tmp_path):
        """Test checking if grammar is compiled (when it's not)."""
        setup = TreeSitterSetup(build_dir=tmp_path)
        assert setup.is_grammar_compiled('python') is False
    
    def test_get_grammar_path_exists(self, tmp_path):
        """Test getting grammar path when it exists."""
        setup = TreeSitterSetup(build_dir=tmp_path)
        lib_path = tmp_path / 'python.so'
        lib_path.touch()
        
        result = setup.get_grammar_path('python')
        assert result == lib_path
    
    def test_get_grammar_path_not_exists(self, tmp_path):
        """Test getting grammar path when it doesn't exist."""
        setup = TreeSitterSetup(build_dir=tmp_path)
        
        with pytest.raises(GrammarSetupError, match="Grammar for python not compiled"):
            setup.get_grammar_path('python')
    
    def test_get_language_for_extension_python(self):
        """Test getting language for .py extension."""
        assert TreeSitterSetup.get_language_for_extension('.py') == 'python'
    
    def test_get_language_for_extension_javascript(self):
        """Test getting language for .js and .jsx extensions."""
        assert TreeSitterSetup.get_language_for_extension('.js') == 'javascript'
        assert TreeSitterSetup.get_language_for_extension('.jsx') == 'javascript'
    
    def test_get_language_for_extension_typescript(self):
        """Test getting language for .ts and .tsx extensions."""
        assert TreeSitterSetup.get_language_for_extension('.ts') == 'typescript'
        assert TreeSitterSetup.get_language_for_extension('.tsx') == 'typescript'
    
    def test_get_language_for_extension_case_insensitive(self):
        """Test that extension matching is case-insensitive."""
        assert TreeSitterSetup.get_language_for_extension('.PY') == 'python'
        assert TreeSitterSetup.get_language_for_extension('.Js') == 'javascript'
    
    def test_get_language_for_extension_unsupported(self):
        """Test getting language for unsupported extension."""
        assert TreeSitterSetup.get_language_for_extension('.unknown') is None
    
    def test_get_supported_extensions(self):
        """Test getting list of supported extensions."""
        extensions = TreeSitterSetup.get_supported_extensions()
        assert isinstance(extensions, list)
        assert '.py' in extensions
        assert '.js' in extensions
        assert '.ts' in extensions
        assert len(extensions) >= 6
    
    def test_get_supported_languages(self):
        """Test getting list of supported languages."""
        languages = TreeSitterSetup.get_supported_languages()
        assert isinstance(languages, list)
        assert 'python' in languages
        assert 'javascript' in languages
        assert 'typescript' in languages
        assert len(languages) >= 6


class TestSetupTreeSitterFunction:
    """Tests for setup_tree_sitter convenience function."""
    
    def test_setup_tree_sitter_default(self, tmp_path):
        """Test setup with default parameters."""
        with patch('taskmaster.parser_setup.TreeSitterSetup') as mock_setup_class:
            mock_instance = MagicMock()
            mock_setup_class.return_value = mock_instance
            
            result = setup_tree_sitter(build_dir=tmp_path)
            
            assert result == mock_instance
            mock_instance.ensure_tree_sitter_installed.assert_called_once()
            mock_instance.compile_all_grammars.assert_called_once_with(languages=None)
    
    def test_setup_tree_sitter_specific_languages(self, tmp_path):
        """Test setup with specific languages."""
        languages = ['python', 'javascript']
        
        with patch('taskmaster.parser_setup.TreeSitterSetup') as mock_setup_class:
            mock_instance = MagicMock()
            mock_setup_class.return_value = mock_instance
            
            result = setup_tree_sitter(languages=languages, build_dir=tmp_path)
            
            assert result == mock_instance
            mock_instance.ensure_tree_sitter_installed.assert_called_once()
            mock_instance.compile_all_grammars.assert_called_once_with(languages=languages)
