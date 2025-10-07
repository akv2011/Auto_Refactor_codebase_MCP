"""
Tests for file scanner and directory walker.
"""

import pytest
from pathlib import Path
from src.scanner import FileScanner
from src.config import RefactorConfig


@pytest.fixture
def mock_directory_structure(tmp_path):
    """Create a mock directory structure for testing."""
    # Create directory structure
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("# main file")
    (tmp_path / "src" / "utils.py").write_text("# utils file")
    (tmp_path / "src" / "main_test.py").write_text("# test file")
    
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("# test file")
    (tmp_path / "tests" / "test_utils.py").write_text("# test file")
    
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "package.json").write_text("{}")
    (tmp_path / "node_modules" / "index.js").write_text("// js file")
    
    (tmp_path / "venv").mkdir()
    (tmp_path / "venv" / "lib").mkdir()
    (tmp_path / "venv" / "lib" / "site-packages").mkdir()
    (tmp_path / "venv" / "lib" / "site-packages" / "module.py").write_text("# venv file")
    
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "bundle.js").write_text("// bundle")
    
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "main.cpython-39.pyc").write_text("compiled")
    
    (tmp_path / "README.md").write_text("# README")
    (tmp_path / "setup.py").write_text("# setup")
    
    return tmp_path


@pytest.fixture
def default_config():
    """Create a default configuration for testing."""
    return RefactorConfig()


@pytest.fixture
def custom_config():
    """Create a custom configuration with specific patterns."""
    return RefactorConfig(
        excludePatterns=[
            "**/tests/**",
            "**/*_test.py",
            "**/node_modules/**",
            "**/venv/**"
        ]
    )


class TestFileScanner:
    """Test FileScanner class."""
    
    def test_scanner_initialization(self, tmp_path, default_config):
        """Test scanner initialization."""
        scanner = FileScanner(tmp_path, default_config)
        
        assert scanner.root_path == tmp_path.resolve()
        assert scanner.config == default_config
        assert len(scanner.exclude_patterns) > 0
    
    def test_scan_with_default_config(self, mock_directory_structure, default_config):
        """Test scanning with default configuration."""
        scanner = FileScanner(mock_directory_structure, default_config)
        files = list(scanner.walk())
        
        # Convert to relative paths for easier assertion
        rel_files = [f.relative_to(mock_directory_structure) for f in files]
        rel_files_str = [str(f) for f in rel_files]
        
        # Should find Python files in src
        assert any("src/main.py" in str(f) or str(f) == "src\\main.py" for f in rel_files_str)
        assert any("src/utils.py" in str(f) or str(f) == "src\\utils.py" for f in rel_files_str)
        
        # Should exclude node_modules, venv, dist, __pycache__ (default patterns)
        assert not any("node_modules" in str(f) for f in rel_files_str)
        assert not any("venv" in str(f) for f in rel_files_str)
        assert not any("dist" in str(f) for f in rel_files_str)
        assert not any("__pycache__" in str(f) for f in rel_files_str)
    
    def test_scan_with_custom_config(self, mock_directory_structure, custom_config):
        """Test scanning with custom exclude patterns."""
        scanner = FileScanner(mock_directory_structure, custom_config)
        files = list(scanner.walk())
        
        rel_files = [f.relative_to(mock_directory_structure) for f in files]
        rel_files_str = [str(f) for f in rel_files]
        
        # Should exclude tests directory and _test.py files
        assert not any("tests" in str(f) for f in rel_files_str)
        assert not any("_test.py" in str(f) for f in rel_files_str)
        
        # Should still find non-test Python files
        assert any("src/main.py" in str(f) or str(f) == "src\\main.py" for f in rel_files_str)
        assert any("src/utils.py" in str(f) or str(f) == "src\\utils.py" for f in rel_files_str)
    
    def test_exclude_specific_extensions(self, tmp_path):
        """Test excluding files by extension."""
        # Create test files
        (tmp_path / "file.py").write_text("# python")
        (tmp_path / "file.js").write_text("// javascript")
        (tmp_path / "file.txt").write_text("text")
        
        config = RefactorConfig(excludePatterns=["**/*.js", "**/*.txt"])
        scanner = FileScanner(tmp_path, config)
        files = list(scanner.walk())
        
        file_names = [f.name for f in files]
        
        assert "file.py" in file_names
        assert "file.js" not in file_names
        assert "file.txt" not in file_names
    
    def test_empty_directory(self, tmp_path, default_config):
        """Test scanning an empty directory."""
        scanner = FileScanner(tmp_path, default_config)
        files = list(scanner.walk())
        
        assert len(files) == 0
    
    def test_nested_structure(self, tmp_path, default_config):
        """Test scanning deeply nested directory structure."""
        # Create nested structure
        nested = tmp_path / "level1" / "level2" / "level3"
        nested.mkdir(parents=True)
        (nested / "deep_file.py").write_text("# deep file")
        
        scanner = FileScanner(tmp_path, default_config)
        files = list(scanner.walk())
        
        assert len(files) == 1
        assert files[0].name == "deep_file.py"


