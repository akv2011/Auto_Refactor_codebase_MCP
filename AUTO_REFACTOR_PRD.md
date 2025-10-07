# TaskMaster MCP Server - Product Requirements Document

## 1. Executive Summary

**Product Name:** TaskMaster MCP Server  
**Version:** 1.0.0  
**Date:** October 5, 2025  
**Owner:** Arun Kumar

### Overview
TaskMaster is an intelligent MCP (Model Context Protocol) server that provides automated code refactoring capabilities. It monitors codebases, identifies files exceeding complexity thresholds (e.g., 1500+ lines), and performs intelligent refactoring operations to maintain code quality and maintainability.

### Target Users
- Software developers working on large codebases
- Development teams maintaining legacy systems
- DevOps engineers managing code quality
- Technical leads enforcing code standards

---

## 2. Problem Statement

### Current Pain Points
1. **Large Files**: Files exceeding 1500 lines become difficult to maintain, test, and understand
2. **Manual Refactoring**: Developers spend significant time manually splitting and refactoring large files
3. **Consistency**: Inconsistent refactoring approaches across team members
4. **Code Debt**: Technical debt accumulates as files grow without regular refactoring
5. **Database Migrations**: Complex database files require careful refactoring to maintain data integrity

### Impact
- Reduced developer productivity (20-30% time spent on manual refactoring)
- Increased bug rates in large files
- Slower onboarding for new team members
- Higher maintenance costs

---

## 3. Goals & Objectives

### Primary Goals
1. **Automated Detection**: Automatically identify files exceeding complexity thresholds
2. **Intelligent Refactoring**: Provide AI-powered refactoring suggestions and execution
3. **Safe Transformations**: Ensure refactoring maintains functionality and tests
4. **Database Safety**: Special handling for database migrations and schema files
5. **Developer Control**: Allow developers to review and approve refactoring actions

### Success Metrics
- Reduce average file size by 40%
- Decrease time spent on manual refactoring by 60%
- Maintain 100% test pass rate after refactoring
- Zero data loss in database refactoring operations
- Developer satisfaction score > 8/10

---

## 4. Features & Requirements

### 4.1 Core Features

#### Feature 1: File Analysis & Detection
**Priority:** P0 (Must Have)

**Description:** Scan codebase and identify files requiring refactoring

**Requirements:**
- Monitor specified directories for file changes
- Calculate file metrics (lines of code, cyclomatic complexity, function count)
- Identify files exceeding configurable thresholds:
  - Line count (default: 1500 lines)
  - Function/method count (default: 50)
  - Cyclomatic complexity (default: 15)
  - Class size (default: 500 lines)
- Support multiple languages: Python, JavaScript, TypeScript, Java, C#, SQL
- Generate detailed analysis reports

**Acceptance Criteria:**
- Successfully scan directories up to 10,000 files
- Accurate line counting (±1% margin of error)
- Analysis completes within 30 seconds for 1,000 files
- Support ignore patterns (.gitignore, .taskmaster-ignore)

---

#### Feature 2: Intelligent Refactoring Suggestions
**Priority:** P0 (Must Have)

**Description:** Generate AI-powered refactoring recommendations

**Requirements:**
- Analyze code structure and identify refactoring opportunities:
  - Extract large functions into smaller functions
  - Split large classes into multiple classes
  - Separate concerns (UI, business logic, data access)
  - Extract utility functions
  - Create facade patterns for complex modules
- Provide multiple refactoring strategies per file
- Rank suggestions by impact and safety level
- Generate preview diffs for each suggestion
- Explain reasoning behind each suggestion

**Acceptance Criteria:**
- Generate at least 3 different refactoring strategies per file
- 90% of suggestions are syntactically valid
- Suggestions maintain existing API contracts
- Clear explanation with code examples

---

#### Feature 3: Automated Refactoring Execution
**Priority:** P0 (Must Have)

**Description:** Execute approved refactoring operations safely

