# Auto-Refactor MCP Server# Auto-Refactor MCP Server



**Intelligent Automated Code Refactoring via Model Context Protocol**🚀 **Intelligent Automated Code Refactoring**



Version 0.1.0 | Python 3.10+Auto-Refactor is an MCP (Model Context Protocol) server that provides automated code refactoring capabilities. It monitors codebases, identifies files exceeding complexity thresholds, and performs intelligent refactoring operations to maintain code quality and maintainability.



---## Features



## Overview- 🔍 **Automated Detection**: Identifies files exceeding complexity thresholds (lines, complexity, functions)

- 🤖 **AI-Powered Suggestions**: Generate intelligent refactoring strategies using GPT-4/Claude

Auto-Refactor is a Model Context Protocol (MCP) server that provides AI-powered code refactoring capabilities. It analyzes source code, suggests improvements, and safely applies refactorings with automatic testing and rollback.- 🛡️ **Safe Execution**: Automatic backups, test validation, and rollback support

- 🗄️ **Database Refactoring**: Specialized handling for migrations and SQL files

### Key Features- 🌐 **Multi-Language Support**: Python, JavaScript, TypeScript, Java, C#, SQL



- **AI-Powered Analysis**: Uses Google Gemini to generate intelligent refactoring suggestions## Installation

- **Safe Refactoring**: Automatic Git backup, testing, and rollback on failure

- **Multi-Language Support**: Python, JavaScript, and TypeScript```bash

- **Database Refactoring**: Split large migrations and extract complex queries# Using uv (recommended)

- **Suggestion Management**: Review, approve, or reject suggestions before applyinguv pip install -e .

- **Operation Tracking**: Complete audit trail of all refactoring operations

# Or using pip

---pip install -e .

```

## Architecture

## Quick Start

```

Auto-Refactor MCP Server### 1. Add to MCP Configuration

├── refactor_server.py          # MCP server entry point

├── src/Edit your `.vscode/mcp.json` or Claude Desktop config:

│   ├── ai_suggestion_service.py    # AI-powered suggestions

│   ├── refactoring_engine.py       # Core refactoring operations```json

│   ├── database_refactoring.py     # Database-specific refactoring{

│   ├── metrics_engine.py           # Code metrics calculation  "servers": {

│   ├── git_manager.py              # Git operations    "auto-refactor": {

│   ├── test_runner.py              # Test execution      "command": "uv",

│   ├── rollback_manager.py         # Operation rollback      "args": [

│   └── suggestion_manager.py       # Suggestion lifecycle        "--directory",

└── tests/                          # Comprehensive test suite        "/path/to/refactor-server",

```        "run",

        "refactor_server.py"

---      ],

      "type": "stdio",

## Installation      "env": {

        "OPENAI_API_KEY": "your-openai-key",

### Prerequisites        "ANTHROPIC_API_KEY": "your-anthropic-key"

      }

- Python 3.10 or higher    }

- Git (required for safe refactoring)  }

- UV package manager (recommended)}

```

### Install with UV

### 2. Test the Connection

```bash

# Clone the repository```bash

git clone https://github.com/akv2011/Auto_Refactor_codebase_MCP.git# Run the server directly

cd Auto_Refactor_codebase_MCPuv run refactor_server.py

```

# Install dependencies

uv sync## MCP Tools



# Run tests### `analyze_codebase`

uv run pytestScan and identify files requiring refactoring based on complexity thresholds.

```

### `suggest_refactoring`

### Install with pipGenerate AI-powered refactoring suggestions for specific files.



```bash### `execute_refactoring`

pip install -e .Apply approved refactoring operations safely with automatic backups.

```

### `refactor_database`

---Specialized refactoring for database migrations and schema files.



## Configuration### `get_refactoring_status`

Track ongoing and completed refactoring operations.

### VS Code MCP Integration

### `rollback_refactoring`

Add to `.vscode/mcp.json`:Rollback a completed refactoring operation.



