"""
Tests for SuggestionManager

This module tests the suggestion caching and state management system.
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from src.suggestion_manager import (
    SuggestionManager,
    SuggestionStatus,
    SuggestionManagerError,
    SuggestionNotFoundError,
    InvalidSuggestionError,
)


# Sample suggestion data
SAMPLE_SUGGESTION = {
    'suggestions': [
        {
            'type': 'extract_function',
            'title': 'Extract helper function',
            'description': 'Extract price summing logic',
            'diff': '--- test.py\n+++ test.py\n@@ -1,5 +1,9 @@\n+def sum_prices(prices):\n+    return sum(prices)\n+\n def calculate_total(prices):\n-    total = 0\n-    for price in prices:\n-        total += price\n-    return total\n+    return sum_prices(prices)\n',
            'rationale': 'Improve code clarity'
        }
    ]
}


@pytest.fixture
def temp_project():
    """Create a temporary project directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def manager(temp_project):
    """Create a SuggestionManager instance."""
    return SuggestionManager(project_root=temp_project)


class TestSuggestionManagerInit:
    """Test SuggestionManager initialization."""
    
    def test_init_creates_taskmaster_directory(self, temp_project):
        """Test that __init__ creates .taskmaster directory."""
        manager = SuggestionManager(project_root=temp_project)
        
        assert manager.taskmaster_dir.exists()
        assert manager.taskmaster_dir.is_dir()
        assert manager.taskmaster_dir.name == '.taskmaster'
    
    def test_init_creates_cache_file(self, temp_project):
        """Test that __init__ creates cache file."""
        manager = SuggestionManager(project_root=temp_project)
        
        assert manager.cache_file.exists()
        assert manager.cache_file.name == 'suggestions_cache.json'
    
    def test_init_with_existing_cache(self, temp_project):
        """Test initialization with existing cache data."""
        # Create manager and add a suggestion
        manager1 = SuggestionManager(project_root=temp_project)
        suggestion_id = manager1.add_suggestion('test.py', SAMPLE_SUGGESTION)
        
        # Create new manager instance
        manager2 = SuggestionManager(project_root=temp_project)
        
        # Should load existing suggestions
        assert suggestion_id in manager2.suggestions
        assert len(manager2.suggestions) == 1
    
    def test_init_with_corrupted_cache(self, temp_project):
        """Test initialization with corrupted cache file."""
        # Create manager
        manager = SuggestionManager(project_root=temp_project)
        
        # Corrupt the cache file
        with open(manager.cache_file, 'w') as f:
            f.write('invalid json{{}')
        
        # Create new manager - should start fresh
        manager2 = SuggestionManager(project_root=temp_project)
        assert len(manager2.suggestions) == 0


class TestAddSuggestion:
    """Test adding suggestions."""
    
    def test_add_suggestion_basic(self, manager):
        """Test adding a basic suggestion."""
        suggestion_id = manager.add_suggestion(
            'test.py',
            SAMPLE_SUGGESTION
        )
        
        assert suggestion_id is not None
        assert len(suggestion_id) == 8  # UUID truncated to 8 chars
        assert suggestion_id in manager.suggestions
    
    def test_add_suggestion_returns_unique_ids(self, manager):
        """Test that multiple suggestions get unique IDs."""
        id1 = manager.add_suggestion('test1.py', SAMPLE_SUGGESTION)
        id2 = manager.add_suggestion('test2.py', SAMPLE_SUGGESTION)
        id3 = manager.add_suggestion('test3.py', SAMPLE_SUGGESTION)
        
        assert id1 != id2
        assert id2 != id3
        assert id1 != id3
    
    def test_add_suggestion_with_metadata(self, manager):
        """Test adding suggestion with metadata."""
        metadata = {
            'strategy': 'extract',
            'metrics': {'complexity': 10}
        }
        
        suggestion_id = manager.add_suggestion(
            'test.py',
            SAMPLE_SUGGESTION,
            metadata=metadata
        )
        
        suggestion = manager.get_suggestion(suggestion_id)
        assert suggestion['metadata'] == metadata
    
    def test_add_suggestion_sets_default_values(self, manager):
        """Test that default values are set correctly."""
        suggestion_id = manager.add_suggestion('test.py', SAMPLE_SUGGESTION)
        suggestion = manager.get_suggestion(suggestion_id)
        
        assert suggestion['status'] == SuggestionStatus.PENDING.value
        assert suggestion['file_path'] == 'test.py'
        assert suggestion['data'] == SAMPLE_SUGGESTION
        assert 'created_at' in suggestion
        assert 'updated_at' in suggestion
        assert suggestion['execution_result'] is None
    
    def test_add_suggestion_invalid_data(self, manager):
        """Test that invalid suggestion data raises error."""
        with pytest.raises(InvalidSuggestionError):
            manager.add_suggestion('test.py', 'not a dict')
    
    def test_add_suggestion_persists_to_file(self, manager):
        """Test that suggestions are persisted to cache file."""
        suggestion_id = manager.add_suggestion('test.py', SAMPLE_SUGGESTION)
        
        # Read cache file directly
        with open(manager.cache_file, 'r') as f:
            cache_data = json.load(f)
        
        assert suggestion_id in cache_data
        assert cache_data[suggestion_id]['file_path'] == 'test.py'


