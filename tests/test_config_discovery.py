"""
Tests for configuration file discovery.
"""

import json
import pytest
from pathlib import Path
from src.config_discovery import ConfigFileDiscovery


@pytest.fixture
def temp_project_structure(tmp_path):
    """Create a temporary project structure for testing."""
    # Create nested directory structure
    root = tmp_path / "project"
    root.mkdir()
    
    subdir1 = root / "src"
    subdir1.mkdir()
    
    subdir2 = subdir1 / "modules"
    subdir2.mkdir()
    
    return {
        'root': root,
        'subdir1': subdir1,
        'subdir2': subdir2,
        'tmp_path': tmp_path
    }


@pytest.fixture
def sample_config():
    """Sample configuration data."""
    return {
        "version": "1.0",
        "name": "Test Config",
        "thresholds": {
            "maxLines": 1500
        }
    }


class TestFindProjectConfig:
    """Test project config discovery."""
    
    def test_find_config_in_current_directory(self, temp_project_structure, sample_config):
        """Test finding config in the current directory."""
        root = temp_project_structure['root']
        config_file = root / ".taskmaster.json"
        
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        found = ConfigFileDiscovery.find_project_config(root)
        assert found == config_file
        assert found.exists()
    
    def test_find_config_in_parent_directory(self, temp_project_structure, sample_config):
        """Test finding config in a parent directory."""
        root = temp_project_structure['root']
        subdir2 = temp_project_structure['subdir2']
        config_file = root / ".taskmaster.json"
        
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        # Search from deeply nested directory
        found = ConfigFileDiscovery.find_project_config(subdir2)
        assert found == config_file
    
    def test_find_config_in_intermediate_directory(self, temp_project_structure, sample_config):
        """Test finding config in an intermediate directory."""
        subdir1 = temp_project_structure['subdir1']
        subdir2 = temp_project_structure['subdir2']
        config_file = subdir1 / ".taskmaster.json"
        
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        # Search from nested subdirectory
        found = ConfigFileDiscovery.find_project_config(subdir2)
        assert found == config_file
    
    def test_no_config_found(self, temp_project_structure):
        """Test when no config file exists."""
        subdir2 = temp_project_structure['subdir2']
        found = ConfigFileDiscovery.find_project_config(subdir2)
        assert found is None
    
    def test_default_to_current_directory(self, temp_project_structure, sample_config, monkeypatch):
        """Test that it defaults to current directory when no path provided."""
        root = temp_project_structure['root']
        config_file = root / ".taskmaster.json"
        
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        # Change to the root directory
        monkeypatch.chdir(root)
        
        found = ConfigFileDiscovery.find_project_config()
        assert found == config_file
    
    def test_stops_at_filesystem_root(self, temp_project_structure):
        """Test that search stops at filesystem root."""
        subdir2 = temp_project_structure['subdir2']
        # No config file created - should traverse to root and stop
        found = ConfigFileDiscovery.find_project_config(subdir2)
        assert found is None


class TestFindGlobalConfig:
    """Test global config discovery."""
    
    def test_find_global_config_exists(self, tmp_path, sample_config, monkeypatch):
        """Test finding global config in home directory."""
        # Mock home directory
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, 'home', lambda: fake_home)
        
        config_file = fake_home / ".taskmaster.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        found = ConfigFileDiscovery.find_global_config()
        assert found == config_file
    
    def test_global_config_not_found(self, tmp_path, monkeypatch):
        """Test when global config doesn't exist."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, 'home', lambda: fake_home)
        
        found = ConfigFileDiscovery.find_global_config()
        assert found is None


class TestDiscoverConfigs:
    """Test combined config discovery."""
    
    def test_both_configs_exist(self, temp_project_structure, tmp_path, sample_config, monkeypatch):
        """Test when both project and global configs exist."""
        root = temp_project_structure['root']
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, 'home', lambda: fake_home)
        
        # Create project config
        project_config = root / ".taskmaster.json"
        with open(project_config, 'w') as f:
            json.dump(sample_config, f)
        
        # Create global config
        global_config = fake_home / ".taskmaster.json"
        with open(global_config, 'w') as f:
            json.dump(sample_config, f)
        
        project_found, global_found = ConfigFileDiscovery.discover_configs(root)
        assert project_found == project_config
        assert global_found == global_config
    
    def test_only_project_config_exists(self, temp_project_structure, tmp_path, sample_config, monkeypatch):
        """Test when only project config exists."""
        root = temp_project_structure['root']
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, 'home', lambda: fake_home)
        
        # Create only project config
        project_config = root / ".taskmaster.json"
        with open(project_config, 'w') as f:
            json.dump(sample_config, f)
        
        project_found, global_found = ConfigFileDiscovery.discover_configs(root)
        assert project_found == project_config
        assert global_found is None
    
    def test_only_global_config_exists(self, temp_project_structure, tmp_path, sample_config, monkeypatch):
        """Test when only global config exists."""
        root = temp_project_structure['root']
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, 'home', lambda: fake_home)
        
        # Create only global config
        global_config = fake_home / ".taskmaster.json"
        with open(global_config, 'w') as f:
            json.dump(sample_config, f)
        
        project_found, global_found = ConfigFileDiscovery.discover_configs(root)
        assert project_found is None
        assert global_found == global_config
    
    def test_neither_config_exists(self, temp_project_structure, tmp_path, monkeypatch):
        """Test when neither config exists."""
        root = temp_project_structure['root']
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, 'home', lambda: fake_home)
        
        project_found, global_found = ConfigFileDiscovery.discover_configs(root)
        assert project_found is None
        assert global_found is None


class TestLoadJsonFile:
    """Test JSON file loading."""
    
    def test_load_valid_json(self, tmp_path, sample_config):
        """Test loading a valid JSON file."""
        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        data = ConfigFileDiscovery.load_json_file(config_file)
        assert data == sample_config
    
    def test_load_nonexistent_file(self, tmp_path):
        """Test loading a file that doesn't exist."""
        config_file = tmp_path / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            ConfigFileDiscovery.load_json_file(config_file)
    
    def test_load_invalid_json(self, tmp_path):
        """Test loading a file with invalid JSON."""
        config_file = tmp_path / "invalid.json"
        with open(config_file, 'w') as f:
            f.write("{ invalid json }")
        
        with pytest.raises(json.JSONDecodeError):
            ConfigFileDiscovery.load_json_file(config_file)
    
    def test_load_empty_file(self, tmp_path):
        """Test loading an empty file."""
        config_file = tmp_path / "empty.json"
        config_file.touch()
        
        with pytest.raises(json.JSONDecodeError):
            ConfigFileDiscovery.load_json_file(config_file)
    
    def test_load_with_utf8_encoding(self, tmp_path):
        """Test loading a file with UTF-8 characters."""
        config_file = tmp_path / "utf8.json"
        config_data = {"name": "Test Config 测试", "emoji": "🚀"}
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        data = ConfigFileDiscovery.load_json_file(config_file)
        assert data == config_data
