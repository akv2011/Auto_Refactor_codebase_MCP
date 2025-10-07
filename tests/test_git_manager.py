"""
Tests for the GitManager class.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from git import Repo
from src.git_manager import (
    GitManager,
    NotAGitRepositoryError,
    GitManagerError,
    GitOperationError
)


class TestGitManagerInit:
    """Tests for GitManager initialization."""
    
    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary Git repository for testing."""
        temp_dir = tempfile.mkdtemp()
        repo = Repo.init(temp_dir)
        
        # Create an initial commit
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Initial content")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def temp_non_git_dir(self):
        """Create a temporary directory that is not a Git repository."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_init_with_valid_repo_string_path(self, temp_git_repo):
        """Test initialization with a valid Git repository using string path."""
        manager = GitManager(temp_git_repo)
        assert manager is not None
        assert manager.repo_path == Path(temp_git_repo).resolve()
        assert manager.repo is not None
    
    def test_init_with_valid_repo_path_object(self, temp_git_repo):
        """Test initialization with a valid Git repository using Path object."""
        manager = GitManager(Path(temp_git_repo))
        assert manager is not None
        assert manager.repo_path == Path(temp_git_repo).resolve()
        assert manager.repo is not None
    
    def test_init_with_non_git_directory(self, temp_non_git_dir):
        """Test initialization with a directory that is not a Git repository."""
        with pytest.raises(NotAGitRepositoryError, match="not a valid Git repository"):
            GitManager(temp_non_git_dir)
    
    def test_init_with_nonexistent_path(self):
        """Test initialization with a path that does not exist."""
        with pytest.raises(NotAGitRepositoryError, match="does not exist"):
            GitManager("/nonexistent/path/to/repo")
    
    def test_init_with_file_path(self, temp_git_repo):
        """Test initialization with a file path instead of directory."""
        file_path = Path(temp_git_repo) / "test.txt"
        with pytest.raises(NotAGitRepositoryError):
            GitManager(str(file_path))
    
    def test_init_stores_resolved_path(self, temp_git_repo):
        """Test that initialization stores the resolved absolute path."""
        # Use a relative path
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(Path(temp_git_repo).parent)
            relative_path = Path(temp_git_repo).name
            manager = GitManager(relative_path)
            
            # Path should be resolved to absolute
            assert manager.repo_path.is_absolute()
            assert manager.repo_path == Path(temp_git_repo).resolve()
        finally:
            os.chdir(original_cwd)


class TestGitManagerMethods:
    """Tests for GitManager methods."""
    
    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary Git repository for testing."""
        temp_dir = tempfile.mkdtemp()
        repo = Repo.init(temp_dir)
        
        # Create an initial commit
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Initial content")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_is_valid_repository(self, temp_git_repo):
        """Test checking if repository is valid."""
        manager = GitManager(temp_git_repo)
        assert manager.is_valid_repository() is True
    
    def test_get_repo_root(self, temp_git_repo):
        """Test getting repository root directory."""
        manager = GitManager(temp_git_repo)
        root = manager.get_repo_root()
        
        assert isinstance(root, Path)
        assert root == Path(temp_git_repo)
    
    def test_get_repo_root_in_subdirectory(self, temp_git_repo):
        """Test getting repo root when initialized from a subdirectory."""
        # Create a subdirectory
        subdir = Path(temp_git_repo) / "subdir"
        subdir.mkdir()
        
        # Initialize manager from subdirectory
        manager = GitManager(temp_git_repo)
        root = manager.get_repo_root()
        
        # Root should still be the top-level repo directory
        assert root == Path(temp_git_repo)


