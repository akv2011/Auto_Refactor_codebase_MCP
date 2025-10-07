"""
Configuration file discovery and loading utilities.

This module provides functionality to locate .taskmaster.json configuration
files in the project directory tree and the user's home directory.
"""

import json
import os
from pathlib import Path
from typing import Optional, Tuple, Dict, Any


class ConfigFileDiscovery:
    """Handles discovery of TaskMaster configuration files."""
    
    PROJECT_CONFIG_NAME = ".taskmaster.json"
    GLOBAL_CONFIG_NAME = ".taskmaster.json"
    
    @classmethod
    def find_project_config(cls, start_path: Optional[Path] = None) -> Optional[Path]:
        """
        Search for project configuration file by traversing up the directory tree.
        
        Args:
            start_path: Starting directory for the search. Defaults to current directory.
            
        Returns:
            Path to the project config file if found, None otherwise.
        """
        if start_path is None:
            start_path = Path.cwd()
        elif isinstance(start_path, str):
            start_path = Path(start_path)
            
        current = start_path.resolve()
        
        # Traverse up the directory tree
        while True:
            config_path = current / cls.PROJECT_CONFIG_NAME
            if config_path.exists() and config_path.is_file():
                return config_path
            
            # Check if we've reached the root
            parent = current.parent
            if parent == current:
                # We've reached the root directory
                break
            current = parent
        
        return None
    
    @classmethod
    def find_global_config(cls) -> Optional[Path]:
        """
        Search for global configuration file in the user's home directory.
        
        Returns:
            Path to the global config file if found, None otherwise.
        """
        home_dir = Path.home()
        config_path = home_dir / cls.GLOBAL_CONFIG_NAME
        
        if config_path.exists() and config_path.is_file():
            return config_path
        
        return None
    
    @classmethod
    def discover_configs(cls, start_path: Optional[Path] = None) -> Tuple[Optional[Path], Optional[Path]]:
        """
        Discover both project and global configuration files.
        
        Args:
            start_path: Starting directory for project config search.
            
        Returns:
            Tuple of (project_config_path, global_config_path).
            Either or both may be None if not found.
        """
        project_config = cls.find_project_config(start_path)
        global_config = cls.find_global_config()
        
        return project_config, global_config
    
    @staticmethod
    def load_json_file(file_path: Path) -> Dict[str, Any]:
        """
        Load and parse a JSON configuration file.
        
        Args:
            file_path: Path to the JSON file.
            
        Returns:
            Parsed JSON data as a dictionary.
            
        Raises:
            FileNotFoundError: If the file doesn't exist.
            json.JSONDecodeError: If the file contains invalid JSON.
            PermissionError: If the file cannot be read.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in configuration file {file_path}: {e.msg}",
                e.doc,
                e.pos
            )
        except PermissionError:
            raise PermissionError(f"Permission denied reading configuration file: {file_path}")
