"""
Tests for the rollback_manager module.

This module tests the RollbackManager class and rollback_refactoring function,
including operation tracking, rollback functionality, and Git integration.
"""

import pytest
import asyncio
from pathlib import Path
import json
import tempfile
import shutil
from datetime import datetime

from src.rollback_manager import (
    RollbackManager,
    RollbackError,
    OperationNotFoundError,
    rollback_refactoring
)
from src.git_manager import GitManager


class TestRollbackManagerInit:
    """Tests for RollbackManager initialization."""
    
    def test_init_creates_history_file(self, temp_git_repo):
        """Test that initialization creates the history file."""
        manager = RollbackManager(temp_git_repo)
        
        assert manager.history_file.exists()
        assert manager.history_file.parent.name == ".taskmaster"
    
    def test_init_creates_taskmaster_directory(self, temp_git_repo):
        """Test that initialization creates .taskmaster directory."""
        manager = RollbackManager(temp_git_repo)
        
        taskmaster_dir = Path(temp_git_repo) / ".taskmaster"
        assert taskmaster_dir.exists()
        assert taskmaster_dir.is_dir()
    
    def test_init_initializes_empty_history(self, temp_git_repo):
        """Test that new history file contains empty list."""
        manager = RollbackManager(temp_git_repo)
        
        with open(manager.history_file) as f:
            history = json.load(f)
        
        assert history == []
    
    def test_init_preserves_existing_history(self, temp_git_repo):
        """Test that existing history is preserved."""
        # Create initial manager and record operation
        manager1 = RollbackManager(temp_git_repo)
        op_id = manager1.record_operation(
            operation_type='test',
            backup_branch='backup-test',
            commit_before='abc123'
        )
        
        # Create new manager with same path
        manager2 = RollbackManager(temp_git_repo)
        
        # Should still have the operation
        operation = manager2.get_operation(op_id)
        assert operation['operation_type'] == 'test'


class TestRecordOperation:
    """Tests for recording operations in history."""
    
    def test_record_operation_basic(self, temp_git_repo):
        """Test recording a basic operation."""
        manager = RollbackManager(temp_git_repo)
        
        op_id = manager.record_operation(
            operation_type='extract_function',
            backup_branch='backup-20231005143022',
            commit_before='abc123'
        )
        
        assert op_id is not None
        assert len(op_id) > 0
    
    def test_record_operation_creates_unique_ids(self, temp_git_repo):
        """Test that each operation gets a unique ID."""
        manager = RollbackManager(temp_git_repo)
        
        op_id1 = manager.record_operation(
            operation_type='extract_function',
            backup_branch='backup-1',
            commit_before='abc123'
        )
        
        op_id2 = manager.record_operation(
            operation_type='split_file',
            backup_branch='backup-2',
            commit_before='def456'
        )
        
        assert op_id1 != op_id2
    
    def test_record_operation_with_all_fields(self, temp_git_repo):
        """Test recording operation with all optional fields."""
        manager = RollbackManager(temp_git_repo)
        
        op_id = manager.record_operation(
            operation_type='extract_function',
            backup_branch='backup-20231005143022',
            commit_before='abc123',
            commit_after='def456',
            files_modified=['app.py', 'utils.py'],
            files_created=['helpers.py'],
            operation_details={'function_name': 'helper', 'target': 'helpers.py'}
        )
        
        operation = manager.get_operation(op_id)
        
        assert operation['operation_type'] == 'extract_function'
        assert operation['backup_branch'] == 'backup-20231005143022'
        assert operation['commit_before'] == 'abc123'
        assert operation['commit_after'] == 'def456'
        assert operation['files_modified'] == ['app.py', 'utils.py']
        assert operation['files_created'] == ['helpers.py']
        assert operation['operation_details']['function_name'] == 'helper'
        assert operation['rolled_back'] is False
    
    def test_record_operation_saves_timestamp(self, temp_git_repo):
        """Test that operation timestamp is recorded."""
        manager = RollbackManager(temp_git_repo)
        
        before = datetime.now()
        op_id = manager.record_operation(
            operation_type='test',
            backup_branch='backup-test',
            commit_before='abc123'
        )
        after = datetime.now()
        
        operation = manager.get_operation(op_id)
        timestamp = datetime.fromisoformat(operation['timestamp'])
        
        assert before <= timestamp <= after