class TestGitManagerRepresentation:
    """Tests for GitManager string representations."""
    
    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary Git repository for testing."""
        temp_dir = tempfile.mkdtemp()
        repo = Repo.init(temp_dir)
        
        # Create an initial commit on main branch
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Initial content")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_repr(self, temp_git_repo):
        """Test __repr__ method."""
        manager = GitManager(temp_git_repo)
        repr_str = repr(manager)
        
        assert "GitManager" in repr_str
        assert "repo_path" in repr_str
        assert str(Path(temp_git_repo).resolve()) in repr_str
    
    def test_str_with_branch(self, temp_git_repo):
        """Test __str__ method with active branch."""
        manager = GitManager(temp_git_repo)
        str_repr = str(manager)
        
        assert "GitManager" in str_repr
        assert "repository at" in str_repr
        assert "branch:" in str_repr
    
    def test_str_detached_head(self, temp_git_repo):
        """Test __str__ method with detached HEAD."""
        manager = GitManager(temp_git_repo)
        
        # Get the first commit hash
        commit = list(manager.repo.iter_commits())[-1]
        
        # Checkout the commit to create detached HEAD
        manager.repo.git.checkout(commit.hexsha)
        
        str_repr = str(manager)
        assert "detached HEAD" in str_repr


class TestGitManagerEdgeCases:
    """Tests for edge cases and error handling."""
    
    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary Git repository for testing."""
        temp_dir = tempfile.mkdtemp()
        repo = Repo.init(temp_dir)
        
        # Create an initial commit
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Initial content")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_empty_git_repo(self):
        """Test with an empty Git repository (no commits)."""
        temp_dir = tempfile.mkdtemp()
        try:
            Repo.init(temp_dir)
            
            # Should be able to initialize GitManager even with no commits
            manager = GitManager(temp_dir)
            assert manager is not None
            assert manager.is_valid_repository()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_bare_repository(self):
        """Test with a bare Git repository."""
        temp_dir = tempfile.mkdtemp()
        try:
            Repo.init(temp_dir, bare=True)
            
            # GitManager should be able to work with bare repos
            manager = GitManager(temp_dir)
            assert manager is not None
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_corrupted_git_directory(self, temp_git_repo):
        """Test with a corrupted .git directory."""
        # Remove the HEAD file to corrupt the repo
        git_dir = Path(temp_git_repo) / ".git"
        head_file = git_dir / "HEAD"
        if head_file.exists():
            head_file.unlink()
        
        # Should raise an error when trying to initialize
        with pytest.raises((NotAGitRepositoryError, GitManagerError)):
            GitManager(temp_git_repo)


class TestGitManagerIntegration:
    """Integration tests for GitManager."""
    
    @pytest.fixture
    def complex_git_repo(self):
        """Create a more complex Git repository for integration testing."""
        temp_dir = tempfile.mkdtemp()
        repo = Repo.init(temp_dir)
        
        # Create multiple files
        for i in range(3):
            file = Path(temp_dir) / f"file{i}.txt"
            file.write_text(f"Content {i}")
        
        # Stage and commit
        repo.index.add(["file0.txt", "file1.txt", "file2.txt"])
        repo.index.commit("Initial commit with multiple files")
        
        # Create a subdirectory with files
        subdir = Path(temp_dir) / "subdir"
        subdir.mkdir()
        subfile = subdir / "subfile.txt"
        subfile.write_text("Subdirectory content")
        
        repo.index.add(["subdir/subfile.txt"])
        repo.index.commit("Add subdirectory")
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_manager_with_complex_repo(self, complex_git_repo):
        """Test GitManager with a more complex repository structure."""
        manager = GitManager(complex_git_repo)
        
        assert manager.is_valid_repository()
        assert manager.get_repo_root() == Path(complex_git_repo)
        
        # Should have multiple commits
        commits = list(manager.repo.iter_commits())
        assert len(commits) == 2


