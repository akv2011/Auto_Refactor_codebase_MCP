"""
Tests for configuration loading and merging.
"""

import json
import pytest
from pathlib import Path

from src.config_loader import ConfigLoader, ConfigMerger
from src.config import RefactorConfig
from src.config_errors import ConfigValidationError


@pytest.fixture
def global_config():
    """Sample global configuration."""
    return {
        "version": "1.0",
        "name": "Global Config",
        "thresholds": {
            "maxLines": 2000,
            "maxFunctions": 60
        },
        "ai": {
            "provider": "openai",
            "model": "gpt-3.5-turbo"
        }
    }


@pytest.fixture
def project_config():
    """Sample project configuration."""
    return {
        "name": "Project Config",
        "thresholds": {
            "maxLines": 1500
        },
        "safety": {
            "requireTests": False
        }
    }


class TestConfigMerger:
    """Test configuration merging logic."""
    
    def test_deep_merge_simple(self):
        """Test simple merge without nesting."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        
        result = ConfigMerger.deep_merge(base, override)
        
        assert result == {"a": 1, "b": 3, "c": 4}
    
    def test_deep_merge_nested(self):
        """Test merge with nested dictionaries."""
        base = {
            "thresholds": {
                "maxLines": 2000,
                "maxFunctions": 60
            },
            "ai": {
                "provider": "openai"
            }
        }
        override = {
            "thresholds": {
                "maxLines": 1500
            }
        }
        
        result = ConfigMerger.deep_merge(base, override)
        
        assert result["thresholds"]["maxLines"] == 1500
        assert result["thresholds"]["maxFunctions"] == 60
        assert result["ai"]["provider"] == "openai"
    
    def test_deep_merge_preserves_base(self):
        """Test that merge doesn't modify the base dictionary."""
        base = {"a": 1, "b": {"c": 2}}
        override = {"b": {"c": 3}}
        
        result = ConfigMerger.deep_merge(base, override)
        
        # Base should be unchanged
        assert base["b"]["c"] == 2
        # Result should have override value
        assert result["b"]["c"] == 3
    
    def test_deep_merge_override_with_non_dict(self):
        """Test overriding a dict with a non-dict value."""
        base = {"a": {"b": 1}}
        override = {"a": "string"}
        
        result = ConfigMerger.deep_merge(base, override)
        
        assert result["a"] == "string"
    
    def test_deep_merge_empty_dicts(self):
        """Test merging empty dictionaries."""
        assert ConfigMerger.deep_merge({}, {}) == {}
        assert ConfigMerger.deep_merge({"a": 1}, {}) == {"a": 1}
        assert ConfigMerger.deep_merge({}, {"a": 1}) == {"a": 1}


class TestConfigLoader:
    """Test configuration loading."""
    
    def test_load_config_from_file(self, tmp_path, global_config):
        """Test loading a single config file."""
        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(global_config, f)
        
        loaded = ConfigLoader.load_config_from_file(config_file)
        assert loaded == global_config
    
    def test_load_and_merge_only_global(self, tmp_path, global_config):
        """Test loading only global config."""
        global_file = tmp_path / "global.json"
        with open(global_file, 'w') as f:
            json.dump(global_config, f)
        
        result = ConfigLoader.load_and_merge_configs(
            global_config_path=global_file
        )
        
        assert result == global_config
    
    def test_load_and_merge_only_project(self, tmp_path, project_config):
        """Test loading only project config."""
        project_file = tmp_path / "project.json"
        with open(project_file, 'w') as f:
            json.dump(project_config, f)
        
        result = ConfigLoader.load_and_merge_configs(
            project_config_path=project_file
        )
        
        assert result == project_config
    
    def test_load_and_merge_both_configs(self, tmp_path, global_config, project_config):
        """Test merging both global and project configs."""
        global_file = tmp_path / "global.json"
        project_file = tmp_path / "project.json"
        
        with open(global_file, 'w') as f:
            json.dump(global_config, f)
        with open(project_file, 'w') as f:
            json.dump(project_config, f)
        
        result = ConfigLoader.load_and_merge_configs(
            project_config_path=project_file,
            global_config_path=global_file
        )
        
        # Project config should override
        assert result["name"] == "Project Config"
        assert result["thresholds"]["maxLines"] == 1500
        
        # Global config values should be preserved where not overridden
        assert result["thresholds"]["maxFunctions"] == 60
        assert result["ai"]["provider"] == "openai"
        
        # Project-only values should be present
        assert result["safety"]["requireTests"] is False
    
    def test_load_and_merge_neither_config(self):
        """Test when neither config file exists."""
        result = ConfigLoader.load_and_merge_configs()
        assert result == {}
    
    def test_load_and_merge_nonexistent_files(self, tmp_path):
        """Test with nonexistent file paths."""
        result = ConfigLoader.load_and_merge_configs(
            project_config_path=tmp_path / "nonexistent.json",
            global_config_path=tmp_path / "also_nonexistent.json"
        )
        assert result == {}


