"""
Tests for configuration error handling.
"""

import json
import pytest
from pathlib import Path
from pydantic import ValidationError

from src.config_errors import (
    ConfigurationError,
    ConfigFileNotFoundError,
    InvalidConfigJSONError,
    ConfigValidationError,
    ConfigPermissionError,
    format_config_error
)
from src.config_loader import ConfigLoader
from src.config import RefactorConfig


class TestConfigurationExceptions:
    """Test custom configuration exception classes."""
    
    def test_config_file_not_found_error(self, tmp_path):
        """Test ConfigFileNotFoundError."""
        file_path = tmp_path / "nonexistent.json"
        error = ConfigFileNotFoundError(file_path)
        
        assert isinstance(error, ConfigurationError)
        assert str(file_path) in str(error)
        assert error.file_path == file_path
    
    def test_invalid_config_json_error(self, tmp_path):
        """Test InvalidConfigJSONError."""
        file_path = tmp_path / "invalid.json"
        error_msg = "Expecting property name"
        error = InvalidConfigJSONError(file_path, error_msg)
        
        assert isinstance(error, ConfigurationError)
        assert str(file_path) in str(error)
        assert error_msg in str(error)
        assert error.file_path == file_path
        assert error.error == error_msg
    
    def test_config_permission_error(self, tmp_path):
        """Test ConfigPermissionError."""
        file_path = tmp_path / "restricted.json"
        error = ConfigPermissionError(file_path)
        
        assert isinstance(error, ConfigurationError)
        assert str(file_path) in str(error)
        assert "Permission denied" in str(error)
        assert error.file_path == file_path
    
    def test_config_validation_error_formatting(self):
        """Test ConfigValidationError message formatting."""
        errors = [
            {
                'loc': ('thresholds', 'maxLines'),
                'msg': 'Input should be greater than 0',
                'type': 'greater_than'
            },
            {
                'loc': ('ai', 'provider'),
                'msg': 'Input should be one of: openai, anthropic, google, local',
                'type': 'enum'
            }
        ]
        
        error = ConfigValidationError(errors)
        
        assert isinstance(error, ConfigurationError)
        error_str = str(error)
        assert "Configuration validation failed" in error_str
        assert "thresholds -> maxLines" in error_str
        assert "ai -> provider" in error_str
        assert "greater_than" in error_str
        assert "enum" in error_str
    
    def test_config_validation_error_from_pydantic(self):
        """Test creating ConfigValidationError from Pydantic ValidationError."""
        try:
            RefactorConfig(thresholds={"maxLines": -100})
        except ValidationError as e:
            config_error = ConfigValidationError.from_pydantic_error(e)
            
            assert isinstance(config_error, ConfigValidationError)
            assert "Configuration validation failed" in str(config_error)
            assert len(config_error.errors) > 0


class TestFormatConfigError:
    """Test error formatting utility."""
    
    def test_format_configuration_error(self, tmp_path):
        """Test formatting ConfigurationError."""
        file_path = tmp_path / "config.json"
        error = ConfigFileNotFoundError(file_path)
        
        formatted = format_config_error(error, file_path)
        assert str(file_path) in formatted
    
    def test_format_validation_error(self):
        """Test formatting ValidationError."""
        try:
            RefactorConfig(thresholds={"maxLines": 0})
        except ValidationError as e:
            formatted = format_config_error(e)
            assert "Configuration validation failed" in formatted
    
    def test_format_file_not_found_error(self, tmp_path):
        """Test formatting FileNotFoundError."""
        file_path = tmp_path / "missing.json"
        error = FileNotFoundError(str(file_path))
        
        formatted = format_config_error(error, file_path)
        assert str(file_path) in formatted
    
    def test_format_permission_error(self, tmp_path):
        """Test formatting PermissionError."""
        file_path = tmp_path / "restricted.json"
        error = PermissionError("Access denied")
        
        formatted = format_config_error(error, file_path)
        assert "Permission denied" in formatted
        assert str(file_path) in formatted
    
    def test_format_generic_error(self):
        """Test formatting generic exception."""
        error = ValueError("Some error")
        
        formatted = format_config_error(error)
        assert "Configuration error" in formatted
        assert "Some error" in formatted


