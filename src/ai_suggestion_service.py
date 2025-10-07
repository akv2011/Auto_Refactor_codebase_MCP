"""
AI Suggestion Service - Abstraction layer for LLM integration.

This module provides AI-powered refactoring suggestions using Google's Gemini API.
"""

import json
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

try:
    from google import genai
    from google.genai import types as genai_types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class RefactoringStrategy(str, Enum):
    """Supported refactoring strategies."""
    AUTO = "auto"
    SPLIT = "split"
    EXTRACT = "extract"
    COMPOSITION = "composition"


class RefactoringSuggestion(BaseModel):
    """Single refactoring suggestion with diff and explanation."""
    title: str = Field(..., description="Brief title for the refactoring")
    description: str = Field(..., description="Detailed explanation of the suggested refactoring")
    strategy: str = Field(..., description="The refactoring strategy applied")
    priority: str = Field(..., description="Priority level: high, medium, or low")
    estimated_impact: str = Field(..., description="Expected impact on code quality")
    diff: str = Field(..., description="Unified diff showing the proposed changes")
    reason: str = Field(..., description="Reasoning for this specific refactoring")


class RefactoringSuggestionsResponse(BaseModel):
    """Complete response containing multiple refactoring suggestions."""
    file_path: str = Field(..., description="Path to the analyzed file")
    language: str = Field(..., description="Programming language detected")
    strategy_used: str = Field(..., description="Overall strategy used for analysis")
    suggestions: List[RefactoringSuggestion] = Field(..., description="List of refactoring suggestions")
    summary: str = Field(..., description="Overall summary of the analysis")


class AISuggestionServiceError(Exception):
    """Base exception for AI suggestion service errors."""
    pass


class APINotConfiguredError(AISuggestionServiceError):
    """Raised when API credentials are not configured."""
    pass


class ModelNotAvailableError(AISuggestionServiceError):
    """Raised when the requested model is not available."""
    pass


