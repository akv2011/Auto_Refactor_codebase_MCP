"""
Auto-Refactor MCP Server - Intelligent Automated Code Refactoring

Main entry point for the Auto-Refactor MCP server.
"""

import os
import json
from pathlib import Path
from typing import Any, Optional, Dict
from mcp.server.fastmcp import FastMCP

from src.ai_suggestion_service import (
    AISuggestionService,
    AISuggestionServiceError,
    APINotConfiguredError,
    ModelNotAvailableError,
)
from src.metrics_engine import MetricsEngine
from src.refactoring_engine import RefactoringEngine, RefactoringError
from src.git_manager import GitManager, GitManagerError
from src.test_runner import TestRunner, TestRunnerError
from src.rollback_manager import RollbackManager, RollbackError
from src.suggestion_manager import (
    SuggestionManager,
    SuggestionStatus,
    SuggestionManagerError,
    SuggestionNotFoundError,
)
from src.database_refactoring import (
    DatabaseRefactoringEngine,
    DatabaseRefactoringError,
)

# Initialize FastMCP server
mcp = FastMCP("auto-refactor")


@mcp.tool()
async def hello_refactor() -> str:
    """
    Test tool to verify Auto-Refactor MCP server is running correctly.
    
    Returns:
        A greeting message from Auto-Refactor
    """
    return "Hello from Auto-Refactor MCP Server! 🚀 Ready to refactor your code."