class TestPatternMatching:
    """Test pattern matching logic."""
    
    def test_matches_simple_pattern(self, tmp_path, default_config):
        """Test simple glob pattern matching."""
        (tmp_path / "test.py").write_text("# test")
        (tmp_path / "main.py").write_text("# main")
        
        config = RefactorConfig(excludePatterns=["test.py"])
        scanner = FileScanner(tmp_path, config)
        files = list(scanner.walk())
        
        file_names = [f.name for f in files]
        assert "main.py" in file_names
        assert "test.py" not in file_names
    
    def test_matches_wildcard_pattern(self, tmp_path):
        """Test wildcard pattern matching."""
        (tmp_path / "test_main.py").write_text("# test")
        (tmp_path / "test_utils.py").write_text("# test")
        (tmp_path / "main.py").write_text("# main")
        
        config = RefactorConfig(excludePatterns=["test_*.py"])
        scanner = FileScanner(tmp_path, config)
        files = list(scanner.walk())
        
        file_names = [f.name for f in files]
        assert "main.py" in file_names
        assert "test_main.py" not in file_names
        assert "test_utils.py" not in file_names
    
    def test_matches_recursive_pattern(self, tmp_path):
        """Test recursive pattern matching (**/)."""
        # Create nested structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "test").mkdir()
        (tmp_path / "src" / "test" / "file.py").write_text("# test")
        (tmp_path / "src" / "main.py").write_text("# main")
        
        config = RefactorConfig(excludePatterns=["**/test/**"])
        scanner = FileScanner(tmp_path, config)
        files = list(scanner.walk())
        
        rel_files = [f.relative_to(tmp_path) for f in files]
        rel_files_str = [str(f) for f in rel_files]
        
        assert any("src/main.py" in str(f) or str(f) == "src\\main.py" for f in rel_files_str)
        assert not any("test" in str(f) for f in rel_files_str)
    
    def test_matches_directory_recursive_pattern(self, tmp_path):
        """Test directory recursive pattern (**)."""
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "pkg").mkdir()
        (tmp_path / "node_modules" / "pkg" / "index.js").write_text("// js")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.js").write_text("// main")
        
        config = RefactorConfig(excludePatterns=["**/node_modules/**"])
        scanner = FileScanner(tmp_path, config)
        files = list(scanner.walk())
        
        rel_files = [f.relative_to(tmp_path) for f in files]
        rel_files_str = [str(f) for f in rel_files]
        
        assert not any("node_modules" in str(f) for f in rel_files_str)
        assert any("src" in str(f) for f in rel_files_str)


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_nonexistent_directory(self, tmp_path, default_config):
        """Test scanning a nonexistent directory."""
        nonexistent = tmp_path / "nonexistent"
        scanner = FileScanner(nonexistent, default_config)
        
        # Should not raise error, just return empty
        files = list(scanner.walk())
        assert len(files) == 0
    
    def test_symlinks(self, tmp_path, default_config):
        """Test handling of symbolic links."""
        # Create a file and a symlink to it
        (tmp_path / "real_file.py").write_text("# real")
        
        # Skip symlink test on Windows if not supported
        try:
            (tmp_path / "link_file.py").symlink_to(tmp_path / "real_file.py")
            has_symlinks = True
        except (OSError, NotImplementedError):
            has_symlinks = False
        
        if has_symlinks:
            scanner = FileScanner(tmp_path, default_config)
            files = list(scanner.walk())
            
            # os.walk follows symlinks by default
            assert len(files) >= 1
    
    def test_special_characters_in_filename(self, tmp_path, default_config):
        """Test files with special characters in names."""
        (tmp_path / "file with spaces.py").write_text("# spaces")
        (tmp_path / "file-with-dashes.py").write_text("# dashes")
        (tmp_path / "file_with_underscores.py").write_text("# underscores")
        
        scanner = FileScanner(tmp_path, default_config)
        files = list(scanner.walk())
        
        file_names = [f.name for f in files]
        assert "file with spaces.py" in file_names
        assert "file-with-dashes.py" in file_names
        assert "file_with_underscores.py" in file_names