class AISuggestionService:
    """
    AI-powered refactoring suggestion service using Google Gemini.
    
    This service abstracts LLM interactions and provides methods for
    generating intelligent refactoring suggestions based on code analysis.
    """
    
    def __init__(
        self,
        model: str = "gemini-2.0-flash-001",
        max_tokens: int = 4000,
        temperature: float = 0.2,
        api_key: Optional[str] = None
    ):
        """
        Initialize the AI suggestion service.
        
        Args:
            model: Gemini model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)
            api_key: Optional API key (uses GOOGLE_API_KEY env var if not provided)
        
        Raises:
            APINotConfiguredError: If Gemini client cannot be initialized
            ModelNotAvailableError: If google-genai package is not installed
        """
        if not GENAI_AVAILABLE:
            raise ModelNotAvailableError(
                "google-genai package is not installed. "
                "Install it with: pip install google-genai"
            )
        
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        try:
            # Initialize Gemini client (uses GOOGLE_API_KEY env var by default)
            if api_key:
                self.client = genai.Client(api_key=api_key)
            else:
                self.client = genai.Client()
        except Exception as e:
            raise APINotConfiguredError(
                f"Failed to initialize Gemini client: {str(e)}. "
                "Ensure GOOGLE_API_KEY environment variable is set."
            ) from e
    
    def _detect_language(self, file_path: str, code: str) -> str:
        """
        Detect programming language from file path and code content.
        
        Args:
            file_path: Path to the file
            code: Source code content
            
        Returns:
            Detected language name
        """
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
        }
        
        for ext, lang in extension_map.items():
            if file_path.endswith(ext):
                return lang
        
        return 'unknown'
    
    def _build_prompt(
        self,
        file_path: str,
        code: str,
        metrics: Optional[Dict[str, Any]],
        strategy: RefactoringStrategy
    ) -> str:
        """
        Build the prompt for the LLM based on code and metrics.
        
        Args:
            file_path: Path to the file being analyzed
            code: Source code content
            metrics: Optional metrics data (LOC, complexity, etc.)
            strategy: Refactoring strategy to apply
            
        Returns:
            Formatted prompt string
        """
        language = self._detect_language(file_path, code)
        
        prompt = f"""You are an expert code refactoring assistant. Analyze the following {language} code and provide refactoring suggestions.

FILE: {file_path}
STRATEGY: {strategy.value}

"""
        
        if metrics:
            prompt += f"""METRICS:
- Lines of Code: {metrics.get('loc', 'N/A')}
- Function Count: {metrics.get('function_count', 'N/A')}
- Cyclomatic Complexity: {metrics.get('cyclomatic_complexity', 'N/A')}

"""
        
        prompt += f"""CODE:
```{language}
{code}
```

"""
        
        strategy_instructions = {
            RefactoringStrategy.AUTO: """Analyze the code and automatically determine the best refactoring approach. 
Consider splitting large functions, extracting reusable code, improving composition, and any other improvements.""",
            
            RefactoringStrategy.SPLIT: """Focus on identifying large functions or classes that should be split into smaller, 
more focused units. Look for functions doing multiple things or classes with too many responsibilities.""",
            
            RefactoringStrategy.EXTRACT: """Focus on identifying reusable code patterns that should be extracted into 
separate functions or modules. Look for duplicated code and common patterns.""",
            
            RefactoringStrategy.COMPOSITION: """Focus on improving object composition and dependency structure. 
Look for opportunities to use composition over inheritance and improve modularity."""
        }
        
        prompt += f"""INSTRUCTIONS:
{strategy_instructions[strategy]}

Provide up to 3 concrete refactoring suggestions. For each suggestion:
1. Give it a clear title
2. Explain what should be refactored and why
3. Specify the priority (high/medium/low)
4. Estimate the impact on code quality
5. Provide a unified diff showing the exact changes
6. Explain the reasoning behind this refactoring

Focus on practical, actionable suggestions that will improve:
- Code readability and maintainability
- Modularity and reusability
- Performance (where applicable)
- Testability
- Adherence to best practices for {language}

Generate suggestions that are specific to this code, not generic advice.
"""
        
        return prompt
    
    async def suggest_refactoring(
        self,
        file_path: str,
        code: str,
        metrics: Optional[Dict[str, Any]] = None,
        strategy: str = "auto"
    ) -> str:
        """
        Generate refactoring suggestions for the given code.
        
        Args:
            file_path: Path to the file being analyzed
            code: Source code content
            metrics: Optional metrics data from MetricsEngine
            strategy: Refactoring strategy ("auto", "split", "extract", "composition")
            
        Returns:
            JSON string containing refactoring suggestions
            
        Raises:
            AISuggestionServiceError: If suggestion generation fails
        """
        try:
            # Validate and convert strategy
            try:
                refactoring_strategy = RefactoringStrategy(strategy.lower())
            except ValueError:
                raise AISuggestionServiceError(
                    f"Invalid strategy: {strategy}. "
                    f"Must be one of: {', '.join([s.value for s in RefactoringStrategy])}"
                )
            
            # Build the prompt
            prompt = self._build_prompt(file_path, code, metrics, refactoring_strategy)
            
            # Call Gemini API with structured output
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    response_mime_type='application/json',
                    response_schema=RefactoringSuggestionsResponse,
                )
            )
            
            # The response.text will be valid JSON matching our schema
            return response.text
            
        except Exception as e:
            if isinstance(e, AISuggestionServiceError):
                raise
            raise AISuggestionServiceError(
                f"Failed to generate refactoring suggestions: {str(e)}"
            ) from e
    
    def suggest_refactoring_sync(
        self,
        file_path: str,
        code: str,
        metrics: Optional[Dict[str, Any]] = None,
        strategy: str = "auto"
    ) -> str:
        """
        Synchronous version of suggest_refactoring.
        
        Args:
            file_path: Path to the file being analyzed
            code: Source code content
            metrics: Optional metrics data from MetricsEngine
            strategy: Refactoring strategy ("auto", "split", "extract", "composition")
            
        Returns:
            JSON string containing refactoring suggestions
            
        Raises:
            AISuggestionServiceError: If suggestion generation fails
        """
        try:
            # Validate and convert strategy
            try:
                refactoring_strategy = RefactoringStrategy(strategy.lower())
            except ValueError:
                raise AISuggestionServiceError(
                    f"Invalid strategy: {strategy}. "
                    f"Must be one of: {', '.join([s.value for s in RefactoringStrategy])}"
                )
            
            # Build the prompt
            prompt = self._build_prompt(file_path, code, metrics, refactoring_strategy)
            
            # Call Gemini API with structured output (synchronous)
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    response_mime_type='application/json',
                    response_schema=RefactoringSuggestionsResponse,
                )
            )
            
            # The response.text will be valid JSON matching our schema
            return response.text
            
        except Exception as e:
            if isinstance(e, AISuggestionServiceError):
                raise
            raise AISuggestionServiceError(
                f"Failed to generate refactoring suggestions: {str(e)}"
            ) from e
