# Auto-Refactor MCP Server# Auto-Refactor MCP Server



**Intelligent Automated Code Refactoring via Model Context Protocol****Intelligent Automated Code Refactoring via Model Context Protocol**



Version 0.1.0 | Python 3.10+Version 0.1.0 | Python 3.10+



------



## Overview## Overview



Auto-Refactor is a Model Context Protocol (MCP) server that provides AI-powered code refactoring capabilities. It analyzes source code, suggests improvements, and safely applies refactorings with automatic testing and rollback.Auto-Refactor is a Model Context Protocol (MCP) server that provides AI-powered code refactoring capabilities. It analyzes source code, suggests improvements, and safely applies refactorings with automatic testing and rollback.



### Key Features### Key Features



- **AI-Powered Analysis**: Uses Google Gemini to generate intelligent refactoring suggestions- **AI-Powered Analysis**: Uses Google Gemini to generate intelligent refactoring suggestions

- **Safe Refactoring**: Automatic Git backup, testing, and rollback on failure- **Safe Refactoring**: Automatic Git backup, testing, and rollback on failure

- **Multi-Language Support**: Python, JavaScript, and TypeScript- **Multi-Language Support**: Python, JavaScript, and TypeScript

- **Database Refactoring**: Split large migrations and extract complex queries- **Database Refactoring**: Split large migrations and extract complex queries

- **Suggestion Management**: Review, approve, or reject suggestions before applying- **Suggestion Management**: Review, approve, or reject suggestions before applying

- **Operation Tracking**: Complete audit trail of all refactoring operations- **Operation Tracking**: Complete audit trail of all refactoring operations



------



## Architecture## Architecture



``````

Auto-Refactor MCP ServerAuto-Refactor MCP Server

├── refactor_server.py          # MCP server entry point├── refactor_server.py          # MCP server entry point

├── src/├── src/

│   ├── ai_suggestion_service.py    # AI-powered suggestions│   ├── ai_suggestion_service.py    # AI-powered suggestions

│   ├── refactoring_engine.py       # Core refactoring operations│   ├── refactoring_engine.py       # Core refactoring operations

│   ├── database_refactoring.py     # Database-specific refactoring│   ├── database_refactoring.py     # Database-specific refactoring

│   ├── metrics_engine.py           # Code metrics calculation│   ├── metrics_engine.py           # Code metrics calculation

│   ├── git_manager.py              # Git operations│   ├── git_manager.py              # Git operations

│   ├── test_runner.py              # Test execution│   ├── test_runner.py              # Test execution

│   ├── rollback_manager.py         # Operation rollback│   ├── rollback_manager.py         # Operation rollback

│   └── suggestion_manager.py       # Suggestion lifecycle│   └── suggestion_manager.py       # Suggestion lifecycle

└── tests/                          # Comprehensive test suite└── tests/                          # Comprehensive test suite

``````



------



## Installation## Installation



### Prerequisites### Prerequisites



- Python 3.10 or higher- Python 3.10 or higher

- Git (required for safe refactoring)- Git (required for safe refactoring)

- UV package manager (recommended)- UV package manager (recommended)



### Install with UV### Install with UV



```bash```bash

# Clone the repository# Clone the repository

git clone https://github.com/akv2011/Auto_Refactor_codebase_MCP.gitgit clone https://github.com/akv2011/Auto_Refactor_codebase_MCP.git

cd Auto_Refactor_codebase_MCPcd Auto_Refactor_codebase_MCP



# Install dependencies# Install dependencies

uv syncuv sync



# Run tests# Run tests

uv run pytestuv run pytest

``````



### Install with pip### Install with pip



```bash```bash

pip install -e .pip install -e .

``````



------



## Configuration## Quick Start



### For VS Code### 1. Add to MCP Configuration



Create or edit `.vscode/mcp.json`:Edit your `.vscode/mcp.json` or Claude Desktop config:



```json```json

{{

  "mcpServers": {  "mcpServers": {

    "auto-refactor": {    "auto-refactor": {

      "command": "uv",      "command": "uv",

      "args": [      "args": [

        "--directory",        "--directory",

        "C:/Users/YourName/Auto_refactor_MCP",        "/absolute/path/to/Auto_refactor_MCP",

        "run",        "run",

        "refactor_server"        "refactor_server"

      ],      ],

      "env": {      "env": {

        "GOOGLE_API_KEY": "your-google-api-key-here"        "GOOGLE_API_KEY": "your-api-key-here"

      }      }

    }    }

  }  }

}}

``````



### For Cursor### 2. Test the Connection



