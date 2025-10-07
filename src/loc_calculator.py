"""
Lines of Code (LOC) Calculator Module

This module provides utilities for calculating the effective lines of code in source files.
It ignores empty lines and single-line comments to provide a more accurate measure of
actual code content.
"""

from pathlib import Path
from typing import Union


class LOCCalculationError(Exception):
    """Raised when LOC calculation fails."""
    pass


# Common single-line comment markers for various languages
COMMENT_MARKERS = {
    'python': '#',
    'javascript': '//',
    'typescript': '//',
    'java': '//',
    'csharp': '//',
    'sql': '--',
    'c': '//',
    'cpp': '//',
    'go': '//',
    'rust': '//',
    'ruby': '#',
    'php': '//',
    'swift': '//',
    'kotlin': '//',
}


def get_comment_marker_for_extension(file_extension: str) -> str:
    """
    Get the single-line comment marker for a given file extension.
    
    Args:
        file_extension: File extension (e.g., '.py', '.js')
        
    Returns:
        Comment marker string (e.g., '#', '//')
        
    Raises:
        ValueError: If extension is not supported
    """
    ext = file_extension.lower().lstrip('.')
    
    # Map extensions to language keys
    ext_to_lang = {
        'py': 'python',
        'js': 'javascript',
        'jsx': 'javascript',
        'ts': 'typescript',
        'tsx': 'typescript',
        'java': 'java',
        'cs': 'csharp',
        'sql': 'sql',
        'c': 'c',
        'cpp': 'cpp',
        'cc': 'cpp',
        'go': 'go',
        'rs': 'rust',
        'rb': 'ruby',
        'php': 'php',
        'swift': 'swift',
        'kt': 'kotlin',
    }
    
    lang = ext_to_lang.get(ext)
    if not lang:
        raise ValueError(f"Unsupported file extension: {file_extension}")
    
    return COMMENT_MARKERS[lang]


def is_code_line(line: str, comment_marker: str) -> bool:
    """
    Determine if a line contains actual code.
    
    A line is considered code if:
    - It's not empty after stripping whitespace
    - It doesn't start with a comment marker
    
    Args:
        line: Line of source code
        comment_marker: Single-line comment marker for the language
        
    Returns:
        True if the line contains code, False otherwise
    """
    stripped = line.strip()
    
    # Empty line
    if not stripped:
        return False
    
    # Comment line
    if stripped.startswith(comment_marker):
        return False
    
    return True


def calculate_loc(file_path: Union[str, Path]) -> int:
    """
    Calculate the effective lines of code in a source file.
    
    This function counts only non-empty lines that don't start with
    single-line comment markers. Block comments are not currently handled
    and may be counted as code lines.
    
    Args:
        file_path: Path to the source file
        
    Returns:
        Number of effective lines of code
        
    Raises:
        LOCCalculationError: If file cannot be read or processed
        ValueError: If file extension is not supported
        
    Example:
        >>> loc = calculate_loc('my_script.py')
        >>> print(f"Lines of code: {loc}")
    """
    try:
        path = Path(file_path)
        
        # Validate file exists
        if not path.exists():
            raise LOCCalculationError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise LOCCalculationError(f"Path is not a file: {file_path}")
        
        # Get comment marker for this file type
        comment_marker = get_comment_marker_for_extension(path.suffix)
        
        # Count lines of code
        loc_count = 0
        
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if is_code_line(line, comment_marker):
                    loc_count += 1
        
        return loc_count
        
    except ValueError as e:
        # Re-raise ValueError for unsupported extensions
        raise
    except LOCCalculationError as e:
        # Re-raise our custom errors
        raise
    except Exception as e:
        # Wrap any other errors
        raise LOCCalculationError(f"Error calculating LOC for {file_path}: {e}") from e


def calculate_loc_batch(file_paths: list[Union[str, Path]]) -> dict[str, int]:
    """
    Calculate LOC for multiple files.
    
    Args:
        file_paths: List of file paths
        
    Returns:
        Dictionary mapping file paths to their LOC counts
        
    Example:
        >>> results = calculate_loc_batch(['file1.py', 'file2.js'])
        >>> print(results)
        {'file1.py': 42, 'file2.js': 35}
    """
    results = {}
    
    for file_path in file_paths:
        try:
            path_str = str(file_path)
            results[path_str] = calculate_loc(file_path)
        except (LOCCalculationError, ValueError) as e:
            # Store error message instead of count
            results[str(file_path)] = f"Error: {e}"
    
    return results