class TestGetSuggestion:
    """Test retrieving suggestions."""
    
    def test_get_suggestion_success(self, manager):
        """Test successfully retrieving a suggestion."""
        suggestion_id = manager.add_suggestion('test.py', SAMPLE_SUGGESTION)
        
        suggestion = manager.get_suggestion(suggestion_id)
        
        assert suggestion['id'] == suggestion_id
        assert suggestion['file_path'] == 'test.py'
        assert suggestion['data'] == SAMPLE_SUGGESTION
    
    def test_get_suggestion_not_found(self, manager):
        """Test retrieving non-existent suggestion."""
        with pytest.raises(SuggestionNotFoundError) as exc_info:
            manager.get_suggestion('nonexistent')
        
        assert 'not found' in str(exc_info.value).lower()


class TestListSuggestions:
    """Test listing suggestions."""
    
    def test_list_suggestions_empty(self, manager):
        """Test listing when cache is empty."""
        suggestions = manager.list_suggestions()
        assert suggestions == []
    
    def test_list_suggestions_all(self, manager):
        """Test listing all suggestions."""
        id1 = manager.add_suggestion('test1.py', SAMPLE_SUGGESTION)
        id2 = manager.add_suggestion('test2.py', SAMPLE_SUGGESTION)
        id3 = manager.add_suggestion('test3.py', SAMPLE_SUGGESTION)
        
        suggestions = manager.list_suggestions()
        
        assert len(suggestions) == 3
        ids = [s['id'] for s in suggestions]
        assert id1 in ids
        assert id2 in ids
        assert id3 in ids
    
    def test_list_suggestions_filter_by_status(self, manager):
        """Test filtering suggestions by status."""
        id1 = manager.add_suggestion('test1.py', SAMPLE_SUGGESTION)
        id2 = manager.add_suggestion('test2.py', SAMPLE_SUGGESTION)
        id3 = manager.add_suggestion('test3.py', SAMPLE_SUGGESTION)
        
        # Update statuses
        manager.update_status(id1, SuggestionStatus.APPROVED)
        manager.update_status(id2, SuggestionStatus.REJECTED)
        # id3 remains PENDING
        
        pending = manager.list_suggestions(status='pending')
        approved = manager.list_suggestions(status='approved')
        rejected = manager.list_suggestions(status='rejected')
        
        assert len(pending) == 1
        assert pending[0]['id'] == id3
        assert len(approved) == 1
        assert approved[0]['id'] == id1
        assert len(rejected) == 1
        assert rejected[0]['id'] == id2
    
    def test_list_suggestions_filter_by_file(self, manager):
        """Test filtering suggestions by file path."""
        id1 = manager.add_suggestion('test1.py', SAMPLE_SUGGESTION)
        id2 = manager.add_suggestion('test2.py', SAMPLE_SUGGESTION)
        id3 = manager.add_suggestion('test1.py', SAMPLE_SUGGESTION)
        
        test1_suggestions = manager.list_suggestions(file_path='test1.py')
        test2_suggestions = manager.list_suggestions(file_path='test2.py')
        
        assert len(test1_suggestions) == 2
        assert len(test2_suggestions) == 1
    
    def test_list_suggestions_with_limit(self, manager):
        """Test limiting number of results."""
        for i in range(10):
            manager.add_suggestion(f'test{i}.py', SAMPLE_SUGGESTION)
        
        suggestions = manager.list_suggestions(limit=5)
        
        assert len(suggestions) == 5
    
    def test_list_suggestions_sorted_by_date(self, manager):
        """Test that suggestions are sorted by creation date (newest first)."""
        id1 = manager.add_suggestion('test1.py', SAMPLE_SUGGESTION)
        id2 = manager.add_suggestion('test2.py', SAMPLE_SUGGESTION)
        id3 = manager.add_suggestion('test3.py', SAMPLE_SUGGESTION)
        
        suggestions = manager.list_suggestions()
        
        # Most recent should be first
        assert suggestions[0]['id'] == id3
        assert suggestions[1]['id'] == id2
        assert suggestions[2]['id'] == id1


