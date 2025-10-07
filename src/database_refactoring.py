"""
Database refactoring engine for specialized database operations.

This module provides functionality to refactor database-related code including
splitting migrations, extracting queries, and optimizing database schemas.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import re
import hashlib
from datetime import datetime


class DatabaseRefactoringError(Exception):
    """Base exception for database refactoring errors."""
    pass


class DatabaseRefactoringEngine:
    """
    Engine for performing database-specific refactoring operations.
    
    Supports operations like splitting migrations, extracting queries to views,
    and generating rollback scripts.
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize the database refactoring engine.
        
        Args:
            project_root: Path to the project root directory.
        """
        self.project_root = Path(project_root)
    
    def split_migration(
        self,
        migration_file: Path,
        max_operations_per_file: int = 5
    ) -> Dict[str, Any]:
        """
        Split a large migration file into smaller migration files.
        
        Args:
            migration_file: Path to the migration file to split.
            max_operations_per_file: Maximum number of operations per split file.
            
        Returns:
            Dictionary containing:
            - split_files: List of generated migration file paths
            - dependency_chain: List showing migration dependencies
            - rollback_script: Path to generated rollback script
            
        Raises:
            DatabaseRefactoringError: If splitting fails.
        """
        try:
            content = migration_file.read_text(encoding='utf-8')
            
            # Detect migration type
            if 'django.db' in content and 'migrations' in content:
                return self._split_django_migration(migration_file, content, max_operations_per_file)
            elif 'alembic' in content.lower():
                return self._split_alembic_migration(migration_file, content, max_operations_per_file)
            elif migration_file.suffix == '.sql':
                return self._split_sql_migration(migration_file, content, max_operations_per_file)
            else:
                raise DatabaseRefactoringError(
                    f"Unsupported migration type for file: {migration_file}"
                )
        except Exception as e:
            raise DatabaseRefactoringError(f"Failed to split migration: {e}")
    
    def extract_query(
        self,
        source_file: Path,
        query_identifier: str,
        view_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract a complex query into a separate SQL view file.
        
        Args:
            source_file: Path to the file containing the query.
            query_identifier: Identifier for the query (function name, line number, etc.)
            view_name: Optional name for the view (auto-generated if not provided).
            
        Returns:
            Dictionary containing:
            - view_file: Path to generated view file
            - modified_source: Path to modified source file
            - rollback_script: Path to rollback script
            
        Raises:
            DatabaseRefactoringError: If extraction fails.
        """
        try:
            content = source_file.read_text(encoding='utf-8')
            
            # Extract the query
            query = self._extract_query_from_code(content, query_identifier)
            
            if not query:
                raise DatabaseRefactoringError(
                    f"Could not find query identified by: {query_identifier}"
                )
            
            # Generate view name if not provided
            if not view_name:
                view_name = self._generate_view_name(query_identifier)
            
            # Create view file
            view_file = self._create_view_file(view_name, query)
            
            # Modify source to use view
            modified_source = self._replace_query_with_view(
                source_file, content, query, view_name
            )
            
            # Generate rollback script
            rollback_script = self._generate_view_rollback(view_name, query)
            
            return {
                'view_file': str(view_file),
                'modified_source': str(modified_source),
                'rollback_script': str(rollback_script),
                'view_name': view_name,
            }
        except Exception as e:
            raise DatabaseRefactoringError(f"Failed to extract query: {e}")
    
    # Helper methods for Django migrations
    
    def _split_django_migration(
        self,
        migration_file: Path,
        content: str,
        max_operations: int
    ) -> Dict[str, Any]:
        """Split a Django migration file."""
        # Extract migration metadata
        dependencies = self._extract_django_dependencies(content)
        operations = self._extract_django_operations(content)
        
        if len(operations) <= max_operations:
            return {
                'split_files': [str(migration_file)],
                'dependency_chain': [],
                'rollback_script': None,
                'message': 'Migration does not need splitting',
            }
        
        # Split operations into chunks
        operation_chunks = [
            operations[i:i + max_operations]
            for i in range(0, len(operations), max_operations)
        ]
        
        # Generate split migration files
        split_files = []
        dependency_chain = []
        base_name = migration_file.stem
        parent_dir = migration_file.parent
        
        previous_migration = dependencies[0] if dependencies else None
        
        for idx, chunk in enumerate(operation_chunks, 1):
            # Generate new migration name
            new_name = f"{base_name}_part{idx}.py"
            new_file = parent_dir / new_name
            
            # Create migration content
            new_content = self._create_django_migration_content(
                chunk,
                [previous_migration] if previous_migration else [],
                f"{base_name} - Part {idx}"
            )
            
            # Write file
            new_file.write_text(new_content, encoding='utf-8')
            split_files.append(str(new_file))
            
            # Update dependency chain
            dependency_chain.append({
                'file': str(new_file),
                'depends_on': previous_migration,
            })
            
            previous_migration = f"('{parent_dir.name}', '{new_file.stem}')"
        
        # Generate rollback script
        rollback_script = self._generate_django_rollback(split_files)
        
        return {
            'split_files': split_files,
            'dependency_chain': dependency_chain,
            'rollback_script': str(rollback_script),
        }
    
    def _extract_django_dependencies(self, content: str) -> List[str]:
        """Extract dependencies from Django migration."""
        dep_pattern = r'dependencies\s*=\s*\[(.*?)\]'
        match = re.search(dep_pattern, content, re.DOTALL)
        
        if not match:
            return []
        
        deps_str = match.group(1)
        # Extract tuples like ('app', 'migration_name')
        tuple_pattern = r'\([\'"](\w+)[\'"]\s*,\s*[\'"]([^\'")]+)[\'"]\)'
        deps = re.findall(tuple_pattern, deps_str)
        
        return [f"('{app}', '{mig}')" for app, mig in deps]
    
    def _extract_django_operations(self, content: str) -> List[str]:
        """Extract operations from Django migration."""
        # Find the operations list with proper bracket matching
        ops_start = content.find('operations = [')
        if ops_start == -1:
            return []
        
        # Start after 'operations = ['
        start_pos = ops_start + len('operations = [')
        bracket_count = 1
        end_pos = start_pos
        
        # Find the matching closing bracket
        for i in range(start_pos, len(content)):
            if content[i] == '[':
                bracket_count += 1
            elif content[i] == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    end_pos = i
                    break
        
        if bracket_count != 0:
            return []
        
        ops_str = content[start_pos:end_pos]
        
        # Split operations by looking for 'migrations.'
        operations = []
        current_op = []
        bracket_count = 0
        paren_count = 0
        
        lines = ops_str.split('\n')
        for line in lines:
            stripped = line.strip()
            
            # Track bracket and parenthesis nesting
            bracket_count += line.count('[') - line.count(']')
            paren_count += line.count('(') - line.count(')')
            
            if 'migrations.' in line and bracket_count == 0 and paren_count == 0 and current_op:
                # Start of new operation and we have a previous one
                operations.append('\n'.join(current_op))
                current_op = [line]
            else:
                current_op.append(line)
            
            # If we're back at zero nesting and have a comma, might be end of operation
            if bracket_count == 0 and paren_count == 0 and stripped.endswith(','):
                if current_op:
                    operations.append('\n'.join(current_op))
                    current_op = []
        
        # Don't forget the last operation
        if current_op:
            op_text = '\n'.join(current_op).strip()
            if op_text and not op_text == ',':
                operations.append(op_text)
        
        # Clean up operations - remove trailing commas and empty entries
        cleaned_operations = []
        for op in operations:
            op = op.strip()
            if op and op != ',' and 'migrations.' in op:
                cleaned_operations.append(op)
        
        return cleaned_operations
    
    def _create_django_migration_content(
        self,
        operations: List[str],
        dependencies: List[str],
        description: str
    ) -> str:
        """Create Django migration file content."""
        ops_str = ',\n'.join(operations)
        deps_str = ',\n        '.join(dependencies) if dependencies else ''
        
        content = f'''
from django.db import migrations, models

class Migration(migrations.Migration):
    """
    {description}
    """
    
    dependencies = [
        {deps_str}
    ]
    
    operations = [
{ops_str}
    ]
'''
        return content.strip()
    
    def _generate_django_rollback(self, split_files: List[str]) -> Path:
        """Generate rollback script for split Django migrations."""
        rollback_dir = self.project_root / ".taskmaster" / "rollback"
        rollback_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        rollback_file = rollback_dir / f"rollback_django_{timestamp}.sh"
        
        # Generate rollback commands
        commands = [
            "#!/bin/bash",
            "# Rollback script for split Django migrations",
            "",
        ]
        
        for split_file in reversed(split_files):
            file_path = Path(split_file)
            app_name = file_path.parent.name
            migration_name = file_path.stem
            commands.append(f"python manage.py migrate {app_name} {migration_name} --fake-initial")
        
        commands.append("")
        
        rollback_file.write_text('\n'.join(commands), encoding='utf-8')
        return rollback_file
    
    # Helper methods for Alembic migrations
    
    def _split_alembic_migration(
        self,
        migration_file: Path,
        content: str,
        max_operations: int
    ) -> Dict[str, Any]:
        """Split an Alembic migration file."""
        # For simplicity, return unsplit for now
        # Full implementation would parse upgrade() and downgrade() functions
        return {
            'split_files': [str(migration_file)],
            'dependency_chain': [],
            'rollback_script': None,
            'message': 'Alembic migration splitting not yet implemented',
        }
    
    # Helper methods for SQL migrations
    
    def _split_sql_migration(
        self,
        migration_file: Path,
        content: str,
        max_operations: int
    ) -> Dict[str, Any]:
        """Split a SQL migration file."""
        # Split by SQL statements
        statements = self._split_sql_statements(content)
        
        if len(statements) <= max_operations:
            return {
                'split_files': [str(migration_file)],
                'dependency_chain': [],
                'rollback_script': None,
                'message': 'SQL migration does not need splitting',
            }
        
        # Split statements into chunks
        statement_chunks = [
            statements[i:i + max_operations]
            for i in range(0, len(statements), max_operations)
        ]
        
        # Generate split files
        split_files = []
        base_name = migration_file.stem
        parent_dir = migration_file.parent
        
        for idx, chunk in enumerate(statement_chunks, 1):
            new_name = f"{base_name}_part{idx}.sql"
            new_file = parent_dir / new_name
            
            new_content = '\n\n'.join(chunk)
            new_file.write_text(new_content, encoding='utf-8')
            split_files.append(str(new_file))
        
        # Generate rollback script
        rollback_script = self._generate_sql_rollback(split_files, statements)
        
        return {
            'split_files': split_files,
            'dependency_chain': [{'file': f, 'order': idx} for idx, f in enumerate(split_files, 1)],
            'rollback_script': str(rollback_script),
        }
    
    def _split_sql_statements(self, content: str) -> List[str]:
        """Split SQL content into individual statements."""
        # Simple split by semicolon (not perfect but works for most cases)
        statements = []
        current_statement = []
        
        for line in content.split('\n'):
            stripped = line.strip()
            
            # Skip comments and empty lines
            if not stripped or stripped.startswith('--'):
                continue
            
            current_statement.append(line)
            
            if stripped.endswith(';'):
                statements.append('\n'.join(current_statement))
                current_statement = []
        
        if current_statement:
            statements.append('\n'.join(current_statement))
        
        return statements
    
    def _generate_sql_rollback(self, split_files: List[str], statements: List[str]) -> Path:
        """Generate rollback script for SQL migrations."""
        rollback_dir = self.project_root / ".taskmaster" / "rollback"
        rollback_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        rollback_file = rollback_dir / f"rollback_sql_{timestamp}.sql"
        
        # Generate reverse statements (very simplistic)
        rollback_statements = []
        
        for stmt in reversed(statements):
            if 'CREATE TABLE' in stmt.upper():
                # Extract table name
                match = re.search(r'CREATE\s+TABLE\s+(\w+)', stmt, re.IGNORECASE)
                if match:
                    table_name = match.group(1)
                    rollback_statements.append(f"DROP TABLE IF EXISTS {table_name};")
            elif 'ALTER TABLE' in stmt.upper() and 'ADD COLUMN' in stmt.upper():
                # Extract table and column name
                match = re.search(r'ALTER\s+TABLE\s+(\w+)\s+ADD\s+COLUMN\s+(\w+)', stmt, re.IGNORECASE)
                if match:
                    table_name, column_name = match.groups()
                    rollback_statements.append(f"ALTER TABLE {table_name} DROP COLUMN {column_name};")
        
        rollback_content = '\n\n'.join(rollback_statements)
        rollback_file.write_text(rollback_content, encoding='utf-8')
        
        return rollback_file
    
    # Helper methods for query extraction
    
    def _extract_query_from_code(self, content: str, identifier: str) -> Optional[str]:
        """Extract SQL query from source code."""
        # Try to find SQL query by identifier (function name, variable, etc.)
        # This is a simplified implementation
        
        # Look for multi-line strings containing SELECT
        query_pattern = r'["\']+(SELECT.*?)["\']+'
        matches = re.findall(query_pattern, content, re.DOTALL | re.IGNORECASE)
        
        if matches:
            # Return first match for now
            return matches[0].strip()
        
        return None
    
    def _generate_view_name(self, identifier: str) -> str:
        """Generate a view name from an identifier."""
        # Clean identifier and create view name
        clean_id = re.sub(r'[^\w]', '_', identifier.lower())
        return f"view_{clean_id}"
    
    def _create_view_file(self, view_name: str, query: str) -> Path:
        """Create a SQL view file."""
        views_dir = self.project_root / "database" / "views"
        views_dir.mkdir(parents=True, exist_ok=True)
        
        view_file = views_dir / f"{view_name}.sql"
        
        view_content = f"""-- View: {view_name}
-- Auto-generated by TaskMaster

CREATE OR REPLACE VIEW {view_name} AS
{query};
"""
        
        view_file.write_text(view_content, encoding='utf-8')
        return view_file
    
    def _replace_query_with_view(
        self,
        source_file: Path,
        content: str,
        query: str,
        view_name: str
    ) -> Path:
        """Replace query in source with view reference."""
        # Replace the query with a reference to the view
        modified_content = content.replace(query, f"SELECT * FROM {view_name}")
        
        # Write to new file (or overwrite)
        modified_file = source_file.parent / f"{source_file.stem}_modified{source_file.suffix}"
        modified_file.write_text(modified_content, encoding='utf-8')
        
        return modified_file
    
    def _generate_view_rollback(self, view_name: str, original_query: str) -> Path:
        """Generate rollback script for view extraction."""
        rollback_dir = self.project_root / ".taskmaster" / "rollback"
        rollback_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        rollback_file = rollback_dir / f"rollback_view_{view_name}_{timestamp}.sql"
        
        rollback_content = f"""-- Rollback script for view: {view_name}

DROP VIEW IF EXISTS {view_name};

-- Original query:
-- {original_query}
"""
        
        rollback_file.write_text(rollback_content, encoding='utf-8')
        return rollback_file
