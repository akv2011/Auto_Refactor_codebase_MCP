# Auto-Refactor MCP Server

🚀 **Intelligent Automated Code Refactoring**

Auto-Refactor is an MCP (Model Context Protocol) server that provides automated code refactoring capabilities. It monitors codebases, identifies files exceeding complexity thresholds, and performs intelligent refactoring operations to maintain code quality and maintainability.

## Features

- 🔍 **Automated Detection**: Identifies files exceeding complexity thresholds (lines, complexity, functions)
- 🤖 **AI-Powered Suggestions**: Generate intelligent refactoring strategies using GPT-4/Claude
- 🛡️ **Safe Execution**: Automatic backups, test validation, and rollback support
- 🗄️ **Database Refactoring**: Specialized handling for migrations and SQL files
- 🌐 **Multi-Language Support**: Python, JavaScript, TypeScript, Java, C#, SQL

## Installation

```bash
# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

## Quick Start

### 1. Add to MCP Configuration

Edit your `.vscode/mcp.json` or Claude Desktop config:

```json
{
  "servers": {
    "auto-refactor": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/refactor-server",
        "run",
        "refactor_server.py"
      ],
      "type": "stdio",
      "env": {
        "OPENAI_API_KEY": "your-openai-key",
        "ANTHROPIC_API_KEY": "your-anthropic-key"
      }
    }
  }
}
```

### 2. Test the Connection

```bash
# Run the server directly
uv run refactor_server.py
```

## MCP Tools

### `analyze_codebase`
Scan and identify files requiring refactoring based on complexity thresholds.

### `suggest_refactoring`
Generate AI-powered refactoring suggestions for specific files.

### `execute_refactoring`
Apply approved refactoring operations safely with automatic backups.

### `refactor_database`
Specialized refactoring for database migrations and schema files.

### `get_refactoring_status`
Track ongoing and completed refactoring operations.

### `rollback_refactoring`
Rollback a completed refactoring operation.

## Configuration

Create a `.taskmaster.json` in your project root:

```json
{
  "thresholds": {
    "maxLines": 1500,
    "maxFunctions": 50,
    "maxComplexity": 15,
    "maxClassSize": 500
  },
  "languages": ["python", "javascript", "typescript"],
  "excludePatterns": ["**/test/**", "**/vendor/**"],
  "safety": {
    "requireTests": true,
    "createBackups": true,
    "dryRunFirst": true
  }
}
```

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
black --check .

# Type checking
mypy src
```

### Project Structure

```
refactor-server/
├── src/                 # Core package
│   ├── __init__.py
│   ├── scanner.py       # File scanning
│   ├── analyzer.py      # Code analysis
│   ├── metrics.py       # Complexity metrics
│   ├── ai_suggester.py  # AI integration
│   ├── refactor.py      # Refactoring engine
│   └── database.py      # Database refactoring
├── tests/               # Test suite
├── refactor_server.py   # Main server entry point
├── pyproject.toml       # Dependencies
└── README.md           # This file
```

## Requirements

- Python 3.10+
- OpenAI API key (for GPT-4 suggestions)
- Anthropic API key (for Claude suggestions)

## License

MIT License

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub.

---

**Built with FastMCP** 🚀