class TestBranchOperations:
    """Tests for branch-related operations."""
    
    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary Git repository for testing."""
        temp_dir = tempfile.mkdtemp()
        repo = Repo.init(temp_dir)
        
        # Create an initial commit
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Initial content")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_get_current_branch_name(self, temp_git_repo):
        """Test getting the current branch name."""
        manager = GitManager(temp_git_repo)
        branch_name = manager.get_current_branch_name()
        
        # Default branch is usually 'master' or 'main'
        assert branch_name in ['master', 'main']
    
    def test_get_current_branch_name_after_switch(self, temp_git_repo):
        """Test getting branch name after switching branches."""
        manager = GitManager(temp_git_repo)
        
        # Create and checkout a new branch
        new_branch = manager.repo.create_head('feature-branch')
        new_branch.checkout()
        
        # Verify we're on the new branch
        assert manager.get_current_branch_name() == 'feature-branch'
    
    def test_get_current_branch_name_detached_head(self, temp_git_repo):
        """Test error when getting branch name in detached HEAD state."""
        manager = GitManager(temp_git_repo)
        
        # Get the first commit hash
        commit = list(manager.repo.iter_commits())[-1]
        
        # Checkout the commit to create detached HEAD
        manager.repo.git.checkout(commit.hexsha)
        
        # Should raise error
        with pytest.raises(GitOperationError, match="detached HEAD state"):
            manager.get_current_branch_name()
    
    def test_is_detached_head_false(self, temp_git_repo):
        """Test is_detached_head returns False when on a branch."""
        manager = GitManager(temp_git_repo)
        assert manager.is_detached_head() is False
    
    def test_is_detached_head_true(self, temp_git_repo):
        """Test is_detached_head returns True in detached HEAD state."""
        manager = GitManager(temp_git_repo)
        
        # Get the first commit hash
        commit = list(manager.repo.iter_commits())[-1]
        
        # Checkout the commit to create detached HEAD
        manager.repo.git.checkout(commit.hexsha)
        
        assert manager.is_detached_head() is True
    
    def test_get_current_commit_hash(self, temp_git_repo):
        """Test getting the current commit hash."""
        manager = GitManager(temp_git_repo)
        
        full_hash = manager.get_current_commit_hash()
        assert len(full_hash) == 40  # Full SHA-1 hash
        assert full_hash.isalnum()
    
    def test_get_current_commit_hash_short(self, temp_git_repo):
        """Test getting the shortened commit hash."""
        manager = GitManager(temp_git_repo)
        
        short_hash = manager.get_current_commit_hash(short=True)
        assert len(short_hash) == 7
        assert short_hash.isalnum()
    
    def test_commit_hash_consistency(self, temp_git_repo):
        """Test that full and short hashes are consistent."""
        manager = GitManager(temp_git_repo)
        
        full_hash = manager.get_current_commit_hash()
        short_hash = manager.get_current_commit_hash(short=True)
        
        # Short hash should be the first 7 chars of full hash
        assert full_hash.startswith(short_hash)


class TestBackupBranchCreation:
    """Tests for backup branch creation."""
    
    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary Git repository for testing."""
        temp_dir = tempfile.mkdtemp()
        repo = Repo.init(temp_dir)
        
        # Create an initial commit
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Initial content")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_create_backup_branch(self, temp_git_repo):
        """Test creating a backup branch."""
        manager = GitManager(temp_git_repo)
        branch_name = manager.create_backup_branch('test-backup')
        
        # Verify branch was created
        assert branch_name.startswith('test-backup-')
        assert manager.branch_exists(branch_name)
    
    def test_create_backup_branch_default_prefix(self, temp_git_repo):
        """Test creating backup branch with default prefix."""
        manager = GitManager(temp_git_repo)
        branch_name = manager.create_backup_branch()
        
        # Should start with default 'backup' prefix
        assert branch_name.startswith('backup-')
    
    def test_backup_branch_timestamp_format(self, temp_git_repo):
        """Test that backup branch name contains properly formatted timestamp."""
        manager = GitManager(temp_git_repo)
        branch_name = manager.create_backup_branch('test')
        
        # Extract timestamp part
        parts = branch_name.split('-')
        assert len(parts) == 2
        timestamp = parts[1]
        
        # Should be 14 digits (YYYYMMDDHHMMSS)
        assert len(timestamp) == 14
        assert timestamp.isdigit()
    
    def test_backup_branch_points_to_same_commit(self, temp_git_repo):
        """Test that backup branch points to the same commit as current HEAD."""
        manager = GitManager(temp_git_repo)
        
        # Get current commit hash
        current_commit = manager.get_current_commit_hash()
        
        # Create backup branch
        branch_name = manager.create_backup_branch('test')
        
        # Get the commit hash of the backup branch
        backup_branch = manager.repo.heads[branch_name]
        backup_commit = backup_branch.commit.hexsha
        
        # Should point to same commit
        assert backup_commit == current_commit
    
    def test_multiple_backup_branches(self, temp_git_repo):
        """Test creating multiple backup branches."""
        import time
        
        manager = GitManager(temp_git_repo)
        
        # Create first backup
        branch1 = manager.create_backup_branch('test')
        time.sleep(1)  # Ensure different timestamps
        
        # Create second backup
        branch2 = manager.create_backup_branch('test')
        
        # Both should exist and have different names
        assert manager.branch_exists(branch1)
        assert manager.branch_exists(branch2)
        assert branch1 != branch2
    
    def test_list_branches(self, temp_git_repo):
        """Test listing all branches."""
        manager = GitManager(temp_git_repo)
        
        # Get initial branches
        initial_branches = manager.list_branches()
        
        # Create backup branch
        backup_name = manager.create_backup_branch('test')
        
        # List branches again
        branches = manager.list_branches()
        
        # Should have one more branch
        assert len(branches) == len(initial_branches) + 1
        assert backup_name in branches
    
    def test_branch_exists(self, temp_git_repo):
        """Test checking if branch exists."""
        manager = GitManager(temp_git_repo)
        
        # Non-existent branch
        assert manager.branch_exists('nonexistent') is False
        
        # Create and check
        branch_name = manager.create_backup_branch('test')
        assert manager.branch_exists(branch_name) is True
    
    def test_backup_branch_with_special_chars(self, temp_git_repo):
        """Test creating backup branch with various prefix characters."""
        manager = GitManager(temp_git_repo)
        
        # Test with slash (common in Git branch naming)
        branch_name = manager.create_backup_branch('refactor/test')
        assert manager.branch_exists(branch_name)
        assert 'refactor/test-' in branch_name


