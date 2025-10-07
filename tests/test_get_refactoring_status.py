"""
Integration tests for get_refactoring_status MCP tool.

These tests verify the RollbackManager's list_operations functionality
which is used by the get_refactoring_status MCP tool.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from src.rollback_manager import RollbackManager


class TestGetRefactoringStatusIntegration:
    """Integration tests for refactoring status retrieval."""
    
    @pytest.fixture
    def setup_project(self, tmp_path):
        """Set up a test project with git repository."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        
        # Initialize git repository
        import subprocess
        subprocess.run(["git", "init"], cwd=project_root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=project_root,
            check=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=project_root,
            check=True
        )
        
        # Create initial commit
        test_file = project_root / "test.py"
        test_file.write_text("print('hello')")
        subprocess.run(["git", "add", "."], cwd=project_root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=project_root,
            check=True
        )
        
        return project_root
    
    def test_get_status_empty_history(self, setup_project):
        """Test getting status when history is empty."""
        manager = RollbackManager(setup_project)
        operations = manager.list_operations()
        
        assert operations == []
    
    def test_get_status_with_operations(self, setup_project):
        """Test getting status with recorded operations."""
        manager = RollbackManager(setup_project)
        
        # Record some operations
        op1_id = manager.record_operation(
            operation_type='extract_function',
            backup_branch='backup-001',
            commit_before='abc123',
            commit_after='def456',
            files_modified=['app.py'],
            files_created=['helpers.py']
        )
        
        op2_id = manager.record_operation(
            operation_type='split_class',
            backup_branch='backup-002',
            commit_before='def456',
            commit_after='ghi789',
            files_modified=['models.py'],
            files_created=['user_model.py', 'order_model.py']
        )
        
        # Get operations
        operations = manager.list_operations()
        
        assert len(operations) == 2
        
        # Check operations are sorted by timestamp (most recent first)
        assert operations[0]['operation_id'] == op2_id
        assert operations[1]['operation_id'] == op1_id
        
        # Verify operation details
        op1 = operations[1]
        assert op1['operation_type'] == 'extract_function'
        assert op1['backup_branch'] == 'backup-001'
        assert op1['commit_before'] == 'abc123'
        assert op1['commit_after'] == 'def456'
        assert op1['files_modified'] == ['app.py']
        assert op1['files_created'] == ['helpers.py']
        assert op1['rolled_back'] is False
    
    def test_get_status_with_limit(self, setup_project):
        """Test limiting the number of operations returned."""
        manager = RollbackManager(setup_project)
        
        # Record multiple operations
        for i in range(5):
            manager.record_operation(
                operation_type=f'operation_{i}',
                backup_branch=f'backup-{i:03d}',
                commit_before=f'commit_{i}',
                files_modified=[f'file_{i}.py']
            )
        
        # Get operations with limit
        operations = manager.list_operations(limit=3)
        
        assert len(operations) == 3
    
    def test_get_status_exclude_rolled_back(self, setup_project):
        """Test excluding rolled back operations by default."""
        manager = RollbackManager(setup_project)
        
        # Record operations
        op1_id = manager.record_operation(
            operation_type='extract_function',
            backup_branch='backup-001',
            commit_before='abc123',
            commit_after='def456',
            files_modified=['app.py']
        )
        
        op2_id = manager.record_operation(
            operation_type='split_class',
            backup_branch='backup-002',
            commit_before='def456',
            commit_after='ghi789',
            files_modified=['models.py']
        )
        
        # Mark one operation as rolled back
        history = manager._load_history()
        for op in history:
            if op['operation_id'] == op1_id:
                op['rolled_back'] = True
        manager._save_history(history)
        
        # Get operations without rolled back
        operations = manager.list_operations(include_rolled_back=False)
        
        assert len(operations) == 1
        assert operations[0]['operation_id'] == op2_id
    
    def test_get_status_include_rolled_back(self, setup_project):
        """Test including rolled back operations when requested."""
        manager = RollbackManager(setup_project)
        
        # Record operations
        op1_id = manager.record_operation(
            operation_type='extract_function',
            backup_branch='backup-001',
            commit_before='abc123',
            commit_after='def456',
            files_modified=['app.py']
        )
        
        op2_id = manager.record_operation(
            operation_type='split_class',
            backup_branch='backup-002',
            commit_before='def456',
            commit_after='ghi789',
            files_modified=['models.py']
        )
        
        # Mark one operation as rolled back
        history = manager._load_history()
        for op in history:
            if op['operation_id'] == op1_id:
                op['rolled_back'] = True
        manager._save_history(history)
        
        # Get operations including rolled back
        operations = manager.list_operations(include_rolled_back=True)
        
        assert len(operations) == 2
        
        # Verify the rolled back operation
        for op in operations:
            if op['operation_id'] == op1_id:
                assert op['rolled_back'] is True
            else:
                assert op['rolled_back'] is False
    
    def test_get_status_with_operation_details(self, setup_project):
        """Test that operation details are included in the response."""
        manager = RollbackManager(setup_project)
        
        # Record operation with details
        operation_details = {
            'suggestion_id': 'abc123',
            'suggestion_title': 'Extract authentication logic',
            'strategy': 'extract'
        }
        
        op_id = manager.record_operation(
            operation_type='extract_function',
            backup_branch='backup-001',
            commit_before='abc123',
            commit_after='def456',
            files_modified=['app.py'],
            operation_details=operation_details
        )
        
        # Get operations
        operations = manager.list_operations()
        
        assert len(operations) == 1
        
        op = operations[0]
        assert 'operation_details' in op
        assert op['operation_details'] == operation_details
    
    def test_invalid_project_root(self, tmp_path):
        """Test handling of invalid project root."""
        nonexistent_path = tmp_path / "nonexistent"
        
        with pytest.raises(Exception):
            # RollbackManager should handle this, but the actual error depends on implementation
            manager = RollbackManager(nonexistent_path)

