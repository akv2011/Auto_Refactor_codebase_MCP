"""
Tests for database file detection and analysis.
"""

import pytest
from pathlib import Path
from src.database_analyzer import (
    DatabaseFileDetector,
    DatabaseFileAnalyzer,
    DatabaseFileType,
)


class TestDatabaseFileDetector:
    """Tests for DatabaseFileDetector."""
    
    @pytest.fixture
    def detector(self):
        """Create a detector instance."""
        return DatabaseFileDetector()
    
    def test_is_sql_file(self, detector, tmp_path):
        """Test SQL file detection by extension."""
        sql_file = tmp_path / "schema.sql"
        sql_file.touch()
        assert detector.is_sql_file(sql_file)
        
        ddl_file = tmp_path / "create_tables.ddl"
        ddl_file.touch()
        assert detector.is_sql_file(ddl_file)
        
        py_file = tmp_path / "models.py"
        py_file.touch()
        assert not detector.is_sql_file(py_file)
    
    def test_is_in_migration_directory(self, detector, tmp_path):
        """Test migration directory detection."""
        migration_file = tmp_path / "migrations" / "0001_initial.py"
        migration_file.parent.mkdir()
        migration_file.touch()
        assert detector.is_in_migration_directory(migration_file)
        
        alembic_file = tmp_path / "alembic" / "versions" / "abc123_create_users.py"
        alembic_file.parent.mkdir(parents=True)
        alembic_file.touch()
        assert detector.is_in_migration_directory(alembic_file)
        
        regular_file = tmp_path / "app" / "models.py"
        regular_file.parent.mkdir()
        regular_file.touch()
        assert not detector.is_in_migration_directory(regular_file)
    
    def test_matches_migration_pattern(self, detector):
        """Test migration filename pattern matching."""
        # Django style
        assert detector.matches_migration_pattern("0001_initial.py")
        assert detector.matches_migration_pattern("0042_add_user_fields.py")
        
        # Alembic style
        assert detector.matches_migration_pattern("abc123def456_create_users.py")
        
        # Generic numbered
        assert detector.matches_migration_pattern("001_create_schema.py")
        
        # Not migrations
        assert not detector.matches_migration_pattern("models.py")
        assert not detector.matches_migration_pattern("views.py")
    
    def test_detect_orm_type_django(self, detector):
        """Test Django ORM detection."""
        django_content = """
from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
"""
        assert detector.detect_orm_type(django_content) == 'django'
    
    def test_detect_orm_type_sqlalchemy(self, detector):
        """Test SQLAlchemy ORM detection."""
        sqlalchemy_content = """
from src.sqlalchemy import Column, Integer, String
from src.sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
"""
        assert detector.detect_orm_type(sqlalchemy_content) == 'sqlalchemy'
    
    def test_detect_orm_type_flask_sqlalchemy(self, detector):
        """Test Flask-SQLAlchemy detection."""
        flask_content = """
from src.flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
"""
        assert detector.detect_orm_type(flask_content) == 'flask_sqlalchemy'
    
    def test_detect_orm_type_none(self, detector):
        """Test ORM detection with non-ORM code."""
        regular_content = """
def hello():
    print("Hello, World!")
"""
        assert detector.detect_orm_type(regular_content) is None
    
    def test_detect_file_type_sql(self, detector, tmp_path):
        """Test SQL file type detection."""
        sql_file = tmp_path / "schema.sql"
        sql_file.write_text("CREATE TABLE users (id INT PRIMARY KEY);")
        assert detector.detect_file_type(sql_file) == DatabaseFileType.SQL_FILE
    
    def test_detect_file_type_django_model(self, detector, tmp_path):
        """Test Django model file type detection."""
        model_file = tmp_path / "models.py"
        model_file.write_text("""
from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
""")
        assert detector.detect_file_type(model_file) == DatabaseFileType.DJANGO_MODEL
    
    def test_detect_file_type_sqlalchemy_model(self, detector, tmp_path):
        """Test SQLAlchemy model file type detection."""
        model_file = tmp_path / "models.py"
        model_file.write_text("""
from src.sqlalchemy import Column, Integer, String
from src.sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
""")
        assert detector.detect_file_type(model_file) == DatabaseFileType.SQLALCHEMY_MODEL
    
    def test_detect_file_type_django_migration(self, detector, tmp_path):
        """Test Django migration file type detection."""
        migration_dir = tmp_path / "migrations"
        migration_dir.mkdir()
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
        assert detector.detect_file_type(migration_file) == DatabaseFileType.MIGRATION_FILE
    
    def test_detect_file_type_alembic_migration(self, detector, tmp_path):
        """Test Alembic migration file type detection."""
        alembic_dir = tmp_path / "alembic" / "versions"
        alembic_dir.mkdir(parents=True)
        migration_file = alembic_dir / "abc123_create_users.py"
        migration_file.write_text("""
from src.alembic import op
import sqlalchemy as sa

revision = 'abc123'
down_revision = None

def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
    )
""")
        assert detector.detect_file_type(migration_file) == DatabaseFileType.ALEMBIC_MIGRATION
    
    def test_detect_file_type_unknown(self, detector, tmp_path):
        """Test unknown file type detection."""
        regular_file = tmp_path / "utils.py"
        regular_file.write_text("def helper(): pass")
        assert detector.detect_file_type(regular_file) == DatabaseFileType.UNKNOWN
    
    def test_is_database_file(self, detector, tmp_path):
        """Test database file identification."""
        # SQL file is database-related
        sql_file = tmp_path / "schema.sql"
        sql_file.write_text("CREATE TABLE users (id INT);")
        assert detector.is_database_file(sql_file)
        
        # Regular Python file is not
        py_file = tmp_path / "utils.py"
        py_file.write_text("def helper(): pass")
        assert not detector.is_database_file(py_file)


