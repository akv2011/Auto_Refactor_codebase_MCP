"""
Configuration loading and merging utilities.

This module provides functionality to load configuration files and
merge them according to precedence rules (project > global).
"""

import json
from typing import Any, Dict, Optional
from pathlib import Path
from pydantic import ValidationError

from .config import RefactorConfig
from .config_discovery import ConfigFileDiscovery
from .config_errors import (
    ConfigFileNotFoundError,
    InvalidConfigJSONError,
    ConfigValidationError,
    ConfigPermissionError
)


class ConfigMerger:
    """Handles merging of configuration dictionaries."""
    
    @staticmethod
    def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a deep merge of two dictionaries.
        
        The override dictionary takes precedence over the base dictionary.
        For nested dictionaries, the merge is recursive.
        
        Args:
            base: Base configuration dictionary.
            override: Override configuration dictionary (takes precedence).
            
        Returns:
            Merged configuration dictionary.
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = ConfigMerger.deep_merge(result[key], value)
            else:
                # Override the value
                result[key] = value
        
        return result


class ConfigLoader:
    """Handles loading and parsing of configuration files."""
    
    @staticmethod
    def load_config_from_file(file_path: Path) -> Dict[str, Any]:
        """
        Load configuration from a single file.
        
        Args:
            file_path: Path to the configuration file.
            
        Returns:
            Configuration data as a dictionary.
            
        Raises:
            ConfigFileNotFoundError: If the file doesn't exist.
            InvalidConfigJSONError: If the file contains invalid JSON.
            ConfigPermissionError: If the file cannot be read.
        """
        if not file_path.exists():
            raise ConfigFileNotFoundError(file_path)
        
        try:
            return ConfigFileDiscovery.load_json_file(file_path)
        except json.JSONDecodeError as e:
            raise InvalidConfigJSONError(file_path, str(e))
        except PermissionError:
            raise ConfigPermissionError(file_path)
    
    @staticmethod
    def load_and_merge_configs(
        project_config_path: Optional[Path] = None,
        global_config_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Load and merge global and project configurations.
        
        Project configuration takes precedence over global configuration.
        If neither file exists, an empty dictionary is returned.
        
        Args:
            project_config_path: Path to project config file (optional).
            global_config_path: Path to global config file (optional).
            
        Returns:
            Merged configuration dictionary.
            
        Raises:
            json.JSONDecodeError: If any config file contains invalid JSON.
        """
        merged_config: Dict[str, Any] = {}
        
        # Load global config first (lower precedence)
        if global_config_path and global_config_path.exists():
            try:
                global_config = ConfigLoader.load_config_from_file(global_config_path)
                merged_config = global_config
            except Exception as e:
                # Log the error but continue (global config is optional)
                print(f"Warning: Could not load global config: {e}")
        
        # Load and merge project config (higher precedence)
        if project_config_path and project_config_path.exists():
            project_config = ConfigLoader.load_config_from_file(project_config_path)
            merged_config = ConfigMerger.deep_merge(merged_config, project_config)
        
        return merged_config
    
    @staticmethod
    def load_and_validate_config(
        project_config_path: Optional[Path] = None,
        global_config_path: Optional[Path] = None
    ) -> RefactorConfig:
        """
        Load, merge, and validate configuration using Pydantic models.
        
        Args:
            project_config_path: Path to project config file (optional).
            global_config_path: Path to global config file (optional).
            
        Returns:
            Validated RefactorConfig instance.
            
        Raises:
            ConfigValidationError: If the merged configuration is invalid.
            InvalidConfigJSONError: If any config file contains invalid JSON.
            ConfigPermissionError: If any config file cannot be read.
        """
        merged_config = ConfigLoader.load_and_merge_configs(
            project_config_path,
            global_config_path
        )
        
        # If no config files were found, use defaults
        if not merged_config:
            return RefactorConfig()
        
        # Validate and create Pydantic model
        try:
            return RefactorConfig(**merged_config)
        except ValidationError as e:
            raise ConfigValidationError.from_pydantic_error(e)
    
    @staticmethod
    def discover_and_load_config(start_path: Optional[Path] = None) -> RefactorConfig:
        """
        Discover, load, merge, and validate configuration files.
        
        This is a convenience method that combines discovery and loading.
        
        Args:
            start_path: Starting directory for project config search.
            
        Returns:
            Validated RefactorConfig instance.
            
        Raises:
            ConfigValidationError: If the merged configuration is invalid.
            InvalidConfigJSONError: If any config file contains invalid JSON.
            ConfigPermissionError: If any config file cannot be read.
        """
        project_config, global_config = ConfigFileDiscovery.discover_configs(start_path)
        return ConfigLoader.load_and_validate_config(project_config, global_config)
