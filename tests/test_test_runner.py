"""
Tests for TestRunner module.

Tests the test runner functionality including sync and async execution,
timeout handling, and configuration parsing.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path

from src.test_runner import (
    TestRunner,
    TestResult,
    TestRunnerError,
    TestCommandNotFoundError,
)


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def runner(temp_project_dir):
    """Create a TestRunner instance."""
    return TestRunner(temp_project_dir)


class TestTestRunnerInit:
    """Tests for TestRunner initialization."""
    
    def test_init_with_valid_directory(self, temp_project_dir):
        """Test initialization with a valid project directory."""
        runner = TestRunner(temp_project_dir)
        assert runner.project_root == temp_project_dir
    
    def test_init_with_current_directory(self):
        """Test initialization without specifying directory uses cwd."""
        runner = TestRunner()
        assert runner.project_root == Path.cwd()
    
    def test_init_with_nonexistent_directory(self):
        """Test initialization with nonexistent directory raises error."""
        with pytest.raises(TestRunnerError, match="does not exist"):
            TestRunner(Path("/nonexistent/path"))
    
    def test_init_with_file_instead_of_directory(self, temp_project_dir):
        """Test initialization with file path raises error."""
        test_file = temp_project_dir / "test.txt"
        test_file.write_text("test")
        
        with pytest.raises(TestRunnerError, match="not a directory"):
            TestRunner(test_file)


class TestSyncTestExecution:
    """Tests for synchronous test execution."""
    
    def test_run_simple_passing_command(self, runner):
        """Test running a simple command that succeeds."""
        # Use echo command which should succeed on all platforms
        result = runner.run_tests_sync('echo "Test passed"')
        
        assert result.success is True
        assert result.exit_code == 0
        assert "Test passed" in result.stdout
        assert result.command == 'echo "Test passed"'
        assert result.duration >= 0
    
    def test_run_simple_failing_command(self, runner):
        """Test running a command that fails."""
        # Use a command that will fail (exit 1)
        if Path("/bin/sh").exists():  # Unix-like
            result = runner.run_tests_sync('exit 1')
        else:  # Windows
            result = runner.run_tests_sync('exit /b 1')
        
        assert result.success is False
        assert result.exit_code == 1
    
    def test_run_with_empty_command(self, runner):
        """Test running with empty command raises error."""
        with pytest.raises(TestCommandNotFoundError, match="empty"):
            runner.run_tests_sync('')
    
    def test_run_with_whitespace_command(self, runner):
        """Test running with whitespace-only command raises error."""
        with pytest.raises(TestCommandNotFoundError, match="empty"):
            runner.run_tests_sync('   ')
    
    def test_run_with_timeout(self, runner):
        """Test command timeout handling."""
        # Use a command that will take a long time
        # On Windows, use ping with delay; on Unix, use sleep
        if Path("/bin/sh").exists():  # Unix-like
            result = runner.run_tests_sync('sleep 5', timeout=0.5)
        else:  # Windows - use ping localhost with delay
            # ping -n 10 will wait ~9 seconds
            result = runner.run_tests_sync('ping -n 10 127.0.0.1', timeout=0.5)
        
        assert result.success is False
        # On timeout, we set exit_code to -1
        assert result.error is not None
        assert "timed out" in result.error.lower()
    
    def test_run_with_stdout_and_stderr(self, runner, temp_project_dir):
        """Test capturing stdout and stderr."""
        # Create a Python script that prints to both
        script = temp_project_dir / "test_script.py"
        script.write_text("""
import sys
print("stdout message")
print("stderr message", file=sys.stderr)
""")
        
        result = runner.run_tests_sync(f'python {script}')
        
        assert "stdout message" in result.stdout
        assert "stderr message" in result.stderr
    
    def test_run_pytest_command(self, runner, temp_project_dir):
        """Test running actual pytest command."""
        # Create a simple test file
        test_file = temp_project_dir / "test_example.py"
        test_file.write_text("""
def test_always_passes():
    assert True

def test_simple_math():
    assert 1 + 1 == 2
