"""
Integration tests for database refactoring functionality.
"""

import pytest
from pathlib import Path
from src.database_refactoring import (
    DatabaseRefactoringEngine,
    DatabaseRefactoringError,
)


class TestDatabaseRefactoringEngine:
    """Integration tests for DatabaseRefactoringEngine."""
    
    @pytest.fixture
    def project_root(self, tmp_path):
        """Create a test project directory."""
        project = tmp_path / "test_project"
        project.mkdir()
        return project
    
    @pytest.fixture
    def engine(self, project_root):
        """Create a DatabaseRefactoringEngine instance."""
        return DatabaseRefactoringEngine(project_root)
    
    # Tests for SQL migration splitting
    
    def test_split_sql_migration_small(self, engine, project_root):
        """Test splitting a small SQL migration that doesn't need splitting."""
        sql_file = project_root / "migration.sql"
        sql_file.write_text("""
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(100)
);

INSERT INTO users VALUES (1, 'John');
""")
        
        result = engine.split_migration(sql_file, max_operations_per_file=5)
        
        assert result['split_files'] == [str(sql_file)]
        assert 'message' in result
        assert 'does not need splitting' in result['message']
    
    def test_split_sql_migration_large(self, engine, project_root):
        """Test splitting a large SQL migration."""
        sql_file = project_root / "large_migration.sql"
        statements = []
        
        # Create 10 CREATE TABLE statements
        for i in range(10):
            statements.append(f"""
CREATE TABLE table_{i} (
    id INT PRIMARY KEY,
    name VARCHAR(100)
);
""")
        
        sql_file.write_text('\n'.join(statements))
        
        result = engine.split_migration(sql_file, max_operations_per_file=3)
        
        # Should split into multiple files
        assert len(result['split_files']) > 1
        assert result['rollback_script'] is not None
        
        # Check that split files exist
        for split_file in result['split_files']:
            assert Path(split_file).exists()
        
        # Check dependency chain
        assert len(result['dependency_chain']) == len(result['split_files'])
    
    def test_split_sql_migration_preserves_statements(self, engine, project_root):
        """Test that splitting preserves all SQL statements."""
        sql_file = project_root / "migration.sql"
        
        # Create statements that are easy to count
        statements = [
            "CREATE TABLE users (id INT);",
            "CREATE TABLE orders (id INT);",
            "CREATE TABLE products (id INT);",
            "CREATE TABLE reviews (id INT);",
            "CREATE TABLE categories (id INT);",
            "CREATE TABLE inventory (id INT);",
        ]
        
        sql_file.write_text('\n\n'.join(statements))
        
        result = engine.split_migration(sql_file, max_operations_per_file=2)
        
        # Count total statements in split files
        total_statements = 0
        for split_file in result['split_files']:
            content = Path(split_file).read_text()
            total_statements += len([s for s in content.split(';') if 'CREATE TABLE' in s])
        
        assert total_statements == len(statements)
    
    # Tests for Django migration splitting
    
    def test_split_django_migration_small(self, engine, project_root):
        """Test splitting a small Django migration."""
        migration_dir = project_root / "app" / "migrations"
        migration_dir.mkdir(parents=True)
        
        migration_file = migration_dir / "0001_initial.py"
        migration_file.write_text("""
from django.db import migrations, models

class Migration(migrations.Migration):
    
    dependencies = []
    
    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(primary_key=True)),
            ],
        ),
    ]
""")
        
        result = engine.split_migration(migration_file, max_operations_per_file=5)
        
        assert 'does not need splitting' in result.get('message', '')
    
    def test_split_django_migration_large(self, engine, project_root):
        """Test splitting a large Django migration."""
        migration_dir = project_root / "app" / "migrations"
        migration_dir.mkdir(parents=True)
        
        # Create a migration with many operations
        operations = []
        for i in range(10):
            operations.append(f"""
        migrations.CreateModel(
            name='Model{i}',
            fields=[
                ('id', models.AutoField(primary_key=True)),
            ],
        ),""")
        
        migration_content = f"""
from django.db import migrations, models

class Migration(migrations.Migration):
    
    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
    ]
    
    operations = [
{''.join(operations)}
    ]
"""
        
        migration_file = migration_dir / "0042_large_migration.py"
        migration_file.write_text(migration_content)
        
        result = engine.split_migration(migration_file, max_operations_per_file=3)
        
        # Should create multiple split files
        assert len(result['split_files']) > 1
        
        # Check that each split file exists and is valid Python
        for split_file in result['split_files']:
            file_path = Path(split_file)
            assert file_path.exists()
            content = file_path.read_text()
            assert 'from django.db import migrations' in content
            assert 'class Migration' in content
        
        # Check rollback script
        assert result['rollback_script'] is not None
        rollback_path = Path(result['rollback_script'])
        assert rollback_path.exists()
    
    def test_split_django_migration_dependencies(self, engine, project_root):
        """Test that split migrations maintain proper dependency chain."""
        migration_dir = project_root / "app" / "migrations"
        migration_dir.mkdir(parents=True)
        
        # Create a migration with operations
        operations = []
        for i in range(8):
            operations.append(f"""
        migrations.AddField(
            model_name='user',
            name='field{i}',
            field=models.CharField(max_length=100),
        ),""")
        
        migration_content = f"""
from django.db import migrations, models

class Migration(migrations.Migration):
    
    dependencies = [
        ('app', '0001_initial'),
    ]
    
    operations = [
{''.join(operations)}
    ]
"""
        
        migration_file = migration_dir / "0002_add_fields.py"
        migration_file.write_text(migration_content)
        
        result = engine.split_migration(migration_file, max_operations_per_file=3)
        
        # Check dependency chain
        chain = result['dependency_chain']
        assert len(chain) > 0
        
        # First migration should depend on 0001_initial
        assert '0001_initial' in chain[0].get('depends_on', '')
        
        # Subsequent migrations should depend on previous parts
        for i in range(1, len(chain)):
            prev_file = Path(chain[i-1]['file'])
            assert prev_file.stem in chain[i].get('depends_on', '')
    
    # Tests for query extraction
    
    def test_extract_query_basic(self, engine, project_root):
        """Test basic query extraction."""
        source_file = project_root / "queries.py"
        source_file.write_text("""
def get_users():
    query = "SELECT id, name, email FROM users WHERE active = true"
    return execute_query(query)
""")
        
        result = engine.extract_query(
            source_file=source_file,
            query_identifier='get_users',
            view_name='active_users'
        )
        
        assert result['view_name'] == 'active_users'
        assert Path(result['view_file']).exists()
        assert Path(result['modified_source']).exists()
        assert Path(result['rollback_script']).exists()
        
        # Check view content
        view_content = Path(result['view_file']).read_text()
        assert 'CREATE OR REPLACE VIEW active_users' in view_content
        assert 'SELECT' in view_content
    
    def test_extract_query_auto_view_name(self, engine, project_root):
        """Test query extraction with auto-generated view name."""
        source_file = project_root / "models.py"
        source_file.write_text("""
class UserReport:
    def get_data(self):
        return "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
""")
        
        result = engine.extract_query(
            source_file=source_file,
            query_identifier='get_data'
        )
        
        # Should auto-generate view name
        assert result['view_name'].startswith('view_')
        assert Path(result['view_file']).exists()
    
    def test_extract_query_rollback(self, engine, project_root):
        """Test that query extraction generates valid rollback script."""
        source_file = project_root / "app.py"
        source_file.write_text("""
query = "SELECT id, name FROM products WHERE price > 100"
""")
        
        result = engine.extract_query(
            source_file=source_file,
            query_identifier='products',
            view_name='expensive_products'
        )
        
        # Check rollback script
        rollback_path = Path(result['rollback_script'])
        assert rollback_path.exists()
        
        rollback_content = rollback_path.read_text()
        assert 'DROP VIEW' in rollback_content
        assert 'expensive_products' in rollback_content
    
    def test_extract_query_no_query_found(self, engine, project_root):
        """Test error handling when query is not found."""
        source_file = project_root / "empty.py"
        source_file.write_text("# No queries here")
        
        with pytest.raises(DatabaseRefactoringError) as exc_info:
            engine.extract_query(
                source_file=source_file,
                query_identifier='nonexistent'
            )
        
        assert 'Could not find query' in str(exc_info.value)
    
    # Tests for error handling
    
    def test_split_migration_invalid_file(self, engine, project_root):
        """Test error handling for invalid migration file."""
        invalid_file = project_root / "not_a_migration.txt"
        invalid_file.write_text("This is not a migration")
        
        with pytest.raises(DatabaseRefactoringError) as exc_info:
            engine.split_migration(invalid_file)
        
        assert 'Unsupported migration type' in str(exc_info.value)
    
    def test_split_migration_nonexistent_file(self, engine, project_root):
        """Test error handling for nonexistent file."""
        nonexistent = project_root / "does_not_exist.py"
        
        with pytest.raises(Exception):
            engine.split_migration(nonexistent)
    
    # Tests for SQL statement splitting
    
    def test_split_sql_statements(self, engine):
        """Test SQL statement splitting."""
        sql_content = """
-- Create users table
CREATE TABLE users (id INT);

-- Insert data
INSERT INTO users VALUES (1);

-- Create orders table  
CREATE TABLE orders (id INT);
"""
        
        statements = engine._split_sql_statements(sql_content)
        
        # Should have 3 statements (comments excluded)
        assert len(statements) == 3
        assert 'CREATE TABLE users' in statements[0]
        assert 'INSERT INTO users' in statements[1]
        assert 'CREATE TABLE orders' in statements[2]
    
    def test_split_sql_statements_multiline(self, engine):
        """Test splitting multi-line SQL statements."""
        sql_content = """
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(255)
);

INSERT INTO users (id, name, email)
VALUES 
    (1, 'John', 'john@example.com'),
    (2, 'Jane', 'jane@example.com');
"""
        
        statements = engine._split_sql_statements(sql_content)
        
        assert len(statements) == 2
        assert 'CREATE TABLE' in statements[0]
        assert 'INSERT INTO' in statements[1]
        assert 'john@example.com' in statements[1]
