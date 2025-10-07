"""
Tests for Import/Export Statement Management utilities.

Tests the _find_imports, _add_import_to_ast, and _add_export_to_ast methods.
"""

import pytest
from pathlib import Path
from src.refactoring_engine import RefactoringEngine
from src.parser_setup import TreeSitterSetup


@pytest.fixture
def engine():
    """Create a RefactoringEngine instance."""
    return RefactoringEngine()


@pytest.fixture
def setup_tree_sitter_grammars():
    """Ensure tree-sitter grammars are installed."""
    ts_setup = TreeSitterSetup()
    ts_setup.ensure_language_installed('python')
    return ts_setup


def test_find_imports_with_regular_imports(engine, setup_tree_sitter_grammars):
    """Test finding regular import statements."""
    source = b"""import os
import sys
import json as js
"""
    
    # Parse the source
    parser = setup_tree_sitter_grammars.get_parser('python')
    tree = parser.parse(source)
    
    # Find imports
    imports = engine._find_imports(tree, source)
    
    # Should find 3 imports
    assert len(imports) == 3
    
    # Check first import
    assert imports[0]['type'] == 'import'
    assert imports[0]['module'] == 'os'
    assert imports[0]['symbols'] == []
    assert imports[0]['alias'] is None
    
    # Check import with alias
    has_json_import = any(
        imp['module'] == 'json' and imp['alias'] == 'js'
        for imp in imports
    )
    assert has_json_import


def test_find_imports_with_from_imports(engine, setup_tree_sitter_grammars):
    """Test finding from-import statements."""
    source = b"""from pathlib import Path
from typing import Any, Dict
from src.os import path as ospath
"""
    
    # Parse the source
    parser = setup_tree_sitter_grammars.get_parser('python')
    tree = parser.parse(source)
    
    # Find imports
    imports = engine._find_imports(tree, source)
    
    # Should find 3 from-imports
    assert len(imports) == 3
    
    # Check first from-import
    assert imports[0]['type'] == 'from_import'
    assert imports[0]['module'] == 'pathlib'
    assert 'Path' in imports[0]['symbols']
    
    # Check from-import with multiple symbols
    typing_import = next(
        (imp for imp in imports if imp['module'] == 'typing'),
        None
    )
    assert typing_import is not None
    assert 'Any' in typing_import['symbols']
    assert 'Dict' in typing_import['symbols']


def test_find_imports_mixed(engine, setup_tree_sitter_grammars):
    """Test finding both regular and from-imports."""
    source = b"""import os
from pathlib import Path
import sys
from typing import Any
"""
    
    # Parse the source
    parser = setup_tree_sitter_grammars.get_parser('python')
    tree = parser.parse(source)
    
    # Find imports
    imports = engine._find_imports(tree, source)
    
    # Should find 4 imports
    assert len(imports) == 4
    
    # Check mix of types
    regular_imports = [imp for imp in imports if imp['type'] == 'import']
    from_imports = [imp for imp in imports if imp['type'] == 'from_import']
    
    assert len(regular_imports) == 2
    assert len(from_imports) == 2


def test_find_imports_empty_file(engine, setup_tree_sitter_grammars):
    """Test finding imports in a file with no imports."""
    source = b"""def hello():
    print("Hello")
"""
    
    # Parse the source
    parser = setup_tree_sitter_grammars.get_parser('python')
    tree = parser.parse(source)
    
    # Find imports
    imports = engine._find_imports(tree, source)
    
    # Should find no imports
    assert len(imports) == 0


def test_add_import_to_ast_regular_import_empty_file(engine, setup_tree_sitter_grammars):
    """Test adding a regular import to a file with no imports."""
    source = b"""def hello():
    print("Hello")
"""
    
    # Parse the source
    parser = setup_tree_sitter_grammars.get_parser('python')
    tree = parser.parse(source)
    
    # Add import
    new_source = engine._add_import_to_ast(tree, source, 'os')
    
    # Verify the import was added
    assert b'import os' in new_source
    
    # Verify code is valid
    new_tree = parser.parse(new_source)
    assert not new_tree.root_node.has_error
    
    # Verify function still exists
    assert b'def hello():' in new_source


def test_add_import_to_ast_from_import_empty_file(engine, setup_tree_sitter_grammars):
    """Test adding a from-import to a file with no imports."""
    source = b"""def hello():
    print("Hello")
"""
    
    # Parse the source
    parser = setup_tree_sitter_grammars.get_parser('python')
    tree = parser.parse(source)
    
    # Add from-import
    new_source = engine._add_import_to_ast(tree, source, 'pathlib', ['Path'])
    
    # Verify the import was added
    assert b'from pathlib import Path' in new_source
    
    # Verify code is valid
    new_tree = parser.parse(new_source)
    assert not new_tree.root_node.has_error


