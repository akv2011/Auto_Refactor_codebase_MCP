"""
Integration tests for execute_refactoring MCP tool.

These tests verify the complete workflow of the execute_refactoring tool,
including dry run mode, successful execution, test verification, and automatic rollback.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import shutil


# Sample code for testing
ORIGINAL_CODE = """def calculate_total(prices):
    total = 0
    for price in prices:
        total += price
    return total
"""

# Sample AI suggestion with diff
SAMPLE_SUGGESTION = {
    "suggestions": [
        {
            "type": "extract_function",
            "severity": "medium",
            "confidence": 0.9,
            "description": "Extract price summing logic into helper function",
            "diff": """--- test.py
+++ test.py
@@ -1,5 +1,9 @@
+def sum_prices(prices):
+    return sum(prices)
+
 def calculate_total(prices):
-    total = 0
-    for price in prices:
-        total += price
-    return total
+    return sum_prices(prices)
""",
            "rationale": "Improve code clarity by extracting helper function"
        }
    ]
}

EXPECTED_MODIFIED_CODE = """def sum_prices(prices):
    return sum(prices)

def calculate_total(prices):
    return sum_prices(prices)
"""


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory with a Python file."""
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create a simple Python file
    test_file = temp_dir / 'test.py'
    test_file.write_text(ORIGINAL_CODE)
    
    # Create a simple test file
    test_test_file = temp_dir / 'test_test.py'
    test_test_file.write_text("""
def test_calculate_total():
    assert True  # Placeholder test
""")
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_git_manager():
    """Mock GitManager for testing."""
    with patch('taskmaster.git_manager.GitManager') as mock_class:
        mock_instance = Mock()
        mock_instance.is_git_repo.return_value = True
        mock_instance.create_backup_branch.return_value = 'backup-branch-123'
        mock_instance.restore_backup_branch.return_value = True
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_rollback_manager():
    """Mock RollbackManager for testing."""
    with patch('taskmaster.rollback_manager.RollbackManager') as mock_class:
        mock_instance = Mock()
        mock_instance.record_operation.return_value = 'op-123'
        mock_instance.rollback_operation.return_value = {
            'status': 'success',
            'operation_id': 'op-123'
        }
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_test_runner_success():
    """Mock TestRunner that always passes tests."""
    with patch('taskmaster.test_runner.TestRunner') as mock_class:
        mock_instance = Mock()
        mock_async = AsyncMock()
        mock_async.return_value = {
            'status': 'success',
            'tests_passed': True,
            'output': 'All tests passed'
        }
        mock_instance.run_async = mock_async
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_test_runner_failure():
    """Mock TestRunner that always fails tests."""
    with patch('taskmaster.test_runner.TestRunner') as mock_class:
        mock_instance = Mock()
        mock_async = AsyncMock()
        mock_async.return_value = {
            'status': 'error',
            'tests_passed': False,
            'output': 'Tests failed'
        }
        mock_instance.run_async = mock_async
        mock_class.return_value = mock_instance
        yield mock_instance


class TestExecuteRefactoringDryRun:
    """Test dry run mode of execute_refactoring."""
    
    @pytest.mark.asyncio
    async def test_dry_run_returns_preview(self, temp_project_dir):
        """Test that dry run mode returns preview without making changes."""
        from taskmaster import execute_refactoring
        
        test_file = temp_project_dir / 'test.py'
        original_content = test_file.read_text()
        
        result_json = await execute_refactoring(
            file_path=str(test_file),
            suggestion_json=json.dumps(SAMPLE_SUGGESTION),
            dry_run=True
        )
        
        result = json.loads(result_json)
        
        # Verify response structure
        assert result['status'] == 'success'
        assert result['dry_run'] is True
        assert result['file_path'] == str(test_file)
        assert 'diff_preview' in result
        assert 'sum_prices' in result['diff_preview']
        
        # Verify file was NOT modified
        assert test_file.read_text() == original_content
    
    @pytest.mark.asyncio
    async def test_dry_run_with_invalid_json(self, temp_project_dir):
        """Test that dry run handles invalid JSON gracefully."""
        from taskmaster import execute_refactoring
        
        test_file = temp_project_dir / 'test.py'
        
        result_json = await execute_refactoring(
            file_path=str(test_file),
            suggestion_json="invalid json",
            dry_run=True
        )
        
        result = json.loads(result_json)
        
        assert result['status'] == 'error'
        assert 'json' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_dry_run_with_missing_suggestions(self, temp_project_dir):
        """Test that dry run handles missing suggestions array."""
        from taskmaster import execute_refactoring
        
        test_file = temp_project_dir / 'test.py'
        
        result_json = await execute_refactoring(
            file_path=str(test_file),
            suggestion_json=json.dumps({"no_suggestions": True}),
            dry_run=True
        )
        
        result = json.loads(result_json)
        
        assert result['status'] == 'error'
        assert 'suggestions' in result['error'].lower()