class TestStagingAndCommitting:
    """Tests for staging and committing operations."""
    
    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary Git repository for testing."""
        temp_dir = tempfile.mkdtemp()
        repo = Repo.init(temp_dir)
        
        # Create an initial commit
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Initial content")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_stage_and_commit_single_file(self, temp_git_repo):
        """Test staging and committing a single file."""
        manager = GitManager(temp_git_repo)
        
        # Modify existing file
        test_file = Path(temp_git_repo) / "test.txt"
        test_file.write_text("Modified content")
        
        # Stage and commit
        commit_hash = manager.stage_and_commit(str(test_file), "Updated test file")
        
        # Verify commit was created
        assert commit_hash is not None
        assert len(commit_hash) == 40  # Full SHA-1 hash
        
        # Verify commit message
        latest_commit = manager.repo.head.commit
        assert latest_commit.message.strip() == "Updated test file"
    
    def test_stage_and_commit_multiple_files(self, temp_git_repo):
        """Test staging and committing multiple files."""
        manager = GitManager(temp_git_repo)
        
        # Create new files
        file1 = Path(temp_git_repo) / "file1.txt"
        file2 = Path(temp_git_repo) / "file2.txt"
        file1.write_text("File 1 content")
        file2.write_text("File 2 content")
        
        # Stage and commit
        commit_hash = manager.stage_and_commit(
            [str(file1), str(file2)],
            "Added two new files"
        )
        
        # Verify commit was created
        assert commit_hash is not None
        
        # Verify files are in the commit
        latest_commit = manager.repo.head.commit
        committed_files = list(latest_commit.stats.files.keys())
        assert "file1.txt" in committed_files
        assert "file2.txt" in committed_files
    
    def test_stage_and_commit_nonexistent_file(self, temp_git_repo):
        """Test error when trying to commit nonexistent file."""
        manager = GitManager(temp_git_repo)
        
        with pytest.raises(GitOperationError, match="File not found"):
            manager.stage_and_commit("nonexistent.txt", "This should fail")
    
    def test_stage_and_commit_file_outside_repo(self, temp_git_repo):
        """Test error when trying to commit file outside repository."""
        manager = GitManager(temp_git_repo)
        
        # Create a file outside the repo
        temp_file = Path(tempfile.gettempdir()) / "outside.txt"
        temp_file.write_text("Outside content")
        
        try:
            with pytest.raises(GitOperationError, match="not within the repository"):
                manager.stage_and_commit(str(temp_file), "This should fail")
        finally:
            temp_file.unlink(missing_ok=True)
    
    def test_get_staged_files(self, temp_git_repo):
        """Test getting list of staged files."""
        manager = GitManager(temp_git_repo)
        
        # Initially no staged files
        staged = manager.get_staged_files()
        assert len(staged) == 0
        
        # Modify and stage a file
        test_file = Path(temp_git_repo) / "test.txt"
        test_file.write_text("Modified content")
        manager.repo.index.add(["test.txt"])
        
        # Should now have staged file
        staged = manager.get_staged_files()
        assert "test.txt" in staged
    
    def test_get_modified_files(self, temp_git_repo):
        """Test getting list of modified files."""
        manager = GitManager(temp_git_repo)
        
        # Initially no modified files
        modified = manager.get_modified_files()
        assert len(modified) == 0
        
        # Modify existing file
        test_file = Path(temp_git_repo) / "test.txt"
        test_file.write_text("Modified content")
        
        # Should now have modified file
        modified = manager.get_modified_files()
        assert "test.txt" in modified
        
        # Create untracked file
        new_file = Path(temp_git_repo) / "new.txt"
        new_file.write_text("New content")
        
        # Should also appear in modified list
        modified = manager.get_modified_files()
        assert "new.txt" in modified
    
    def test_has_uncommitted_changes_false(self, temp_git_repo):
        """Test has_uncommitted_changes when clean."""
        manager = GitManager(temp_git_repo)
        assert manager.has_uncommitted_changes() is False
    
    def test_has_uncommitted_changes_with_modified(self, temp_git_repo):
        """Test has_uncommitted_changes with modified files."""
        manager = GitManager(temp_git_repo)
        
        # Modify file
        test_file = Path(temp_git_repo) / "test.txt"
        test_file.write_text("Modified content")
        
        assert manager.has_uncommitted_changes() is True
    
    def test_has_uncommitted_changes_with_untracked(self, temp_git_repo):
        """Test has_uncommitted_changes with untracked files."""
        manager = GitManager(temp_git_repo)
        
        # Create new file
        new_file = Path(temp_git_repo) / "new.txt"
        new_file.write_text("New content")
        
        assert manager.has_uncommitted_changes() is True
    
    def test_commit_message_preserved(self, temp_git_repo):
        """Test that commit messages are properly preserved."""
        manager = GitManager(temp_git_repo)
        
        message = "This is a detailed commit message\nWith multiple lines"
        
        # Create and commit a new file
        new_file = Path(temp_git_repo) / "new.txt"
        new_file.write_text("Content")
        
        manager.stage_and_commit(str(new_file), message)
        
        # Verify message
        latest_commit = manager.repo.head.commit
        assert latest_commit.message.strip() == message.strip()


class TestRollbackFunctionality:
    """Tests for rollback and recovery operations."""
    
    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary Git repository for testing."""
        temp_dir = tempfile.mkdtemp()
        repo = Repo.init(temp_dir)
        
        # Create an initial commit
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Initial content")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_rollback_to_branch(self, temp_git_repo):
        """Test rolling back to a backup branch."""
        manager = GitManager(temp_git_repo)
        
        # Create backup
        backup_branch = manager.create_backup_branch('backup')
        
        # Modify file on main branch
        test_file = Path(temp_git_repo) / "test.txt"
        test_file.write_text("Modified content")
        manager.stage_and_commit(str(test_file), "Modified on main")
        
        # Rollback to backup
        manager.rollback_to_branch(backup_branch, force=True)
        
        # Verify we're on backup branch
        assert manager.get_current_branch_name() == backup_branch
        
        # Verify file content is original
        assert test_file.read_text() == "Initial content"
    
    def test_rollback_to_nonexistent_branch(self, temp_git_repo):
        """Test error when rolling back to nonexistent branch."""
        manager = GitManager(temp_git_repo)
        
        with pytest.raises(GitOperationError, match="does not exist"):
            manager.rollback_to_branch('nonexistent', force=True)
    
    def test_rollback_to_commit_hard(self, temp_git_repo):
        """Test hard reset to a previous commit."""
        manager = GitManager(temp_git_repo)
        
        # Get original commit
        original_commit = manager.get_current_commit_hash()
        
        # Make a change and commit
        test_file = Path(temp_git_repo) / "test.txt"
        test_file.write_text("Modified content")
        manager.stage_and_commit(str(test_file), "Modified file")
        
        # Rollback to original
        manager.rollback_to_commit(original_commit, hard=True)
        
        # File should be reverted
        assert test_file.read_text() == "Initial content"
    
    def test_rollback_to_commit_soft(self, temp_git_repo):
        """Test soft reset to a previous commit."""
        manager = GitManager(temp_git_repo)
        
        # Get original commit
        original_commit = manager.get_current_commit_hash()
        
        # Make a change and commit
        test_file = Path(temp_git_repo) / "test.txt"
        test_file.write_text("Modified content")
        manager.stage_and_commit(str(test_file), "Modified file")
        
        # Soft rollback (keep changes)
        manager.rollback_to_commit(original_commit, hard=False)
        
        # File should still have modifications
        assert test_file.read_text() == "Modified content"
    
    def test_delete_branch(self, temp_git_repo):
        """Test deleting a branch."""
        manager = GitManager(temp_git_repo)
        
        # Create a branch
        branch_name = manager.create_backup_branch('test')
        assert manager.branch_exists(branch_name)
        
        # Delete it
        manager.delete_branch(branch_name, force=True)
        
        # Should no longer exist
        assert manager.branch_exists(branch_name) is False
    
    def test_delete_current_branch(self, temp_git_repo):
        """Test error when trying to delete current branch."""
        manager = GitManager(temp_git_repo)
        
        current = manager.get_current_branch_name()
        
        with pytest.raises(GitOperationError, match="currently active branch"):
            manager.delete_branch(current)
    
    def test_delete_nonexistent_branch(self, temp_git_repo):
        """Test error when deleting nonexistent branch."""
        manager = GitManager(temp_git_repo)
        
        with pytest.raises(GitOperationError, match="does not exist"):
            manager.delete_branch('nonexistent')
    
    def test_checkout_files_from_head(self, temp_git_repo):
        """Test checking out files from HEAD."""
        manager = GitManager(temp_git_repo)
        
        # Modify file
        test_file = Path(temp_git_repo) / "test.txt"
        test_file.write_text("Modified content")
        
        # Checkout from HEAD (revert)
        manager.checkout_files(str(test_file))
        
        # Should be reverted
        assert test_file.read_text() == "Initial content"
    
    def test_checkout_multiple_files(self, temp_git_repo):
        """Test checking out multiple files."""
        manager = GitManager(temp_git_repo)
        
        # Create and commit new files
        file1 = Path(temp_git_repo) / "file1.txt"
        file2 = Path(temp_git_repo) / "file2.txt"
        file1.write_text("File 1")
        file2.write_text("File 2")
        manager.stage_and_commit([str(file1), str(file2)], "Add files")
        
        # Modify both
        file1.write_text("Modified 1")
        file2.write_text("Modified 2")
        
        # Checkout both from HEAD
        manager.checkout_files([str(file1), str(file2)])
        
        # Both should be reverted
        assert file1.read_text() == "File 1"
        assert file2.read_text() == "File 2"
    
    def test_checkout_files_from_commit(self, temp_git_repo):
        """Test checking out files from specific commit."""
        manager = GitManager(temp_git_repo)
        
        # Get original commit
        original_commit = manager.get_current_commit_hash()
        
        # Modify and commit
        test_file = Path(temp_git_repo) / "test.txt"
        test_file.write_text("Modified once")
        manager.stage_and_commit(str(test_file), "First modification")
        
        # Modify again
        test_file.write_text("Modified twice")
        manager.stage_and_commit(str(test_file), "Second modification")
        
        # Checkout from original commit
        manager.checkout_files(str(test_file), commit=original_commit)
        
        # Should have original content
        assert test_file.read_text() == "Initial content"
    
    def test_integrated_backup_and_rollback(self, temp_git_repo):
        """Integration test: full backup and rollback workflow."""
        manager = GitManager(temp_git_repo)
        
        # Create backup before changes
        backup = manager.create_backup_branch('refactor')
        original_content = Path(temp_git_repo) / "test.txt"
        original_text = original_content.read_text()
        
        # Make changes
        original_content.write_text("Refactored content")
        manager.stage_and_commit(str(original_content), "Refactored code")
        
        # Something went wrong, rollback
        manager.rollback_to_branch(backup, force=True)
        
        # Verify rollback successful
        assert original_content.read_text() == original_text
        assert manager.get_current_branch_name() == backup
        
        # Clean up backup branch by switching back and deleting
        main_branch = [b for b in manager.list_branches() if b in ['master', 'main']][0]
        manager.rollback_to_branch(main_branch, force=True)
        manager.delete_branch(backup, force=True)
        
        assert not manager.branch_exists(backup)
