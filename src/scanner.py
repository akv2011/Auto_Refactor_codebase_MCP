"""
File scanner and directory walker for TaskMaster.

This module provides utilities to scan directories and discover files
that match specified patterns while excluding unwanted files and directories.
"""

import os
from pathlib import Path
from typing import Iterator, List, Optional
from fnmatch import fnmatch

from .config import RefactorConfig


class FileScanner:
    """
    Scans directories for files matching include/exclude patterns.
    
    This class provides efficient directory walking with pattern matching
    based on configuration settings.
    """
    
    def __init__(self, root_path: Path, config: RefactorConfig):
        """
        Initialize the file scanner.
        
        Args:
            root_path: Root directory to scan.
            config: TaskMaster configuration containing exclude patterns.
        """
        self.root_path = Path(root_path).resolve()
        self.config = config
        self.exclude_patterns = config.exclude_patterns
    
    def _matches_any_pattern(self, path: str, patterns: List[str]) -> bool:
        """
        Check if a path matches any of the given patterns.
        
        Args:
            path: Path to check (relative or absolute).
            patterns: List of glob patterns to match against.
            
        Returns:
            True if path matches any pattern, False otherwise.
        """
        # Convert path to forward slashes for consistent pattern matching
        normalized_path = path.replace(os.sep, '/')
        
        for pattern in patterns:
            # Normalize pattern as well
            normalized_pattern = pattern.replace(os.sep, '/')
            
            # Handle different pattern types
            if normalized_pattern.startswith('**/'):
                # Recursive pattern - match anywhere in path
                sub_pattern = normalized_pattern[3:]
                if fnmatch(normalized_path, f'*/{sub_pattern}') or fnmatch(normalized_path, sub_pattern):
                    return True
            elif normalized_pattern.endswith('/**'):
                # Directory recursive pattern - match directory and all contents
                dir_pattern = normalized_pattern[:-3]
                if f'/{dir_pattern}/' in f'/{normalized_path}/' or normalized_path.startswith(f'{dir_pattern}/'):
                    return True
            elif '**' in normalized_pattern:
                # Pattern contains ** in the middle
                parts = normalized_pattern.split('**')
                if len(parts) == 2 and normalized_path.startswith(parts[0].rstrip('/')) and normalized_path.endswith(parts[1].lstrip('/')):
                    return True
            else:
                # Standard glob pattern
                if fnmatch(normalized_path, normalized_pattern):
                    return True
                # Also try matching just the basename
                basename = os.path.basename(normalized_path)
                if fnmatch(basename, normalized_pattern):
                    return True
        
        return False
    
    def _should_exclude_file(self, file_path: Path) -> bool:
        """
        Check if a file should be excluded based on configuration patterns.
        
        Args:
            file_path: Path to the file to check.
            
        Returns:
            True if file should be excluded, False otherwise.
        """
        try:
            # Get relative path from root
            rel_path = file_path.relative_to(self.root_path)
            rel_path_str = str(rel_path)
            
            # Check against exclude patterns
            if self._matches_any_pattern(rel_path_str, self.exclude_patterns):
                return True
            
            # Check if file extension should be excluded
            # (in case patterns include things like "*.pyc")
            return False
            
        except ValueError:
            # Path is not relative to root - exclude it
            return True
    
    def walk(self) -> Iterator[Path]:
        """
        Walk the directory tree and yield file paths.
        
        Yields file paths that are not excluded by configuration patterns.
        This is a synchronous generator function.
        
        Yields:
            Path objects for files that should be processed.
        """
        for dirpath, dirnames, filenames in os.walk(self.root_path):
            dirpath_obj = Path(dirpath)
            
            # Process files in current directory
            for filename in filenames:
                file_path = dirpath_obj / filename
                
                # Check if file should be excluded
                if not self._should_exclude_file(file_path):
                    yield file_path
