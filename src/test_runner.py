"""
Test Runner for executing project test suites.

This module provides functionality to run test commands specified in the
configuration and determine if tests pass or fail.
"""

import subprocess
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TestResult:
    """Result of running a test suite."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration: float  # in seconds
    command: str
    error: Optional[str] = None


class TestRunnerError(Exception):
    """Base exception for test runner errors."""
    pass


class TestCommandNotFoundError(TestRunnerError):
    """Raised when no test command is configured."""
    pass


class TestRunner:
    """
    Runs project test suites and reports results.
    
    This class executes test commands (like pytest, npm test, etc.) in the
    project directory and captures their output to determine success or failure.
    
    Example:
        >>> runner = TestRunner('/path/to/project')
        >>> result = await runner.run_tests('pytest tests/')
        >>> print(f"Tests passed: {result.success}")
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the TestRunner.
        
        Args:
            project_root: Root directory of the project. If None, uses current directory.
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        
        if not self.project_root.exists():
            raise TestRunnerError(
                f"Project root does not exist: {self.project_root}"
            )
        
        if not self.project_root.is_dir():
            raise TestRunnerError(
                f"Project root is not a directory: {self.project_root}"
            )
    
    async def run_tests(
        self,
        test_command: str,
        timeout: Optional[float] = None
    ) -> TestResult:
        """
        Run tests using the specified command.
        
        Args:
            test_command: Command to execute (e.g., 'pytest', 'npm test')
            timeout: Maximum time to wait for tests (seconds). None = no timeout.
            
        Returns:
            TestResult object with test execution details
            
        Raises:
            TestRunnerError: If command execution fails unexpectedly
            asyncio.TimeoutError: If tests exceed timeout
            
        Example:
            >>> runner = TestRunner('/path/to/project')
            >>> result = await runner.run_tests('pytest -v', timeout=300)
            >>> if result.success:
            ...     print("All tests passed!")
        """
        if not test_command or not test_command.strip():
            raise TestCommandNotFoundError("Test command is empty or not provided")
        
        import time
        start_time = time.time()
        
        try:
            # Create the subprocess
            process = await asyncio.create_subprocess_shell(
                test_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_root)
            )
            
            # Wait for completion with optional timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                # Kill the process if it times out
                process.kill()
                await process.wait()
                
                duration = time.time() - start_time
                return TestResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr="",
                    duration=duration,
                    command=test_command,
                    error=f"Test execution timed out after {timeout} seconds"
                )
            
            duration = time.time() - start_time
            
            # Decode output
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            
            # Determine success based on exit code
            # Exit code 0 typically means success
            success = process.returncode == 0
            
            return TestResult(
                success=success,
                exit_code=process.returncode,
                stdout=stdout_str,
                stderr=stderr_str,
                duration=duration,
                command=test_command
            )
            
        except FileNotFoundError as e:
            duration = time.time() - start_time
            return TestResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                duration=duration,
                command=test_command,
                error=f"Command not found: {str(e)}"
            )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                duration=duration,
                command=test_command,
                error=f"Unexpected error: {str(e)}"
            )
    
    def run_tests_sync(
        self,
        test_command: str,
        timeout: Optional[float] = None
    ) -> TestResult:
        """
        Synchronous wrapper for run_tests.
        
        This is a convenience method for cases where async execution
        is not needed or desired.
        
        Args:
            test_command: Command to execute (e.g., 'pytest', 'npm test')
            timeout: Maximum time to wait for tests (seconds). None = no timeout.
            
        Returns:
            TestResult object with test execution details
            
        Example:
            >>> runner = TestRunner('/path/to/project')
            >>> result = runner.run_tests_sync('pytest')
            >>> print(f"Exit code: {result.exit_code}")
        """
        if not test_command or not test_command.strip():
            raise TestCommandNotFoundError("Test command is empty or not provided")
        
        import time
        start_time = time.time()
        
        try:
            # Run subprocess synchronously
            process = subprocess.run(
                test_command,
                shell=True,
                cwd=str(self.project_root),
                capture_output=True,
                timeout=timeout,
                text=True
            )
            
            duration = time.time() - start_time
            
            # Determine success based on exit code
            success = process.returncode == 0
            
            return TestResult(
                success=success,
                exit_code=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
                duration=duration,
                command=test_command
            )
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return TestResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                duration=duration,
                command=test_command,
                error=f"Test execution timed out after {timeout} seconds"
            )
        except FileNotFoundError as e:
            duration = time.time() - start_time
            return TestResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                duration=duration,
                command=test_command,
                error=f"Command not found: {str(e)}"
            )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                duration=duration,
                command=test_command,
                error=f"Unexpected error: {str(e)}"
            )
    
    def get_test_command_from_config(
        self,
        config: Dict[str, Any],
        language: str = 'python'
    ) -> str:
        """
        Extract test command from configuration.
        
        Args:
            config: Configuration dictionary
            language: Programming language to get test command for
            
        Returns:
            Test command string
            
        Raises:
            TestCommandNotFoundError: If no test command is configured
            
        Example:
            >>> runner = TestRunner()
            >>> config = {'languages': {'python': {'testCommand': 'pytest'}}}
            >>> cmd = runner.get_test_command_from_config(config, 'python')
            >>> print(cmd)
            pytest
        """
        try:
            # Navigate config structure to find test command
            test_command = config.get('languages', {}).get(language, {}).get('testCommand', '')
            
            if not test_command or not test_command.strip():
                raise TestCommandNotFoundError(
                    f"No test command configured for language: {language}"
                )
            
            return test_command.strip()
            
        except (KeyError, AttributeError) as e:
            raise TestCommandNotFoundError(
                f"Invalid configuration structure: {e}"
            )
