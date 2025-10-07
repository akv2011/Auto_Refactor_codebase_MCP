"""
Tests for ConfigManager singleton.
"""

import json
import pytest
import threading
from pathlib import Path
from src.config_manager import ConfigManager, get_config
from src.config import RefactorConfig


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset singleton before each test."""
    ConfigManager.reset()
    yield
    ConfigManager.reset()


@pytest.fixture
def config_file(tmp_path):
    """Create a test configuration file."""
    config_data = {
        "version": "1.0",
        "name": "Test Config",
        "thresholds": {
            "maxLines": 3000
        }
    }
    
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    config_path = project_dir / ".taskmaster.json"
    
    with open(config_path, 'w') as f:
        json.dump(config_data, f)
    
    return project_dir


class TestConfigManagerSingleton:
    """Test ConfigManager singleton behavior."""
    
    def test_singleton_instance(self):
        """Test that ConfigManager returns the same instance."""
        manager1 = ConfigManager()
        manager2 = ConfigManager()
        
        assert manager1 is manager2
    
    def test_get_config_returns_same_instance(self, config_file):
        """Test that get_config returns the same config instance."""
        config1 = ConfigManager.get_config(config_file)
        config2 = ConfigManager.get_config(config_file)
        
        assert config1 is config2
    
    def test_config_loaded_only_once(self, config_file, monkeypatch):
        """Test that configuration is loaded only once."""
        load_count = []
        
        original_load = ConfigManager.get_config.__func__
        
        def counting_load(cls, start_path=None, reload=False):
            if cls._config is None or reload:
                load_count.append(1)
            return original_load(cls, start_path, reload)
        
        # First call should load
        config1 = ConfigManager.get_config(config_file)
        
        # Second call should not load again
        config2 = ConfigManager.get_config(config_file)
        
        assert config1 is config2
        assert ConfigManager.is_loaded()
    
    def test_is_loaded_before_loading(self):
        """Test is_loaded returns False before loading config."""
        assert ConfigManager.is_loaded() is False
    
    def test_is_loaded_after_loading(self, config_file):
        """Test is_loaded returns True after loading config."""
        ConfigManager.get_config(config_file)
        assert ConfigManager.is_loaded() is True
    
    def test_get_start_path(self, config_file):
        """Test get_start_path returns the path used for loading."""
        ConfigManager.get_config(config_file)
        assert ConfigManager.get_start_path() == config_file
    
    def test_reset_clears_config(self, config_file):
        """Test that reset clears the loaded configuration."""
        ConfigManager.get_config(config_file)
        assert ConfigManager.is_loaded()
        
        ConfigManager.reset()
        
        assert ConfigManager.is_loaded() is False
        assert ConfigManager.get_start_path() is None


class TestConfigManagerLoading:
    """Test configuration loading behavior."""
    
    def test_load_with_config_file(self, config_file):
        """Test loading with a valid config file."""
        config = ConfigManager.get_config(config_file)
        
        assert isinstance(config, RefactorConfig)
        assert config.name == "Test Config"
        assert config.thresholds.max_lines == 3000
    
    def test_load_without_config_file(self, tmp_path):
        """Test loading when no config file exists (uses defaults)."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        config = ConfigManager.get_config(empty_dir)
        
        assert isinstance(config, RefactorConfig)
        assert config.name == "TaskMaster Configuration"
        assert config.thresholds.max_lines == 1500  # Default value
    
    def test_reload_config(self, config_file):
        """Test reloading configuration."""
        # Load initial config
        config1 = ConfigManager.get_config(config_file)
        assert config1.thresholds.max_lines == 3000
        
        # Modify config file
        config_path = config_file / ".taskmaster.json"
        new_config_data = {
            "version": "1.0",
            "name": "Updated Config",
            "thresholds": {
                "maxLines": 4000
            }
        }
        with open(config_path, 'w') as f:
            json.dump(new_config_data, f)
        
        # Reload config
        config2 = ConfigManager.get_config(config_file, reload=True)
        
        assert config2.name == "Updated Config"
        assert config2.thresholds.max_lines == 4000
        assert config1 is not config2  # Different instance after reload


class TestConfigManagerThreadSafety:
    """Test thread safety of ConfigManager."""
    
    def test_concurrent_access(self, config_file):
        """Test that concurrent access returns the same config instance."""
        configs = []
        exceptions = []
        
        def load_config():
            try:
                config = ConfigManager.get_config(config_file)
                configs.append(config)
            except Exception as e:
                exceptions.append(e)
        
        # Create multiple threads that try to load config simultaneously
        threads = [threading.Thread(target=load_config) for _ in range(10)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check no exceptions occurred
        assert len(exceptions) == 0
        
        # Check all threads got the same instance
        assert len(configs) == 10
        first_config = configs[0]
        assert all(config is first_config for config in configs)


class TestConvenienceFunction:
    """Test the get_config convenience function."""
    
    def test_convenience_function(self, config_file):
        """Test that convenience function works correctly."""
        config = get_config(config_file)
        
        assert isinstance(config, RefactorConfig)
        assert config.name == "Test Config"
    
    def test_convenience_function_uses_singleton(self, config_file):
        """Test that convenience function uses the singleton."""
        config1 = get_config(config_file)
        config2 = ConfigManager.get_config(config_file)
        
        assert config1 is config2
