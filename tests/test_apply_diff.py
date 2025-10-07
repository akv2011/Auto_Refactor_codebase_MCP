"""
Tests for apply_diff refactoring operation.

This module tests the _handle_apply_diff method of RefactoringEngine.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.refactoring_engine import (
    RefactoringEngine,
    RefactoringError,
    RefactoringValidationError,
)


# Sample Python code for testing
ORIGINAL_CODE = '''def calculate_total(items):
    total = 0
    for item in items:
        total += item['price']
    return total

def main():
    items = [{'price': 10}, {'price': 20}]
    print(calculate_total(items))
'''

# Unified diff that extracts a helper function
SAMPLE_DIFF = '''--- a/test.py
+++ b/test.py
@@ -1,8 +1,12 @@
+def sum_prices(items):
+    total = 0
+    for item in items:
+        total += item['price']
+    return total
+
 def calculate_total(items):
-    total = 0
-    for item in items:
-        total += item['price']
-    return total
+    return sum_prices(items)
 
 def main():
     items = [{'price': 10}, {'price': 20}]
'''

EXPECTED_MODIFIED_CODE = '''def sum_prices(items):
    total = 0
    for item in items:
        total += item['price']
    return total

def calculate_total(items):
    return sum_prices(items)

def main():
    items = [{'price': 10}, {'price': 20}]
    print(calculate_total(items))
'''


class TestApplyDiff:
    """Test apply_diff refactoring operation."""
    
    @pytest.fixture
    def temp_file(self):
        """Create a temporary Python file for testing."""
        temp_dir = tempfile.mkdtemp()
        file_path = Path(temp_dir) / 'test.py'
        
        # Write original code
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(ORIGINAL_CODE)
        
        yield file_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_apply_diff_success(self, temp_file):
        """Test successful diff application."""
        engine = RefactoringEngine()
        
        result = engine.apply({
            'type': 'apply_diff',
            'file': str(temp_file),
            'diff': SAMPLE_DIFF
        })
        
        assert result['status'] == 'success'
        assert str(temp_file) in result['modified_files']
        assert 'Successfully applied diff' in result['message']
        
        # Verify file was modified correctly
        with open(temp_file, 'r', encoding='utf-8') as f:
            modified_content = f.read()
        
        # Check that new function exists
        assert 'def sum_prices(items):' in modified_content
        assert 'return sum_prices(items)' in modified_content
    
    def test_apply_diff_missing_file_parameter(self):
        """Test that missing file parameter returns error status."""
        engine = RefactoringEngine()
        
        result = engine.apply({
            'type': 'apply_diff',
            'diff': SAMPLE_DIFF
        })
        
        assert result['status'] == 'error'
        assert 'file' in result['error'].lower()
    
    def test_apply_diff_missing_diff_parameter(self, temp_file):
        """Test that missing diff parameter returns error status."""
        engine = RefactoringEngine()
        
        result = engine.apply({
            'type': 'apply_diff',
            'file': str(temp_file)
        })
        
        assert result['status'] == 'error'
        assert 'diff' in result['error'].lower()
    
    def test_apply_diff_file_not_found(self):
        """Test that non-existent file returns error status."""
        engine = RefactoringEngine()
        
        result = engine.apply({
            'type': 'apply_diff',
            'file': '/nonexistent/file.py',
            'diff': SAMPLE_DIFF
        })
        
        assert result['status'] == 'error'
        assert 'not found' in result['error'].lower()
    
    def test_apply_diff_to_directory(self, temp_file):
        """Test that applying diff to directory returns error status."""
        engine = RefactoringEngine()
        
        result = engine.apply({
            'type': 'apply_diff',
            'file': str(temp_file.parent),  # Directory, not file
            'diff': SAMPLE_DIFF
        })
        
        assert result['status'] == 'error'
        assert 'not a file' in result['error'].lower()
    
    def test_apply_diff_manual_fallback(self, temp_file, monkeypatch):
        """Test manual diff application when patch tools aren't available."""
        engine = RefactoringEngine()
        
        # Mock subprocess to simulate missing patch/git commands
        def mock_run(*args, **kwargs):
            raise FileNotFoundError("patch command not found")
        
        import subprocess
        monkeypatch.setattr(subprocess, 'run', mock_run)
        
        result = engine.apply({
            'type': 'apply_diff',
            'file': str(temp_file),
            'diff': SAMPLE_DIFF
        })
        
        assert result['status'] == 'success'
        assert 'manually' in result['message'].lower()
        
        # Verify the file was modified
        with open(temp_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'def sum_prices(items):' in content


class TestApplyDiffEdgeCases:
    """Test edge cases for apply_diff operation."""
    
    @pytest.fixture
    def temp_file(self):
        """Create a temporary Python file."""
        temp_dir = tempfile.mkdtemp()
        file_path = Path(temp_dir) / 'test.py'
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(ORIGINAL_CODE)
        
        yield file_path
        
        shutil.rmtree(temp_dir)
    
    def test_apply_diff_with_empty_diff(self, temp_file):
        """Test applying an empty diff succeeds with no changes."""
        engine = RefactoringEngine()
        
        # Empty diff should be handled gracefully - no changes to apply
        result = engine.apply({
            'type': 'apply_diff',
            'file': str(temp_file),
            'diff': ''
        })
        
        # Empty diff can be considered successful (no changes to apply)
        assert result['status'] == 'success'
        
        # File content should remain unchanged
        with open(temp_file, 'r') as f:
            content = f.read()
        assert content == ORIGINAL_CODE
    
    def test_apply_diff_with_invalid_diff_format(self, temp_file):
        """Test applying a malformed diff returns error status."""
        engine = RefactoringEngine()
        
        invalid_diff = "This is not a valid unified diff format"
        
        result = engine.apply({
            'type': 'apply_diff',
            'file': str(temp_file),
            'diff': invalid_diff
        })
        
        assert result['status'] == 'error'
    
    def test_apply_diff_multiple_hunks(self, temp_file):
        """Test applying a diff with multiple hunks."""
        engine = RefactoringEngine()
        
        # Diff with multiple changes
        multi_hunk_diff = '''--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
+# New comment at top
 def calculate_total(items):
     total = 0
     for item in items:
@@ -7,3 +8,4 @@ def calculate_total(items):
 def main():
     items = [{'price': 10}, {'price': 20}]
     print(calculate_total(items))
+    # New comment at bottom
'''
        
        result = engine.apply({
            'type': 'apply_diff',
            'file': str(temp_file),
            'diff': multi_hunk_diff
        })
        
        assert result['status'] == 'success'
        
        # Verify both changes were applied
        with open(temp_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert '# New comment at top' in content
        assert '# New comment at bottom' in content


class TestManualDiffApplication:
    """Test the manual diff application fallback."""
    
    @pytest.fixture
    def temp_file(self):
        """Create a temporary file."""
        temp_dir = tempfile.mkdtemp()
        file_path = Path(temp_dir) / 'test.py'
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(ORIGINAL_CODE)
        
        yield file_path
        
        shutil.rmtree(temp_dir)
    
    def test_manual_diff_simple_change(self, temp_file):
        """Test manual diff application with a simple change."""
        engine = RefactoringEngine()
        
        # Force manual application
        result = engine._apply_diff_manually(temp_file, SAMPLE_DIFF)
        
        assert result['status'] == 'success'
        
        with open(temp_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'def sum_prices(items):' in content
    
    def test_manual_diff_no_hunks(self, temp_file):
        """Test manual diff application with no valid hunks."""
        engine = RefactoringEngine()
        
        invalid_diff = "--- a/test.py\n+++ b/test.py\nNo hunks here"
        
        with pytest.raises(RefactoringError) as exc_info:
            engine._apply_diff_manually(temp_file, invalid_diff)
        
        assert "No valid hunks" in str(exc_info.value)
