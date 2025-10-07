# Auto-Refactor MCP Server - Testing Guide

## 🚀 Quick Start Testing

### Step 1: Restart VS Code
After updating `.vscode/mcp.json`, restart VS Code to load the new MCP server configuration.

### Step 2: Verify Server is Running
Open the **MCP Output Panel** in VS Code to confirm the `auto-refactor` server started successfully.

---

## 📋 Test Prompts by Feature

### 1️⃣ Hello/Test Connection
**Prompt:**
```
Test the auto-refactor MCP server connection
```
**Expected:** Should return a hello message confirming the server is active.

---

### 2️⃣ Scan Files for Refactoring Candidates
**Prompt:**
```
Scan the src/ directory for files that need refactoring based on complexity thresholds
```
**Alternative:**
```
Use the scan_files tool to analyze my codebase and find files exceeding complexity limits
```
**Expected:** List of files with metrics (lines, functions, complexity) that exceed thresholds.

---

### 3️⃣ Get AI Refactoring Suggestions
**Prompt:**
```
Get refactoring suggestions for src/database_analyzer.py
```
**Alternative:**
```
Analyze src/rollback_manager.py and suggest refactoring strategies
```
**Expected:** AI-generated refactoring recommendations (extract function, split file, reduce complexity).

---

### 4️⃣ Execute Refactoring (Extract Function)
**Prompt:**
```
Extract the function starting at line 150 in src/database_refactoring.py into a new function called parse_sql_statements
```
**Alternative:**
```
Refactor src/config_loader.py by extracting lines 100-150 into a helper function
```
**Expected:** Refactored code with new function extracted, tests run, backup created.

---

### 5️⃣ Get Refactoring Status/History
**Prompt:**
```
Show me the recent refactoring operations history
```
**Alternative:**
```
What refactoring operations have been performed? Show the last 10
```
**Expected:** List of recent operations with timestamps, file paths, operation types, and status.

---

### 6️⃣ Rollback Refactoring
**Prompt:**
```
Rollback the last refactoring operation
```
**Alternative:**
```
Undo the refactoring with operation ID abc123
```
**Expected:** Restored original code, git branch reverted, confirmation message.

---

### 7️⃣ Database-Specific Refactoring

#### Split Large Migration
**Prompt:**
```
Split the Django migration file migrations/0005_large_migration.py because it's too complex
```
**Alternative:**
```
Break down the SQL migration file db/migrations/001_initial.sql into smaller parts
```
**Expected:** Multiple smaller migration files created, dependencies maintained.

#### Extract Query to View
**Prompt:**
```
Extract the SQL query in src/models/user.py lines 50-60 into a database view
```
**Alternative:**
```
Refactor the complex SELECT statement into a view called user_summary_view
```
**Expected:** View created, query replaced with view reference, rollback script generated.

---

### 8️⃣ Apply Suggestion by ID
**Prompt:**
```
Apply the refactoring suggestion with ID sug_123abc
```
**Expected:** Suggestion executed, code refactored, tests run.

---

### 9️⃣ List Available Suggestions
**Prompt:**
```
Show me all pending refactoring suggestions for this project
```
**Alternative:**
```
List all refactoring suggestions that haven't been applied yet
```
**Expected:** List of suggestions with IDs, file paths, strategies, and priorities.

---

### 🔟 Approve/Reject Suggestions
**Prompt:**
```
Approve the suggestion sug_456def
```
**Alternative:**
```
Reject suggestion sug_789ghi because the code is used in production
```
**Expected:** Suggestion status updated, ready for application or archived.

---

## 🎯 End-to-End Test Scenario

**Complete Workflow Prompt:**
```
I want to refactor my src/ directory:
1. First scan for files that need refactoring
2. Then get AI suggestions for the top 3 most complex files
3. Show me the suggestions and let me pick one to apply
4. Execute the chosen refactoring
5. Show me the operation history
```

