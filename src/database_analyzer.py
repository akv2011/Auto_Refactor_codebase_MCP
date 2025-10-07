"""
Database file detection and analysis module.

This module provides functionality to detect and analyze database-related files
including SQL migrations, ORM models, and raw SQL files.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from enum import Enum
import re


class DatabaseFileType(Enum):
    """Types of database-related files."""
    SQL_FILE = "sql_file"
    MIGRATION_FILE = "migration_file"
    DJANGO_MODEL = "django_model"
    SQLALCHEMY_MODEL = "sqlalchemy_model"
    ALEMBIC_MIGRATION = "alembic_migration"
    FLASK_MIGRATE = "flask_migrate"
    UNKNOWN = "unknown"


class DatabaseFileDetector:
    """
    Detects database-related files based on patterns and content.
    
    This class identifies SQL files, migration files, and ORM model definitions
    across various frameworks like Django, SQLAlchemy, Flask-Migrate, etc.
    """
    
    # File extension patterns
    SQL_EXTENSIONS = {'.sql', '.ddl', '.dml'}
    PYTHON_EXTENSIONS = {'.py'}
    
    # Directory patterns for migrations
    MIGRATION_DIRECTORIES = {
        'migrations',
        'alembic',
        'db/migrate',
        'database/migrations',
    }
    
    # File name patterns for migrations
    MIGRATION_PATTERNS = [
        r'^\d{4}_\d{2}_\d{2}_.*\.py$',  # Django: 0001_initial.py
        r'^migration_\d+\.py$',           # Generic
        r'^.*_migration\.py$',            # Suffix-based
        r'^\d+_.*\.py$',                  # Numbered migrations
        r'^[a-f0-9]{12}_.*\.py$',         # Alembic: abc123def456_create_users.py
    ]
    
    # ORM model patterns (to be searched in file content)
    ORM_PATTERNS = {
        'django': [
            r'from\s+django\.db\s+import\s+models',
            r'class\s+\w+\s*\(\s*models\.Model\s*\)',
        ],
        'sqlalchemy': [
            r'from\s+sqlalchemy\s+import',
            r'from\s+sqlalchemy\.ext\.declarative\s+import',
            r'class\s+\w+\s*\(\s*Base\s*\)',
            r'__tablename__\s*=',
        ],
        'flask_sqlalchemy': [
            r'from\s+flask_sqlalchemy\s+import',
            r'db\s*=\s*SQLAlchemy',
            r'class\s+\w+\s*\(\s*db\.Model\s*\)',
        ],
    }
    
    def __init__(self):
        """Initialize the database file detector."""
        self.compiled_migration_patterns = [
            re.compile(pattern) for pattern in self.MIGRATION_PATTERNS
        ]
    
    def is_sql_file(self, file_path: Path) -> bool:
        """
        Check if a file is a SQL file based on extension.
        
        Args:
            file_path: Path to the file to check.
            
        Returns:
            True if file has SQL extension, False otherwise.
        """
        return file_path.suffix.lower() in self.SQL_EXTENSIONS
    
    def is_in_migration_directory(self, file_path: Path) -> bool:
        """
        Check if a file is in a migration directory.
        
        Args:
            file_path: Path to the file to check.
            
        Returns:
            True if file is in a migration directory, False otherwise.
        """
        parts = file_path.parts
        for part in parts:
            if part.lower() in self.MIGRATION_DIRECTORIES:
                return True
        return False
    
    def matches_migration_pattern(self, filename: str) -> bool:
        """
        Check if a filename matches migration naming patterns.
        
        Args:
            filename: Name of the file to check.
            
        Returns:
            True if filename matches migration patterns, False otherwise.
        """
        for pattern in self.compiled_migration_patterns:
            if pattern.match(filename):
                return True
        return False
    
    def detect_orm_type(self, content: str) -> Optional[str]:
        """
        Detect ORM framework used in a Python file.
        
        Args:
            content: Content of the Python file.
            
        Returns:
            Name of detected ORM ('django', 'sqlalchemy', 'flask_sqlalchemy')
            or None if no ORM detected.
        """
        for orm_name, patterns in self.ORM_PATTERNS.items():
            matches = sum(1 for pattern in patterns if re.search(pattern, content))
            # Require at least 2 pattern matches to confirm ORM usage
            if matches >= 2:
                return orm_name
        return None
    
    def detect_file_type(self, file_path: Path) -> DatabaseFileType:
        """
        Detect the type of database-related file.
        
        Args:
            file_path: Path to the file to analyze.
            
        Returns:
            DatabaseFileType enum indicating the file type.
        """
        # Check for SQL files
        if self.is_sql_file(file_path):
            return DatabaseFileType.SQL_FILE
        
        # Check for Python files
        if file_path.suffix.lower() not in self.PYTHON_EXTENSIONS:
            return DatabaseFileType.UNKNOWN
        
        filename = file_path.name
        
        # Check if it's in a migration directory
        in_migration_dir = self.is_in_migration_directory(file_path)
        matches_migration = self.matches_migration_pattern(filename)
        
        if in_migration_dir or matches_migration:
            # Try to determine specific migration type
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                if 'alembic' in content.lower():
                    return DatabaseFileType.ALEMBIC_MIGRATION
                elif 'flask-migrate' in content.lower() or 'flask_migrate' in content:
                    return DatabaseFileType.FLASK_MIGRATE
                elif 'django.db.migrations' in content:
                    return DatabaseFileType.MIGRATION_FILE
                else:
                    return DatabaseFileType.MIGRATION_FILE
            except Exception:
                return DatabaseFileType.MIGRATION_FILE
        
        # Check for ORM models
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            orm_type = self.detect_orm_type(content)
            
            if orm_type == 'django':
                return DatabaseFileType.DJANGO_MODEL
            elif orm_type in ('sqlalchemy', 'flask_sqlalchemy'):
                return DatabaseFileType.SQLALCHEMY_MODEL
        except Exception:
            pass
        
        return DatabaseFileType.UNKNOWN
    
    def is_database_file(self, file_path: Path) -> bool:
        """
        Check if a file is database-related.
        
        Args:
            file_path: Path to the file to check.
            
        Returns:
            True if file is database-related, False otherwise.
        """
        file_type = self.detect_file_type(file_path)
        return file_type != DatabaseFileType.UNKNOWN


class DatabaseFileAnalyzer:
    """
    Analyzes database-related files to extract schema information.
    
    This class parses SQL files, migrations, and ORM models to extract
    information like table definitions, query complexity, and dependencies.
    """
    
    def __init__(self):
        """Initialize the database file analyzer."""
        self.detector = DatabaseFileDetector()
    
    def analyze_sql_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze a SQL file to extract schema information.
        
        Args:
            file_path: Path to the SQL file.
            
        Returns:
            Dictionary containing analysis results with keys:
            - tables: List of table names referenced
            - statements: List of statement types (CREATE, ALTER, SELECT, etc.)
            - complexity: Estimated complexity score
        """
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Extract table names
            tables = self._extract_table_names(content)
            
            # Extract statement types
            statements = self._extract_statement_types(content)
            
            # Calculate complexity
            complexity = self._calculate_sql_complexity(content, statements)
            
            return {
                'file_type': 'sql',
                'tables': list(tables),
                'statements': statements,
                'complexity': complexity,
                'line_count': len(content.splitlines()),
            }
        except Exception as e:
            return {
                'file_type': 'sql',
                'error': str(e),
                'tables': [],
                'statements': [],
                'complexity': 0,
            }
    
    def analyze_orm_model(self, file_path: Path, orm_type: str) -> Dict[str, Any]:
        """
        Analyze an ORM model file to extract schema information.
        
        Args:
            file_path: Path to the model file.
            orm_type: Type of ORM ('django', 'sqlalchemy', etc.)
            
        Returns:
            Dictionary containing analysis results with keys:
            - models: List of model class names
            - fields: Dictionary mapping model names to field lists
            - relationships: List of detected relationships
        """
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            if orm_type == 'django':
                return self._analyze_django_model(content)
            elif orm_type in ('sqlalchemy', 'flask_sqlalchemy'):
                return self._analyze_sqlalchemy_model(content)
            else:
                return self._analyze_generic_model(content)
        except Exception as e:
            return {
                'file_type': 'orm_model',
                'orm_type': orm_type,
                'error': str(e),
                'models': [],
            }
    
    def analyze_migration(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze a migration file to extract operations.
        
        Args:
            file_path: Path to the migration file.
            
        Returns:
            Dictionary containing analysis results with keys:
            - operations: List of migration operations
            - dependencies: List of migration dependencies
            - tables_affected: List of tables affected by this migration
        """
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Detect migration type - check for Django patterns first
            if 'django.db' in content and 'migrations' in content:
                return self._analyze_django_migration(content)
            elif 'alembic' in content.lower():
                return self._analyze_alembic_migration(content)
            else:
                return self._analyze_generic_migration(content)
        except Exception as e:
            return {
                'file_type': 'migration',
                'error': str(e),
                'operations': [],
            }
    
    def analyze_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Analyze a database-related file and extract information.
        
        Args:
            file_path: Path to the file to analyze.
            
        Returns:
            Dictionary containing analysis results, or None if file is not
            database-related.
        """
        file_type = self.detector.detect_file_type(file_path)
        
        if file_type == DatabaseFileType.UNKNOWN:
            return None
        
        if file_type == DatabaseFileType.SQL_FILE:
            return self.analyze_sql_file(file_path)
        elif file_type in (DatabaseFileType.DJANGO_MODEL, DatabaseFileType.SQLALCHEMY_MODEL):
            orm_type = 'django' if file_type == DatabaseFileType.DJANGO_MODEL else 'sqlalchemy'
            return self.analyze_orm_model(file_path, orm_type)
        elif file_type in (DatabaseFileType.MIGRATION_FILE, DatabaseFileType.ALEMBIC_MIGRATION, DatabaseFileType.FLASK_MIGRATE):
            return self.analyze_migration(file_path)
        
        return None
    
    # Helper methods for extraction
    
    def _extract_table_names(self, sql_content: str) -> Set[str]:
        """Extract table names from SQL content."""
        tables = set()
        
        # Pattern for CREATE TABLE
        create_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([`"\']?\w+[`"\']?)'
        tables.update(re.findall(create_pattern, sql_content, re.IGNORECASE))
        
        # Pattern for FROM clause
        from_pattern = r'FROM\s+([`"\']?\w+[`"\']?)'
        tables.update(re.findall(from_pattern, sql_content, re.IGNORECASE))
        
        # Pattern for JOIN clauses
        join_pattern = r'JOIN\s+([`"\']?\w+[`"\']?)'
        tables.update(re.findall(join_pattern, sql_content, re.IGNORECASE))
        
        # Pattern for INSERT INTO
        insert_pattern = r'INSERT\s+INTO\s+([`"\']?\w+[`"\']?)'
        tables.update(re.findall(insert_pattern, sql_content, re.IGNORECASE))
        
        # Pattern for UPDATE
        update_pattern = r'UPDATE\s+([`"\']?\w+[`"\']?)'
        tables.update(re.findall(update_pattern, sql_content, re.IGNORECASE))
        
        # Clean table names (remove quotes)
        cleaned_tables = {name.strip('`"\'') for name in tables}
        return cleaned_tables
    
    def _extract_statement_types(self, sql_content: str) -> List[str]:
        """Extract SQL statement types from content."""
        statement_patterns = {
            'CREATE': r'\bCREATE\s+(?:TABLE|INDEX|VIEW|DATABASE)',
            'ALTER': r'\bALTER\s+(?:TABLE|DATABASE)',
            'DROP': r'\bDROP\s+(?:TABLE|INDEX|VIEW|DATABASE)',
            'INSERT': r'\bINSERT\s+INTO',
            'UPDATE': r'\bUPDATE\s+',
            'DELETE': r'\bDELETE\s+FROM',
            'SELECT': r'\bSELECT\s+',
            'TRUNCATE': r'\bTRUNCATE\s+TABLE',
        }
        
        statements = []
        for stmt_type, pattern in statement_patterns.items():
            if re.search(pattern, sql_content, re.IGNORECASE):
                statements.append(stmt_type)
        
        return statements
    
    def _calculate_sql_complexity(self, content: str, statements: List[str]) -> int:
        """Calculate complexity score for SQL content."""
        complexity = 0
        
        # Base complexity from statement types
        complexity += len(statements) * 2
        
        # Add complexity for JOINs
        join_count = len(re.findall(r'\bJOIN\b', content, re.IGNORECASE))
        complexity += join_count * 3
        
        # Add complexity for subqueries
        subquery_count = len(re.findall(r'SELECT.*FROM.*\(.*SELECT', content, re.IGNORECASE | re.DOTALL))
        complexity += subquery_count * 5
        
        # Add complexity for UNION
        union_count = len(re.findall(r'\bUNION\b', content, re.IGNORECASE))
        complexity += union_count * 3
        
        # Add complexity for WHERE clauses
        where_count = len(re.findall(r'\bWHERE\b', content, re.IGNORECASE))
        complexity += where_count
        
        return complexity
    
    def _analyze_django_model(self, content: str) -> Dict[str, Any]:
        """Analyze Django model file."""
        models = []
        
        # Find model classes
        model_pattern = r'class\s+(\w+)\s*\(\s*models\.Model\s*\)'
        models = re.findall(model_pattern, content)
        
        return {
            'file_type': 'django_model',
            'orm_type': 'django',
            'models': models,
            'model_count': len(models),
        }
    
    def _analyze_sqlalchemy_model(self, content: str) -> Dict[str, Any]:
        """Analyze SQLAlchemy model file."""
        models = []
        tables = []
        
        # Find model classes (inheriting from Base)
        model_pattern = r'class\s+(\w+)\s*\(\s*Base\s*\)'
        models = re.findall(model_pattern, content)
        
        # Find table names
        table_pattern = r'__tablename__\s*=\s*["\'](\w+)["\']'
        tables = re.findall(table_pattern, content)
        
        return {
            'file_type': 'sqlalchemy_model',
            'orm_type': 'sqlalchemy',
            'models': models,
            'tables': tables,
            'model_count': len(models),
        }
    
    def _analyze_generic_model(self, content: str) -> Dict[str, Any]:
        """Analyze generic model file."""
        return {
            'file_type': 'orm_model',
            'orm_type': 'unknown',
            'models': [],
        }
    
    def _analyze_django_migration(self, content: str) -> Dict[str, Any]:
        """Analyze Django migration file."""
        operations = []
        dependencies = []
        
        # Extract dependencies
        dep_pattern = r'dependencies\s*=\s*\[(.*?)\]'
        dep_match = re.search(dep_pattern, content, re.DOTALL)
        if dep_match:
            dependencies = [d.strip() for d in dep_match.group(1).split(',') if d.strip()]
        
        # Extract operations (simplified)
        if 'CreateModel' in content:
            operations.append('CreateModel')
        if 'DeleteModel' in content:
            operations.append('DeleteModel')
        if 'AddField' in content:
            operations.append('AddField')
        if 'RemoveField' in content:
            operations.append('RemoveField')
        if 'AlterField' in content:
            operations.append('AlterField')
        
        return {
            'file_type': 'django_migration',
            'operations': operations,
            'dependencies': dependencies,
        }
    
    def _analyze_alembic_migration(self, content: str) -> Dict[str, Any]:
        """Analyze Alembic migration file."""
        operations = []
        
        # Extract Alembic operations
        if 'create_table' in content:
            operations.append('create_table')
        if 'drop_table' in content:
            operations.append('drop_table')
        if 'add_column' in content:
            operations.append('add_column')
        if 'drop_column' in content:
            operations.append('drop_column')
        if 'alter_column' in content:
            operations.append('alter_column')
        
        # Extract revision info
        revision = None
        down_revision = None
        
        rev_pattern = r'revision\s*=\s*["\']([^"\']+)["\']'
        down_pattern = r'down_revision\s*=\s*["\']([^"\']+)["\']'
        
        rev_match = re.search(rev_pattern, content)
        down_match = re.search(down_pattern, content)
        
        if rev_match:
            revision = rev_match.group(1)
        if down_match:
            down_revision = down_match.group(1)
        
        return {
            'file_type': 'alembic_migration',
            'operations': operations,
            'revision': revision,
            'down_revision': down_revision,
        }
    
    def _analyze_generic_migration(self, content: str) -> Dict[str, Any]:
        """Analyze generic migration file."""
        return {
            'file_type': 'migration',
            'operations': [],
        }
