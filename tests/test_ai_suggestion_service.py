"""
Tests for AI Suggestion Service.

This module tests the AISuggestionService class and its integration with
Google's Gemini API using mocks.
"""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from pathlib import Path

from src.ai_suggestion_service import (
    AISuggestionService,
    RefactoringStrategy,
    RefactoringSuggestion,
    RefactoringSuggestionsResponse,
    AISuggestionServiceError,
    APINotConfiguredError,
    ModelNotAvailableError,
)


# Sample Python code for testing
SAMPLE_PYTHON_CODE = '''
def process_user_data(user_id):
    # Fetch user
    user = database.get_user(user_id)
    if not user:
        return None
    
    # Process data
    processed = {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'status': 'active' if user.active else 'inactive'
    }
    
    # Send notification
    if user.email:
        send_email(user.email, 'Welcome!')
    
    # Log activity
    logger.info(f"Processed user {user_id}")
    
    return processed
'''


# Sample response from Gemini (structured JSON)
SAMPLE_GEMINI_RESPONSE = {
    "file_path": "test.py",
    "language": "python",
    "strategy_used": "auto",
    "suggestions": [
        {
            "title": "Extract user data transformation logic",
            "description": "The user data transformation logic can be extracted into a separate function for better reusability and testability.",
            "strategy": "extract",
            "priority": "medium",
            "estimated_impact": "Improves code modularity and makes the transformation logic reusable across the codebase.",
            "diff": "--- a/test.py\n+++ b/test.py\n@@ -1,10 +1,14 @@\n+def transform_user_data(user):\n+    return {\n+        'id': user.id,\n+        'name': user.name,\n+        'email': user.email,\n+        'status': 'active' if user.active else 'inactive'\n+    }\n+\n def process_user_data(user_id):\n     user = database.get_user(user_id)\n     if not user:\n         return None\n-    processed = {\n-        'id': user.id,\n-        'name': user.name,\n-        'email': user.email,\n-        'status': 'active' if user.active else 'inactive'\n-    }\n+    processed = transform_user_data(user)\n",
            "reason": "Extracting this logic improves separation of concerns and makes the transformation testable in isolation."
        }
    ],
    "summary": "The code would benefit from extracting the data transformation logic and notification sending into separate functions to improve modularity and testability."
}


class TestAISuggestionService:
    """Test AISuggestionService initialization and configuration."""
    
    @patch('taskmaster.ai_suggestion_service.GENAI_AVAILABLE', True)
    @patch('taskmaster.ai_suggestion_service.genai')
    def test_initialization_success(self, mock_genai):
        """Test successful service initialization."""
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client
        
        service = AISuggestionService(
            model="gemini-2.0-flash-001",
            max_tokens=4000,
            temperature=0.2
        )
        
        assert service.model == "gemini-2.0-flash-001"
        assert service.max_tokens == 4000
        assert service.temperature == 0.2
        assert service.client == mock_client
        mock_genai.Client.assert_called_once()
    
    @patch('taskmaster.ai_suggestion_service.GENAI_AVAILABLE', True)
    @patch('taskmaster.ai_suggestion_service.genai')
    def test_initialization_with_api_key(self, mock_genai):
        """Test initialization with explicit API key."""
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client
        
        service = AISuggestionService(api_key="test-api-key")
        
        mock_genai.Client.assert_called_once_with(api_key="test-api-key")
    
    @patch('taskmaster.ai_suggestion_service.GENAI_AVAILABLE', False)
    def test_initialization_genai_not_installed(self):
        """Test initialization fails when google-genai is not installed."""
        with pytest.raises(ModelNotAvailableError) as exc_info:
            AISuggestionService()
        
        assert "google-genai package is not installed" in str(exc_info.value)
    
    @patch('taskmaster.ai_suggestion_service.GENAI_AVAILABLE', True)
    @patch('taskmaster.ai_suggestion_service.genai')
    def test_initialization_api_not_configured(self, mock_genai):
        """Test initialization fails when API key is not configured."""
        mock_genai.Client.side_effect = Exception("API key not found")
        
        with pytest.raises(APINotConfiguredError) as exc_info:
            AISuggestionService()
        
        assert "Failed to initialize Gemini client" in str(exc_info.value)
        assert "GOOGLE_API_KEY" in str(exc_info.value)