---

## 🔧 Advanced Testing Prompts

### Test with Configuration
**Prompt:**
```
Scan files using these thresholds: max 500 lines, max 20 functions, max complexity 10
```

### Test Safety Features
**Prompt:**
```
Refactor src/metrics_engine.py but ensure tests pass before committing changes
```

### Test Git Integration
**Prompt:**
```
Create a backup branch before refactoring src/scanner.py
```

### Test Rollback
**Prompt:**
```
Something went wrong with the last refactoring - rollback to the previous version
```

---

## 🐛 Troubleshooting Test Prompts

### Check Server Status
**Prompt:**
```
Is the auto-refactor MCP server running? Show me its status
```

### Verify Tools Available
**Prompt:**
```
What tools are available from the auto-refactor server?
```

### Test Error Handling
**Prompt:**
```
Try to refactor a non-existent file: src/does_not_exist.py
```
**Expected:** Error message explaining file not found.

---

## 📊 Expected Response Patterns

### Successful Operation
```json
{
  "success": true,
  "operation_id": "op_abc123",
  "message": "Refactoring completed successfully",
  "details": {
    "file": "src/example.py",
    "operation": "extract_function",
    "backup_branch": "refactor-backup-20251008-120000"
  }
}
```

### Failed Operation
```json
{
  "success": false,
  "error": "Tests failed after refactoring",
  "message": "Rolled back changes automatically",
  "details": {
    "test_output": "..."
  }
}
```

---

## ✅ Verification Checklist

After each test, verify:
- [ ] Server responded without errors
- [ ] Response contains expected data
- [ ] Files were modified correctly (if applicable)
- [ ] Tests still pass: `python -m pytest tests/ -v`
- [ ] Git backup branch created (for refactoring operations)
- [ ] `.taskmaster/` directory contains operation history

---

## 🎓 Pro Tips

1. **Start Simple:** Test `hello_refactor` first to confirm server connectivity
2. **Check History:** Always review `get_refactoring_status` after operations
3. **Safety First:** Let the server run tests automatically - don't skip them
4. **Rollback Ready:** Keep operation IDs handy for quick rollbacks
5. **Use Dry Run:** For complex refactorings, ask for suggestions before applying

---

## 📝 Sample Test Session

```
You: "Test the auto-refactor server"
AI: "✅ Server is running - auto-refactor v0.1.0"

You: "Scan src/ directory for refactoring candidates"
AI: "Found 3 files exceeding thresholds:
     - src/database_refactoring.py (450 lines, complexity: 18)
     - src/codebase_analyzer.py (520 lines, 35 functions)
     - src/config_loader.py (380 lines, complexity: 16)"

You: "Get suggestions for src/database_refactoring.py"
AI: "Generated 3 refactoring suggestions:
     1. Extract _split_sql_statements into separate file
     2. Reduce cyclomatic complexity in split_migration
     3. Split class into DatabaseSQLRefactor and DatabaseDjangoRefactor"

You: "Apply suggestion 1"
AI: "✅ Extracted function successfully
     - Created: src/sql_splitter.py
     - Modified: src/database_refactoring.py
     - Tests: All passing ✅
     - Backup: refactor-backup-20251008-143022"

You: "Show refactoring history"
AI: "Recent operations:
     1. extract_function (2 min ago) - SUCCESS
     2. split_migration (1 hour ago) - SUCCESS
     3. reduce_complexity (2 hours ago) - ROLLED_BACK"
```

---

## 🚨 Important Notes

1. **API Keys Required:** Ensure OPENAI_API_KEY or ANTHROPIC_API_KEY is set in `.vscode/mcp.json`
2. **Git Repository:** Server works best in a git repository for backup/rollback features
3. **Test Suite:** Keep your test suite updated for automatic validation
4. **Backup First:** Server creates automatic backups, but manual git commits are recommended before major refactorings

---

Happy Testing! 🎉
