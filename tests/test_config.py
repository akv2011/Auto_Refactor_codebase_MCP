"""
Tests for configuration models.
"""

import pytest
from pydantic import ValidationError
from src.config import (
    RefactorConfig,
    ThresholdsConfig,
    LanguageConfig,
    RefactoringStrategiesConfig,
    SafetyConfig,
    AIConfig,
)


class TestThresholdsConfig:
    """Test ThresholdsConfig model."""
    
    def test_valid_thresholds(self):
        """Test valid threshold configuration."""
        config = ThresholdsConfig(
            maxLines=2000,
            maxFunctions=60,
            maxComplexity=20,
            maxClassSize=600,
            maxMethodLength=120
        )
        assert config.max_lines == 2000
        assert config.max_functions == 60
        assert config.max_complexity == 20
        assert config.max_class_size == 600
        assert config.max_method_length == 120
    
    def test_default_thresholds(self):
        """Test default threshold values."""
        config = ThresholdsConfig()
        assert config.max_lines == 1500
        assert config.max_functions == 50
        assert config.max_complexity == 15
        assert config.max_class_size == 500
        assert config.max_method_length == 100
    
    def test_invalid_negative_value(self):
        """Test that negative values are rejected."""
        with pytest.raises(ValidationError):
            ThresholdsConfig(maxLines=-100)
    
    def test_invalid_zero_value(self):
        """Test that zero values are rejected."""
        with pytest.raises(ValidationError):
            ThresholdsConfig(maxLines=0)
    
    def test_invalid_exceeds_maximum(self):
        """Test that values exceeding maximum are rejected."""
        with pytest.raises(ValidationError):
            ThresholdsConfig(maxLines=15000)


class TestLanguageConfig:
    """Test LanguageConfig model."""
    
    def test_valid_language_config(self):
        """Test valid language configuration."""
        config = LanguageConfig(
            enabled=True,
            parser="tree-sitter",
            testCommand="npm test"
        )
        assert config.enabled is True
        assert config.parser == "tree-sitter"
        assert config.test_command == "npm test"
    
    def test_default_language_config(self):
        """Test default language values."""
        config = LanguageConfig()
        assert config.enabled is True
        assert config.parser == "ast"
        assert config.test_command == ""
    
    def test_invalid_parser(self):
        """Test that invalid parser is rejected."""
        with pytest.raises(ValidationError):
            LanguageConfig(parser="invalid-parser")
    
    def test_valid_parsers(self):
        """Test all valid parser types."""
        for parser in ['ast', 'tree-sitter', 'regex']:
            config = LanguageConfig(parser=parser)
            assert config.parser == parser


class TestRefactoringStrategiesConfig:
    """Test RefactoringStrategiesConfig model."""
    
    def test_valid_strategies(self):
        """Test valid refactoring strategies."""
        config = RefactoringStrategiesConfig(
            preferComposition=False,
            extractUtilities=True,
            maintainNamespaces=False,
            preserveComments=True,
            updateImports=False
        )
        assert config.prefer_composition is False
        assert config.extract_utilities is True
        assert config.maintain_namespaces is False
        assert config.preserve_comments is True
        assert config.update_imports is False
    
    def test_default_strategies(self):
        """Test default strategy values."""
        config = RefactoringStrategiesConfig()
        assert config.prefer_composition is True
        assert config.extract_utilities is True
        assert config.maintain_namespaces is True
        assert config.preserve_comments is True
        assert config.update_imports is True


class TestSafetyConfig:
    """Test SafetyConfig model."""
    
    def test_valid_safety_config(self):
        """Test valid safety configuration."""
        config = SafetyConfig(
            requireTests=False,
            createBackups=True,
            dryRunFirst=False,
            requireApproval=True,
            maxFilesPerOperation=20
        )
        assert config.require_tests is False
        assert config.create_backups is True
        assert config.dry_run_first is False
        assert config.require_approval is True
        assert config.max_files_per_operation == 20
    
    def test_default_safety_config(self):
        """Test default safety values."""
        config = SafetyConfig()
        assert config.require_tests is True
        assert config.create_backups is True
        assert config.dry_run_first is True
        assert config.require_approval is True
        assert config.max_files_per_operation == 10
    
    def test_invalid_max_files(self):
        """Test that invalid max files value is rejected."""
        with pytest.raises(ValidationError):
            SafetyConfig(maxFilesPerOperation=0)
        
        with pytest.raises(ValidationError):
            SafetyConfig(maxFilesPerOperation=200)