Create or edit `.cursor/mcp.json`:```bash

# Run the server directly

```jsonuv run refactor_server.py

{```

  "mcpServers": {

    "auto-refactor": {---

      "command": "uv",

      "args": [## MCP Tools

        "--directory",

        "/absolute/path/to/Auto_refactor_MCP",### `hello_refactor`

        "run",Verify server is running.

        "refactor_server"

      ],### `suggest_refactoring`

      "env": {Generate AI-powered refactoring suggestions for specific files.

        "GOOGLE_API_KEY": "your-google-api-key-here"

      }

    }

  }## Configuration### `get_refactoring_status`

}

```Track ongoing and completed refactoring operations.



### For Claude Desktop### VS Code MCP Integration



Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):### `rollback_refactoring`



```jsonAdd to `.vscode/mcp.json`:Rollback a completed refactoring operation.

{

  "mcpServers": {

    "auto-refactor": {

      "command": "uv",```json## Configuration

      "args": [

        "--directory",{

        "/absolute/path/to/Auto_refactor_MCP",

        "run",  "mcpServers": {Create a `.taskmaster.json` in your project root:

        "refactor_server"

      ],    "auto-refactor": {

      "env": {

        "GOOGLE_API_KEY": "your-google-api-key-here"      "command": "uv",```json

      }

    }      "args": [{

  }

}        "--directory",  "thresholds": {

```

        "/absolute/path/to/Auto_refactor_MCP",    "maxLines": 1500,

### Environment Variables

        "run",    "maxFunctions": 50,

Required:

- `GOOGLE_API_KEY`: Google Gemini API key for AI suggestions        "refactor_server"    "maxComplexity": 15,



Optional (for future use):      ],    "maxClassSize": 500

- `OPENAI_API_KEY`: For OpenAI integration

- `ANTHROPIC_API_KEY`: For Claude integration      "env": {  },



### Project Configuration        "GOOGLE_API_KEY": "your-api-key-here"  "languages": ["python", "javascript", "typescript"],



Create `.refactor/config.json` in your project root:      }  "excludePatterns": ["**/test/**", "**/vendor/**"],



```json    }  "safety": {

{

  "languages": {  }    "requireTests": true,

    "python": {

      "enabled": true,}    "createBackups": true,

      "max_function_lines": 50,

      "max_complexity": 10```    "dryRunFirst": true

    },

    "javascript": {  }

      "enabled": true,

      "max_function_lines": 40,### Environment Variables}

      "max_complexity": 8

    }```

  },

  "thresholds": {Required:

    "complexity": 10,

    "lines": 50,- `GOOGLE_API_KEY`: Google Gemini API key for AI suggestions## Development

    "parameters": 5

  },

  "testing": {

    "python": {Optional:### Setup Development Environment

      "command": "pytest",

      "args": ["-v"]- `OPENAI_API_KEY`: For future OpenAI integration

    },

    "javascript": {- `ANTHROPIC_API_KEY`: For future Claude integration```bash

      "command": "npm",

      "args": ["test"]# Install with dev dependencies

    }

  },### Project Configurationuv pip install -e ".[dev]"

  "git": {

    "auto_backup": true,

    "backup_prefix": "backup-"

  }Create `.refactor/config.json` in your project:# Run tests

}

```pytest



---```json



## MCP Tools{# Run linting



### `hello_refactor`  "languages": {ruff check .

Verify server is running correctly.

    "python": {black --check .

**Returns:** Greeting message confirming server status

      "enabled": true,

### `suggest_refactoring`

Generate AI-powered refactoring suggestions for a source file.      "max_function_lines": 50,# Type checking



**Parameters:**      "max_complexity": 10mypy src

- `file_path` (required): Absolute path to source file

- `strategy` (optional): "auto" (default), "split", "extract", or "composition"    }```



**Returns:** JSON with suggestions, diffs, and cached suggestion ID  },



### `execute_refactoring`  "thresholds": {### Project Structure

Apply refactoring with automatic testing and rollback.

    "complexity": 10,

**Parameters:**

- `file_path` (required): File to refactor    "lines": 50,```

- `suggestion_json` (required): JSON from suggest_refactoring

- `dry_run` (optional, default: true): Preview without applying changes    "parameters": 5refactor-server/



**Returns:** Execution report with status, tests, and rollback info  },├── src/                 # Core package



### `approve_suggestion`  "testing": {│   ├── __init__.py