@mcp.tool()
async def suggest_refactoring(
    file_path: str,
    strategy: str = "auto"
) -> str:
    """
    Generate AI-powered refactoring suggestions for a source code file.
    
    This tool analyzes the given file using Google's Gemini AI and provides
    intelligent refactoring suggestions with diffs and explanations.
    
    Args:
        file_path: Absolute path to the source code file to analyze
        strategy: Refactoring strategy to apply. Options:
                  - "auto" (default): Automatically determine best approach
                  - "split": Focus on splitting large functions/classes
                  - "extract": Focus on extracting reusable code
                  - "composition": Focus on improving object composition
    
    Returns:
        JSON string containing refactoring suggestions with structure:
        {
            "file_path": "path/to/file",
            "language": "python",
            "strategy_used": "auto",
            "suggestions": [
                {
                    "title": "Extract authentication logic",
                    "description": "...",
                    "strategy": "extract",
                    "priority": "high",
                    "estimated_impact": "Improves modularity...",
                    "diff": "--- a/file.py\n+++ b/file.py\n...",
                    "reason": "..."
                }
            ],
            "summary": "Overall analysis summary"
        }
    
    Raises:
        ValueError: If file doesn't exist or strategy is invalid
        APINotConfiguredError: If GOOGLE_API_KEY is not configured
        AISuggestionServiceError: If suggestion generation fails
    
    Environment Variables:
        GOOGLE_API_KEY: Required API key for Google Gemini
    """
    # Validate file exists
    file = Path(file_path)
    if not file.exists():
        raise ValueError(f"File not found: {file_path}")
    
    if not file.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    # Read file content
    try:
        with open(file, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        raise ValueError(f"Failed to read file {file_path}: {str(e)}")
    
    # Get metrics for the file (optional, enhances suggestions)
    metrics = None
    try:
        metrics_engine = MetricsEngine()
        metrics_result = metrics_engine.calculate(str(file))
        if metrics_result['status'] == 'success':
            metrics = metrics_result.get('metrics', {})
    except Exception:
        # Metrics are optional, continue without them
        pass
    
    # Initialize AI service (reads GOOGLE_API_KEY from environment)
    try:
        ai_service = AISuggestionService(
            model="gemini-2.0-flash-001",
            max_tokens=4000,
            temperature=0.2
        )
    except (APINotConfiguredError, ModelNotAvailableError) as e:
        raise APINotConfiguredError(str(e))
    
    # Generate suggestions
    try:
        suggestions_json = await ai_service.suggest_refactoring(
            file_path=str(file),
            code=code,
            metrics=metrics,
            strategy=strategy
        )
        
        # Parse the JSON to add suggestion_id to the response
        suggestions_data = json.loads(suggestions_json)
        
        # Cache the suggestion for interactive review
        try:
            manager = SuggestionManager()
            suggestion_id = manager.add_suggestion(
                file_path=str(file),
                suggestion_data=suggestions_data,
                metadata={
                    'strategy': strategy,
                    'metrics': metrics
                }
            )
            
            # Add the suggestion_id to the response
            suggestions_data['suggestion_id'] = suggestion_id
            suggestions_data['cache_info'] = {
                'message': 'Suggestion has been cached for review',
                'use_approve_suggestion': f'Use approve_suggestion("{suggestion_id}") to apply this refactoring'
            }
            
        except SuggestionManagerError:
            # If caching fails, continue without it
            suggestions_data['suggestion_id'] = None
            suggestions_data['cache_info'] = {
                'message': 'Warning: Failed to cache suggestion'
            }
        
        return json.dumps(suggestions_data, indent=2)
        
    except AISuggestionServiceError as e:
        raise AISuggestionServiceError(f"Failed to generate suggestions: {str(e)}")


@mcp.tool()
async def execute_refactoring(
    file_path: str,
    suggestion_json: str,
    dry_run: bool = True
) -> str:
    """
    Execute an approved refactoring operation with automatic testing and rollback.
    
    This tool applies a refactoring suggestion to a file. It creates a Git backup,
    applies the changes, runs tests, and automatically rolls back if tests fail.
    
    Args:
        file_path: Absolute path to the source code file to refactor
        suggestion_json: JSON string from suggest_refactoring containing the diff to apply.
                        Should contain at least one suggestion with a 'diff' field.
        dry_run: If True (default), only show what would be changed without applying.
                 If False, actually apply the changes and run tests.
    
    Returns:
        JSON string containing execution report with structure:
        {
            "status": "success|dry_run|rolled_back|error",
            "dry_run": true|false,
            "file_path": "path/to/file",
            "operation_id": "backup-branch-name" (if not dry_run),
            "changes_applied": true|false,
            "diff_preview": "...diff content..." (if dry_run),
            "tests_run": true|false,
            "tests_passed": true|false (if tests were run),
            "test_output": "..." (if tests were run),
            "rolled_back": true|false,
            "message": "Human-readable status message",
            "error": "Error details" (if status is error)
        }
    
    Raises:
        ValueError: If file doesn't exist or suggestion JSON is invalid
        RefactoringError: If refactoring operation fails
        GitManagerError: If Git operations fail
    
    Note:
        Requires a Git repository. The current directory must be within a Git repo.
    """
    # Validate file exists
    file = Path(file_path)
    if not file.exists():
        raise ValueError(f"File not found: {file_path}")
    
    if not file.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    # Parse suggestion JSON
    try:
        suggestions_data = json.loads(suggestion_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in suggestion_json: {str(e)}")
    
    # Extract the first suggestion's diff
    if 'suggestions' not in suggestions_data or not suggestions_data['suggestions']:
        raise ValueError("suggestion_json must contain at least one suggestion")
    
    first_suggestion = suggestions_data['suggestions'][0]
    if 'diff' not in first_suggestion:
        raise ValueError("Suggestion must contain a 'diff' field")
    
    diff_content = first_suggestion['diff']
    suggestion_title = first_suggestion.get('title', 'Refactoring')
    
    # Initialize result
    result = {
        "status": "unknown",
        "dry_run": dry_run,
        "file_path": str(file),
        "changes_applied": False,
        "tests_run": False,
        "rolled_back": False,
    }
    
    if dry_run:
        # Dry run mode: just show what would be done
        result.update({
            "status": "dry_run",
            "diff_preview": diff_content,
            "message": f"Dry run complete. Would apply: {suggestion_title}",
        })
        return json.dumps(result, indent=2)
    
    # NOT dry run - actually apply the refactoring
    operation_id = None
    rollback_manager = None
    
    try:
        # Step 1: Initialize Git and create backup
        git_manager = GitManager(str(file.parent))
        
        # Check if we're in a Git repo
        if not git_manager.is_git_repo():
            raise GitManagerError(
                f"Directory {file.parent} is not a Git repository. "
                "Git is required for safe refactoring with automatic rollback."
            )
        
        # Create backup branch
        backup_branch = git_manager.create_backup_branch()
        operation_id = backup_branch
        result["operation_id"] = operation_id
        
        # Initialize rollback manager to track the operation
        rollback_manager = RollbackManager(str(file.parent))
        rollback_manager.record_operation(
            operation_type="refactoring",
            file_paths=[str(file)],
            backup_branch=backup_branch,
            description=f"Apply refactoring: {suggestion_title}"
        )
        
        # Step 2: Apply the diff using RefactoringEngine
        refactoring_engine = RefactoringEngine()
        
        # Apply the diff
        refactor_result = refactoring_engine.apply({
            'type': 'apply_diff',
            'file': str(file),
            'diff': diff_content
        })
        
        if refactor_result['status'] != 'success':
            raise RefactoringError(
                f"Refactoring failed: {refactor_result.get('message', 'Unknown error')}"
            )
        
        result["changes_applied"] = True
        
        # Step 3: Run tests
        test_runner = TestRunner(str(file.parent))
        
        # Try to get test command from config, if available
        try:
            # Determine language from file extension
            ext_to_lang = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
            }
            language = ext_to_lang.get(file.suffix, 'python')
            
            from src.config_loader import load_config
            config = load_config(str(file.parent))
            test_command = test_runner.get_test_command_from_config(config, language)
        except Exception:
            # If config loading fails, use default pytest
            test_command = "pytest"
        
        # Run tests asynchronously
        test_result = await test_runner.run_async(test_command, timeout=60)
        result["tests_run"] = True
        result["tests_passed"] = (test_result.exit_code == 0)
        result["test_output"] = test_result.stdout if test_result.stdout else test_result.stderr
        
        # Step 4: Check if tests passed
        if test_result.exit_code != 0:
            # Tests failed - rollback!
            rollback_manager.rollback_operation(operation_id)
            result["rolled_back"] = True
            result["status"] = "rolled_back"
            result["message"] = (
                f"Refactoring applied but tests failed. "
                f"Changes have been automatically rolled back. "
                f"Test output: {test_result.stderr[:200]}"
            )
        else:
            # Success!
            result["status"] = "success"
            result["message"] = (
                f"Refactoring '{suggestion_title}' applied successfully. "
                f"All tests passed."
            )
        
        return json.dumps(result, indent=2)
        
    except (GitManagerError, RefactoringError, TestRunnerError) as e:
        # Operation failed - try to rollback if we created a backup
        if operation_id and rollback_manager:
            try:
                rollback_manager.rollback_operation(operation_id)
                result["rolled_back"] = True
            except RollbackError:
                pass  # Rollback failed, but we'll report the original error
        
        result["status"] = "error"
        result["error"] = str(e)
        result["message"] = f"Refactoring failed: {str(e)}"
        return json.dumps(result, indent=2)


@mcp.tool()
async def list_suggestions(
    status: Optional[str] = None,
    file_path: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    List cached refactoring suggestions with optional filtering.
    
    This tool shows all suggestions that have been generated but not yet
    approved, rejected, or executed. Useful for reviewing pending suggestions.
    
    Args:
        status: Filter by status (pending, approved, rejected, executed, failed)
        file_path: Filter suggestions for a specific file
        limit: Maximum number of suggestions to return (default: 10)
    
    Returns:
        JSON string containing list of suggestions with structure:
        {
            "suggestions": [
                {
                    "id": "abc123",
                    "file_path": "path/to/file.py",
                    "status": "pending",
                    "created_at": "2025-10-08T10:30:00",
                    "summary": "Brief description of suggestion"
                },
                ...
            ],
            "total": 5,
            "filtered_by": {"status": "pending", "limit": 10}
        }
    """
    try:
        manager = SuggestionManager()
        suggestions = manager.list_suggestions(
            status=status,
            file_path=file_path,
            limit=limit
        )
        
        # Format for output (simplified view)
        formatted = []
        for suggestion in suggestions:
            # Extract summary from suggestion data
            data = suggestion.get('data', {})
            summary = "No summary available"
            
            if 'suggestions' in data and data['suggestions']:
                first_sug = data['suggestions'][0]
                summary = first_sug.get('description', summary)
            
            formatted.append({
                'id': suggestion['id'],
                'file_path': suggestion['file_path'],
                'status': suggestion['status'],
                'created_at': suggestion['created_at'],
                'summary': summary[:100]  # Truncate long summaries
            })
        
        result = {
            'suggestions': formatted,
            'total': len(formatted),
            'filtered_by': {
                'status': status,
                'file_path': file_path,
                'limit': limit
            }
        }
        
        return json.dumps(result, indent=2)
        
    except SuggestionManagerError as e:
        return json.dumps({
            'status': 'error',
            'error': str(e)
        }, indent=2)


@mcp.tool()
async def get_suggestion(suggestion_id: str) -> str:
    """
    Get detailed information about a specific cached suggestion.
    
    This tool retrieves the full details of a suggestion, including all
    the refactoring operations, diffs, and metadata.
    
    Args:
        suggestion_id: The ID of the suggestion to retrieve
    
    Returns:
        JSON string containing the full suggestion details
    
    Raises:
        SuggestionNotFoundError: If suggestion_id doesn't exist
    """
    try:
        manager = SuggestionManager()
        suggestion = manager.get_suggestion(suggestion_id)
        
        return json.dumps(suggestion, indent=2)
        
    except SuggestionNotFoundError as e:
        return json.dumps({
            'status': 'error',
            'error': str(e)
        }, indent=2)


@mcp.tool()
async def approve_suggestion(
    suggestion_id: str,
    dry_run: bool = False
) -> str:
    """
    Approve and execute a cached refactoring suggestion.
    
    This tool approves a suggestion and triggers its execution using the
    execute_refactoring workflow (Git backup, apply changes, run tests,
    automatic rollback on failure).
    
    Args:
        suggestion_id: The ID of the suggestion to approve and execute
        dry_run: If True, show what would be done without executing
    
    Returns:
        JSON string containing execution result (same format as execute_refactoring)
    
    Raises:
        SuggestionNotFoundError: If suggestion_id doesn't exist
    """
    try:
        manager = SuggestionManager()
        suggestion = manager.get_suggestion(suggestion_id)
        
        # Check if already executed
        if suggestion['status'] in ['executed', 'approved']:
            return json.dumps({
                'status': 'error',
                'error': f"Suggestion {suggestion_id} has already been {suggestion['status']}"
            }, indent=2)
        
        # Mark as approved
        manager.update_status(suggestion_id, SuggestionStatus.APPROVED)
        
        # Execute the refactoring
        file_path = suggestion['file_path']
        suggestion_json = json.dumps(suggestion['data'])
        
        result_json = await execute_refactoring(
            file_path=file_path,
            suggestion_json=suggestion_json,
            dry_run=dry_run
        )
        
        result = json.loads(result_json)
        
        # Update suggestion status based on execution result
        if not dry_run:
            if result['status'] == 'success':
                manager.update_status(
                    suggestion_id,
                    SuggestionStatus.EXECUTED,
                    execution_result=result
                )
            else:
                manager.update_status(
                    suggestion_id,
                    SuggestionStatus.FAILED,
                    execution_result=result
                )
        
        # Add suggestion_id to result
        result['suggestion_id'] = suggestion_id
        
        return json.dumps(result, indent=2)
        
    except (SuggestionNotFoundError, SuggestionManagerError) as e:
        return json.dumps({
            'status': 'error',
            'error': str(e)
        }, indent=2)


@mcp.tool()
async def reject_suggestion(
    suggestion_id: str,
    reason: Optional[str] = None
) -> str:
    """
    Reject a cached refactoring suggestion.
    
    This tool marks a suggestion as rejected, preventing it from being executed.
    The suggestion remains in the cache for reference but won't appear in
    default listings.
    
    Args:
        suggestion_id: The ID of the suggestion to reject
        reason: Optional reason for rejection
    
    Returns:
        JSON string confirming rejection
    
    Raises:
        SuggestionNotFoundError: If suggestion_id doesn't exist
    """
    try:
        manager = SuggestionManager()
        suggestion = manager.get_suggestion(suggestion_id)
        
        # Update status
        metadata = suggestion.get('metadata', {})
        if reason:
            metadata['rejection_reason'] = reason
        
        manager.update_status(suggestion_id, SuggestionStatus.REJECTED)
        
        return json.dumps({
            'status': 'success',
            'message': f"Suggestion {suggestion_id} has been rejected",
            'suggestion_id': suggestion_id,
            'file_path': suggestion['file_path']
        }, indent=2)
        
    except SuggestionNotFoundError as e:
        return json.dumps({
            'status': 'error',
            'error': str(e)
        }, indent=2)


@mcp.tool()
async def clear_suggestions(
    status: Optional[str] = None,
    older_than_days: Optional[int] = None
) -> str:
    """
    Clear cached suggestions from the cache.
    
    This tool removes suggestions from the cache to keep it clean. By default,
    clears all suggestions, but can be filtered by status or age.
    
    Args:
        status: Only clear suggestions with this status (pending, rejected, etc.)
        older_than_days: Only clear suggestions older than this many days
    
    Returns:
        JSON string indicating how many suggestions were cleared
    """
    try:
        manager = SuggestionManager()
        count = manager.clear_cache(
            status=status,
            older_than_days=older_than_days
        )
        
        return json.dumps({
            'status': 'success',
            'message': f"Cleared {count} suggestion(s) from cache",
            'count': count,
            'filters': {
                'status': status,
                'older_than_days': older_than_days
            }
        }, indent=2)
        
    except SuggestionManagerError as e:
        return json.dumps({
            'status': 'error',
            'error': str(e)
        }, indent=2)


@mcp.tool()
async def get_refactoring_status(
    project_root: str,
    limit: int = 10,
    include_rolled_back: bool = False
) -> str:
    """
    Get the status of recent refactoring operations.
    
    This tool queries the Operation State Management system to retrieve
    the history of refactoring operations, including their status,
    timestamps, and outcomes.
    
    Args:
        project_root: Absolute path to the project root directory
        limit: Maximum number of operations to return (default: 10, most recent first)
        include_rolled_back: If True, include operations that were rolled back (default: False)
    
    Returns:
        JSON string containing operation history with structure:
        {
            "status": "success",
            "project_root": "/path/to/project",
            "total_operations": 5,
            "operations": [
                {
                    "operation_id": "20231005143022123456",
                    "operation_type": "extract_function",
                    "timestamp": "2023-10-05T14:30:22.123456",
                    "status": "success",
                    "backup_branch": "backup-20231005143022",
                    "commit_before": "abc123",
                    "commit_after": "def456",
                    "files_modified": ["app.py"],
                    "files_created": ["helpers.py"],
                    "rolled_back": false
                },
                ...
            ]
        }
    
    Raises:
        ValueError: If project_root doesn't exist
        RollbackError: If retrieving history fails
    
    Example:
        To check recent refactoring operations:
        >>> status = await get_refactoring_status('/path/to/project')
    """
    try:
        # Validate project root exists
        project_path = Path(project_root)
        if not project_path.exists():
            return json.dumps({
                'status': 'error',
                'error': f"Project root does not exist: {project_root}"
            }, indent=2)
        
        if not project_path.is_dir():
            return json.dumps({
                'status': 'error',
                'error': f"Project root is not a directory: {project_root}"
            }, indent=2)
        
        # Initialize RollbackManager for the project
        rollback_manager = RollbackManager(project_root)
        
        # Retrieve operation history
        operations = rollback_manager.list_operations(
            limit=limit,
            include_rolled_back=include_rolled_back
        )
        
        # Format the response
        result = {
            'status': 'success',
            'project_root': str(project_path),
            'total_operations': len(operations),
            'operations': []
        }
        
        # Add each operation to the result
        for op in operations:
            operation_data = {
                'operation_id': op['operation_id'],
                'operation_type': op['operation_type'],
                'timestamp': op['timestamp'],
                'status': 'rolled_back' if op.get('rolled_back', False) else 'success',
                'backup_branch': op['backup_branch'],
                'commit_before': op['commit_before'],
                'commit_after': op.get('commit_after'),
                'files_modified': op.get('files_modified', []),
                'files_created': op.get('files_created', []),
                'rolled_back': op.get('rolled_back', False)
            }
            
            # Include operation details if present
            if op.get('operation_details'):
                operation_data['operation_details'] = op['operation_details']
            
            result['operations'].append(operation_data)
        
        return json.dumps(result, indent=2)
        
    except RollbackError as e:
        return json.dumps({
            'status': 'error',
            'error': f"Failed to retrieve refactoring status: {str(e)}"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            'status': 'error',
            'error': f"Unexpected error: {str(e)}"
        }, indent=2)


@mcp.tool()
async def refactor_database(
    project_root: str,
    operation: str,
    file_path: Optional[str] = None,
    max_operations_per_file: int = 5,
    query_identifier: Optional[str] = None,
    view_name: Optional[str] = None
) -> str:
    """
    Perform specialized database refactoring operations.
    
    This tool provides database-specific refactoring capabilities including
    splitting large migrations and extracting complex queries to views.
    
    Args:
        project_root: Absolute path to the project root directory
        operation: Type of operation to perform:
                   - "split_migration": Split large migration into smaller files
                   - "extract_query": Extract complex query to a SQL view
        file_path: Path to the file to refactor (relative to project_root or absolute)
        max_operations_per_file: Maximum operations per split file (default: 5)
        query_identifier: Identifier for query extraction (function name, line number)
        view_name: Optional custom view name for extracted queries
    
    Returns:
        JSON string containing operation results with structure:
        For split_migration:
        {
            "status": "success",
            "operation": "split_migration",
            "original_file": "path/to/migration.py",
            "split_files": ["part1.py", "part2.py", ...],
            "dependency_chain": [{"file": "...", "depends_on": "..."}],
            "rollback_script": "path/to/rollback.sh"
        }
        
        For extract_query:
        {
            "status": "success",
            "operation": "extract_query",
            "view_file": "path/to/view.sql",
            "modified_source": "path/to/modified_source.py",
            "rollback_script": "path/to/rollback.sql",
            "view_name": "view_user_reports"
        }
    
    Raises:
        ValueError: If operation type is invalid or required parameters are missing
        DatabaseRefactoringError: If refactoring operation fails
    
    Example:
        To split a large Django migration:
        >>> result = await refactor_database(
        ...     project_root='/path/to/project',
        ...     operation='split_migration',
        ...     file_path='app/migrations/0042_large_migration.py',
        ...     max_operations_per_file=3
        ... )
        
        To extract a complex query:
        >>> result = await refactor_database(
        ...     project_root='/path/to/project',
        ...     operation='extract_query',
        ...     file_path='app/views.py',
        ...     query_identifier='get_user_reports',
        ...     view_name='user_reports_view'
        ... )
    """
    try:
        # Validate project root
        project_path = Path(project_root)
        if not project_path.exists():
            return json.dumps({
                'status': 'error',
                'error': f"Project root does not exist: {project_root}"
            }, indent=2)
        
        if not project_path.is_dir():
            return json.dumps({
                'status': 'error',
                'error': f"Project root is not a directory: {project_root}"
            }, indent=2)
        
        # Validate operation type
        valid_operations = {'split_migration', 'extract_query'}
        if operation not in valid_operations:
            return json.dumps({
                'status': 'error',
                'error': f"Invalid operation: {operation}. Must be one of: {', '.join(valid_operations)}"
            }, indent=2)
        
        # Validate file_path is provided
        if not file_path:
            return json.dumps({
                'status': 'error',
                'error': 'file_path is required'
            }, indent=2)
        
        # Resolve file path
        file = Path(file_path)
        if not file.is_absolute():
            file = project_path / file
        
        if not file.exists():
            return json.dumps({
                'status': 'error',
                'error': f"File not found: {file}"
            }, indent=2)
        
        # Initialize database refactoring engine
        engine = DatabaseRefactoringEngine(project_path)
        
        # Perform the requested operation
        if operation == 'split_migration':
            result = engine.split_migration(
                migration_file=file,
                max_operations_per_file=max_operations_per_file
            )
            
            return json.dumps({
                'status': 'success',
                'operation': 'split_migration',
                'original_file': str(file),
                'split_files': result['split_files'],
                'dependency_chain': result.get('dependency_chain', []),
                'rollback_script': result.get('rollback_script'),
                'message': result.get('message', f"Migration split into {len(result['split_files'])} files")
            }, indent=2)
        
        elif operation == 'extract_query':
            if not query_identifier:
                return json.dumps({
                    'status': 'error',
                    'error': 'query_identifier is required for extract_query operation'
                }, indent=2)
            
            result = engine.extract_query(
                source_file=file,
                query_identifier=query_identifier,
                view_name=view_name
            )
            
            return json.dumps({
                'status': 'success',
                'operation': 'extract_query',
                'view_file': result['view_file'],
                'modified_source': result['modified_source'],
                'rollback_script': result['rollback_script'],
                'view_name': result['view_name'],
                'message': f"Query extracted to view '{result['view_name']}'"
            }, indent=2)
        
    except DatabaseRefactoringError as e:
        return json.dumps({
            'status': 'error',
            'error': f"Database refactoring failed: {str(e)}"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            'status': 'error',
            'error': f"Unexpected error: {str(e)}"
        }, indent=2)


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