class TestGetOperation:
    """Tests for retrieving operations from history."""
    
    def test_get_operation_exists(self, temp_git_repo):
        """Test getting an existing operation."""
        manager = RollbackManager(temp_git_repo)
        
        op_id = manager.record_operation(
            operation_type='extract_function',
            backup_branch='backup-test',
            commit_before='abc123'
        )
        
        operation = manager.get_operation(op_id)
        
        assert operation['operation_id'] == op_id
        assert operation['operation_type'] == 'extract_function'
    
    def test_get_operation_not_found(self, temp_git_repo):
        """Test getting a non-existent operation raises error."""
        manager = RollbackManager(temp_git_repo)
        
        with pytest.raises(OperationNotFoundError) as exc_info:
            manager.get_operation('nonexistent-id')
        
        assert 'not found' in str(exc_info.value).lower()
    
    def test_get_operation_returns_all_fields(self, temp_git_repo):
        """Test that all operation fields are returned."""
        manager = RollbackManager(temp_git_repo)
        
        op_id = manager.record_operation(
            operation_type='extract_function',
            backup_branch='backup-test',
            commit_before='abc123',
            commit_after='def456',
            files_modified=['file1.py'],
            files_created=['file2.py'],
            operation_details={'key': 'value'}
        )
        
        operation = manager.get_operation(op_id)
        
        assert 'operation_id' in operation
        assert 'operation_type' in operation
        assert 'timestamp' in operation
        assert 'backup_branch' in operation
        assert 'commit_before' in operation
        assert 'commit_after' in operation
        assert 'files_modified' in operation
        assert 'files_created' in operation
        assert 'operation_details' in operation
        assert 'rolled_back' in operation


class TestListOperations:
    """Tests for listing operations."""
    
    def test_list_operations_empty(self, temp_git_repo):
        """Test listing operations when history is empty."""
        manager = RollbackManager(temp_git_repo)
        
        operations = manager.list_operations()
        
        assert operations == []
    
    def test_list_operations_all(self, temp_git_repo):
        """Test listing all operations."""
        manager = RollbackManager(temp_git_repo)
        
        # Record multiple operations
        op_id1 = manager.record_operation(
            operation_type='extract_function',
            backup_branch='backup-1',
            commit_before='abc123'
        )
        op_id2 = manager.record_operation(
            operation_type='split_file',
            backup_branch='backup-2',
            commit_before='def456'
        )
        
        operations = manager.list_operations()
        
        assert len(operations) == 2
        # Should be in reverse chronological order (most recent first)
        assert operations[0]['operation_id'] == op_id2
        assert operations[1]['operation_id'] == op_id1
    
    def test_list_operations_with_limit(self, temp_git_repo):
        """Test listing operations with limit."""
        manager = RollbackManager(temp_git_repo)
        
        # Record 5 operations
        for i in range(5):
            manager.record_operation(
                operation_type=f'test_{i}',
                backup_branch=f'backup-{i}',
                commit_before=f'commit-{i}'
            )
        
        # Get only 3 most recent
        operations = manager.list_operations(limit=3)
        
        assert len(operations) == 3
        assert operations[0]['operation_type'] == 'test_4'  # Most recent
        assert operations[1]['operation_type'] == 'test_3'
        assert operations[2]['operation_type'] == 'test_2'
    
    def test_list_operations_excludes_rolled_back(self, temp_git_repo):
        """Test that rolled-back operations are excluded by default."""
        manager = RollbackManager(temp_git_repo)
        
        # Record operation
        op_id = manager.record_operation(
            operation_type='test',
            backup_branch='backup-test',
            commit_before='abc123'
        )
        
        # Manually mark as rolled back
        history = manager._load_history()
        history[0]['rolled_back'] = True
        manager._save_history(history)
        
        # Should not appear in list
        operations = manager.list_operations(include_rolled_back=False)
        assert len(operations) == 0
    
    def test_list_operations_includes_rolled_back_when_requested(self, temp_git_repo):
        """Test that rolled-back operations can be included."""
        manager = RollbackManager(temp_git_repo)
        
        # Record operation
        op_id = manager.record_operation(
            operation_type='test',
            backup_branch='backup-test',
            commit_before='abc123'
        )
        
        # Manually mark as rolled back
        history = manager._load_history()
        history[0]['rolled_back'] = True
        manager._save_history(history)
        
        # Should appear when explicitly requested
        operations = manager.list_operations(include_rolled_back=True)
        assert len(operations) == 1
        assert operations[0]['rolled_back'] is True


