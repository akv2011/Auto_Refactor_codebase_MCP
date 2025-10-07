"""
Configuration models for TaskMaster MCP Server.

This module defines Pydantic models that map to the .taskmaster.json
configuration file structure, providing validation and type safety.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ThresholdsConfig(BaseModel):
    """Thresholds for code analysis metrics."""
    
    model_config = ConfigDict(extra='forbid')
    
    max_lines: int = Field(default=1500, gt=0, le=10000, alias='maxLines')
    max_functions: int = Field(default=50, gt=0, le=500, alias='maxFunctions')
    max_complexity: int = Field(default=15, gt=0, le=100, alias='maxComplexity')
    max_class_size: int = Field(default=500, gt=0, le=5000, alias='maxClassSize')
    max_method_length: int = Field(default=100, gt=0, le=1000, alias='maxMethodLength')


class LanguageConfig(BaseModel):
    """Configuration for a specific programming language."""
    
    model_config = ConfigDict(extra='forbid')
    
    enabled: bool = Field(default=True)
    parser: str = Field(default="ast")
    test_command: str = Field(default="", alias='testCommand')
    
    @field_validator('parser')
    @classmethod
    def validate_parser(cls, v: str) -> str:
        """Validate parser type."""
        valid_parsers = {'ast', 'tree-sitter', 'regex'}
        if v not in valid_parsers:
            raise ValueError(f"Parser must be one of {valid_parsers}")
        return v


class RefactoringStrategiesConfig(BaseModel):
    """Refactoring strategy preferences."""
    
    model_config = ConfigDict(extra='forbid')
    
    prefer_composition: bool = Field(default=True, alias='preferComposition')
    extract_utilities: bool = Field(default=True, alias='extractUtilities')
    maintain_namespaces: bool = Field(default=True, alias='maintainNamespaces')
    preserve_comments: bool = Field(default=True, alias='preserveComments')
    update_imports: bool = Field(default=True, alias='updateImports')


class SafetyConfig(BaseModel):
    """Safety and backup configuration."""
    
    model_config = ConfigDict(extra='forbid')
    
    require_tests: bool = Field(default=True, alias='requireTests')
    create_backups: bool = Field(default=True, alias='createBackups')
    dry_run_first: bool = Field(default=True, alias='dryRunFirst')
    require_approval: bool = Field(default=True, alias='requireApproval')
    max_files_per_operation: int = Field(
        default=10, 
        gt=0, 
        le=100, 
        alias='maxFilesPerOperation'
    )


class AIConfig(BaseModel):
    """AI provider configuration."""
    
    model_config = ConfigDict(extra='forbid')
    
    provider: str = Field(default="openai")
    model: str = Field(default="gpt-4")
    max_tokens: int = Field(default=4000, gt=0, le=32000, alias='maxTokens')
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate AI provider."""
        valid_providers = {'openai', 'anthropic', 'google', 'local'}
        if v not in valid_providers:
            raise ValueError(f"Provider must be one of {valid_providers}")
        return v


class RefactorConfig(BaseModel):
    """Main configuration model for Auto-Refactor."""
    
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    
    version: str = Field(default="1.0")
    name: str = Field(default="Auto-Refactor Configuration")
    thresholds: ThresholdsConfig = Field(default_factory=ThresholdsConfig)
    languages: Dict[str, LanguageConfig] = Field(default_factory=dict)
    exclude_patterns: List[str] = Field(
        default_factory=lambda: [
            "**/node_modules/**",
            "**/venv/**",
            "**/dist/**",
            "**/build/**",
            "**/__pycache__/**",
            "**/test/**",
            "**/*.test.js",
            "**/*.spec.ts"
        ],
        alias='excludePatterns'
    )
    refactoring_strategies: RefactoringStrategiesConfig = Field(
        default_factory=RefactoringStrategiesConfig,
        alias='refactoringStrategies'
    )
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    
    @field_validator('version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate version format."""
        parts = v.split('.')
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            raise ValueError("Version must be in format 'X.Y'")
        return v