```json## Configuration

{

  "mcpServers": {Create a `.taskmaster.json` in your project root:

    "auto-refactor": {

      "command": "uv",```json

      "args": [{

        "--directory",  "thresholds": {

        "/absolute/path/to/Auto_refactor_MCP",    "maxLines": 1500,

        "run",    "maxFunctions": 50,

        "refactor_server"    "maxComplexity": 15,

      ],    "maxClassSize": 500

      "env": {  },

        "GOOGLE_API_KEY": "your-api-key-here"  "languages": ["python", "javascript", "typescript"],

      }  "excludePatterns": ["**/test/**", "**/vendor/**"],

    }  "safety": {

  }    "requireTests": true,

}    "createBackups": true,

```    "dryRunFirst": true

  }

### Environment Variables}

```

Required:

- `GOOGLE_API_KEY`: Google Gemini API key for AI suggestions## Development



Optional:### Setup Development Environment

- `OPENAI_API_KEY`: For future OpenAI integration

- `ANTHROPIC_API_KEY`: For future Claude integration```bash

# Install with dev dependencies

### Project Configurationuv pip install -e ".[dev]"



Create `.refactor/config.json` in your project:# Run tests

pytest

```json

{# Run linting

  "languages": {ruff check .

    "python": {black --check .

      "enabled": true,

      "max_function_lines": 50,# Type checking

      "max_complexity": 10mypy src

    }```

  },

  "thresholds": {### Project Structure

    "complexity": 10,

    "lines": 50,```

    "parameters": 5refactor-server/

  },├── src/                 # Core package

  "testing": {│   ├── __init__.py

    "python": {│   ├── scanner.py       # File scanning

      "command": "pytest",│   ├── analyzer.py      # Code analysis

      "args": ["-v"]│   ├── metrics.py       # Complexity metrics

    }│   ├── ai_suggester.py  # AI integration

  }│   ├── refactor.py      # Refactoring engine

}│   └── database.py      # Database refactoring

```├── tests/               # Test suite

├── refactor_server.py   # Main server entry point

---├── pyproject.toml       # Dependencies

└── README.md           # This file

## Usage```



### Available MCP Tools## Requirements



The server exposes 10 MCP tools:- Python 3.10+

- OpenAI API key (for GPT-4 suggestions)

#### 1. hello_refactor- Anthropic API key (for Claude suggestions)

Verify server is running.

## License

#### 2. suggest_refactoring

Generate AI-powered refactoring suggestions.MIT License



**Parameters:**## Contributing

- `file_path` (required): Absolute path to source file

- `strategy` (optional): "auto", "split", "extract", or "composition"Contributions welcome! Please feel free to submit a Pull Request.



**Returns:** JSON with suggestions, diffs, and cached suggestion ID## Support



#### 3. execute_refactoringFor issues and questions, please open an issue on GitHub.

Apply refactoring with automatic testing and rollback.

---

**Parameters:**

- `file_path` (required): File to refactor**Built with FastMCP** 🚀

- `suggestion_json` (required): JSON from suggest_refactoring
- `dry_run` (optional, default: true): Preview without applying

#### 4. approve_suggestion
Execute a cached suggestion by ID.

**Parameters:**
- `suggestion_id` (required): ID from suggest_refactoring
- `dry_run` (optional, default: false): Preview mode

#### 5. list_suggestions
View cached suggestions.

**Parameters:**
- `status` (optional): Filter by status
- `file_path` (optional): Filter by file
- `limit` (optional, default: 10): Max results

#### 6. get_suggestion
Get detailed information about a suggestion.

**Parameters:**
- `suggestion_id` (required): Suggestion ID

#### 7. reject_suggestion
Reject a cached suggestion.

**Parameters:**
- `suggestion_id` (required): Suggestion ID
- `reason` (optional): Rejection reason

#### 8. clear_suggestions
Clean up suggestion cache.

**Parameters:**
- `status` (optional): Clear by status
- `older_than_days` (optional): Clear old suggestions

#### 9. get_refactoring_status
View refactoring operation history.