class TestRollbackOperation:
    """Tests for rollback functionality."""
    
    def test_rollback_operation_restores_backup_branch(self, temp_git_repo):
        """Test that rollback checks out the backup branch."""
        # Setup: Create a file, commit, create backup, modify file, commit again
        repo_path = Path(temp_git_repo)
        test_file = repo_path / "test.py"
        
        # Initial state
        test_file.write_text("original content")
        git_mgr = GitManager(repo_path)
        git_mgr.stage_and_commit(str(test_file), "Initial commit")
        commit_before = git_mgr.get_current_commit_hash()
        
        # Create backup branch
        backup_branch = git_mgr.create_backup_branch("refactor")
        
        # Modify file
        test_file.write_text("modified content")
        git_mgr.stage_and_commit(str(test_file), "Modified")
        commit_after = git_mgr.get_current_commit_hash()
        
        # Record operation
        manager = RollbackManager(repo_path)
        op_id = manager.record_operation(
            operation_type='test',
            backup_branch=backup_branch,
            commit_before=commit_before,
            commit_after=commit_after,
            files_modified=['test.py']
        )
        
        # Rollback
        result = manager.rollback_operation(op_id)
        
        # Verify result
        assert result['status'] == 'success'
        assert result['operation_id'] == op_id
        
        # Verify file was restored
        assert test_file.read_text() == "original content"
    
    def test_rollback_operation_marks_as_rolled_back(self, temp_git_repo):
        """Test that rollback marks operation as rolled back in history."""
        repo_path = Path(temp_git_repo)
        git_mgr = GitManager(repo_path)
        
        # Create backup branch
        backup_branch = git_mgr.create_backup_branch("test")
        commit = git_mgr.get_current_commit_hash()
        
        # Record and rollback
        manager = RollbackManager(repo_path)
        op_id = manager.record_operation(
            operation_type='test',
            backup_branch=backup_branch,
            commit_before=commit
        )
        
        manager.rollback_operation(op_id)
        
        # Check history
        operation = manager.get_operation(op_id)
        assert operation['rolled_back'] is True
        assert 'rollback_timestamp' in operation
    
    def test_rollback_operation_not_found(self, temp_git_repo):
        """Test rollback with non-existent operation ID."""
        manager = RollbackManager(temp_git_repo)
        
        with pytest.raises(OperationNotFoundError):
            manager.rollback_operation('nonexistent-id')
    
    def test_rollback_operation_already_rolled_back(self, temp_git_repo):
        """Test that rolling back twice raises error."""
        repo_path = Path(temp_git_repo)
        git_mgr = GitManager(repo_path)
        
        backup_branch = git_mgr.create_backup_branch("test")
        commit = git_mgr.get_current_commit_hash()
        
        manager = RollbackManager(repo_path)
        op_id = manager.record_operation(
            operation_type='test',
            backup_branch=backup_branch,
            commit_before=commit
        )
        
        # First rollback
        manager.rollback_operation(op_id)
        
        # Second rollback should fail
        with pytest.raises(RollbackError) as exc_info:
            manager.rollback_operation(op_id)
        
        assert 'already been rolled back' in str(exc_info.value)
    
    def test_rollback_operation_backup_branch_missing(self, temp_git_repo):
        """Test rollback when backup branch no longer exists."""
        repo_path = Path(temp_git_repo)
        git_mgr = GitManager(repo_path)
        
        # Create and delete backup branch
        backup_branch = git_mgr.create_backup_branch("test")
        commit = git_mgr.get_current_commit_hash()
        
        manager = RollbackManager(repo_path)
        op_id = manager.record_operation(
            operation_type='test',
            backup_branch=backup_branch,
            commit_before=commit
        )
        
        # Delete the backup branch
        git_mgr.delete_branch(backup_branch, force=True)
        
        # Rollback should fail
        with pytest.raises(RollbackError) as exc_info:
            manager.rollback_operation(op_id)
        
        assert 'no longer exists' in str(exc_info.value)