Execute a cached suggestion by ID.

    "python": {│   ├── scanner.py       # File scanning

**Parameters:**

- `suggestion_id` (required): ID from suggest_refactoring      "command": "pytest",│   ├── analyzer.py      # Code analysis

- `dry_run` (optional, default: false): Preview mode

      "args": ["-v"]│   ├── metrics.py       # Complexity metrics

**Returns:** Same format as execute_refactoring

    }│   ├── ai_suggester.py  # AI integration

### `list_suggestions`

View cached refactoring suggestions.  }│   ├── refactor.py      # Refactoring engine



**Parameters:**}│   └── database.py      # Database refactoring

- `status` (optional): Filter by status (pending, approved, rejected, executed, failed)

- `file_path` (optional): Filter by specific file```├── tests/               # Test suite

- `limit` (optional, default: 10): Maximum results to return

├── refactor_server.py   # Main server entry point

**Returns:** List of suggestions with metadata

---├── pyproject.toml       # Dependencies

### `get_suggestion`

Get detailed information about a specific suggestion.└── README.md           # This file



**Parameters:**## Usage```

- `suggestion_id` (required): Suggestion ID to retrieve



**Returns:** Full suggestion details including diffs and metadata

### Available MCP Tools## Requirements

### `reject_suggestion`

Reject a cached refactoring suggestion.



**Parameters:**The server exposes 10 MCP tools:- Python 3.10+

- `suggestion_id` (required): Suggestion ID to reject

- `reason` (optional): Reason for rejection- OpenAI API key (for GPT-4 suggestions)



**Returns:** Confirmation of rejection#### 1. hello_refactor- Anthropic API key (for Claude suggestions)



### `clear_suggestions`Verify server is running.

Clean up cached suggestions.

## License

**Parameters:**

- `status` (optional): Clear by status (e.g., "rejected", "executed")#### 2. suggest_refactoring

- `older_than_days` (optional): Clear suggestions older than N days

Generate AI-powered refactoring suggestions.MIT License

**Returns:** Count of cleared suggestions



### `get_refactoring_status`

View refactoring operation history.**Parameters:**## Contributing



**Parameters:**- `file_path` (required): Absolute path to source file

- `project_root` (required): Absolute path to project directory

- `limit` (optional, default: 10): Maximum operations to return- `strategy` (optional): "auto", "split", "extract", or "composition"Contributions welcome! Please feel free to submit a Pull Request.

- `include_rolled_back` (optional, default: false): Include rollbacks



**Returns:** Operation history with details

**Returns:** JSON with suggestions, diffs, and cached suggestion ID## Support

### `refactor_database`

Database-specific refactoring operations.



**Parameters:**#### 3. execute_refactoringFor issues and questions, please open an issue on GitHub.

- `project_root` (required): Project directory path

- `operation` (required): "split_migration" or "extract_query"Apply refactoring with automatic testing and rollback.

- `file_path` (required): Database file to refactor

- `max_operations_per_file` (optional, default: 5): For split_migration---

- `query_identifier` (optional): For extract_query

- `view_name` (optional): Custom view name for extracted queries**Parameters:**



**Returns:** Operation-specific results with rollback scripts- `file_path` (required): File to refactor**Built with FastMCP** 🚀



---- `suggestion_json` (required): JSON from suggest_refactoring

- `dry_run` (optional, default: true): Preview without applying

## Usage Examples

#### 4. approve_suggestion

### Example 1: Analyze and Refactor a FileExecute a cached suggestion by ID.



```**Parameters:**

User: "Analyze src/app.py for refactoring opportunities"- `suggestion_id` (required): ID from suggest_refactoring

```- `dry_run` (optional, default: false): Preview mode



AI will:#### 5. list_suggestions

1. Call `suggest_refactoring` with file_path="src/app.py"View cached suggestions.

2. Present suggestions with cached ID

3. Wait for approval**Parameters:**

- `status` (optional): Filter by status

```- `file_path` (optional): Filter by file

User: "Apply the first suggestion"- `limit` (optional, default: 10): Max results

```

#### 6. get_suggestion

AI will:Get detailed information about a suggestion.

1. Call `approve_suggestion` with dry_run=true

2. Show preview**Parameters:**

3. Call `approve_suggestion` with dry_run=false to apply- `suggestion_id` (required): Suggestion ID



### Example 2: Review Pending Suggestions#### 7. reject_suggestion

Reject a cached suggestion.

```

User: "Show me all pending refactoring suggestions"**Parameters:**

```- `suggestion_id` (required): Suggestion ID

- `reason` (optional): Rejection reason

AI will:

1. Call `list_suggestions` with status="pending"#### 8. clear_suggestions

2. Display suggestions in a tableClean up suggestion cache.



