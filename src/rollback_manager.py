"""
Rollback manager for refactoring operations.

This module provides functionality to track refactoring operations and
rollback changes using Git integration.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from .git_manager import GitManager, GitOperationError


class RollbackError(Exception):
    """Base exception for rollback errors."""
    pass


class OperationNotFoundError(RollbackError):
    """Raised when an operation ID is not found in history."""
    pass


class RollbackManager:
    """
    Manager for tracking and rolling back refactoring operations.
    
    This class maintains a history of refactoring operations and provides
    functionality to rollback changes using Git integration.
    
    Attributes:
        project_root: Path to the project root directory
        git_manager: GitManager instance for Git operations
        history_file: Path to the operation history JSON file
    
    Example:
        >>> manager = RollbackManager('/path/to/project')
        >>> operation_id = manager.record_operation(
        ...     operation_type='extract_function',
        ...     backup_branch='backup-20231005143022',
        ...     commit_hash='abc123',
        ...     files_modified=['app.py', 'helpers.py']
        ... )
        >>> manager.rollback_operation(operation_id)
    """
    
    def __init__(self, project_root: str | Path):
        """
        Initialize the RollbackManager.
        
        Args:
            project_root: Path to the project root directory
            
        Raises:
            RollbackError: If initialization fails
        """
        self.project_root = Path(project_root).resolve()
        
        # Initialize GitManager
        try:
            self.git_manager = GitManager(self.project_root)
        except Exception as e:
            raise RollbackError(f"Failed to initialize GitManager: {e}")
        
        # Set up history file location
        self.history_file = self.project_root / ".taskmaster" / "refactoring_history.json"
        
        # Ensure .taskmaster directory exists
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize history file if it doesn't exist
        if not self.history_file.exists():
            self._save_history([])
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """
        Load operation history from JSON file.
        
        Returns:
            List of operation records
            
        Raises:
            RollbackError: If history file is corrupted
        """
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise RollbackError(f"Corrupted history file: {e}")
        except Exception as e:
            raise RollbackError(f"Failed to load history: {e}")
    
    def _save_history(self, history: List[Dict[str, Any]]) -> None:
        """
        Save operation history to JSON file.
        
        Args:
            history: List of operation records to save
            
        Raises:
            RollbackError: If saving fails
        """
        try:
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            raise RollbackError(f"Failed to save history: {e}")
    
    def record_operation(
        self,
        operation_type: str,
        backup_branch: str,
        commit_before: str,
        commit_after: Optional[str] = None,
        files_modified: Optional[List[str]] = None,
        files_created: Optional[List[str]] = None,
        operation_details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Record a refactoring operation in the history.
        
        Args:
            operation_type: Type of refactoring operation
            backup_branch: Name of the backup branch created
            commit_before: Commit hash before the operation
            commit_after: Commit hash after the operation (optional)
            files_modified: List of modified file paths
            files_created: List of created file paths
            operation_details: Additional operation details
            
        Returns:
            Unique operation ID (timestamp-based)
            
        Raises:
            RollbackError: If recording fails
            
        Example:
            >>> manager = RollbackManager('/path/to/project')
            >>> op_id = manager.record_operation(
            ...     operation_type='extract_function',
            ...     backup_branch='backup-20231005143022',
            ...     commit_before='abc123',
            ...     commit_after='def456',
            ...     files_modified=['app.py'],
            ...     files_created=['helpers.py']
            ... )
        """
        try:
            # Generate operation ID based on timestamp
            timestamp = datetime.now()
            operation_id = timestamp.strftime("%Y%m%d%H%M%S%f")
            
            # Create operation record
            record = {
                'operation_id': operation_id,
                'operation_type': operation_type,
                'timestamp': timestamp.isoformat(),
                'backup_branch': backup_branch,
                'commit_before': commit_before,
                'commit_after': commit_after,
                'files_modified': files_modified or [],
                'files_created': files_created or [],
                'operation_details': operation_details or {},
                'rolled_back': False
            }
            
            # Load current history
            history = self._load_history()
            
            # Add new record
            history.append(record)
            
            # Save updated history
            self._save_history(history)
            
            return operation_id
            
        except Exception as e:
            raise RollbackError(f"Failed to record operation: {e}")
    
    def get_operation(self, operation_id: str) -> Dict[str, Any]:
        """
        Retrieve an operation record by ID.
        
        Args:
            operation_id: The operation ID to retrieve
            
        Returns:
            Operation record dictionary
            
        Raises:
            OperationNotFoundError: If operation ID is not found
            
        Example:
            >>> manager = RollbackManager('/path/to/project')
            >>> operation = manager.get_operation('20231005143022123456')
            >>> print(operation['operation_type'])
            extract_function
        """
        history = self._load_history()
        
        for record in history:
            if record['operation_id'] == operation_id:
                return record
        
        raise OperationNotFoundError(
            f"Operation ID '{operation_id}' not found in history"
        )
    
    def list_operations(
        self,
        limit: Optional[int] = None,
        include_rolled_back: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List recorded operations.
        
        Args:
            limit: Maximum number of operations to return (most recent first)
            include_rolled_back: If True, include rolled-back operations
            
        Returns:
            List of operation records
            
        Example:
            >>> manager = RollbackManager('/path/to/project')
            >>> recent_ops = manager.list_operations(limit=10)
            >>> for op in recent_ops:
            ...     print(f"{op['operation_id']}: {op['operation_type']}")
        """
        history = self._load_history()
        
        # Filter out rolled-back operations if requested
        if not include_rolled_back:
            history = [op for op in history if not op.get('rolled_back', False)]
        
        # Sort by timestamp (most recent first)
        history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Apply limit
        if limit:
            history = history[:limit]
        
        return history
    
    def rollback_operation(
        self,
        operation_id: str,
        delete_backup_branch: bool = False
    ) -> Dict[str, Any]:
        """
        Rollback a refactoring operation using Git.
        
        This function reverts the changes made by a refactoring operation by
        checking out the backup branch created before the operation.
        
        Args:
            operation_id: The operation ID to rollback
            delete_backup_branch: If True, delete the backup branch after rollback
            
        Returns:
            Dictionary containing:
                - status: 'success' or 'error'
                - operation_id: The operation ID that was rolled back
                - message: Description of the result
                - restored_branch: The branch that was restored
                
        Raises:
            OperationNotFoundError: If operation ID is not found
            RollbackError: If rollback operation fails
            
        Example:
            >>> manager = RollbackManager('/path/to/project')
            >>> result = manager.rollback_operation('20231005143022123456')
            >>> print(result['status'])
            success
        """
        try:
            # Get the operation record
            operation = self.get_operation(operation_id)
            
            # Check if already rolled back
            if operation.get('rolled_back', False):
                raise RollbackError(
                    f"Operation '{operation_id}' has already been rolled back"
                )
            
            # Get backup branch name
            backup_branch = operation['backup_branch']
            
            # Verify backup branch exists
            if not self.git_manager.branch_exists(backup_branch):
                raise RollbackError(
                    f"Backup branch '{backup_branch}' no longer exists. "
                    "Cannot perform rollback."
                )
            
            # Get current branch to restore later if needed
            current_branch = None
            if not self.git_manager.is_detached_head():
                current_branch = self.git_manager.get_current_branch_name()
            
            # Checkout the backup branch (force=True to discard changes)
            self.git_manager.rollback_to_branch(backup_branch, force=True)
            
            # If we were on a different branch, create a new commit there
            # and switch back
            if current_branch and current_branch != backup_branch:
                # Get the state from backup branch
                backup_commit = self.git_manager.get_current_commit_hash()
                
                # Switch back to original branch
                self.git_manager.rollback_to_branch(current_branch, force=False)
                
                # Reset to backup state
                self.git_manager.rollback_to_commit(backup_commit, hard=True)
            
            # Delete backup branch if requested
            if delete_backup_branch and backup_branch != current_branch:
                try:
                    # Need to be on a different branch to delete
                    if self.git_manager.get_current_branch_name() == backup_branch:
                        # Switch to main or master
                        for branch in ['main', 'master']:
                            if self.git_manager.branch_exists(branch):
                                self.git_manager.rollback_to_branch(branch, force=False)
                                break
                    
                    self.git_manager.delete_branch(backup_branch, force=True)
                except Exception as e:
                    # Don't fail rollback if branch deletion fails
                    pass
            
            # Mark operation as rolled back in history
            history = self._load_history()
            for record in history:
                if record['operation_id'] == operation_id:
                    record['rolled_back'] = True
                    record['rollback_timestamp'] = datetime.now().isoformat()
                    break
            self._save_history(history)
            
            return {
                'status': 'success',
                'operation_id': operation_id,
                'message': f"Successfully rolled back operation '{operation_id}'",
                'restored_branch': backup_branch,
                'files_affected': (
                    operation.get('files_modified', []) +
                    operation.get('files_created', [])
                )
            }
            
        except OperationNotFoundError:
            raise
        except GitOperationError as e:
            raise RollbackError(f"Git operation failed during rollback: {e}")
        except Exception as e:
            raise RollbackError(f"Rollback failed: {e}")
    
    def clear_history(self, confirm: bool = False) -> None:
        """
        Clear the entire operation history.
        
        WARNING: This permanently deletes all operation records.
        
        Args:
            confirm: Must be True to proceed with clearing
            
        Raises:
            RollbackError: If confirm is not True
            
        Example:
            >>> manager = RollbackManager('/path/to/project')
            >>> manager.clear_history(confirm=True)
        """
        if not confirm:
            raise RollbackError(
                "Must set confirm=True to clear history. This action is permanent."
            )
        
        self._save_history([])


async def rollback_refactoring(
    project_root: str | Path,
    operation_id: str,
    delete_backup_branch: bool = False
) -> Dict[str, Any]:
    """
    Async function to rollback a refactoring operation.
    
    This is the main MCP tool entry point for rollback operations.
    
    Args:
        project_root: Path to the project root directory
        operation_id: The operation ID to rollback
        delete_backup_branch: If True, delete the backup branch after rollback
        
    Returns:
        Dictionary containing:
            - status: 'success' or 'error'
            - operation_id: The operation ID that was rolled back
            - message: Description of the result
            - error: Error message if status is 'error'
            
    Example:
        >>> result = await rollback_refactoring(
        ...     project_root='/path/to/project',
        ...     operation_id='20231005143022123456'
        ... )
        >>> print(result['status'])
        success
    """
    try:
        manager = RollbackManager(project_root)
        result = manager.rollback_operation(
            operation_id=operation_id,
            delete_backup_branch=delete_backup_branch
        )
        return result
        
    except OperationNotFoundError as e:
        return {
            'status': 'error',
            'operation_id': operation_id,
            'message': str(e),
            'error': 'operation_not_found'
        }
    except RollbackError as e:
        return {
            'status': 'error',
            'operation_id': operation_id,
            'message': str(e),
            'error': 'rollback_failed'
        }
    except Exception as e:
        return {
            'status': 'error',
            'operation_id': operation_id,
            'message': f"Unexpected error: {e}",
            'error': 'unexpected_error'
        }