**Requirements:**
- Create backup branches before refactoring
- Execute refactoring transformations:
  - File splitting with proper imports
  - Function extraction with parameter handling
  - Class decomposition with inheritance/composition
  - Module reorganization with re-exports
- Maintain import relationships
- Update all references across codebase
- Generate migration guide for breaking changes
- Run tests after refactoring
- Rollback on test failures

**Acceptance Criteria:**
- 100% of imports remain valid after refactoring
- All existing tests pass after refactoring
- Automatic rollback on any failure
- Complete operation log for audit trail

---

#### Feature 4: Database Refactoring
**Priority:** P1 (Should Have)

**Description:** Specialized refactoring for database files and migrations

**Requirements:**
- Detect database-related files:
  - SQL migration files
  - ORM models (SQLAlchemy, Django, Entity Framework)
  - Stored procedures
  - Database schema files
- Split large migrations into smaller, atomic migrations
- Extract complex queries into views or stored procedures
- Normalize large tables (suggest splitting strategies)
- Generate rollback scripts
- Validate referential integrity
- Create data migration scripts

**Safety Features:**
- Dry-run mode for all database operations
- Backup database before execution
- Transaction-based migrations
- Integrity checks pre and post migration

**Acceptance Criteria:**
- Zero data loss in refactoring operations
- All foreign key relationships maintained
- Rollback scripts generated for every migration
- Performance impact analysis provided

---

#### Feature 5: Interactive Review & Approval
**Priority:** P0 (Must Have)

**Description:** Allow developers to review and approve refactoring actions

**Requirements:**
- Present refactoring suggestions in readable format
- Show side-by-side diffs
- Allow developers to:
  - Approve suggestions
  - Reject suggestions
  - Modify suggestions
  - Request alternative strategies
- Save approval history
- Support batch approvals for trusted patterns

**Acceptance Criteria:**
- Clear, readable diff presentation
- Response time < 2 seconds for approval actions
- Support keyboard shortcuts for quick review
- Undo/redo functionality

---

#### Feature 6: Configuration & Customization
**Priority:** P1 (Should Have)

**Description:** Flexible configuration system

**Requirements:**
- Configuration file (`.taskmaster.json`):
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
    "refactoringStrategies": {
      "preferComposition": true,
      "extractUtilities": true,
      "maintainNamespaces": true
    },
    "safety": {
      "requireTests": true,
      "createBackups": true,
      "dryRunFirst": true
    }
  }
  ```
- Per-project and global configurations
- Override thresholds per directory
- Custom refactoring rules

**Acceptance Criteria:**
- Configuration changes take effect immediately
- Invalid configurations show clear error messages
- Support for JSON Schema validation

---

### 4.2 MCP Tools

#### Tool 1: `analyze_codebase`
```python
@mcp.tool()
async def analyze_codebase(
    directory: str,
    threshold_lines: int = 1500,
    include_patterns: list[str] = None,
    exclude_patterns: list[str] = None
) -> str:
    """
    Analyze codebase and identify files requiring refactoring.
    
    Args:
        directory: Root directory to analyze
        threshold_lines: Maximum lines per file (default: 1500)
        include_patterns: File patterns to include (e.g., ["*.py", "*.js"])
        exclude_patterns: Patterns to exclude (e.g., ["**/test/**"])
    
    Returns:
        JSON report with files exceeding thresholds and metrics
    """
```

#### Tool 2: `suggest_refactoring`
```python
@mcp.tool()
async def suggest_refactoring(
    file_path: str,
    strategy: str = "auto"
) -> str:
    """
    Generate refactoring suggestions for a specific file.
    
    Args:
        file_path: Path to file requiring refactoring
        strategy: Refactoring strategy ("auto", "split", "extract", "composition")
    
    Returns:
        List of refactoring suggestions with diffs and explanations
    """
```

#### Tool 3: `execute_refactoring`
```python
@mcp.tool()
async def execute_refactoring(
    file_path: str,
    suggestion_id: str,
    dry_run: bool = True
) -> str:
    """
    Execute approved refactoring operation.
    
    Args:
        file_path: Path to file to refactor
        suggestion_id: ID of approved suggestion
        dry_run: If True, show changes without applying (default: True)
    
    Returns:
        Status report with changes applied and test results
    """
