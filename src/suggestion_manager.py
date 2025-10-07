"""
Suggestion Manager for TaskMaster MCP Server

This module provides state management for refactoring suggestions,
allowing users to review, approve, reject, or modify suggestions
before applying them.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from enum import Enum


class SuggestionStatus(Enum):
    """Status of a refactoring suggestion."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"


class SuggestionManagerError(Exception):
    """Base exception for SuggestionManager errors."""
    pass


class SuggestionNotFoundError(SuggestionManagerError):
    """Raised when a suggestion is not found."""
    pass


class InvalidSuggestionError(SuggestionManagerError):
    """Raised when a suggestion is invalid."""
    pass


class SuggestionManager:
    """
    Manages refactoring suggestions with caching and state tracking.
    
    This class provides a persistent cache for AI-generated refactoring
    suggestions, allowing users to review and approve them before execution.
    
    Attributes:
        cache_file: Path to the JSON file storing cached suggestions
        suggestions: In-memory cache of suggestions
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the SuggestionManager.
        
        Args:
            project_root: Root directory of the project. If None, uses current directory.
        """
        if project_root is None:
            project_root = Path.cwd()
        else:
            project_root = Path(project_root)
        
        # Create .taskmaster directory if it doesn't exist
        self.taskmaster_dir = project_root / '.taskmaster'
        self.taskmaster_dir.mkdir(exist_ok=True)
        
        # Cache file for suggestions
        self.cache_file = self.taskmaster_dir / 'suggestions_cache.json'
        
        # Load existing suggestions
        self.suggestions: Dict[str, Dict[str, Any]] = {}
        self._load_cache()
        
        # Ensure cache file exists
        if not self.cache_file.exists():
            self._save_cache()
    
    def _load_cache(self) -> None:
        """Load suggestions from the cache file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.suggestions = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                # If cache is corrupted, start fresh
                self.suggestions = {}
                self._save_cache()
    
    def _save_cache(self) -> None:
        """Save suggestions to the cache file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.suggestions, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise SuggestionManagerError(f"Failed to save cache: {str(e)}")
    
    def _generate_suggestion_id(self) -> str:
        """Generate a unique suggestion ID."""
        return str(uuid.uuid4())[:8]
    
    def add_suggestion(
        self,
        file_path: str,
        suggestion_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a new suggestion to the cache.
        
        Args:
            file_path: Path to the file the suggestion applies to
            suggestion_data: The suggestion content (from AI service)
            metadata: Optional additional metadata (strategy, parameters, etc.)
        
        Returns:
            The generated suggestion ID
        
        Raises:
            InvalidSuggestionError: If suggestion_data is invalid
        """
        # Validate suggestion data
        if not isinstance(suggestion_data, dict):
            raise InvalidSuggestionError("suggestion_data must be a dictionary")
        
        # Generate unique ID
        suggestion_id = self._generate_suggestion_id()
        
        # Ensure unique ID
        while suggestion_id in self.suggestions:
            suggestion_id = self._generate_suggestion_id()
        
        # Create suggestion record
        suggestion_record = {
            'id': suggestion_id,
            'file_path': file_path,
            'data': suggestion_data,
            'status': SuggestionStatus.PENDING.value,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'metadata': metadata or {},
            'execution_result': None
        }
        
        # Store in cache
        self.suggestions[suggestion_id] = suggestion_record
        self._save_cache()
        
        return suggestion_id
    
    def get_suggestion(self, suggestion_id: str) -> Dict[str, Any]:
        """
        Retrieve a suggestion by ID.
        
        Args:
            suggestion_id: The suggestion ID
        
        Returns:
            The suggestion record
        
        Raises:
            SuggestionNotFoundError: If suggestion is not found
        """
        if suggestion_id not in self.suggestions:
            raise SuggestionNotFoundError(
                f"Suggestion not found: {suggestion_id}"
            )
        
        return self.suggestions[suggestion_id]
    
    def list_suggestions(
        self,
        status: Optional[str] = None,
        file_path: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List suggestions with optional filtering.
        
        Args:
            status: Filter by status (pending, approved, rejected, executed, failed)
            file_path: Filter by file path
            limit: Maximum number of results to return
        
        Returns:
            List of suggestion records
        """
        results = []
        
        for suggestion in self.suggestions.values():
            # Apply filters
            if status and suggestion['status'] != status:
                continue
            
            if file_path and suggestion['file_path'] != file_path:
                continue
            
            results.append(suggestion)
        
        # Sort by created_at (newest first)
        results.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Apply limit
        if limit:
            results = results[:limit]
        
        return results
    
    def update_status(
        self,
        suggestion_id: str,
        status: SuggestionStatus,
        execution_result: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update the status of a suggestion.
        
        Args:
            suggestion_id: The suggestion ID
            status: The new status
            execution_result: Optional execution result data
        
        Raises:
            SuggestionNotFoundError: If suggestion is not found
        """
        if suggestion_id not in self.suggestions:
            raise SuggestionNotFoundError(
                f"Suggestion not found: {suggestion_id}"
            )
        
        suggestion = self.suggestions[suggestion_id]
        suggestion['status'] = status.value
        suggestion['updated_at'] = datetime.now().isoformat()
        
        if execution_result:
            suggestion['execution_result'] = execution_result
        
        self._save_cache()
    
    def delete_suggestion(self, suggestion_id: str) -> None:
        """
        Delete a suggestion from the cache.
        
        Args:
            suggestion_id: The suggestion ID
        
        Raises:
            SuggestionNotFoundError: If suggestion is not found
        """
        if suggestion_id not in self.suggestions:
            raise SuggestionNotFoundError(
                f"Suggestion not found: {suggestion_id}"
            )
        
        del self.suggestions[suggestion_id]
        self._save_cache()
    
    def clear_cache(
        self,
        status: Optional[str] = None,
        older_than_days: Optional[int] = None
    ) -> int:
        """
        Clear suggestions from the cache.
        
        Args:
            status: Only clear suggestions with this status
            older_than_days: Only clear suggestions older than this many days
        
        Returns:
            Number of suggestions cleared
        """
        to_delete = []
        
        for suggestion_id, suggestion in self.suggestions.items():
            # Apply filters
            if status and suggestion['status'] != status:
                continue
            
            if older_than_days:
                created_at = datetime.fromisoformat(suggestion['created_at'])
                age_days = (datetime.now() - created_at).days
                if age_days < older_than_days:
                    continue
            
            to_delete.append(suggestion_id)
        
        # Delete matching suggestions
        for suggestion_id in to_delete:
            del self.suggestions[suggestion_id]
        
        if to_delete:
            self._save_cache()
        
        return len(to_delete)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about cached suggestions.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total': len(self.suggestions),
            'by_status': {
                'pending': 0,
                'approved': 0,
                'rejected': 0,
                'executed': 0,
                'failed': 0
            },
            'by_file': {}
        }
        
        for suggestion in self.suggestions.values():
            # Count by status
            status = suggestion['status']
            if status in stats['by_status']:
                stats['by_status'][status] += 1
            
            # Count by file
            file_path = suggestion['file_path']
            if file_path not in stats['by_file']:
                stats['by_file'][file_path] = 0
            stats['by_file'][file_path] += 1
        
        return stats