class TestLoadAndValidateConfig:
    """Test configuration validation."""
    
    def test_validate_valid_config(self, tmp_path):
        """Test validation with valid config."""
        config_data = {
            "version": "1.0",
            "thresholds": {
                "maxLines": 1500
            }
        }
        
        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        result = ConfigLoader.load_and_validate_config(project_config_path=config_file)
        
        assert isinstance(result, RefactorConfig)
        assert result.version == "1.0"
        assert result.thresholds.max_lines == 1500
    
    def test_validate_with_defaults(self):
        """Test validation with no config files (use defaults)."""
        result = ConfigLoader.load_and_validate_config()
        
        assert isinstance(result, RefactorConfig)
        assert result.version == "1.0"
        assert result.thresholds.max_lines == 1500
    
    def test_validate_invalid_config(self, tmp_path):
        """Test validation with invalid config data."""
        config_data = {
            "version": "1.0",
            "thresholds": {
                "maxLines": -100  # Invalid: negative value
            }
        }
        
        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        with pytest.raises(ConfigValidationError):
            ConfigLoader.load_and_validate_config(project_config_path=config_file)
    
    def test_validate_merged_config(self, tmp_path, global_config, project_config):
        """Test validation of merged configuration."""
        global_file = tmp_path / "global.json"
        project_file = tmp_path / "project.json"
        
        with open(global_file, 'w') as f:
            json.dump(global_config, f)
        with open(project_file, 'w') as f:
            json.dump(project_config, f)
        
        result = ConfigLoader.load_and_validate_config(
            project_config_path=project_file,
            global_config_path=global_file
        )
        
        assert isinstance(result, RefactorConfig)
        # Project values override
        assert result.name == "Project Config"
        assert result.thresholds.max_lines == 1500
        # Global values preserved
        assert result.thresholds.max_functions == 60
        assert result.ai.model == "gpt-3.5-turbo"
        # Project-specific overrides
        assert result.safety.require_tests is False


class TestDiscoverAndLoadConfig:
    """Test the integrated discovery and loading."""
    
    def test_discover_and_load_with_project_config(self, tmp_path, monkeypatch):
        """Test discovering and loading project config."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        
        config_data = {
            "version": "1.0",
            "name": "Discovered Config"
        }
        
        config_file = project_dir / ".taskmaster.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        result = ConfigLoader.discover_and_load_config(project_dir)
        
        assert isinstance(result, RefactorConfig)
        assert result.name == "Discovered Config"
    
    def test_discover_and_load_no_config(self, tmp_path):
        """Test discovering when no config exists."""
        project_dir = tmp_path / "empty_project"
        project_dir.mkdir()
        
        result = ConfigLoader.discover_and_load_config(project_dir)
        
        # Should return default config
        assert isinstance(result, RefactorConfig)
        assert result.name == "TaskMaster Configuration"