```

#### Tool 4: `refactor_database`
```python
@mcp.tool()
async def refactor_database(
    file_path: str,
    operation: str,
    target_size: int = 500
) -> str:
    """
    Refactor database migration or schema file.
    
    Args:
        file_path: Path to database file
        operation: "split_migration", "extract_query", "normalize_table"
        target_size: Target lines per file (default: 500)
    
    Returns:
        Refactoring plan with rollback scripts
    """
```

#### Tool 5: `get_refactoring_status`
```python
@mcp.tool()
async def get_refactoring_status(
    project_directory: str
) -> str:
    """
    Get status of ongoing and completed refactoring operations.
    
    Args:
        project_directory: Project root directory
    
    Returns:
        Status report with progress and history
    """
```

#### Tool 6: `rollback_refactoring`
```python
@mcp.tool()
async def rollback_refactoring(
    operation_id: str
) -> str:
    """
    Rollback a completed refactoring operation.
    
    Args:
        operation_id: ID of operation to rollback
    
    Returns:
        Rollback status and restored files
    """
```

---

## 5. Technical Architecture

### 5.1 Technology Stack
- **Language:** Python 3.10+
- **Framework:** FastMCP (Model Context Protocol)
- **Code Analysis:** 
  - `ast` (Python AST parsing)
  - `tree-sitter` (multi-language parsing)
  - `radon` (complexity metrics)
- **AI Integration:**
  - OpenAI GPT-4 (refactoring suggestions)
  - Claude (code analysis)
- **Testing:** `pytest`, `coverage`
- **Version Control:** `gitpython`

### 5.2 System Components

```
┌─────────────────────────────────────────────┐
│         TaskMaster MCP Server               │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐     ┌──────────────┐    │
│  │   File       │     │   Code       │    │
│  │   Scanner    │────▶│   Analyzer   │    │
│  └──────────────┘     └──────────────┘    │
│         │                     │            │
│         ▼                     ▼            │
│  ┌──────────────┐     ┌──────────────┐    │
│  │   Metrics    │     │   AI         │    │
│  │   Calculator │     │   Suggester  │    │
│  └──────────────┘     └──────────────┘    │
│         │                     │            │
│         └─────────┬───────────┘            │
│                   ▼                        │
│         ┌──────────────────┐               │
│         │   Refactoring    │               │
│         │   Engine         │               │
│         └──────────────────┘               │
│                   │                        │
│         ┌─────────┴─────────┐              │
│         ▼                   ▼              │
│  ┌──────────────┐    ┌──────────────┐     │
│  │   Code       │    │   Database   │     │
│  │   Refactor   │    │   Refactor   │     │
│  └──────────────┘    └──────────────┘     │
│         │                   │              │
│         └─────────┬─────────┘              │
│                   ▼                        │
│         ┌──────────────────┐               │
│         │   Test Runner &  │               │
│         │   Validator      │               │
│         └──────────────────┘               │
└─────────────────────────────────────────────┘
```

### 5.3 Data Flow
1. **Scan Phase:** File Scanner discovers files
2. **Analysis Phase:** Code Analyzer calculates metrics
3. **Detection Phase:** Metrics Calculator identifies violations
4. **Suggestion Phase:** AI Suggester generates recommendations
5. **Review Phase:** Developer reviews via MCP client
6. **Execution Phase:** Refactoring Engine applies changes
7. **Validation Phase:** Test Runner validates changes
8. **Completion Phase:** Results logged and reported

---

## 6. Implementation Phases

### Phase 1: MVP (Weeks 1-3)
**Deliverables:**
- Basic file scanning and line counting
- Simple refactoring: split files by functions
- Python language support only
- Manual approval workflow
- Basic MCP tools: `analyze_codebase`, `suggest_refactoring`, `execute_refactoring`

**Success Criteria:**
- Can analyze Python projects up to 1,000 files
- Successfully split files > 1500 lines
- Zero breaking changes after refactoring

### Phase 2: Enhanced Analysis (Weeks 4-6)
**Deliverables:**
- Complexity metrics (cyclomatic, cognitive)
- AI-powered suggestions using GPT-4
- JavaScript/TypeScript support
- Interactive review interface improvements
- Add tools: `get_refactoring_status`, `rollback_refactoring`

**Success Criteria:**
- 90% accuracy in refactoring suggestions
- Support 3+ languages
- < 5 minute analysis time for 5,000 files

### Phase 3: Database Support (Weeks 7-9)
**Deliverables:**
- Database file detection
- Migration splitting logic
- SQL parsing and analysis
- Rollback script generation
- Add tool: `refactor_database`

**Success Criteria:**
- Zero data loss in 100 test migrations
- Support PostgreSQL, MySQL, SQLite
- Generate valid rollback scripts

### Phase 4: Production Ready (Weeks 10-12)
**Deliverables:**
- Configuration system
- Batch processing
- Performance optimizations
- Comprehensive documentation
- CI/CD integration examples
- VSCode extension integration

**Success Criteria:**
- Process 10,000+ file projects
- < 1 second response time for MCP tools
- 100% documentation coverage

---

## 7. Security & Safety

### Safety Mechanisms
1. **Backup Creation:** Automatic Git branch creation before refactoring
2. **Dry Run Mode:** Preview all changes before execution
3. **Test Validation:** Run test suite after refactoring
4. **Rollback Support:** One-click rollback for any operation
5. **Audit Logging:** Complete log of all operations
6. **Access Control:** Configurable permissions for destructive operations

### Risk Mitigation
- **Data Loss:** Multiple backup layers (Git, file snapshots)
- **Breaking Changes:** Mandatory test runs, gradual rollout
- **Performance:** Rate limiting, resource quotas
- **Security:** Input validation, sandboxed execution

---

## 8. User Experience

### Developer Workflow

1. **Setup:**
```bash
# Install TaskMaster
uv pip install taskmaster-mcp-server