class TestLanguageDetection:
    """Test programming language detection."""
    
    @patch('taskmaster.ai_suggestion_service.GENAI_AVAILABLE', True)
    @patch('taskmaster.ai_suggestion_service.genai')
    def test_detect_python(self, mock_genai):
        """Test detecting Python language."""
        mock_genai.Client.return_value = Mock()
        service = AISuggestionService()
        
        language = service._detect_language("test.py", "print('hello')")
        assert language == "python"
    
    @patch('taskmaster.ai_suggestion_service.GENAI_AVAILABLE', True)
    @patch('taskmaster.ai_suggestion_service.genai')
    def test_detect_javascript(self, mock_genai):
        """Test detecting JavaScript language."""
        mock_genai.Client.return_value = Mock()
        service = AISuggestionService()
        
        language = service._detect_language("test.js", "console.log('hello')")
        assert language == "javascript"
    
    @patch('taskmaster.ai_suggestion_service.GENAI_AVAILABLE', True)
    @patch('taskmaster.ai_suggestion_service.genai')
    def test_detect_unknown_language(self, mock_genai):
        """Test detecting unknown language."""
        mock_genai.Client.return_value = Mock()
        service = AISuggestionService()
        
        language = service._detect_language("test.xyz", "some code")
        assert language == "unknown"


class TestPromptBuilding:
    """Test prompt construction for different strategies."""
    
    @patch('taskmaster.ai_suggestion_service.GENAI_AVAILABLE', True)
    @patch('taskmaster.ai_suggestion_service.genai')
    def test_build_prompt_auto_strategy(self, mock_genai):
        """Test prompt building with auto strategy."""
        mock_genai.Client.return_value = Mock()
        service = AISuggestionService()
        
        prompt = service._build_prompt(
            "test.py",
            "def test(): pass",
            {"loc": 100, "function_count": 5},
            RefactoringStrategy.AUTO
        )
        
        assert "test.py" in prompt
        assert "auto" in prompt
        assert "Lines of Code: 100" in prompt
        assert "Function Count: 5" in prompt
        assert "automatically determine the best refactoring approach" in prompt
    
    @patch('taskmaster.ai_suggestion_service.GENAI_AVAILABLE', True)
    @patch('taskmaster.ai_suggestion_service.genai')
    def test_build_prompt_split_strategy(self, mock_genai):
        """Test prompt building with split strategy."""
        mock_genai.Client.return_value = Mock()
        service = AISuggestionService()
        
        prompt = service._build_prompt(
            "test.py",
            "def test(): pass",
            None,
            RefactoringStrategy.SPLIT
        )
        
        assert "split" in prompt
        assert "identifying large functions or classes" in prompt
    
    @patch('taskmaster.ai_suggestion_service.GENAI_AVAILABLE', True)
    @patch('taskmaster.ai_suggestion_service.genai')
    def test_build_prompt_extract_strategy(self, mock_genai):
        """Test prompt building with extract strategy."""
        mock_genai.Client.return_value = Mock()
        service = AISuggestionService()
        
        prompt = service._build_prompt(
            "test.py",
            "def test(): pass",
            None,
            RefactoringStrategy.EXTRACT
        )
        
        assert "extract" in prompt
        assert "reusable code patterns" in prompt
    
    @patch('taskmaster.ai_suggestion_service.GENAI_AVAILABLE', True)
    @patch('taskmaster.ai_suggestion_service.genai')
    def test_build_prompt_composition_strategy(self, mock_genai):
        """Test prompt building with composition strategy."""
        mock_genai.Client.return_value = Mock()
        service = AISuggestionService()
        
        prompt = service._build_prompt(
            "test.py",
            "def test(): pass",
            None,
            RefactoringStrategy.COMPOSITION
        )
        
        assert "composition" in prompt
        assert "object composition" in prompt
    
    @patch('taskmaster.ai_suggestion_service.GENAI_AVAILABLE', True)
    @patch('taskmaster.ai_suggestion_service.genai')
    def test_build_prompt_without_metrics(self, mock_genai):
        """Test prompt building without metrics."""
        mock_genai.Client.return_value = Mock()
        service = AISuggestionService()
        
        prompt = service._build_prompt(
            "test.py",
            "def test(): pass",
            None,
            RefactoringStrategy.AUTO
        )
        
        assert "METRICS:" not in prompt
        assert "Lines of Code:" not in prompt