def test_add_import_to_ast_after_existing_imports(engine, setup_tree_sitter_grammars):
    """Test adding import after existing imports."""
    source = b"""import os
import sys

def hello():
    print("Hello")
"""
    
    # Parse the source
    parser = setup_tree_sitter_grammars.get_parser('python')
    tree = parser.parse(source)
    
    # Add import
    new_source = engine._add_import_to_ast(tree, source, 'json')
    
    # Verify the import was added
    assert b'import json' in new_source
    
    # Verify code is valid
    new_tree = parser.parse(new_source)
    assert not new_tree.root_node.has_error
    
    # Verify all imports are present
    assert b'import os' in new_source
    assert b'import sys' in new_source
    assert b'import json' in new_source


def test_add_import_to_ast_with_docstring(engine, setup_tree_sitter_grammars):
    """Test adding import to file with module docstring."""
    source = b'''"""Module docstring."""

def hello():
    print("Hello")
'''
    
    # Parse the source
    parser = setup_tree_sitter_grammars.get_parser('python')
    tree = parser.parse(source)
    
    # Add import
    new_source = engine._add_import_to_ast(tree, source, 'os')
    
    # Verify the import was added after docstring
    assert b'"""Module docstring."""' in new_source
    assert b'import os' in new_source
    
    # Verify code is valid
    new_tree = parser.parse(new_source)
    assert not new_tree.root_node.has_error
    
    # Docstring should come before import
    docstring_pos = new_source.find(b'"""Module docstring."""')
    import_pos = new_source.find(b'import os')
    assert docstring_pos < import_pos


def test_add_export_to_ast_creates_all_if_missing(engine, setup_tree_sitter_grammars):
    """Test adding export creates __all__ if it doesn't exist."""
    source = b"""def my_function():
    pass
"""
    
    # Parse the source
    parser = setup_tree_sitter_grammars.get_parser('python')
    tree = parser.parse(source)
    
    # Add export
    new_source = engine._add_export_to_ast(tree, source, 'my_function')
    
    # Verify __all__ was created
    assert b"__all__ = ['my_function']" in new_source
    
    # Verify code is valid
    new_tree = parser.parse(new_source)
    assert not new_tree.root_node.has_error


def test_add_export_to_ast_adds_to_existing_all(engine, setup_tree_sitter_grammars):
    """Test adding export to existing __all__."""
    source = b"""__all__ = ['existing_function']

def existing_function():
    pass

def new_function():
    pass
"""
    
    # Parse the source
    parser = setup_tree_sitter_grammars.get_parser('python')
    tree = parser.parse(source)
    
    # Add export
    new_source = engine._add_export_to_ast(tree, source, 'new_function')
    
    # Verify symbol was added to __all__
    assert b"'new_function'" in new_source
    assert b"'existing_function'" in new_source
    
    # Verify code is valid
    new_tree = parser.parse(new_source)
    assert not new_tree.root_node.has_error


def test_add_export_to_ast_empty_all(engine, setup_tree_sitter_grammars):
    """Test adding export to empty __all__."""
    source = b"""__all__ = []

def my_function():
    pass
"""
    
    # Parse the source
    parser = setup_tree_sitter_grammars.get_parser('python')
    tree = parser.parse(source)
    
    # Add export
    new_source = engine._add_export_to_ast(tree, source, 'my_function')
    
    # Verify symbol was added to __all__
    assert b"__all__ = ['my_function']" in new_source
    
    # Verify code is valid
    new_tree = parser.parse(new_source)
    assert not new_tree.root_node.has_error


def test_add_export_to_ast_after_imports(engine, setup_tree_sitter_grammars):
    """Test that __all__ is added after imports."""
    source = b"""import os
from pathlib import Path

def my_function():
    pass
"""
    
    # Parse the source
    parser = setup_tree_sitter_grammars.get_parser('python')
    tree = parser.parse(source)
    
    # Add export
    new_source = engine._add_export_to_ast(tree, source, 'my_function')
    
    # Verify __all__ was created
    assert b"__all__ = ['my_function']" in new_source
    
    # Verify code is valid
    new_tree = parser.parse(new_source)
    assert not new_tree.root_node.has_error
    
    # __all__ should come after imports
    import_pos = new_source.find(b'from pathlib import Path')
    all_pos = new_source.find(b"__all__ =")
    assert import_pos < all_pos