class TestDatabaseFileAnalyzer:
    """Tests for DatabaseFileAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create an analyzer instance."""
        return DatabaseFileAnalyzer()
    
    def test_analyze_sql_file(self, analyzer, tmp_path):
        """Test SQL file analysis."""
        sql_file = tmp_path / "schema.sql"
        sql_file.write_text("""
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(255)
);

CREATE TABLE orders (
    id INT PRIMARY KEY,
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

INSERT INTO users (name, email) VALUES ('John', 'john@example.com');

SELECT u.name, o.id
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE u.name = 'John';
""")
        
        result = analyzer.analyze_sql_file(sql_file)
        
        assert result['file_type'] == 'sql'
        assert 'users' in result['tables']
        assert 'orders' in result['tables']
        assert 'CREATE' in result['statements']
        assert 'INSERT' in result['statements']
        assert 'SELECT' in result['statements']
        assert result['complexity'] > 0
        assert result['line_count'] > 0
    
    def test_analyze_sql_file_with_joins(self, analyzer, tmp_path):
        """Test SQL file analysis with complex joins."""
        sql_file = tmp_path / "complex_query.sql"
        sql_file.write_text("""
SELECT u.name, o.total, p.name
FROM users u
JOIN orders o ON u.id = o.user_id
JOIN products p ON o.product_id = p.id
WHERE u.active = true;
""")
        
        result = analyzer.analyze_sql_file(sql_file)
        
        # Should detect high complexity due to multiple joins
        assert result['complexity'] > 5
        assert len(result['tables']) >= 3
    
    def test_analyze_django_model(self, analyzer, tmp_path):
        """Test Django model analysis."""
        model_file = tmp_path / "models.py"
        model_file.write_text("""
from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField()
""")
        
        result = analyzer.analyze_orm_model(model_file, 'django')
        
        assert result['file_type'] == 'django_model'
        assert result['orm_type'] == 'django'
        assert 'User' in result['models']
        assert 'Profile' in result['models']
        assert result['model_count'] == 2
    
    def test_analyze_sqlalchemy_model(self, analyzer, tmp_path):
        """Test SQLAlchemy model analysis."""
        model_file = tmp_path / "models.py"
        model_file.write_text("""
from src.sqlalchemy import Column, Integer, String
from src.sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
""")
        
        result = analyzer.analyze_orm_model(model_file, 'sqlalchemy')
        
        assert result['file_type'] == 'sqlalchemy_model'
        assert result['orm_type'] == 'sqlalchemy'
        assert 'User' in result['models']
        assert 'Order' in result['models']
        assert 'users' in result['tables']
        assert 'orders' in result['tables']
        assert result['model_count'] == 2
    
    def test_analyze_django_migration(self, analyzer, tmp_path):
        """Test Django migration analysis."""
        migration_file = tmp_path / "0001_initial.py"
        migration_file.write_text("""
from django.db import migrations, models

class Migration(migrations.Migration):
    
    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
    ]
    
    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='email',
            field=models.EmailField(),
        ),
    ]
""")
        
        result = analyzer.analyze_migration(migration_file)
        
        assert result['file_type'] == 'django_migration'
        assert 'CreateModel' in result['operations']
        assert 'AddField' in result['operations']
        assert len(result['dependencies']) > 0
    
    def test_analyze_alembic_migration(self, analyzer, tmp_path):
        """Test Alembic migration analysis."""
        migration_file = tmp_path / "abc123_create_users.py"
        migration_file.write_text("""
from src.alembic import op
import sqlalchemy as sa

revision = 'abc123def456'
down_revision = None
branch_labels = None

def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.add_column('orders', sa.Column('user_id', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('orders', 'user_id')
    op.drop_table('users')
""")
        
        result = analyzer.analyze_migration(migration_file)
        
        assert result['file_type'] == 'alembic_migration'
        assert 'create_table' in result['operations']
        assert 'add_column' in result['operations']
        assert result['revision'] == 'abc123def456'
        assert result['down_revision'] is None
    
    def test_analyze_file_sql(self, analyzer, tmp_path):
        """Test general file analysis for SQL files."""
        sql_file = tmp_path / "test.sql"
        sql_file.write_text("CREATE TABLE test (id INT);")
        
        result = analyzer.analyze_file(sql_file)
        
        assert result is not None
        assert result['file_type'] == 'sql'
    
    def test_analyze_file_django_model(self, analyzer, tmp_path):
        """Test general file analysis for Django models."""
        model_file = tmp_path / "models.py"
        model_file.write_text("""
from django.db import models

class Test(models.Model):
    name = models.CharField(max_length=100)
""")
        
        result = analyzer.analyze_file(model_file)
        
        assert result is not None
        assert result['orm_type'] == 'django'
    
    def test_analyze_file_unknown(self, analyzer, tmp_path):
        """Test general file analysis for unknown files."""
        regular_file = tmp_path / "utils.py"
        regular_file.write_text("def helper(): pass")
        
        result = analyzer.analyze_file(regular_file)
        
        assert result is None
    
    def test_extract_table_names(self, analyzer):
        """Test table name extraction."""
        sql = """
        CREATE TABLE users (id INT);
        INSERT INTO orders (id, user_id) VALUES (1, 1);
        SELECT * FROM products WHERE id = 1;
        UPDATE inventory SET count = 10;
        """
        
        tables = analyzer._extract_table_names(sql)
        
        assert 'users' in tables
        assert 'orders' in tables
        assert 'products' in tables
        assert 'inventory' in tables
    
    def test_extract_statement_types(self, analyzer):
        """Test SQL statement type extraction."""
        sql = """
        CREATE TABLE users (id INT);
        INSERT INTO users VALUES (1);
        SELECT * FROM users;
        UPDATE users SET name = 'John';
        DELETE FROM users WHERE id = 1;
        ALTER TABLE users ADD COLUMN email VARCHAR(255);
        DROP TABLE old_table;
        """
        
        statements = analyzer._extract_statement_types(sql)
        
        assert 'CREATE' in statements
        assert 'INSERT' in statements
        assert 'SELECT' in statements
        assert 'UPDATE' in statements
        assert 'DELETE' in statements
        assert 'ALTER' in statements
        assert 'DROP' in statements
    
    def test_calculate_sql_complexity(self, analyzer):
        """Test SQL complexity calculation."""
        simple_sql = "SELECT * FROM users;"
        complex_sql = """
        SELECT u.*, o.total, p.name
        FROM users u
        JOIN orders o ON u.id = o.user_id
        JOIN products p ON o.product_id = p.id
        WHERE u.active = true AND o.total > 100
        UNION
        SELECT u.*, NULL, NULL
        FROM users u
        WHERE u.admin = true;
        """
        
        simple_complexity = analyzer._calculate_sql_complexity(simple_sql, ['SELECT'])
        complex_complexity = analyzer._calculate_sql_complexity(
            complex_sql, 
            ['SELECT', 'UNION']
        )
        
        assert complex_complexity > simple_complexity
        assert complex_complexity > 10  # Should have high complexity due to joins, union, etc.
    
    def test_analyze_sql_file_error_handling(self, analyzer, tmp_path):
        """Test error handling in SQL file analysis."""
        # Create a file that can't be read properly
        sql_file = tmp_path / "bad.sql"
        sql_file.write_bytes(b'\xff\xfe invalid utf-8')
        
        result = analyzer.analyze_sql_file(sql_file)
        
        # Should return a result with error info rather than raising
        assert result['file_type'] == 'sql'
        assert result['tables'] == []
        assert result['statements'] == []