**Parameters:**
- `project_root` (required): Project directory path
- `limit` (optional, default: 10): Max operations
- `include_rolled_back` (optional, default: false): Include rollbacks

#### 10. refactor_database
Database-specific refactoring operations.

**Parameters:**
- `project_root` (required): Project directory
- `operation` (required): "split_migration" or "extract_query"
- `file_path` (required): Database file to refactor
- Additional parameters based on operation type

---

## Workflow Examples

### Basic Refactoring Workflow

```python
# 1. Analyze a file
result = suggest_refactoring(
    file_path="/path/to/app.py",
    strategy="auto"
)

# 2. Review the suggestion
suggestion = get_suggestion(suggestion_id="abc123")

# 3. Preview changes
preview = approve_suggestion(
    suggestion_id="abc123",
    dry_run=True
)

# 4. Apply refactoring
final = approve_suggestion(
    suggestion_id="abc123",
    dry_run=False
)

# 5. Check status
status = get_refactoring_status(project_root="/path/to/project")
```

### Database Migration Splitting

```python
result = refactor_database(
    project_root="/path/to/project",
    operation="split_migration",
    file_path="app/migrations/0042_large_migration.py",
    max_operations_per_file=3
)
```

---

## Testing

### Run All Tests

```bash
uv run pytest
```

### Run Specific Test Category

```bash
uv run pytest tests/test_ai_suggestion_service.py
uv run pytest tests/test_refactoring_engine.py
```

### Coverage Report

```bash
uv run pytest --cov=src --cov-report=term
```

---

## Development

### Project Structure

```
Auto_refactor_MCP/
├── docs/                   # Documentation
├── src/                    # Source code
├── tests/                  # Test suite
├── examples/               # Usage examples
├── .vscode/               # VS Code configuration
├── pyproject.toml         # Project metadata
└── refactor_server.py     # Server entry point
```

### Code Quality

```bash
# Format code
uv run black src tests

# Lint code
uv run ruff check src tests

# Type checking
uv run mypy src
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass
5. Submit a pull request

---

## Troubleshooting

### Server Won't Start

- Verify Python version: `python --version` (requires 3.10+)
- Check UV installation: `uv --version`
- Review logs in VS Code Output panel (MCP section)

### API Errors

- Verify `GOOGLE_API_KEY` is set in `mcp.json`
- Check API key validity at Google AI Studio
- Ensure network connectivity

### Test Failures During Refactoring

- Ensure tests pass before refactoring
- Check test command in `.refactor/config.json`
- Automatic rollback will restore code if tests fail

### Git Issues

- Initialize Git repository: `git init`
- Commit pending changes: `git commit -am "Save work"`
- Check Git status: `git status`

---

## Documentation

- **Testing Guide**: `docs/TESTING_GUIDE.md`
- **Quick Test Prompts**: `docs/QUICK_TEST_PROMPTS.md`
- **API Reference**: `.github/instructions/auto_refactor.instructions.md`

---

## Requirements

### Core Dependencies

- mcp >= 1.2.0
- fastmcp >= 0.1.0
- pydantic >= 2.0.0
- gitpython >= 3.1.0
- google-genai >= 1.0.0
- tree-sitter >= 0.21.0
- radon >= 6.0.0
- pytest >= 8.0.0

### Supported Languages

- Python (.py)
- JavaScript (.js)
- TypeScript (.ts)

---

## License

See LICENSE file for details.

---

## Version History

### v0.1.0 (2025-10-08)

- Initial release
- AI-powered refactoring suggestions
- Automatic testing and rollback
- Suggestion management system
- Operation tracking and history
- Database refactoring capabilities
- Python, JavaScript, TypeScript support

---

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/akv2011/Auto_Refactor_codebase_MCP/issues
- Repository: https://github.com/akv2011/Auto_Refactor_codebase_MCP

---

## Acknowledgments

Built with:
- Model Context Protocol (MCP) by Anthropic
- FastMCP framework
- Google Gemini AI
- Tree-sitter for code parsing
- Radon for complexity metrics