class TestExecuteRefactoringWithMocks:
    """Test execute_refactoring with mocked dependencies."""
    
    @pytest.mark.asyncio
    async def test_successful_execution(
        self, 
        temp_project_dir, 
        mock_git_manager, 
        mock_rollback_manager,
        mock_test_runner_success
    ):
        """Test successful refactoring execution with passing tests."""
        from taskmaster import execute_refactoring
        
        test_file = temp_project_dir / 'test.py'
        
        # Mock GitManager to avoid actual Git operations
        with patch('taskmaster.GitManager') as MockGit:
            MockGit.return_value = mock_git_manager
            
            with patch('taskmaster.RollbackManager') as MockRollback:
                MockRollback.return_value = mock_rollback_manager
                
                with patch('taskmaster.TestRunner') as MockTest:
                    MockTest.return_value = mock_test_runner_success
                    
                    result_json = await execute_refactoring(
                        file_path=str(test_file),
                        suggestion_json=json.dumps(SAMPLE_SUGGESTION),
                        dry_run=False
                    )
        
        result = json.loads(result_json)
        
        # Verify successful execution
        assert result['status'] == 'success'
        assert result['dry_run'] is False
        assert result['changes_applied'] is True
        assert result['tests_passed'] is True
        assert result['rolled_back'] is False
        
        # Verify mocks were called correctly
        mock_git_manager.create_backup_branch.assert_called_once()
        mock_rollback_manager.record_operation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rollback_on_test_failure(
        self, 
        temp_project_dir, 
        mock_git_manager, 
        mock_rollback_manager,
        mock_test_runner_failure
    ):
        """Test that refactoring is rolled back when tests fail."""
        from taskmaster import execute_refactoring
        
        test_file = temp_project_dir / 'test.py'
        
        with patch('taskmaster.GitManager') as MockGit:
            MockGit.return_value = mock_git_manager
            
            with patch('taskmaster.RollbackManager') as MockRollback:
                MockRollback.return_value = mock_rollback_manager
                
                with patch('taskmaster.TestRunner') as MockTest:
                    MockTest.return_value = mock_test_runner_failure
                    
                    result_json = await execute_refactoring(
                        file_path=str(test_file),
                        suggestion_json=json.dumps(SAMPLE_SUGGESTION),
                        dry_run=False
                    )
        
        result = json.loads(result_json)
        
        # Verify rollback occurred
        assert result['status'] == 'error'
        assert result['tests_passed'] is False
        assert result['rolled_back'] is True
        assert 'rolled back' in result['message'].lower()
        
        # Verify rollback was called
        mock_rollback_manager.rollback_operation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_no_git_repo_uses_refactoring_only(
        self, 
        temp_project_dir,
        mock_test_runner_success
    ):
        """Test that refactoring works without Git (no backup/rollback)."""
        from taskmaster import execute_refactoring
        
        test_file = temp_project_dir / 'test.py'
        
        # Mock GitManager to return False for is_git_repo
        with patch('taskmaster.GitManager') as MockGit:
            mock_git = Mock()
            mock_git.is_git_repo.return_value = False
            MockGit.return_value = mock_git
            
            with patch('taskmaster.TestRunner') as MockTest:
                MockTest.return_value = mock_test_runner_success
                
                result_json = await execute_refactoring(
                    file_path=str(test_file),
                    suggestion_json=json.dumps(SAMPLE_SUGGESTION),
                    dry_run=False
                )
        
        result = json.loads(result_json)
        
        # Should still succeed but without Git backup
        assert result['status'] == 'success'
        assert result['changes_applied'] is True
        
        # Verify backup branch was NOT created
        mock_git.create_backup_branch.assert_not_called()