### Example 3: Split Large Migration**Parameters:**

- `status` (optional): Clear by status

```- `older_than_days` (optional): Clear old suggestions

User: "Split the large Django migration in migrations/0042_large.py"

```#### 9. get_refactoring_status

View refactoring operation history.

AI will:

1. Call `refactor_database` with:**Parameters:**

   - operation="split_migration"- `project_root` (required): Project directory path

   - file_path="migrations/0042_large.py"- `limit` (optional, default: 10): Max operations

   - max_operations_per_file=3- `include_rolled_back` (optional, default: false): Include rollbacks

2. Show split files and dependency chain

#### 10. refactor_database

### Example 4: Check Refactoring HistoryDatabase-specific refactoring operations.



```**Parameters:**

User: "What refactorings have been done recently?"- `project_root` (required): Project directory

```- `operation` (required): "split_migration" or "extract_query"

- `file_path` (required): Database file to refactor

AI will:- Additional parameters based on operation type

1. Call `get_refactoring_status` with project_root

2. Display operation history with statuses---



---## Workflow Examples



## Workflow Patterns### Basic Refactoring Workflow



### Safe Refactoring Workflow (Recommended)```python

# 1. Analyze a file

1. **Analyze Code**: Use `suggest_refactoring` to get AI suggestionsresult = suggest_refactoring(

2. **Review Suggestion**: Use `get_suggestion` to examine details    file_path="/path/to/app.py",

3. **Preview Changes**: Use `approve_suggestion` with dry_run=true    strategy="auto"

4. **Apply Refactoring**: Use `approve_suggestion` with dry_run=false)

5. **Verify Status**: Use `get_refactoring_status` to confirm

# 2. Review the suggestion

### Batch Analysis Workflowsuggestion = get_suggestion(suggestion_id="abc123")



1. Analyze multiple files with `suggest_refactoring`# 3. Preview changes

2. Use `list_suggestions` to review all pendingpreview = approve_suggestion(

3. Selectively approve high-priority suggestions    suggestion_id="abc123",

4. Track progress with `get_refactoring_status`    dry_run=True

)

### Database Migration Workflow

# 4. Apply refactoring

1. Use `refactor_database` with operation="split_migration"final = approve_suggestion(

2. Review split files and dependency chain    suggestion_id="abc123",

3. Test migrations manually    dry_run=False

4. Apply if tests pass)



---# 5. Check status

status = get_refactoring_status(project_root="/path/to/project")

## Testing```



### Run All Tests### Database Migration Splitting



```bash```python

uv run pytestresult = refactor_database(

```    project_root="/path/to/project",

    operation="split_migration",

### Run Specific Test Category    file_path="app/migrations/0042_large_migration.py",

    max_operations_per_file=3

```bash)

uv run pytest tests/test_ai_suggestion_service.py```

uv run pytest tests/test_refactoring_engine.py

uv run pytest tests/test_database_refactoring.py---

```

## Testing

### Coverage Report

### Run All Tests

```bash

uv run pytest --cov=src --cov-report=term```bash

```uv run pytest

```

---

### Run Specific Test Category

## Development

```bash

### Project Structureuv run pytest tests/test_ai_suggestion_service.py

uv run pytest tests/test_refactoring_engine.py

``````

Auto_refactor_MCP/

├── docs/                   # Documentation### Coverage Report

│   ├── TESTING_GUIDE.md

│   └── QUICK_TEST_PROMPTS.md```bash

├── src/                    # Source codeuv run pytest --cov=src --cov-report=term

├── tests/                  # Test suite (646 tests)```

├── examples/               # Usage examples

├── .vscode/               # VS Code configuration---

├── pyproject.toml         # Project metadata

└── refactor_server.py     # Server entry point## Development

```

### Project Structure

### Code Quality

```

```bashAuto_refactor_MCP/

# Format code├── docs/                   # Documentation

uv run black src tests├── src/                    # Source code

├── tests/                  # Test suite

# Lint code├── examples/               # Usage examples

uv run ruff check src tests├── .vscode/               # VS Code configuration

├── pyproject.toml         # Project metadata

# Type checking└── refactor_server.py     # Server entry point

uv run mypy src```

```

### Code Quality

### Contributing

```bash

1. Fork the repository# Format code

2. Create a feature branchuv run black src tests

3. Make your changes with tests

4. Ensure all tests pass# Lint code

5. Submit a pull requestuv run ruff check src tests



---# Type checking

uv run mypy src

## Troubleshooting```



### Server Won't Start### Contributing



- Verify Python version: `python --version` (requires 3.10+)1. Fork the repository