class TestConfigLoaderErrorHandling:
    """Test error handling in ConfigLoader."""
    
    def test_load_nonexistent_file(self, tmp_path):
        """Test loading a nonexistent file raises appropriate error."""
        file_path = tmp_path / "nonexistent.json"
        
        with pytest.raises(ConfigFileNotFoundError) as exc_info:
            ConfigLoader.load_config_from_file(file_path)
        
        assert exc_info.value.file_path == file_path
    
    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON raises appropriate error."""
        file_path = tmp_path / "invalid.json"
        with open(file_path, 'w') as f:
            f.write("{ invalid json }")
        
        with pytest.raises(InvalidConfigJSONError) as exc_info:
            ConfigLoader.load_config_from_file(file_path)
        
        assert exc_info.value.file_path == file_path
    
    def test_validate_invalid_config(self, tmp_path):
        """Test validation of invalid config raises ConfigValidationError."""
        config_data = {
            "version": "1.0",
            "thresholds": {
                "maxLines": -100  # Invalid
            }
        }
        
        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigLoader.load_and_validate_config(project_config_path=config_file)
        
        assert len(exc_info.value.errors) > 0
        assert "Configuration validation failed" in str(exc_info.value)
    
    def test_validate_invalid_type(self, tmp_path):
        """Test validation with wrong data type."""
        config_data = {
            "version": "1.0",
            "thresholds": {
                "maxLines": "not a number"  # Should be integer
            }
        }
        
        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        with pytest.raises(ConfigValidationError):
            ConfigLoader.load_and_validate_config(project_config_path=config_file)
    
    def test_validate_invalid_enum_value(self, tmp_path):
        """Test validation with invalid enum value."""
        config_data = {
            "version": "1.0",
            "ai": {
                "provider": "invalid-provider"
            }
        }
        
        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigLoader.load_and_validate_config(project_config_path=config_file)
        
        error_str = str(exc_info.value)
        assert "ai -> provider" in error_str or "provider" in error_str
    
    def test_validate_out_of_range(self, tmp_path):
        """Test validation with out-of-range values."""
        config_data = {
            "version": "1.0",
            "safety": {
                "maxFilesPerOperation": 200  # Exceeds maximum of 100
            }
        }
        
        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        with pytest.raises(ConfigValidationError):
            ConfigLoader.load_and_validate_config(project_config_path=config_file)
    
    def test_validate_missing_required_nested_structure(self, tmp_path):
        """Test that partial nested configs work with defaults."""
        config_data = {
            "version": "1.0",
            "thresholds": {
                "maxLines": 2000
                # Other threshold fields should use defaults
            }
        }
        
        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Should succeed with defaults for missing fields
        config = ConfigLoader.load_and_validate_config(project_config_path=config_file)
        assert config.thresholds.max_lines == 2000
        assert config.thresholds.max_functions == 50  # Default


class TestIntegratedErrorHandling:
    """Test integrated error handling scenarios."""
    
    def test_discover_and_load_with_invalid_config(self, tmp_path):
        """Test discovery and loading with invalid config."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        
        config_file = project_dir / ".taskmaster.json"
        with open(config_file, 'w') as f:
            f.write("{ invalid }")
        
        with pytest.raises(InvalidConfigJSONError):
            ConfigLoader.discover_and_load_config(project_dir)
    
    def test_error_message_clarity(self, tmp_path):
        """Test that error messages are clear and helpful."""
        config_data = {
            "version": "1.0",
            "thresholds": {
                "maxLines": 0,  # Invalid: must be > 0
                "maxComplexity": 200  # Invalid: must be <= 100
            },
            "ai": {
                "temperature": 3.0  # Invalid: must be <= 2.0
            }
        }
        
        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigLoader.load_and_validate_config(project_config_path=config_file)
        
        error_str = str(exc_info.value)
        # Should mention specific fields
        assert "thresholds" in error_str or "maxLines" in error_str or "temperature" in error_str
        # Should provide context about what's wrong
        assert "Configuration validation failed" in error_str