class TestAIConfig:
    """Test AIConfig model."""
    
    def test_valid_ai_config(self):
        """Test valid AI configuration."""
        config = AIConfig(
            provider="anthropic",
            model="claude-3-opus",
            maxTokens=8000,
            temperature=0.5
        )
        assert config.provider == "anthropic"
        assert config.model == "claude-3-opus"
        assert config.max_tokens == 8000
        assert config.temperature == 0.5
    
    def test_default_ai_config(self):
        """Test default AI values."""
        config = AIConfig()
        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.max_tokens == 4000
        assert config.temperature == 0.2
    
    def test_invalid_provider(self):
        """Test that invalid provider is rejected."""
        with pytest.raises(ValidationError):
            AIConfig(provider="invalid-provider")
    
    def test_valid_providers(self):
        """Test all valid AI providers."""
        for provider in ['openai', 'anthropic', 'google', 'local']:
            config = AIConfig(provider=provider)
            assert config.provider == provider
    
    def test_invalid_temperature(self):
        """Test that invalid temperature is rejected."""
        with pytest.raises(ValidationError):
            AIConfig(temperature=-0.1)
        
        with pytest.raises(ValidationError):
            AIConfig(temperature=2.5)
    
    def test_invalid_max_tokens(self):
        """Test that invalid max tokens is rejected."""
        with pytest.raises(ValidationError):
            AIConfig(maxTokens=0)
        
        with pytest.raises(ValidationError):
            AIConfig(maxTokens=50000)


class TestRefactorConfig:
    """Test RefactorConfig model."""
    
    def test_valid_full_config(self):
        """Test valid complete configuration."""
        config_dict = {
            "version": "1.0",
            "name": "Test Config",
            "thresholds": {
                "maxLines": 2000,
                "maxFunctions": 60,
                "maxComplexity": 20,
                "maxClassSize": 600,
                "maxMethodLength": 120
            },
            "languages": {
                "python": {
                    "enabled": True,
                    "parser": "ast",
                    "testCommand": "pytest"
                }
            },
            "excludePatterns": ["**/test/**"],
            "refactoringStrategies": {
                "preferComposition": True,
                "extractUtilities": True,
                "maintainNamespaces": True,
                "preserveComments": True,
                "updateImports": True
            },
            "safety": {
                "requireTests": True,
                "createBackups": True,
                "dryRunFirst": True,
                "requireApproval": True,
                "maxFilesPerOperation": 10
            },
            "ai": {
                "provider": "openai",
                "model": "gpt-4",
                "maxTokens": 4000,
                "temperature": 0.2
            }
        }
        config = RefactorConfig(**config_dict)
        assert config.version == "1.0"
        assert config.name == "Test Config"
        assert config.thresholds.max_lines == 2000
        assert "python" in config.languages
        assert config.languages["python"].enabled is True
        assert len(config.exclude_patterns) == 1
    
    def test_default_config(self):
        """Test default configuration values."""
        config = RefactorConfig()
        assert config.version == "1.0"
        assert config.name == "TaskMaster Configuration"
        assert config.thresholds.max_lines == 1500
        assert len(config.exclude_patterns) == 8
        assert config.safety.require_tests is True
        assert config.ai.provider == "openai"
    
    def test_invalid_version_format(self):
        """Test that invalid version format is rejected."""
        with pytest.raises(ValidationError):
            RefactorConfig(version="1.0.0")
        
        with pytest.raises(ValidationError):
            RefactorConfig(version="abc")
    
    def test_partial_config(self):
        """Test configuration with partial data."""
        config = RefactorConfig(
            name="Partial Config",
            thresholds={"maxLines": 3000}
        )
        assert config.name == "Partial Config"
        assert config.thresholds.max_lines == 3000
        # Other thresholds should use defaults
        assert config.thresholds.max_functions == 50
        assert config.version == "1.0"
    
    def test_extra_fields_rejected(self):
        """Test that extra fields are rejected."""
        with pytest.raises(ValidationError):
            RefactorConfig(unknownField="value")
    
    def test_nested_validation(self):
        """Test that nested validation works correctly."""
        with pytest.raises(ValidationError):
            RefactorConfig(
                thresholds={"maxLines": -100}
            )
        
        with pytest.raises(ValidationError):
            RefactorConfig(
                ai={"provider": "invalid"}
            )
