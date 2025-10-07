"""TaskMaster MCP Server - Core Package"""

__version__ = "0.1.0"
__author__ = "Arun Kumar"
__description__ = "Intelligent automated code refactoring MCP server"

# Import core classes for easier access
from .parser_setup import TreeSitterSetup, GrammarSetupError
from .parser_factory import ParserFactory, ParserNotAvailableError
from .ast_wrapper import ASTWrapper, ASTParsingError
from .code_node import CodeNode, CodeNodeCollection
from .loc_calculator import calculate_loc, calculate_loc_batch, LOCCalculationError
from .python_metrics import (
    calculate_python_metrics,
    calculate_python_metrics_batch,
    get_complexity_grade,
    PythonMetricsError
)
from .js_function_counter import (
    count_functions_ast,
    count_functions_in_file,
    count_functions_batch,
    get_function_details_from_ast,
    JSFunctionCountError
)
from .js_complexity import (
    calculate_complexity_ast,
    calculate_complexity_in_file,
    calculate_complexity_batch,
    calculate_per_function_complexity,
    JSComplexityError
)
from .git_manager import (
    GitManager,
    GitManagerError,
    NotAGitRepositoryError,
    GitOperationError
)
from .refactoring_engine import (
    RefactoringEngine,
    RefactoringError,
    UnsupportedOperationError,
    RefactoringValidationError
)
from .test_runner import (
    TestRunner,
    TestResult,
    TestRunnerError,
    TestCommandNotFoundError
)
from .rollback_manager import (
    RollbackManager,
    RollbackError,
    OperationNotFoundError,
    rollback_refactoring
)
from .codebase_analyzer import (
    analyze_codebase,
    CodebaseAnalysisError
)
from .ai_suggestion_service import (
    AISuggestionService,
    RefactoringStrategy,
    RefactoringSuggestion,
    RefactoringSuggestionsResponse,
    AISuggestionServiceError,
    APINotConfiguredError,
    ModelNotAvailableError,
)
from .suggestion_manager import (
    SuggestionManager,
    SuggestionStatus,
    SuggestionManagerError,
    SuggestionNotFoundError,
    InvalidSuggestionError,
)

__all__ = [
    "TreeSitterSetup",
    "GrammarSetupError",
    "ParserFactory",
    "ParserNotAvailableError",
    "ASTWrapper",
    "ASTParsingError",
    "CodeNode",
    "CodeNodeCollection",
    "calculate_loc",
    "calculate_loc_batch",
    "LOCCalculationError",
    "calculate_python_metrics",
    "calculate_python_metrics_batch",
    "get_complexity_grade",
    "PythonMetricsError",
    "count_functions_ast",
    "count_functions_in_file",
    "count_functions_batch",
    "get_function_details_from_ast",
    "JSFunctionCountError",
    "calculate_complexity_ast",
    "calculate_complexity_in_file",
    "calculate_complexity_batch",
    "calculate_per_function_complexity",
    "JSComplexityError",
    "GitManager",
    "GitManagerError",
    "NotAGitRepositoryError",
    "GitOperationError",
    "RefactoringEngine",
    "RefactoringError",
    "UnsupportedOperationError",
    "RefactoringValidationError",
    "TestRunner",
    "TestResult",
    "TestRunnerError",
    "TestCommandNotFoundError",
    "RollbackManager",
    "RollbackError",
    "OperationNotFoundError",
    "rollback_refactoring",
    "analyze_codebase",
    "CodebaseAnalysisError",
    "AISuggestionService",
    "RefactoringStrategy",
    "RefactoringSuggestion",
    "RefactoringSuggestionsResponse",
    "AISuggestionServiceError",
    "APINotConfiguredError",
    "ModelNotAvailableError",
    "SuggestionManager",
    "SuggestionStatus",
    "SuggestionManagerError",
    "SuggestionNotFoundError",
    "InvalidSuggestionError",
]
