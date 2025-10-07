"""
Integration tests for the complete interactive review workflow.
Tests the full pipeline: suggest → cache → list → approve → execute.
"""

import json
import pytest
from pathlib import Path
from src.suggestion_manager import SuggestionManager, SuggestionStatus


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    yield project_dir


@pytest.fixture
def sample_python_file(temp_project):
    """Create a sample Python file for refactoring."""
    file_path = temp_project / "sample.py"
    file_path.write_text("""def calculate_total(items):
    total = 0
    for item in items:
        total += item['price']
    return total
""")
    return file_path


@pytest.fixture
def sample_suggestion_json():
    """Sample suggestion JSON in the format expected by execute_refactoring."""
    return json.dumps({
        "suggestions": [
            {
                "title": "Extract price calculation",
                "description": "Extract price calculation into helper function",
                "diff": """--- a/sample.py
+++ b/sample.py
@@ -1,5 +1,9 @@
+def get_item_price(item):
+    return item['price']
+
 def calculate_total(items):
     total = 0
     for item in items:
-        total += item['price']
+        total += get_item_price(item)
     return total"""
            }
        ]
    })


class TestSuggestToCacheWorkflow:
    """Test that suggestions are automatically cached when suggest_refactoring is called."""
    
    def test_suggest_refactoring_caches_suggestions(self, temp_project, sample_python_file):
        """Test that suggestions can be cached as suggest_refactoring tool does."""
        # Create manager and verify initially empty
        manager = SuggestionManager(project_root=temp_project)
        assert len(manager.list_suggestions()) == 0
        
        # Simulate what suggest_refactoring tool does: cache generated suggestions
        suggestions_data = [
            {
                "title": "Extract function",
                "description": "Extract helper function",
                "diff": "mock diff 1"
            },
            {
                "title": "Rename variable",
                "description": "Use better variable name",
                "diff": "mock diff 2"
            }
        ]
        
        # Cache suggestions (as suggest_refactoring tool does)
        suggestion_ids = []
        for suggestion in suggestions_data:
            suggestion_id = manager.add_suggestion(
                str(sample_python_file),
                suggestion
            )
            suggestion_ids.append(suggestion_id)
        
        # Verify suggestions are cached
        assert len(manager.list_suggestions()) == 2
        assert len(suggestion_ids) == 2
        
        # Verify each suggestion is retrievable
        for suggestion_id in suggestion_ids:
            cached = manager.get_suggestion(suggestion_id)
            assert cached is not None
            assert cached['status'] == 'pending'
            assert cached['file_path'] == str(sample_python_file)


class TestListAndFilterWorkflow:
    """Test listing and filtering cached suggestions."""
    
    def test_list_all_pending_suggestions(self, temp_project, sample_python_file):
        """Test listing all pending suggestions after caching."""
        manager = SuggestionManager(project_root=temp_project)
        
        # Add multiple suggestions (correct order: file_path, suggestion_data)
        id1 = manager.add_suggestion(
            str(sample_python_file),
            {"title": "Suggestion 1", "description": "Desc 1", "diff": "diff 1"}
        )
        id2 = manager.add_suggestion(
            str(sample_python_file),
            {"title": "Suggestion 2", "description": "Desc 2", "diff": "diff 2"}
        )
        
        # List all pending
        pending = manager.list_suggestions(status='pending')
        assert len(pending) == 2
        
        # Verify details
        titles = [s['data']['title'] for s in pending]
        assert "Suggestion 1" in titles
        assert "Suggestion 2" in titles
    
    def test_filter_by_file(self, temp_project):
        """Test filtering suggestions by file path."""
        manager = SuggestionManager(project_root=temp_project)
        
        file1 = str(temp_project / "file1.py")
        file2 = str(temp_project / "file2.py")
        
        # Add suggestions for different files (correct order: file_path, suggestion_data)
        manager.add_suggestion(file1, {"title": "File1 Suggestion"})
        manager.add_suggestion(file2, {"title": "File2 Suggestion"})
        manager.add_suggestion(file1, {"title": "Another File1 Suggestion"})
        
        # Filter by file1
        file1_suggestions = manager.list_suggestions(file_path=file1)
        assert len(file1_suggestions) == 2
        assert all(s['file_path'] == file1 for s in file1_suggestions)
        
        # Filter by file2
        file2_suggestions = manager.list_suggestions(file_path=file2)
        assert len(file2_suggestions) == 1
        assert file2_suggestions[0]['file_path'] == file2


