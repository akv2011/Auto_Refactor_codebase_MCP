"""
Code Node - Standardized data structure for code constructs.

This module provides a dataclass for representing code constructs (functions, classes, etc.)
in a language-agnostic way, abstracting away the underlying tree-sitter node differences.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, List
from pathlib import Path


@dataclass
class CodeNode:
    """
    Standardized representation of a code construct.
    
    This class provides a language-agnostic way to represent functions, classes,
    and other code constructs, abstracting away the differences in tree-sitter
    node structures across different programming languages.
    """
    
    type: str
    """Type of code construct ('function', 'class', 'method', etc.)"""
    
    name: str
    """Name of the construct"""
    
    start_line: int
    """Starting line number (1-indexed)"""
    
    end_line: int
    """Ending line number (1-indexed)"""
    
    source_text: str
    """Full source code of the construct"""
    
    file_path: Optional[Path] = None
    """Path to the file containing this construct"""
    
    language: Optional[str] = None
    """Programming language of the construct"""
    
    node: Optional[Any] = field(default=None, repr=False)
    """
    Original tree-sitter node (excluded from repr for readability).
    Useful for advanced operations requiring access to the raw AST.
    """
    
    metadata: dict = field(default_factory=dict)
    """
    Additional metadata about the construct.
    Can contain language-specific information like:
    - decorators: List of decorators (Python)
    - modifiers: Access modifiers (Java, C#)
    - parameters: Function parameters
    - return_type: Return type annotation
    - extends: Parent class/interface
    - implements: Implemented interfaces
    """
    
    def __post_init__(self):
        """Validate fields after initialization."""
        if self.start_line < 1:
            raise ValueError(f"start_line must be >= 1, got {self.start_line}")
        if self.end_line < self.start_line:
            raise ValueError(
                f"end_line ({self.end_line}) must be >= start_line ({self.start_line})"
            )
        if not self.name:
            raise ValueError("name cannot be empty")
        if not self.type:
            raise ValueError("type cannot be empty")
    
    @property
    def line_count(self) -> int:
        """Get the number of lines in this construct."""
        return self.end_line - self.start_line + 1
    
    @property
    def is_function(self) -> bool:
        """Check if this is a function-like construct."""
        return self.type in ('function', 'method', 'constructor')
    
    @property
    def is_class(self) -> bool:
        """Check if this is a class-like construct."""
        return self.type in ('class', 'interface', 'struct')
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary representation.
        
        Returns:
            Dictionary with all fields except the tree-sitter node
        """
        return {
            'type': self.type,
            'name': self.name,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'source_text': self.source_text,
            'file_path': str(self.file_path) if self.file_path else None,
            'language': self.language,
            'metadata': self.metadata,
            'line_count': self.line_count,
        }
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        location = f"{self.file_path.name if self.file_path else '?'}:{self.start_line}"
        return f"{self.type} '{self.name}' at {location} ({self.line_count} lines)"


@dataclass
class CodeNodeCollection:
    """
    Collection of CodeNode objects with utility methods.
    
    Provides convenient filtering and grouping operations on sets of code nodes.
    """
    
    nodes: List[CodeNode] = field(default_factory=list)
    
    def __len__(self) -> int:
        """Get number of nodes in collection."""
        return len(self.nodes)
    
    def __iter__(self):
        """Iterate over nodes."""
        return iter(self.nodes)
    
    def __getitem__(self, index):
        """Get node by index."""
        return self.nodes[index]
    
    def filter_by_type(self, node_type: str) -> 'CodeNodeCollection':
        """
        Filter nodes by type.
        
        Args:
            node_type: Type to filter by ('function', 'class', etc.)
        
        Returns:
            New collection with filtered nodes
        """
        filtered = [n for n in self.nodes if n.type == node_type]
        return CodeNodeCollection(filtered)
    
    def filter_by_language(self, language: str) -> 'CodeNodeCollection':
        """
        Filter nodes by language.
        
        Args:
            language: Language to filter by ('python', 'javascript', etc.)
        
        Returns:
            New collection with filtered nodes
        """
        filtered = [n for n in self.nodes if n.language == language]
        return CodeNodeCollection(filtered)
    
    def filter_by_name(self, name: str, exact: bool = True) -> 'CodeNodeCollection':
        """
        Filter nodes by name.
        
        Args:
            name: Name to search for
            exact: If True, match exactly; if False, match substring
        
        Returns:
            New collection with filtered nodes
        """
        if exact:
            filtered = [n for n in self.nodes if n.name == name]
        else:
            filtered = [n for n in self.nodes if name.lower() in n.name.lower()]
        return CodeNodeCollection(filtered)
    
    def get_functions(self) -> 'CodeNodeCollection':
        """Get all function-like nodes."""
        filtered = [n for n in self.nodes if n.is_function]
        return CodeNodeCollection(filtered)
    
    def get_classes(self) -> 'CodeNodeCollection':
        """Get all class-like nodes."""
        filtered = [n for n in self.nodes if n.is_class]
        return CodeNodeCollection(filtered)
    
    def group_by_file(self) -> dict[Path, 'CodeNodeCollection']:
        """
        Group nodes by file path.
        
        Returns:
            Dictionary mapping file paths to collections
        """
        grouped = {}
        for node in self.nodes:
            if node.file_path:
                if node.file_path not in grouped:
                    grouped[node.file_path] = CodeNodeCollection()
                grouped[node.file_path].nodes.append(node)
        return grouped
    
    def group_by_type(self) -> dict[str, 'CodeNodeCollection']:
        """
        Group nodes by type.
        
        Returns:
            Dictionary mapping types to collections
        """
        grouped = {}
        for node in self.nodes:
            if node.type not in grouped:
                grouped[node.type] = CodeNodeCollection()
            grouped[node.type].nodes.append(node)
        return grouped
    
    def to_list(self) -> List[dict]:
        """Convert all nodes to dictionary representations."""
        return [node.to_dict() for node in self.nodes]