# Configure in mcp.json
{
  "taskmaster": {
    "command": "uv",
    "args": ["run", "taskmaster.py"],
    "type": "stdio"
  }
}
```

2. **Analyze Project:**
```
Developer: "Analyze my codebase for files that need refactoring"
TaskMaster: "Found 15 files exceeding 1500 lines:
1. src/database/migrations.py (2,345 lines)
2. src/api/handlers.py (1,876 lines)
..."
```

3. **Get Suggestions:**
```
Developer: "Suggest refactoring for database/migrations.py"
TaskMaster: "I recommend 3 strategies:
1. Split by migration timestamp (creates 8 files)
2. Extract common utilities (reduces by 30%)
3. Combine: Split + Extract (optimal)
..."
```

4. **Execute:**
```
Developer: "Execute strategy 3 for migrations.py"
TaskMaster: "Starting refactoring...
✓ Created backup branch: refactor/migrations-20251005
✓ Split into 8 migration files
✓ Extracted 12 utility functions
✓ Updated 34 import statements
✓ Running tests... [PASSED]
✓ Refactoring complete!"
```

---

## 9. Success Metrics & KPIs

### Quantitative Metrics
- **Code Quality:**
  - Average file size reduced by 40%
  - Cyclomatic complexity reduced by 30%
  - Test coverage maintained at 100%
  
- **Developer Productivity:**
  - 60% reduction in manual refactoring time
  - 50% faster onboarding for new developers
  - 40% fewer bugs in refactored code

- **System Performance:**
  - < 30 seconds to analyze 1,000 files
  - < 2 seconds MCP tool response time
  - 99.9% uptime

### Qualitative Metrics
- Developer satisfaction: > 8/10
- Code review velocity improved
- Reduced cognitive load
- Improved code maintainability scores

---

## 10. Future Enhancements (Post-MVP)

### Phase 5 & Beyond
1. **AI Code Generation:** Generate new utility classes/functions
2. **Pattern Detection:** Identify and apply design patterns
3. **Cross-File Refactoring:** Refactor across multiple related files
4. **Performance Optimization:** Suggest performance improvements
5. **Documentation Generation:** Auto-generate documentation
6. **Microservices Extraction:** Suggest service boundaries
7. **API Versioning:** Manage breaking changes with versioning
8. **Team Collaboration:** Multi-developer approval workflows
9. **IDE Integration:** Direct IDE plugins (VSCode, IntelliJ)
10. **Cloud Integration:** Cloud-based analysis for large projects

---

## 11. Dependencies & Resources

### Team Requirements
- 1 Senior Python Developer (FastMCP, AST)
- 1 AI/ML Engineer (LLM integration)
- 1 DevOps Engineer (deployment, CI/CD)
- 1 QA Engineer (testing, validation)

### Infrastructure
- Development environments (local + cloud)
- CI/CD pipeline (GitHub Actions)
- Test databases (PostgreSQL, MySQL)
- AI API access (OpenAI, Anthropic)

### Third-Party Services
- OpenAI API (GPT-4)
- Anthropic API (Claude)
- GitHub API (version control)

---

## 12. Open Questions

1. Should we support real-time monitoring vs. on-demand analysis?
2. What's the maximum project size we should support (100k files)?
3. Should we provide a web UI in addition to MCP?
4. How do we handle custom refactoring rules per team?
5. What's the pricing model (free, freemium, enterprise)?
6. Should we support monorepo-specific features?
7. Integration with code review tools (GitHub PR, GitLab MR)?

---

## 13. Appendix

### A. Example Configuration File
```json
{
  "version": "1.0",
  "name": "TaskMaster Configuration",
  "thresholds": {
    "maxLines": 1500,
    "maxFunctions": 50,
    "maxComplexity": 15,
    "maxClassSize": 500,
    "maxMethodLength": 100
  },
  "languages": {
    "python": {
      "enabled": true,
      "parser": "ast",
      "testCommand": "pytest"
    },
    "javascript": {
      "enabled": true,
      "parser": "tree-sitter",
      "testCommand": "npm test"
    },
    "typescript": {
      "enabled": true,
      "parser": "tree-sitter",
      "testCommand": "npm test"
    }
  },
  "excludePatterns": [
    "**/node_modules/**",
    "**/venv/**",
    "**/dist/**",
    "**/build/**",
    "**/__pycache__/**",
    "**/test/**",
    "**/*.test.js",
    "**/*.spec.ts"
  ],
  "refactoringStrategies": {
    "preferComposition": true,
    "extractUtilities": true,
    "maintainNamespaces": true,
    "preserveComments": true,
    "updateImports": true
  },
  "safety": {
    "requireTests": true,
    "createBackups": true,
    "dryRunFirst": true,
    "requireApproval": true,
    "maxFilesPerOperation": 10
  },
  "ai": {
    "provider": "openai",
    "model": "gpt-4",
    "maxTokens": 4000,
    "temperature": 0.2
  }
}
```

### B. Sample Analysis Report
```json
{
  "timestamp": "2025-10-05T10:30:00Z",
  "projectPath": "/path/to/project",
  "summary": {
    "totalFiles": 1247,
    "filesAnalyzed": 1247,
    "filesExceedingThreshold": 15,
    "totalLines": 123456,
    "averageFileSize": 99
  },
  "violations": [
    {
      "file": "src/database/migrations.py",
      "lines": 2345,
      "functions": 67,
      "complexity": 23,
      "severity": "high",
      "recommendations": [
        "Split by migration timestamp",
        "Extract utility functions",
        "Create migration base class"
      ]
    }
  ]
}
```

---

## Document History
- **v1.0** - October 5, 2025 - Initial PRD created
- **Author:** Arun Kumar
- **Reviewers:** TBD
- **Status:** Draft
- **Next Review:** October 12, 2025