class TestUpdateStatus:
    """Test updating suggestion status."""
    
    def test_update_status_basic(self, manager):
        """Test basic status update."""
        suggestion_id = manager.add_suggestion('test.py', SAMPLE_SUGGESTION)
        
        manager.update_status(suggestion_id, SuggestionStatus.APPROVED)
        
        suggestion = manager.get_suggestion(suggestion_id)
        assert suggestion['status'] == SuggestionStatus.APPROVED.value
    
    def test_update_status_with_execution_result(self, manager):
        """Test status update with execution result."""
        suggestion_id = manager.add_suggestion('test.py', SAMPLE_SUGGESTION)
        
        execution_result = {
            'status': 'success',
            'tests_passed': True
        }
        
        manager.update_status(
            suggestion_id,
            SuggestionStatus.EXECUTED,
            execution_result=execution_result
        )
        
        suggestion = manager.get_suggestion(suggestion_id)
        assert suggestion['status'] == SuggestionStatus.EXECUTED.value
        assert suggestion['execution_result'] == execution_result
    
    def test_update_status_updates_timestamp(self, manager):
        """Test that status update changes updated_at timestamp."""
        suggestion_id = manager.add_suggestion('test.py', SAMPLE_SUGGESTION)
        
        suggestion_before = manager.get_suggestion(suggestion_id)
        original_updated_at = suggestion_before['updated_at']
        
        # Wait a moment and update
        import time
        time.sleep(0.01)
        
        manager.update_status(suggestion_id, SuggestionStatus.APPROVED)
        
        suggestion_after = manager.get_suggestion(suggestion_id)
        new_updated_at = suggestion_after['updated_at']
        
        assert new_updated_at != original_updated_at
    
    def test_update_status_not_found(self, manager):
        """Test updating status of non-existent suggestion."""
        with pytest.raises(SuggestionNotFoundError):
            manager.update_status('nonexistent', SuggestionStatus.APPROVED)


class TestDeleteSuggestion:
    """Test deleting suggestions."""
    
    def test_delete_suggestion_success(self, manager):
        """Test successfully deleting a suggestion."""
        suggestion_id = manager.add_suggestion('test.py', SAMPLE_SUGGESTION)
        
        assert suggestion_id in manager.suggestions
        
        manager.delete_suggestion(suggestion_id)
        
        assert suggestion_id not in manager.suggestions
    
    def test_delete_suggestion_not_found(self, manager):
        """Test deleting non-existent suggestion."""
        with pytest.raises(SuggestionNotFoundError):
            manager.delete_suggestion('nonexistent')
    
    def test_delete_suggestion_persists(self, manager):
        """Test that deletion is persisted to cache file."""
        suggestion_id = manager.add_suggestion('test.py', SAMPLE_SUGGESTION)
        
        manager.delete_suggestion(suggestion_id)
        
        # Read cache file directly
        with open(manager.cache_file, 'r') as f:
            cache_data = json.load(f)
        
        assert suggestion_id not in cache_data


class TestClearCache:
    """Test clearing the suggestion cache."""
    
    def test_clear_cache_all(self, manager):
        """Test clearing all suggestions."""
        # Add multiple suggestions
        for i in range(5):
            manager.add_suggestion(f'test{i}.py', SAMPLE_SUGGESTION)
        
        assert len(manager.suggestions) == 5
        
        count = manager.clear_cache()
        
        assert count == 5
        assert len(manager.suggestions) == 0
    
    def test_clear_cache_by_status(self, manager):
        """Test clearing suggestions by status."""
        id1 = manager.add_suggestion('test1.py', SAMPLE_SUGGESTION)
        id2 = manager.add_suggestion('test2.py', SAMPLE_SUGGESTION)
        id3 = manager.add_suggestion('test3.py', SAMPLE_SUGGESTION)
        
        manager.update_status(id1, SuggestionStatus.REJECTED)
        manager.update_status(id2, SuggestionStatus.REJECTED)
        # id3 remains PENDING
        
        count = manager.clear_cache(status='rejected')
        
        assert count == 2
        assert len(manager.suggestions) == 1
        assert id3 in manager.suggestions
    
    def test_clear_cache_by_age(self, manager, monkeypatch):
        """Test clearing old suggestions."""
        # Add suggestions
        id1 = manager.add_suggestion('test1.py', SAMPLE_SUGGESTION)
        id2 = manager.add_suggestion('test2.py', SAMPLE_SUGGESTION)
        
        # Make id1 appear old by modifying created_at
        old_date = (datetime.now() - timedelta(days=10)).isoformat()
        manager.suggestions[id1]['created_at'] = old_date
        manager._save_cache()
        
        # Clear suggestions older than 5 days
        count = manager.clear_cache(older_than_days=5)
        
        assert count == 1
        assert id1 not in manager.suggestions
        assert id2 in manager.suggestions


class TestGetStatistics:
    """Test getting cache statistics."""
    
    def test_get_statistics_empty(self, manager):
        """Test statistics for empty cache."""
        stats = manager.get_statistics()
        
        assert stats['total'] == 0
        assert stats['by_status']['pending'] == 0
    
    def test_get_statistics_with_suggestions(self, manager):
        """Test statistics with various suggestions."""
        id1 = manager.add_suggestion('test1.py', SAMPLE_SUGGESTION)
        id2 = manager.add_suggestion('test2.py', SAMPLE_SUGGESTION)
        id3 = manager.add_suggestion('test1.py', SAMPLE_SUGGESTION)
        
        manager.update_status(id1, SuggestionStatus.APPROVED)
        manager.update_status(id2, SuggestionStatus.EXECUTED)
        # id3 remains PENDING
        
        stats = manager.get_statistics()
        
        assert stats['total'] == 3
        assert stats['by_status']['pending'] == 1
        assert stats['by_status']['approved'] == 1
        assert stats['by_status']['executed'] == 1
        assert stats['by_file']['test1.py'] == 2
        assert stats['by_file']['test2.py'] == 1