class TestAsyncRollbackRefactoring:
    """Tests for the async rollback_refactoring function."""
    
    @pytest.mark.asyncio
    async def test_rollback_refactoring_success(self, temp_git_repo):
        """Test successful async rollback."""
        repo_path = Path(temp_git_repo)
        git_mgr = GitManager(repo_path)
        
        # Setup operation
        backup_branch = git_mgr.create_backup_branch("test")
        commit = git_mgr.get_current_commit_hash()
        
        manager = RollbackManager(repo_path)
        op_id = manager.record_operation(
            operation_type='test',
            backup_branch=backup_branch,
            commit_before=commit
        )
        
        # Async rollback
        result = await rollback_refactoring(
            project_root=repo_path,
            operation_id=op_id
        )
        
        assert result['status'] == 'success'
        assert result['operation_id'] == op_id
    
    @pytest.mark.asyncio
    async def test_rollback_refactoring_operation_not_found(self, temp_git_repo):
        """Test async rollback with non-existent operation."""
        result = await rollback_refactoring(
            project_root=temp_git_repo,
            operation_id='nonexistent-id'
        )
        
        assert result['status'] == 'error'
        assert result['error'] == 'operation_not_found'
    
    @pytest.mark.asyncio
    async def test_rollback_refactoring_handles_errors(self, temp_git_repo):
        """Test that errors are caught and returned properly."""
        repo_path = Path(temp_git_repo)
        git_mgr = GitManager(repo_path)
        
        # Create operation with missing backup branch
        manager = RollbackManager(repo_path)
        op_id = manager.record_operation(
            operation_type='test',
            backup_branch='nonexistent-branch',
            commit_before='abc123'
        )
        
        # Should return error result, not raise exception
        result = await rollback_refactoring(
            project_root=repo_path,
            operation_id=op_id
        )
        
        assert result['status'] == 'error'
        assert result['error'] == 'rollback_failed'
        assert 'no longer exists' in result['message']


class TestClearHistory:
    """Tests for clearing operation history."""
    
    def test_clear_history_requires_confirmation(self, temp_git_repo):
        """Test that clear_history requires confirm=True."""
        manager = RollbackManager(temp_git_repo)
        
        with pytest.raises(RollbackError) as exc_info:
            manager.clear_history(confirm=False)
        
        assert 'confirm=True' in str(exc_info.value)
    
    def test_clear_history_removes_all_operations(self, temp_git_repo):
        """Test that clear_history removes all operations."""
        manager = RollbackManager(temp_git_repo)
        
        # Record some operations
        for i in range(3):
            manager.record_operation(
                operation_type=f'test_{i}',
                backup_branch=f'backup-{i}',
                commit_before=f'commit-{i}'
            )
        
        # Verify operations exist
        assert len(manager.list_operations(include_rolled_back=True)) == 3
        
        # Clear history
        manager.clear_history(confirm=True)
        
        # Verify all gone
        assert len(manager.list_operations(include_rolled_back=True)) == 0


# Fixtures

@pytest.fixture
def temp_git_repo():
    """Create a temporary Git repository for testing."""
    temp_dir = tempfile.mkdtemp()
    repo_path = Path(temp_dir)
    
    # Initialize Git repo
    import git
    repo = git.Repo.init(repo_path)
    
    # Create initial commit
    readme = repo_path / "README.md"
    readme.write_text("# Test Repository")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")
    
    yield str(repo_path)
    
    # Cleanup
    shutil.rmtree(temp_dir)