""")
        
        # Use python -m pytest to ensure pytest is available
        result = runner.run_tests_sync('python -m pytest -v')
        
        # pytest should succeed
        assert result.success is True
        assert result.exit_code == 0
        # Check for test output
        combined_output = result.stdout + result.stderr
        assert ("test_always_passes" in combined_output or 
                "2 passed" in combined_output or
                "passed" in combined_output.lower())


class TestAsyncTestExecution:
    """Tests for asynchronous test execution."""
    
    @pytest.mark.asyncio
    async def test_run_simple_passing_command_async(self, runner):
        """Test async execution of passing command."""
        result = await runner.run_tests('echo "Async test"')
        
        assert result.success is True
        assert result.exit_code == 0
        assert "Async test" in result.stdout
    
    @pytest.mark.asyncio
    async def test_run_simple_failing_command_async(self, runner):
        """Test async execution of failing command."""
        if Path("/bin/sh").exists():  # Unix-like
            result = await runner.run_tests('exit 1')
        else:  # Windows
            result = await runner.run_tests('exit /b 1')
        
        assert result.success is False
        assert result.exit_code == 1
    
    @pytest.mark.asyncio
    async def test_run_with_timeout_async(self, runner):
        """Test async command timeout handling."""
        if Path("/bin/sh").exists():  # Unix-like
            result = await runner.run_tests('sleep 5', timeout=0.5)
        else:  # Windows - use ping with delay
            result = await runner.run_tests('ping -n 10 127.0.0.1', timeout=0.5)
        
        assert result.success is False
        assert result.error is not None
        assert "timed out" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_run_empty_command_async(self, runner):
        """Test async execution with empty command raises error."""
        with pytest.raises(TestCommandNotFoundError):
            await runner.run_tests('')


class TestConfigurationIntegration:
    """Tests for configuration parsing."""
    
    def test_get_test_command_from_config(self, runner):
        """Test extracting test command from config."""
        config = {
            'languages': {
                'python': {
                    'testCommand': 'pytest -v'
                }
            }
        }
        
        command = runner.get_test_command_from_config(config, 'python')
        assert command == 'pytest -v'
    
    def test_get_test_command_strips_whitespace(self, runner):
        """Test that test command is stripped of whitespace."""
        config = {
            'languages': {
                'python': {
                    'testCommand': '  pytest -v  '
                }
            }
        }
        
        command = runner.get_test_command_from_config(config, 'python')
        assert command == 'pytest -v'
    
    def test_get_test_command_missing_language(self, runner):
        """Test error when language not in config."""
        config = {
            'languages': {
                'python': {
                    'testCommand': 'pytest'
                }
            }
        }
        
        with pytest.raises(TestCommandNotFoundError, match="javascript"):
            runner.get_test_command_from_config(config, 'javascript')
    
    def test_get_test_command_empty_command(self, runner):
        """Test error when test command is empty."""
        config = {
            'languages': {
                'python': {
                    'testCommand': ''
                }
            }
        }
        
        with pytest.raises(TestCommandNotFoundError):
            runner.get_test_command_from_config(config, 'python')
    
    def test_get_test_command_invalid_structure(self, runner):
        """Test error with invalid config structure."""
        config = {'invalid': 'structure'}
        
        with pytest.raises(TestCommandNotFoundError):
            runner.get_test_command_from_config(config, 'python')
    
    def test_get_test_command_for_javascript(self, runner):
        """Test getting test command for JavaScript."""
        config = {
            'languages': {
                'javascript': {
                    'testCommand': 'npm test'
                },
                'python': {
                    'testCommand': 'pytest'
                }
            }
        }
        
        command = runner.get_test_command_from_config(config, 'javascript')
        assert command == 'npm test'


class TestTestResult:
    """Tests for TestResult dataclass."""
    
    def test_test_result_creation(self):
        """Test creating a TestResult instance."""
        result = TestResult(
            success=True,
            exit_code=0,
            stdout="Test output",
            stderr="",
            duration=1.5,
            command="pytest",
            error=None
        )
        
        assert result.success is True
        assert result.exit_code == 0
        assert result.stdout == "Test output"
        assert result.duration == 1.5
        assert result.command == "pytest"
        assert result.error is None
    
    def test_test_result_with_error(self):
        """Test TestResult with error message."""
        result = TestResult(
            success=False,
            exit_code=-1,
            stdout="",
            stderr="",
            duration=0.1,
            command="bad_command",
            error="Command not found"
        )
        
        assert result.success is False
        assert result.error == "Command not found"