class TestSuggestRefactoringAsync:
    """Test async suggest_refactoring method."""
    
    @pytest.mark.asyncio
    @patch('taskmaster.ai_suggestion_service.GENAI_AVAILABLE', True)
    @patch('taskmaster.ai_suggestion_service.genai')
    async def test_suggest_refactoring_success(self, mock_genai):
        """Test successful refactoring suggestion generation."""
        # Setup mock client
        mock_client = Mock()
        mock_aio = Mock()
        mock_models = Mock()
        mock_client.aio.models = mock_models
        
        # Create async mock for generate_content
        mock_response = Mock()
        mock_response.text = json.dumps(SAMPLE_GEMINI_RESPONSE)
        mock_models.generate_content = AsyncMock(return_value=mock_response)
        
        mock_genai.Client.return_value = mock_client
        
        service = AISuggestionService()
        result = await service.suggest_refactoring(
            "test.py",
            SAMPLE_PYTHON_CODE,
            {"loc": 20, "function_count": 1},
            "auto"
        )
        
        # Verify result is valid JSON
        result_dict = json.loads(result)
        assert result_dict["file_path"] == "test.py"
        assert result_dict["language"] == "python"
        assert len(result_dict["suggestions"]) > 0
        
        # Verify API was called correctly
        mock_models.generate_content.assert_called_once()
        call_args = mock_models.generate_content.call_args
        assert call_args[1]["model"] == "gemini-2.0-flash-001"
        assert "test.py" in call_args[1]["contents"]
    
    @pytest.mark.asyncio
    @patch('taskmaster.ai_suggestion_service.GENAI_AVAILABLE', True)
    @patch('taskmaster.ai_suggestion_service.genai')
    async def test_suggest_refactoring_invalid_strategy(self, mock_genai):
        """Test suggest_refactoring with invalid strategy."""
        mock_genai.Client.return_value = Mock()
        service = AISuggestionService()
        
        with pytest.raises(AISuggestionServiceError) as exc_info:
            await service.suggest_refactoring(
                "test.py",
                SAMPLE_PYTHON_CODE,
                None,
                "invalid_strategy"
            )
        
        assert "Invalid strategy" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('taskmaster.ai_suggestion_service.GENAI_AVAILABLE', True)
    @patch('taskmaster.ai_suggestion_service.genai')
    async def test_suggest_refactoring_api_error(self, mock_genai):
        """Test suggest_refactoring handles API errors."""
        mock_client = Mock()
        mock_models = Mock()
        mock_client.aio.models = mock_models
        mock_models.generate_content = AsyncMock(
            side_effect=Exception("API rate limit exceeded")
        )
        
        mock_genai.Client.return_value = mock_client
        
        service = AISuggestionService()
        
        with pytest.raises(AISuggestionServiceError) as exc_info:
            await service.suggest_refactoring(
                "test.py",
                SAMPLE_PYTHON_CODE,
                None,
                "auto"
            )
        
        assert "Failed to generate refactoring suggestions" in str(exc_info.value)


class TestSuggestRefactoringSync:
    """Test synchronous suggest_refactoring_sync method."""
    
    @patch('taskmaster.ai_suggestion_service.GENAI_AVAILABLE', True)
    @patch('taskmaster.ai_suggestion_service.genai')
    def test_suggest_refactoring_sync_success(self, mock_genai):
        """Test successful synchronous refactoring suggestion generation."""
        # Setup mock client
        mock_client = Mock()
        mock_models = Mock()
        mock_client.models = mock_models
        
        # Create mock for generate_content
        mock_response = Mock()
        mock_response.text = json.dumps(SAMPLE_GEMINI_RESPONSE)
        mock_models.generate_content = Mock(return_value=mock_response)
        
        mock_genai.Client.return_value = mock_client
        
        service = AISuggestionService()
        result = service.suggest_refactoring_sync(
            "test.py",
            SAMPLE_PYTHON_CODE,
            {"loc": 20, "function_count": 1},
            "split"
        )
        
        # Verify result is valid JSON
        result_dict = json.loads(result)
        assert result_dict["file_path"] == "test.py"
        assert len(result_dict["suggestions"]) > 0
        
        # Verify API was called
        mock_models.generate_content.assert_called_once()
    
    @patch('taskmaster.ai_suggestion_service.GENAI_AVAILABLE', True)
    @patch('taskmaster.ai_suggestion_service.genai')
    def test_suggest_refactoring_sync_invalid_strategy(self, mock_genai):
        """Test sync method with invalid strategy."""
        mock_genai.Client.return_value = Mock()
        service = AISuggestionService()
        
        with pytest.raises(AISuggestionServiceError) as exc_info:
            service.suggest_refactoring_sync(
                "test.py",
                SAMPLE_PYTHON_CODE,
                None,
                "bad_strategy"
            )
        
        assert "Invalid strategy" in str(exc_info.value)


class TestPydanticModels:
    """Test Pydantic models for structured responses."""
    
    def test_refactoring_suggestion_model(self):
        """Test RefactoringSuggestion Pydantic model."""
        suggestion = RefactoringSuggestion(
            title="Test Refactoring",
            description="Test description",
            strategy="extract",
            priority="high",
            estimated_impact="Improves modularity",
            diff="--- a/test.py\n+++ b/test.py",
            reason="Better separation of concerns"
        )
        
        assert suggestion.title == "Test Refactoring"
        assert suggestion.strategy == "extract"
        assert suggestion.priority == "high"
    
    def test_refactoring_suggestions_response_model(self):
        """Test RefactoringSuggestionsResponse Pydantic model."""
        suggestion = RefactoringSuggestion(
            title="Test",
            description="Desc",
            strategy="auto",
            priority="medium",
            estimated_impact="Impact",
            diff="diff",
            reason="reason"
        )
        
        response = RefactoringSuggestionsResponse(
            file_path="test.py",
            language="python",
            strategy_used="auto",
            suggestions=[suggestion],
            summary="Overall summary"
        )
        
        assert response.file_path == "test.py"
        assert response.language == "python"
        assert len(response.suggestions) == 1
        assert response.suggestions[0].title == "Test"