- Check UV installation: `uv --version`2. Create a feature branch

- Review logs in VS Code Output panel (MCP section)3. Make your changes with tests

- Restart VS Code after configuration changes4. Ensure all tests pass

5. Submit a pull request

### API Errors

---

- Verify `GOOGLE_API_KEY` is set in mcp.json `env` section

- Check API key validity at Google AI Studio## Troubleshooting

- Ensure network connectivity

- Check API rate limits### Server Won't Start



### Test Failures During Refactoring- Verify Python version: `python --version` (requires 3.10+)

- Check UV installation: `uv --version`

- Ensure tests pass before refactoring: `pytest`- Review logs in VS Code Output panel (MCP section)

- Check test command in `.refactor/config.json`

- Automatic rollback will restore code if tests fail### API Errors

- Review operation status with `get_refactoring_status`

- Verify `GOOGLE_API_KEY` is set in `mcp.json`

### Git Issues- Check API key validity at Google AI Studio

- Ensure network connectivity

- Initialize Git repository: `git init`

- Commit pending changes: `git commit -am "Save work"`### Test Failures During Refactoring

- Check Git status: `git status`

- Verify backup branches are created- Ensure tests pass before refactoring

- Check test command in `.refactor/config.json`

### Import Errors- Automatic rollback will restore code if tests fail



- Ensure all dependencies installed: `uv sync`### Git Issues

- Check Python environment: `uv run python --version`

- Reinstall if needed: `uv pip install -e .`- Initialize Git repository: `git init`

- Commit pending changes: `git commit -am "Save work"`

---- Check Git status: `git status`



## Documentation---



- **Testing Guide**: `docs/TESTING_GUIDE.md`## Documentation

- **Quick Test Prompts**: `docs/QUICK_TEST_PROMPTS.md`

- **API Reference**: `.github/instructions/auto_refactor.instructions.md`- **Testing Guide**: `docs/TESTING_GUIDE.md`

- **Quick Test Prompts**: `docs/QUICK_TEST_PROMPTS.md`

---- **API Reference**: `.github/instructions/auto_refactor.instructions.md`



## Requirements---



### Core Dependencies## Requirements



- mcp >= 1.2.0### Core Dependencies

- fastmcp >= 0.1.0

- pydantic >= 2.0.0- mcp >= 1.2.0

- gitpython >= 3.1.0- fastmcp >= 0.1.0

- google-genai >= 1.0.0- pydantic >= 2.0.0

- tree-sitter >= 0.21.0- gitpython >= 3.1.0

- radon >= 6.0.0- google-genai >= 1.0.0

- pytest >= 8.0.0- tree-sitter >= 0.21.0

- radon >= 6.0.0

### Supported Languages- pytest >= 8.0.0



- Python (.py)### Supported Languages

- JavaScript (.js)

- TypeScript (.ts)- Python (.py)

- JavaScript (.js)

### Supported Platforms- TypeScript (.ts)



- Windows 10/11---

- macOS 10.15+

- Linux (Ubuntu 20.04+)## License



---See LICENSE file for details.



## License---



See LICENSE file for details.## Version History



---### v0.1.0 (2025-10-08)



## Version History- Initial release

- AI-powered refactoring suggestions

### v0.1.0 (2025-10-08)- Automatic testing and rollback

- Suggestion management system

- Initial release- Operation tracking and history

- AI-powered refactoring suggestions using Google Gemini- Database refactoring capabilities

- Automatic testing and rollback capabilities- Python, JavaScript, TypeScript support

- Suggestion management system

- Operation tracking and history---

- Database refactoring capabilities

- Python, JavaScript, TypeScript support## Support

- 646 comprehensive tests

For issues, questions, or contributions:

---- GitHub Issues: https://github.com/akv2011/Auto_Refactor_codebase_MCP/issues

- Repository: https://github.com/akv2011/Auto_Refactor_codebase_MCP

## Support

---

For issues, questions, or contributions:

- **GitHub Issues**: https://github.com/akv2011/Auto_Refactor_codebase_MCP/issues## Acknowledgments

- **Repository**: https://github.com/akv2011/Auto_Refactor_codebase_MCP

- **Documentation**: See `docs/` directoryBuilt with:

- Model Context Protocol (MCP) by Anthropic

---- FastMCP framework

- Google Gemini AI

## Acknowledgments- Tree-sitter for code parsing

- Radon for complexity metrics

Built with:
- Model Context Protocol (MCP) by Anthropic
- FastMCP framework
- Google Gemini AI
- Tree-sitter for code parsing
- Radon for complexity metrics