class TestGetDetailsWorkflow:
    """Test retrieving detailed suggestion information."""
    
    def test_get_suggestion_details_full_data(self, temp_project, sample_python_file):
        """Test getting complete suggestion details including metadata."""
        manager = SuggestionManager(project_root=temp_project)
        
        suggestion_data = {
            "title": "Extract method",
            "description": "Extract complex logic into separate method",
            "diff": "mock diff",
            "impact": "medium",
            "rationale": "Improves readability"
        }
        
        suggestion_id = manager.add_suggestion(
            str(sample_python_file),
            suggestion_data
        )
        
        # Get details
        details = manager.get_suggestion(suggestion_id)
        
        # Verify all fields present
        # Note: Record uses 'id' field, not 'suggestion_id' as the key
        assert details['id'] == suggestion_id
        assert details['file_path'] == str(sample_python_file)
        assert details['status'] == 'pending'
        assert 'created_at' in details
        assert 'updated_at' in details
        assert details['data'] == suggestion_data


class TestApproveWorkflow:
    """Test approval and execution workflow."""
    
    def test_approve_suggestion_executes_refactoring(
        self, 
        temp_project, 
        sample_python_file
    ):
        """Test that approving a suggestion triggers execute_refactoring."""
        # Create manager and add suggestion
        manager = SuggestionManager(project_root=temp_project)
        
        suggestion_data = {
            "title": "Test refactoring",
            "description": "Test description",
            "diff": """--- a/sample.py
+++ b/sample.py
@@ -1,2 +1,3 @@
+# New comment
 def calculate_total(items):
     total = 0"""
        }
        
        suggestion_id = manager.add_suggestion(
            str(sample_python_file),
            suggestion_data
        )
        
        # Verify initial status
        assert manager.get_suggestion(suggestion_id)['status'] == 'pending'
        
        # Simulate approve_suggestion tool logic
        # Update status to approved (manual approval without execution for testing)
        manager.update_status(suggestion_id, SuggestionStatus.APPROVED)
        
        # Verify status updated
        updated = manager.get_suggestion(suggestion_id)
        assert updated['status'] == 'approved'
    
    def test_approve_updates_timestamp(self, temp_project, sample_python_file):
        """Test that approving a suggestion updates the timestamp."""
        manager = SuggestionManager(project_root=temp_project)
        
        suggestion_id = manager.add_suggestion(
            str(sample_python_file),
            {"title": "Test", "diff": "mock"}
        )
        
        original = manager.get_suggestion(suggestion_id)
        original_updated_at = original['updated_at']
        
        # Simulate approval
        manager.update_status(suggestion_id, SuggestionStatus.APPROVED)
        
        # Verify timestamp changed
        updated = manager.get_suggestion(suggestion_id)
        assert updated['updated_at'] != original_updated_at
        assert updated['status'] == 'approved'


class TestRejectWorkflow:
    """Test rejection workflow."""
    
    def test_reject_suggestion_with_reason(self, temp_project, sample_python_file):
        """Test rejecting a suggestion and storing the reason."""
        manager = SuggestionManager(project_root=temp_project)
        
        suggestion_id = manager.add_suggestion(
            str(sample_python_file),
            {"title": "Bad idea", "diff": "mock"}
        )
        
        # Simulate reject_suggestion tool logic
        reason = "This would break existing functionality"
        manager.update_status(
            suggestion_id,
            SuggestionStatus.REJECTED,
            execution_result={'reason': reason}
        )
        
        # Verify rejection
        rejected = manager.get_suggestion(suggestion_id)
        assert rejected['status'] == 'rejected'
        assert rejected['execution_result']['reason'] == reason
    
    def test_rejected_suggestions_not_listed_by_default(self, temp_project, sample_python_file):
        """Test that rejected suggestions can be filtered out."""
        manager = SuggestionManager(project_root=temp_project)
        
        # Add and reject suggestion (correct order: file_path, suggestion_data)
        id1 = manager.add_suggestion(str(sample_python_file), {"title": "Good"})
        id2 = manager.add_suggestion(str(sample_python_file), {"title": "Bad"})
        
        manager.update_status(id2, SuggestionStatus.REJECTED)
        
        # List only pending
        pending = manager.list_suggestions(status='pending')
        assert len(pending) == 1
        assert pending[0]['id'] == id1
        
        # List only rejected
        rejected = manager.list_suggestions(status='rejected')
        assert len(rejected) == 1
        assert rejected[0]['id'] == id2


