"""
Configuration Manager - Singleton for configuration access.

This module provides a singleton ConfigManager that ensures configuration
is loaded only once and provides a consistent access point throughout
the application.
"""

import threading
from typing import Optional
from pathlib import Path

from .config import RefactorConfig
from .config_loader import ConfigLoader


class ConfigManager:
    """
    Singleton manager for TaskMaster configuration.
    
    This class ensures that configuration is loaded only once and provides
    thread-safe access to the configuration throughout the application.
    """
    
    _instance: Optional['ConfigManager'] = None
    _lock: threading.Lock = threading.Lock()
    _config: Optional[RefactorConfig] = None
    _start_path: Optional[Path] = None
    
    def __new__(cls) -> 'ConfigManager':
        """
        Create or return the singleton instance.
        
        Returns:
            The singleton ConfigManager instance.
        """
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_config(cls, start_path: Optional[Path] = None, reload: bool = False) -> RefactorConfig:
        """
        Get the configuration, loading it if necessary.
        
        The configuration is loaded on first access and cached. Subsequent
        calls return the cached configuration unless reload=True.
        
        Args:
            start_path: Starting directory for config discovery (used on first load).
            reload: If True, force reload of configuration.
            
        Returns:
            RefactorConfig instance.
        """
        # Ensure we have an instance
        instance = cls()
        
        # Load config if not loaded or reload requested
        if cls._config is None or reload:
            with cls._lock:
                # Double-check locking
                if cls._config is None or reload:
                    cls._start_path = start_path
                    cls._config = ConfigLoader.discover_and_load_config(start_path)
        
        return cls._config
    
    @classmethod
    def reset(cls) -> None:
        """
        Reset the singleton instance.
        
        This is primarily useful for testing to ensure a clean state.
        In production, configuration should typically not be reset.
        """
        with cls._lock:
            cls._instance = None
            cls._config = None
            cls._start_path = None
    
    @classmethod
    def is_loaded(cls) -> bool:
        """
        Check if configuration has been loaded.
        
        Returns:
            True if configuration is loaded, False otherwise.
        """
        return cls._config is not None
    
    @classmethod
    def get_start_path(cls) -> Optional[Path]:
        """
        Get the start path used for configuration discovery.
        
        Returns:
            The start path if configuration was loaded, None otherwise.
        """
        return cls._start_path


# Convenience function for easy access
def get_config(start_path: Optional[Path] = None, reload: bool = False) -> RefactorConfig:
    """
    Convenience function to get configuration.
    
    Args:
        start_path: Starting directory for config discovery.
        reload: If True, force reload of configuration.
        
    Returns:
        RefactorConfig instance.
    """
    return ConfigManager.get_config(start_path, reload)
