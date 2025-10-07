"""
Git interaction layer using GitPython for safety operations.

This module provides a GitManager class to handle backup branch creation,
commits, and rollbacks for safe refactoring operations.
"""

from pathlib import Path
from typing import Optional
import git
from git.exc import InvalidGitRepositoryError, NoSuchPathError, GitCommandError


class GitManagerError(Exception):
    """Base exception for GitManager errors."""
    pass


class NotAGitRepositoryError(GitManagerError):
    """Raised when the provided path is not a valid Git repository."""
    pass


class GitOperationError(GitManagerError):
    """Raised when a Git operation fails."""
    pass


class GitManager:
    """
    Manager for Git operations including branch creation, commits, and rollbacks.
    
    This class provides a safe interface for Git operations during refactoring,
    allowing for backup creation and rollback capabilities.
    
    Attributes:
        repo_path: Path to the Git repository
        repo: git.Repo object representing the repository
    
    Example:
        >>> manager = GitManager('/path/to/repo')
        >>> branch = manager.create_backup_branch('refactor')
        >>> manager.stage_and_commit(['file.py'], 'Refactored code')
        >>> manager.rollback_to_branch(branch)
    """
    
    def __init__(self, repo_path: str | Path):
        """
        Initialize the GitManager with a repository path.
        
        Args:
            repo_path: Path to the Git repository
            
        Raises:
            NotAGitRepositoryError: If the path is not a valid Git repository
            
        Example:
            >>> manager = GitManager('/path/to/repo')
            >>> manager = GitManager(Path('/path/to/repo'))
        """
        self.repo_path = Path(repo_path).resolve()
        
        try:
            self.repo = git.Repo(self.repo_path)
        except InvalidGitRepositoryError:
            raise NotAGitRepositoryError(
                f"'{self.repo_path}' is not a valid Git repository. "
                "Please initialize a Git repository first with 'git init'."
            )
        except NoSuchPathError:
            raise NotAGitRepositoryError(
                f"Path '{self.repo_path}' does not exist."
            )
        except Exception as e:
            raise GitManagerError(
                f"Failed to initialize Git repository: {e}"
            )
    
    def is_valid_repository(self) -> bool:
        """
        Check if the repository is valid and accessible.
        
        Returns:
            True if the repository is valid, False otherwise
            
        Example:
            >>> manager = GitManager('/path/to/repo')
            >>> if manager.is_valid_repository():
            ...     print("Repository is valid")
        """
        try:
            # Try to access the repo's git directory
            _ = self.repo.git_dir
            return True
        except Exception:
            return False
    
    def get_repo_root(self) -> Path:
        """
        Get the root directory of the repository.
        
        Returns:
            Path object pointing to the repository root
            
        Example:
            >>> manager = GitManager('/path/to/repo')
            >>> root = manager.get_repo_root()
        """
        return Path(self.repo.working_tree_dir)
    
    def __repr__(self) -> str:
        """String representation of GitManager."""
        return f"GitManager(repo_path='{self.repo_path}')"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        try:
            branch = self.repo.active_branch.name
            return f"GitManager for repository at {self.repo_path} (branch: {branch})"
        except TypeError:
            return f"GitManager for repository at {self.repo_path} (detached HEAD)"
    
    def get_current_branch_name(self) -> str:
        """
        Get the name of the currently active branch.
        
        Returns:
            Name of the current branch
            
        Raises:
            GitOperationError: If the repository is in a detached HEAD state
            
        Example:
            >>> manager = GitManager('/path/to/repo')
            >>> branch = manager.get_current_branch_name()
            >>> print(f"Current branch: {branch}")
            Current branch: main
        """
        try:
            if self.repo.head.is_detached:
                # Get the current commit hash
                commit_hash = self.repo.head.commit.hexsha[:7]
                raise GitOperationError(
                    f"Repository is in detached HEAD state at commit {commit_hash}. "
                    "Cannot determine branch name. Please checkout a branch first."
                )
            
            return self.repo.active_branch.name
        except AttributeError as e:
            raise GitOperationError(
                f"Failed to get current branch name: {e}"
            )
    
    def is_detached_head(self) -> bool:
        """
        Check if the repository is in a detached HEAD state.
        
        Returns:
            True if HEAD is detached, False otherwise
            
        Example:
            >>> manager = GitManager('/path/to/repo')
            >>> if manager.is_detached_head():
            ...     print("Warning: detached HEAD state")
        """
        try:
            return self.repo.head.is_detached
        except Exception:
            return False
    
    def get_current_commit_hash(self, short: bool = False) -> str:
        """
        Get the current commit hash.
        
        Args:
            short: If True, return shortened hash (7 chars), otherwise full hash
            
        Returns:
            Current commit hash
            
        Example:
            >>> manager = GitManager('/path/to/repo')
            >>> full_hash = manager.get_current_commit_hash()
            >>> short_hash = manager.get_current_commit_hash(short=True)
        """
        commit_hash = self.repo.head.commit.hexsha
        return commit_hash[:7] if short else commit_hash
    
    def create_backup_branch(self, prefix: str = "backup") -> str:
        """
        Create a new backup branch from the current HEAD with a timestamp.
        
        Args:
            prefix: Prefix for the branch name (default: "backup")
            
        Returns:
            Full name of the created backup branch
            
        Raises:
            GitOperationError: If branch creation fails
            
        Example:
            >>> manager = GitManager('/path/to/repo')
            >>> branch = manager.create_backup_branch('refactor')
            >>> print(f"Created backup: {branch}")
            Created backup: refactor-20231005143022
        """
        from datetime import datetime
        
        try:
            # Generate timestamp (YYYYMMDDHHMMSS format)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # Create branch name
            branch_name = f"{prefix}-{timestamp}"
            
            # Create the branch pointing to current HEAD
            new_branch = self.repo.create_head(branch_name)
            
            return branch_name
            
        except Exception as e:
            raise GitOperationError(
                f"Failed to create backup branch: {e}"
            )
    
    def list_branches(self, include_remote: bool = False) -> list[str]:
        """
        List all branches in the repository.
        
        Args:
            include_remote: If True, include remote branches
            
        Returns:
            List of branch names
            
        Example:
            >>> manager = GitManager('/path/to/repo')
            >>> branches = manager.list_branches()
            >>> print(f"Branches: {', '.join(branches)}")
        """
        try:
            branches = [head.name for head in self.repo.heads]
            
            if include_remote:
                remote_branches = [ref.name for ref in self.repo.remote().refs]
                branches.extend(remote_branches)
            
            return branches
        except Exception as e:
            raise GitOperationError(
                f"Failed to list branches: {e}"
            )
    
    def branch_exists(self, branch_name: str) -> bool:
        """
        Check if a branch exists in the repository.
        
        Args:
            branch_name: Name of the branch to check
            
        Returns:
            True if the branch exists, False otherwise
            
        Example:
            >>> manager = GitManager('/path/to/repo')
            >>> if not manager.branch_exists('feature'):
            ...     print("Branch does not exist")
        """
        try:
            return branch_name in [head.name for head in self.repo.heads]
        except Exception:
            return False
    
    def stage_and_commit(
        self, 
        file_paths: list[str] | str, 
        message: str
    ) -> str:
        """
        Stage files and create a commit with the given message.
        
        Args:
            file_paths: Single file path or list of file paths to stage
            message: Commit message
            
        Returns:
            Commit hash of the newly created commit
            
        Raises:
            GitOperationError: If staging or committing fails
            
        Example:
            >>> manager = GitManager('/path/to/repo')
            >>> commit = manager.stage_and_commit(['file1.py', 'file2.py'], 'Refactored code')
            >>> print(f"Created commit: {commit}")
        """
        try:
            # Normalize to list
            if isinstance(file_paths, str):
                file_paths = [file_paths]
            
            # Convert to relative paths if needed
            relative_paths = []
            repo_root = self.get_repo_root()
            
            for path in file_paths:
                abs_path = Path(path).resolve()
                
                # Check if file exists
                if not abs_path.exists():
                    raise GitOperationError(
                        f"File not found: {path}"
                    )
                
                # Get relative path from repo root
                try:
                    rel_path = abs_path.relative_to(repo_root)
                    relative_paths.append(str(rel_path).replace('\\', '/'))
                except ValueError:
                    raise GitOperationError(
                        f"File '{path}' is not within the repository"
                    )
            
            # Stage the files
            self.repo.index.add(relative_paths)
            
            # Create commit
            commit = self.repo.index.commit(message)
            
            return commit.hexsha
            
        except GitCommandError as e:
            raise GitOperationError(
                f"Git command failed: {e}"
            )
        except Exception as e:
            raise GitOperationError(
                f"Failed to stage and commit: {e}"
            )
    
    def get_staged_files(self) -> list[str]:
        """
        Get list of currently staged files.
        
        Returns:
            List of staged file paths
            
        Example:
            >>> manager = GitManager('/path/to/repo')
            >>> staged = manager.get_staged_files()
            >>> print(f"Staged files: {', '.join(staged)}")
        """
        try:
            # Get diff between HEAD and index
            diffs = self.repo.index.diff('HEAD')
            return [diff.a_path for diff in diffs]
        except Exception:
            # If HEAD doesn't exist (first commit), return all staged files
            try:
                return [entry.path for entry in self.repo.index.entries.keys()]
            except Exception:
                return []
    
    def get_modified_files(self) -> list[str]:
        """
        Get list of modified files in the working directory.
        
        Returns:
            List of modified file paths
            
        Example:
            >>> manager = GitManager('/path/to/repo')
            >>> modified = manager.get_modified_files()
            >>> print(f"Modified files: {', '.join(modified)}")
        """
        try:
            # Get untracked files
            untracked = self.repo.untracked_files
            
            # Get modified tracked files
            modified = [item.a_path for item in self.repo.index.diff(None)]
            
            return untracked + modified
        except Exception as e:
            raise GitOperationError(
                f"Failed to get modified files: {e}"
            )
    
    def has_uncommitted_changes(self) -> bool:
        """
        Check if there are any uncommitted changes in the repository.
        
        Returns:
            True if there are uncommitted changes, False otherwise
            
        Example:
            >>> manager = GitManager('/path/to/repo')
            >>> if manager.has_uncommitted_changes():
            ...     print("Warning: uncommitted changes detected")
        """
        try:
            # Check for modified files
            if self.repo.is_dirty(untracked_files=True):
                return True
            
            # Check for staged files
            if self.get_staged_files():
                return True
            
            return False
        except Exception:
            return False
    
    def rollback_to_branch(self, branch_name: str, force: bool = False) -> None:
        """
        Rollback to a specific branch by checking it out.
        
        This performs a hard checkout, discarding local changes unless force=False.
        
        Args:
            branch_name: Name of the branch to rollback to
            force: If True, discard local changes. If False, preserve them.
            
        Raises:
            GitOperationError: If branch doesn't exist or checkout fails
            
        Example:
            >>> manager = GitManager('/path/to/repo')
            >>> backup = manager.create_backup_branch('backup')
            >>> # ... make some changes ...
            >>> manager.rollback_to_branch(backup, force=True)
        """
        try:
            # Check if branch exists
            if not self.branch_exists(branch_name):
                raise GitOperationError(
                    f"Branch '{branch_name}' does not exist"
                )
            
            # Get the branch
            branch = self.repo.heads[branch_name]
            
            # Checkout the branch
            branch.checkout(force=force)
            
        except Exception as e:
            raise GitOperationError(
                f"Failed to rollback to branch '{branch_name}': {e}"
            )
    
    def rollback_to_commit(self, commit_hash: str, hard: bool = False) -> None:
        """
        Rollback to a specific commit.
        
        Args:
            commit_hash: Hash of the commit to rollback to
            hard: If True, perform hard reset (discard changes).
                  If False, perform soft reset (keep changes staged).
            
        Raises:
            GitOperationError: If commit doesn't exist or rollback fails
            
        Example:
            >>> manager = GitManager('/path/to/repo')
            >>> # Get current commit before changes
            >>> original = manager.get_current_commit_hash()
            >>> # ... make changes ...
            >>> manager.rollback_to_commit(original, hard=True)
        """
        try:
            # Try to get the commit
            commit = self.repo.commit(commit_hash)
            
            # Perform reset
            if hard:
                self.repo.head.reset(commit, index=True, working_tree=True)
            else:
                self.repo.head.reset(commit, index=False, working_tree=False)
                
        except Exception as e:
            raise GitOperationError(
                f"Failed to rollback to commit '{commit_hash}': {e}"
            )
    
    def delete_branch(self, branch_name: str, force: bool = False) -> None:
        """
        Delete a branch.
        
        Args:
            branch_name: Name of the branch to delete
            force: If True, force deletion even if not fully merged
            
        Raises:
            GitOperationError: If branch doesn't exist or deletion fails
            
        Example:
            >>> manager = GitManager('/path/to/repo')
            >>> backup = manager.create_backup_branch('backup')
            >>> # ... use backup if needed ...
            >>> manager.delete_branch(backup, force=True)
        """
        try:
            # Check if branch exists
            if not self.branch_exists(branch_name):
                raise GitOperationError(
                    f"Branch '{branch_name}' does not exist"
                )
            
            # Cannot delete current branch
            if not self.is_detached_head():
                current = self.get_current_branch_name()
                if current == branch_name:
                    raise GitOperationError(
                        f"Cannot delete the currently active branch '{branch_name}'"
                    )
            
            # Delete the branch
            self.repo.delete_head(branch_name, force=force)
            
        except Exception as e:
            raise GitOperationError(
                f"Failed to delete branch '{branch_name}': {e}"
            )
    
    def checkout_files(
        self, 
        file_paths: list[str] | str, 
        commit: str | None = None
    ) -> None:
        """
        Checkout specific files from a commit or HEAD.
        
        This reverts files without changing branches.
        
        Args:
            file_paths: Single file path or list of file paths
            commit: Commit hash to checkout from (default: HEAD)
            
        Raises:
            GitOperationError: If checkout fails
            
        Example:
            >>> manager = GitManager('/path/to/repo')
            >>> # Revert a file to HEAD
            >>> manager.checkout_files('file.py')
            >>> # Revert to specific commit
            >>> manager.checkout_files(['file1.py', 'file2.py'], commit='abc123')
        """
        try:
            # Normalize to list
            if isinstance(file_paths, str):
                file_paths = [file_paths]
            
            # Convert to relative paths
            relative_paths = []
            repo_root = self.get_repo_root()
            
            for path in file_paths:
                abs_path = Path(path).resolve()
                try:
                    rel_path = abs_path.relative_to(repo_root)
                    relative_paths.append(str(rel_path).replace('\\', '/'))
                except ValueError:
                    raise GitOperationError(
                        f"File '{path}' is not within the repository"
                    )
            
            # Perform checkout
            if commit:
                self.repo.git.checkout(commit, '--', *relative_paths)
            else:
                self.repo.git.checkout('HEAD', '--', *relative_paths)
                
        except Exception as e:
            raise GitOperationError(
                f"Failed to checkout files: {e}"
            )