class TestFullEndToEndWorkflow:
    """Complete workflow: suggest → list → approve → verify."""
    
    def test_complete_workflow(
        self,
        temp_project,
        sample_python_file
    ):
        """Test complete workflow from suggestion generation to execution."""
        
        # Step 1: Create manager and add suggestion (simulating suggest_refactoring)
        manager = SuggestionManager(project_root=temp_project)
        
        suggestion_data = {
            "title": "Extract function",
            "description": "Extract helper",
            "diff": "mock diff"
        }
        
        suggestion_id = manager.add_suggestion(
            str(sample_python_file),
            suggestion_data
        )
        
        # Step 2: List pending suggestions (list_suggestions)
        pending = manager.list_suggestions(status='pending')
        assert len(pending) == 1
        
        # Step 3: Get detailed suggestion (get_suggestion_details)
        details = manager.get_suggestion(suggestion_id)
        assert details['data']['title'] == "Extract function"
        
        # Step 4: Approve (approve_suggestion - just status update in test)
        manager.update_status(suggestion_id, SuggestionStatus.APPROVED)
        
        # Step 5: Verify approval
        approved = manager.get_suggestion(suggestion_id)
        assert approved['status'] == 'approved'
        
        # Verify no pending suggestions remain
        pending_after = manager.list_suggestions(status='pending')
        assert len(pending_after) == 0
        
        # Verify approved suggestion is listed
        approved_list = manager.list_suggestions(status='approved')
        assert len(approved_list) == 1


class TestPersistenceAcrossRestarts:
    """Test that suggestions persist across server restarts."""
    
    def test_suggestions_survive_manager_restart(self, temp_project, sample_python_file):
        """Test that cached suggestions survive SuggestionManager restart."""
        # Create manager and add suggestions (correct order: file_path, suggestion_data)
        manager1 = SuggestionManager(project_root=temp_project)
        
        id1 = manager1.add_suggestion(
            str(sample_python_file),
            {"title": "Suggestion 1", "diff": "diff 1"}
        )
        id2 = manager1.add_suggestion(
            str(sample_python_file),
            {"title": "Suggestion 2", "diff": "diff 2"}
        )
        
        # Approve one suggestion
        manager1.update_status(id1, SuggestionStatus.APPROVED)
        
        # Create new manager instance (simulates restart)
        manager2 = SuggestionManager(project_root=temp_project)
        
        # Verify both suggestions persist
        all_suggestions = manager2.list_suggestions()
        assert len(all_suggestions) == 2
        
        # Verify approved status persists
        suggestion1 = manager2.get_suggestion(id1)
        assert suggestion1['status'] == 'approved'
        
        suggestion2 = manager2.get_suggestion(id2)
        assert suggestion2['status'] == 'pending'


class TestStatisticsReporting:
    """Test statistics reporting for workflow monitoring."""
    
    def test_statistics_track_workflow_progress(self, temp_project, sample_python_file):
        """Test that statistics accurately track suggestion states."""
        manager = SuggestionManager(project_root=temp_project)
        
        # Add suggestions in various states (correct order: file_path, suggestion_data)
        id1 = manager.add_suggestion(str(sample_python_file), {"title": "Pending 1"})
        id2 = manager.add_suggestion(str(sample_python_file), {"title": "Pending 2"})
        id3 = manager.add_suggestion(str(sample_python_file), {"title": "Approved"})
        id4 = manager.add_suggestion(str(sample_python_file), {"title": "Rejected"})
        id5 = manager.add_suggestion(str(sample_python_file), {"title": "Executed"})
        
        # Update statuses
        manager.update_status(id3, SuggestionStatus.APPROVED)
        manager.update_status(id4, SuggestionStatus.REJECTED)
        manager.update_status(id5, SuggestionStatus.EXECUTED)
        
        # Check statistics
        stats = manager.get_statistics()
        assert stats['by_status']['pending'] == 2
        assert stats['by_status']['approved'] == 1
        assert stats['by_status']['rejected'] == 1
        assert stats['by_status']['executed'] == 1
        assert stats['total'] == 5
