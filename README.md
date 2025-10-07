# Auto-Refactor MCP Server

**Intelligent Automated Code Refactoring powered by AI**

An advanced Model Context Protocol (MCP) server that provides AI-powered code refactoring capabilities with automatic testing, Git-based rollback, and intelligent suggestion management.

---

## Table of Contents

- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
  - [VS Code Setup](#vs-code-setup)
  - [Cursor Setup](#cursor-setup)
  - [Claude Desktop Setup](#claude-desktop-setup)
- [Environment Variables](#-environment-variables)
- [Available Tools](#-available-tools)
- [Usage Examples](#-usage-examples)
- [Architecture](#-architecture)
- [Development](#-development)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## Features

- **AI-Powered Suggestions**: Generate intelligent refactoring suggestions using Google Gemini AI
- **Multiple Refactoring Strategies**: Support for auto, split, extract, and composition strategies
- **Safe Execution**: Automatic Git backup, test running, and rollback on failure
- **Suggestion Management**: Cache, review, approve, or reject refactoring suggestions
- **Database Refactoring**: Specialized tools for splitting migrations and extracting SQL queries
- **Multi-Language Support**: Python, JavaScript, TypeScript support via tree-sitter
- **Code Metrics**: Built-in complexity analysis and LOC calculation
- **Interactive Workflow**: Review suggestions before applying changes

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+**: Required for running the server
- **uv**: Fast Python package installer ([install instructions](https://github.com/astral-sh/uv))
- **Git**: Required for automatic backup and rollback features
- **Google API Key**: For AI-powered refactoring suggestions (Gemini)
- **MCP-Compatible Client**: VS Code, Cursor, Claude Desktop, or other MCP clients

### Installing uv (if not already installed)

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Using pip
pip install uv
```

---

## Installation

1. **Clone the repository**:

```bash
git clone https://github.com/akv2011/Auto_Refactor_codebase_MCP.git
cd Auto_Refactor_codebase_MCP
```

2. **Install dependencies using uv**:

```bash
uv sync
```

This will create a virtual environment and install all required dependencies from `pyproject.toml`.

3. **Verify installation**:

```bash
uv run refactor_server.py --help
```

---

## Configuration

The Auto-Refactor MCP server can be configured in multiple MCP clients. Below are setup instructions for the most popular ones.

### VS Code Setup

1. **Install the MCP Extension** (if not already installed):
   - Open VS Code
   - Go to Extensions (Ctrl+Shift+X)
   - Search for "Model Context Protocol"
   - Install the extension

2. **Open MCP Settings**:
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "MCP: Edit Configuration"
   - Select the command

3. **Add the Auto-Refactor server configuration**:

   Add the following JSON to your MCP configuration file (`mcp.json`):

```json
{
  "mcpServers": {
    "auto-refactor": {
      "command": "uv",
      "args": [
        "--directory",
        "C:/Users/arunk/Auto_refactor_MCP",
        "run",
        "refactor_server.py"
      ],
      "type": "stdio",
      "env": {
        "GOOGLE_API_KEY": "your-google-api-key-here"
      }
    }
  }
}
```

**Important**: Replace the following values:
- `C:/Users/arunk/Auto_refactor_MCP` → Your actual project path
- `your-google-api-key-here` → Your Google API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

4. **Reload VS Code**:
   - Press `Ctrl+Shift+P`
   - Type "Developer: Reload Window"
   - Select the command

5. **Verify the connection**:
   - Open the MCP panel
   - You should see "auto-refactor" listed as a connected server
   - Try the `hello_refactor` tool to test connectivity

---

### Cursor Setup

Cursor uses the same MCP configuration format as VS Code.

1. **Locate Cursor's configuration directory**:
   - **Windows**: `%APPDATA%\Cursor\User\`
   - **macOS**: `~/Library/Application Support/Cursor/User/`
   - **Linux**: `~/.config/Cursor/User/`

2. **Create or edit `mcp.json`**:

   Navigate to the configuration directory and create/edit `mcp.json`:

```json
{
  "mcpServers": {
    "auto-refactor": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/Auto_refactor_MCP",
        "run",
        "refactor_server.py"
      ],
      "type": "stdio",
      "env": {
        "GOOGLE_API_KEY": "your-google-api-key-here"
      }
    }
  }
}
```

**Path formats**:
- **Windows**: `C:/Users/YourName/Auto_refactor_MCP` (use forward slashes)
- **macOS/Linux**: `/Users/YourName/Auto_refactor_MCP`

3. **Restart Cursor** completely (quit and reopen)

4. **Test the connection**:
   - Open Cursor's AI chat
   - Ask it to use the `hello_refactor` tool
   - You should receive a greeting from the Auto-Refactor server

---

### Claude Desktop Setup

1. **Locate Claude Desktop's configuration**:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. **Edit the configuration file**:

```json
{
  "mcpServers": {
    "auto-refactor": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/Auto_refactor_MCP",
        "run",
        "refactor_server.py"
      ],
      "env": {
        "GOOGLE_API_KEY": "your-google-api-key-here"
      }
    }
  }
}
```

3. **Restart Claude Desktop**

4. **Verify in Claude**:
   - Start a new conversation
   - Ask Claude: "What MCP servers are available?"
   - You should see `auto-refactor` in the list

---

### Other MCP Clients

For other MCP-compatible clients, use this generic configuration:

```json
{
  "command": "uv",
  "args": [
    "--directory",
    "<absolute-path-to-project>",
    "run",
    "refactor_server.py"
  ],
  "type": "stdio",
  "env": {
    "GOOGLE_API_KEY": "<your-api-key>"
  }
}
```

Refer to your client's documentation for specific configuration details.

---

## Environment Variables

The server requires the following environment variables:

| Variable | Required | Description | How to Obtain |
|----------|----------|-------------|---------------|
| `GOOGLE_API_KEY` | Yes | Google Gemini API key for AI suggestions | [Google AI Studio](https://makersuite.google.com/app/apikey) |
| `OPENAI_API_KEY` | Optional | OpenAI API key (future support) | [OpenAI Platform](https://platform.openai.com/api-keys) |
| `ANTHROPIC_API_KEY` | Optional | Anthropic API key (future support) | [Anthropic Console](https://console.anthropic.com/) |

### Getting a Google API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key
5. Add it to your MCP configuration under the `env` section

**Security Note**: Never commit API keys to version control. Use environment variables or secure secret management.

---

## Available Tools

The Auto-Refactor MCP server provides the following tools:

### 1. `hello_refactor`
Test tool to verify server connectivity.

**Parameters**: None

**Returns**: Greeting message

**Example**:
```
"Hello from Auto-Refactor MCP Server! Ready to refactor your code."
```

---

### 2. `suggest_refactoring`
Generate AI-powered refactoring suggestions for a file.

**Parameters**:
- `file_path` (string, required): Absolute path to the source file
- `strategy` (string, optional): Refactoring strategy
  - `"auto"` (default): Automatically determine best approach
  - `"split"`: Focus on splitting large functions/classes
  - `"extract"`: Focus on extracting reusable code
  - `"composition"`: Focus on improving object composition

**Returns**: JSON with suggestions, diffs, and a suggestion_id for later approval

**Example**:
```json
{
  "file_path": "/path/to/file.py",
  "language": "python",
  "strategy_used": "auto",
  "suggestion_id": "abc123",
  "suggestions": [
    {
      "title": "Extract database logic to service layer",
      "description": "Move complex database queries...",
      "strategy": "extract",
      "priority": "high",
      "diff": "--- a/file.py\n+++ b/file.py\n..."
    }
  ]
}
```

---

### 3. `execute_refactoring`
Execute a refactoring with automatic testing and rollback.

**Parameters**:
- `file_path` (string, required): Path to the file
- `suggestion_json` (string, required): JSON from `suggest_refactoring`
- `dry_run` (boolean, optional): If true, preview without applying (default: true)

**Returns**: Execution report with status, test results, and rollback info

**Features**:
- Creates Git backup branch automatically
- Applies the refactoring changes
- Runs tests automatically
- Rolls back changes if tests fail
- Safe and reversible

---

### 4. `approve_suggestion`
Approve and execute a cached suggestion (recommended workflow).

**Parameters**:
- `suggestion_id` (string, required): ID from `suggest_refactoring`
- `dry_run` (boolean, optional): Preview mode (default: false)

**Returns**: Execution report

---

### 5. `list_suggestions`
List cached refactoring suggestions.

**Parameters**:
- `status` (string, optional): Filter by status (pending, approved, rejected, executed)
- `file_path` (string, optional): Filter by file
- `limit` (integer, optional): Max results (default: 10)

**Returns**: List of suggestions with IDs and summaries

---

### 6. `get_suggestion`
Get detailed information about a specific suggestion.

**Parameters**:
- `suggestion_id` (string, required): Suggestion ID

**Returns**: Full suggestion details including all diffs

---

### 7. `reject_suggestion`
Reject a cached suggestion.

**Parameters**:
- `suggestion_id` (string, required): Suggestion ID
- `reason` (string, optional): Rejection reason

**Returns**: Confirmation message

---

### 8. `clear_suggestions`
Clear suggestions from cache.

**Parameters**:
- `status` (string, optional): Only clear suggestions with this status
- `older_than_days` (integer, optional): Only clear old suggestions

**Returns**: Number of cleared suggestions

---

### 9. `get_refactoring_status`
Get history of refactoring operations.

**Parameters**:
- `project_root` (string, required): Project directory path
- `limit` (integer, optional): Max operations to return (default: 10)
- `include_rolled_back` (boolean, optional): Include rolled-back operations

**Returns**: Operation history with timestamps, status, and file changes

---

### 10. `refactor_database`
Specialized database refactoring operations.

**Parameters**:
- `project_root` (string, required): Project path
- `operation` (string, required): `"split_migration"` or `"extract_query"`
- `file_path` (string, required): Migration/source file path
- `max_operations_per_file` (integer, optional): For split operations
- `query_identifier` (string, optional): For query extraction
- `view_name` (string, optional): Custom view name

**Returns**: Operation results with created files and rollback scripts

---

## Usage Examples

### Example 1: Basic Refactoring Workflow

```typescript
// 1. Generate suggestions
const suggestions = await use_mcp_tool("auto-refactor", "suggest_refactoring", {
  file_path: "/path/to/my_module.py",
  strategy: "auto"
});

// 2. Review the suggestions (they're cached automatically)

// 3. Approve and execute
const result = await use_mcp_tool("auto-refactor", "approve_suggestion", {
  suggestion_id: suggestions.suggestion_id,
  dry_run: false
});

// 4. Check if it was successful
if (result.status === "success") {
  console.log("Refactoring applied successfully!");
} else if (result.status === "rolled_back") {
  console.log("Tests failed, changes rolled back automatically");
}
```

### Example 2: Database Migration Splitting

```typescript
const result = await use_mcp_tool("auto-refactor", "refactor_database", {
  project_root: "/path/to/django_project",
  operation: "split_migration",
  file_path: "app/migrations/0042_large_migration.py",
  max_operations_per_file: 3
});

console.log(`Migration split into ${result.split_files.length} files`);
```

### Example 3: Review Pending Suggestions

```typescript
// List all pending suggestions
const pending = await use_mcp_tool("auto-refactor", "list_suggestions", {
  status: "pending",
  limit: 20
});

// Get details for a specific suggestion
const details = await use_mcp_tool("auto-refactor", "get_suggestion", {
  suggestion_id: "abc123"
});

// Reject if not needed
await use_mcp_tool("auto-refactor", "reject_suggestion", {
  suggestion_id: "abc123",
  reason: "Not applicable for this use case"
});
```

---

## Architecture

### Core Components

```
Auto-Refactor MCP Server
├── refactor_server.py          # MCP server entry point
├── src/
│   ├── ai_suggestion_service.py    # AI integration (Gemini)
│   ├── refactoring_engine.py       # Core refactoring logic
│   ├── suggestion_manager.py       # Suggestion caching & workflow
│   ├── git_manager.py              # Git operations & backup
│   ├── test_runner.py              # Automatic test execution
│   ├── rollback_manager.py         # Operation rollback
│   ├── metrics_engine.py           # Code complexity analysis
│   ├── database_refactoring.py     # Database-specific operations
│   ├── ast_wrapper.py              # AST manipulation
│   └── parser_factory.py           # Multi-language parsing
├── tests/                          # Comprehensive test suite
└── pyproject.toml                  # Dependencies & configuration
```

### Key Technologies

- **FastMCP**: Modern Python framework for MCP servers
- **Google Gemini**: AI-powered suggestion generation
- **Tree-sitter**: Multi-language AST parsing
- **GitPython**: Git integration for safe operations
- **Pydantic**: Data validation and serialization
- **pytest**: Testing framework

---

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_refactoring_engine.py

# Run with verbose output
uv run pytest -v
```

### Code Quality

```bash
# Format code with black
uv run black src/ tests/

# Lint with ruff
uv run ruff check src/ tests/

# Type checking with mypy
uv run mypy src/
```

### Adding New Refactoring Operations

1. Add the handler in `refactoring_engine.py`
2. Register in `_operation_handlers` dict
3. Create a new MCP tool in `refactor_server.py`
4. Add tests in `tests/`
5. Update documentation

---

## Testing

The project includes a comprehensive test suite with 100+ tests covering:

- AI suggestion generation
- Refactoring engine operations
- Git backup and rollback
- Suggestion management workflow
- Database refactoring
- AST manipulation
- Multi-language parsing

**Test Coverage**: >85%

Run tests before submitting contributions:

```bash
uv run pytest -v
```

---

## Troubleshooting

### Common Issues

#### 1. Server not connecting in VS Code/Cursor

**Problem**: MCP server shows as disconnected

**Solutions**:
- Verify the absolute path in `mcp.json` is correct
- Ensure `uv` is installed and in PATH
- Check that `GOOGLE_API_KEY` is set correctly
- Restart the editor completely (quit and reopen)
- Check editor logs for error messages

#### 2. "API Key not configured" error

**Problem**: Tools fail with API key errors

**Solutions**:
- Verify `GOOGLE_API_KEY` is set in the `env` section of `mcp.json`
- Get a valid key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- Ensure no extra spaces or quotes around the key

#### 3. Refactoring fails with Git errors

**Problem**: "Not a Git repository" error

**Solutions**:
- Ensure your project directory is a Git repository
- Run `git init` in your project root if needed
- Check that you have proper Git permissions

#### 4. Tests fail after refactoring

**Problem**: Changes are rolled back automatically

**Solutions**:
- Review test output in the execution result
- Fix failing tests before re-applying refactoring
- Use `dry_run: true` to preview changes first
- Check that test command in config is correct

#### 5. Import errors or module not found

**Problem**: Python modules not found when running server

**Solutions**:
- Run `uv sync` to install all dependencies
- Verify you're using Python 3.10 or higher
- Check that tree-sitter is properly installed

### Debug Mode

Enable detailed logging by setting environment variable:

```json
{
  "env": {
    "GOOGLE_API_KEY": "...",
    "DEBUG": "true",
    "LOG_LEVEL": "DEBUG"
  }
}
```

### Getting Help

If you encounter issues not covered here:

1. Check the [GitHub Issues](https://github.com/akv2011/Auto_Refactor_codebase_MCP/issues)
2. Review MCP client logs
3. Enable debug mode and capture error messages
4. Open a new issue with:
   - Your configuration (without API keys)
   - Error messages
   - Steps to reproduce

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Add tests** for new functionality
5. **Run tests**: `uv run pytest`
6. **Format code**: `uv run black src/ tests/`
7. **Commit changes**: `git commit -m 'Add amazing feature'`
8. **Push to branch**: `git push origin feature/amazing-feature`
9. **Open a Pull Request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Auto_Refactor_codebase_MCP.git
cd Auto_Refactor_codebase_MCP

# Install development dependencies
uv sync --dev

# Install pre-commit hooks (optional)
uv run pre-commit install
```

### Contribution Ideas

- [ ] Add support for more programming languages (Java, Go, Rust)
- [ ] Implement additional refactoring strategies
- [ ] Improve AI prompt engineering for better suggestions
- [ ] Add support for OpenAI and Anthropic models
- [ ] Create VS Code extension wrapper
- [ ] Add web UI for suggestion review
- [ ] Improve test detection and execution
- [ ] Add refactoring templates/presets

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Google Gemini** for powerful AI capabilities
- **FastMCP** for excellent MCP server framework
- **Tree-sitter** for robust multi-language parsing
- **Anthropic** for the Model Context Protocol specification
- The open-source community for inspiration and tools

---

## Contact

**Author**: Arun Kumar  
**GitHub**: [@akv2011](https://github.com/akv2011)  
**Project**: [Auto_Refactor_codebase_MCP](https://github.com/akv2011/Auto_Refactor_codebase_MCP)

---

## Quick Start Checklist

- [ ] Install Python 3.10+
- [ ] Install `uv` package manager
- [ ] Clone the repository
- [ ] Run `uv sync` to install dependencies
- [ ] Get Google API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- [ ] Configure MCP client (VS Code/Cursor/Claude Desktop)
- [ ] Add absolute path to project in `mcp.json`
- [ ] Add `GOOGLE_API_KEY` to env section
- [ ] Restart your MCP client
- [ ] Test with `hello_refactor` tool
- [ ] Start refactoring!

---

**Happy Refactoring!**