class TestExecuteRefactoringRealIntegration:
    """Test execute_refactoring with real (non-mocked) components."""
    
    @pytest.mark.asyncio
    async def test_real_diff_application(self, temp_project_dir):
        """Test actual diff application without mocks."""
        from taskmaster import execute_refactoring
        
        test_file = temp_project_dir / 'test.py'
        original_content = test_file.read_text()
        
        # First, do dry run
        dry_result_json = await execute_refactoring(
            file_path=str(test_file),
            suggestion_json=json.dumps(SAMPLE_SUGGESTION),
            dry_run=True
        )
        
        dry_result = json.loads(dry_result_json)
        assert dry_result['status'] == 'success'
        assert dry_result['dry_run'] is True
        
        # File should be unchanged after dry run
        assert test_file.read_text() == original_content
        
        # Now apply for real (but skip Git/tests with mocks)
        with patch('taskmaster.GitManager') as MockGit:
            mock_git = Mock()
            mock_git.is_git_repo.return_value = False
            MockGit.return_value = mock_git
            
            with patch('taskmaster.TestRunner') as MockTest:
                mock_test = Mock()
                mock_async = AsyncMock()
                mock_async.return_value = {
                    'status': 'success',
                    'tests_passed': True,
                    'output': 'Tests passed'
                }
                mock_test.run_async = mock_async
                MockTest.return_value = mock_test
                
                result_json = await execute_refactoring(
                    file_path=str(test_file),
                    suggestion_json=json.dumps(SAMPLE_SUGGESTION),
                    dry_run=False
                )
        
        result = json.loads(result_json)
        
        # Verify execution succeeded
        assert result['status'] == 'success'
        assert result['changes_applied'] is True
        
        # Verify file WAS modified
        modified_content = test_file.read_text()
        assert modified_content != original_content
        assert 'sum_prices' in modified_content


class TestExecuteRefactoringEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_nonexistent_file(self):
        """Test that nonexistent file returns error."""
        from taskmaster import execute_refactoring
        
        result_json = await execute_refactoring(
            file_path="/nonexistent/file.py",
            suggestion_json=json.dumps(SAMPLE_SUGGESTION),
            dry_run=True
        )
        
        result = json.loads(result_json)
        
        assert result['status'] == 'error'
        assert 'not found' in result['error'].lower() or 'exist' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_empty_diff(self, temp_project_dir):
        """Test handling of suggestion with empty diff."""
        from taskmaster import execute_refactoring
        
        test_file = temp_project_dir / 'test.py'
        
        empty_suggestion = {
            "suggestions": [
                {
                    "type": "test",
                    "diff": "",
                    "description": "No changes"
                }
            ]
        }
        
        result_json = await execute_refactoring(
            file_path=str(test_file),
            suggestion_json=json.dumps(empty_suggestion),
            dry_run=True
        )
        
        result = json.loads(result_json)
        
        # Empty diff should succeed (no changes to apply)
        assert result['status'] == 'success'
    
    @pytest.mark.asyncio
    async def test_multiple_suggestions_uses_first(self, temp_project_dir):
        """Test that tool uses the first suggestion when multiple are provided."""
        from taskmaster import execute_refactoring
        
        test_file = temp_project_dir / 'test.py'
        
        multi_suggestion = {
            "suggestions": [
                SAMPLE_SUGGESTION["suggestions"][0],
                {
                    "type": "other",
                    "diff": "--- different.py\n+++ different.py\n",
                    "description": "Another change"
                }
            ]
        }
        
        result_json = await execute_refactoring(
            file_path=str(test_file),
            suggestion_json=json.dumps(multi_suggestion),
            dry_run=True
        )
        
        result = json.loads(result_json)
        
        # Should use first suggestion
        assert result['status'] == 'success'
        assert 'sum_prices' in result['diff_preview']
