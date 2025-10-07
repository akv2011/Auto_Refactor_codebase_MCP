"""
Tests for the codebase_analyzer module.

This module tests the analyze_codebase MCP tool and related functionality.
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path

from src.codebase_analyzer import (
    analyze_codebase,
    CodebaseAnalysisError,
    _calculate_severity,
    _generate_recommendations
)


class TestAnalyzeCodebase:
    """Tests for the main analyze_codebase function."""
    
    @pytest.mark.asyncio
    async def test_analyze_simple_project(self, temp_project):
        """Test analyzing a simple project with a few files."""
        result_json = await analyze_codebase(
            directory=str(temp_project),
            threshold_lines=50
        )
        
        result = json.loads(result_json)
        
        # Verify structure
        assert 'timestamp' in result
        assert 'projectPath' in result
        assert 'summary' in result
        assert 'violations' in result
        
        # Verify summary
        assert result['summary']['totalFiles'] > 0
        assert result['summary']['filesAnalyzed'] > 0
    
    @pytest.mark.asyncio
    async def test_analyze_with_threshold(self, temp_project):
        """Test that files exceeding threshold are identified."""
        # Create a large file with actual code (not comments)
        large_file = Path(temp_project) / "large_module.py"
        code_lines = ["x = " + str(i) for i in range(200)]  # 200 lines of actual code
        large_file.write_text("\n".join(code_lines))
        
        result_json = await analyze_codebase(
            directory=str(temp_project),
            threshold_lines=100
        )
        
        result = json.loads(result_json)
        
        # Should have at least one violation
        assert result['summary']['filesExceedingThreshold'] >= 1
        
        # Check violation details
        violations = result['violations']
        large_file_violation = next(
            (v for v in violations if 'large_module.py' in v['file']),
            None
        )
        
        assert large_file_violation is not None
        assert large_file_violation['lines'] == 200
        assert large_file_violation['severity'] in ['low', 'medium', 'high', 'critical']
        assert len(large_file_violation['recommendations']) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_with_exclude_patterns(self, temp_project):
        """Test that exclude patterns are respected."""
        # Create files in different directories
        (Path(temp_project) / "src").mkdir(parents=True, exist_ok=True)
        (Path(temp_project) / "tests").mkdir(parents=True, exist_ok=True)
        
        src_file = Path(temp_project) / "src" / "module.py"
        src_file.write_text("print('hello')")
        
        test_file = Path(temp_project) / "tests" / "test_module.py"
        test_file.write_text("# Test\n" * 200)  # Large test file
        
        result_json = await analyze_codebase(
            directory=str(temp_project),
            threshold_lines=50,
            exclude_patterns=["**/tests/**"]
        )
        
        result = json.loads(result_json)
        violations = result['violations']
        
        # Test file should be excluded
        test_file_in_violations = any(
            'test_module.py' in v['file']
            for v in violations
        )
        
        assert not test_file_in_violations
    
    @pytest.mark.asyncio
    async def test_analyze_nonexistent_directory(self):
        """Test that analyzing nonexistent directory raises error."""
        with pytest.raises(CodebaseAnalysisError) as exc_info:
            await analyze_codebase(directory="/nonexistent/path")
        
        assert 'not found' in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_analyze_file_instead_of_directory(self, temp_project):
        """Test that analyzing a file instead of directory raises error."""
        file_path = Path(temp_project) / "file.py"
        file_path.write_text("print('hello')")
        
        with pytest.raises(CodebaseAnalysisError) as exc_info:
            await analyze_codebase(directory=str(file_path))
        
        assert 'not a directory' in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_analyze_only_supported_files(self):
        """Test that only supported file types are analyzed."""
        # Create a fresh temp directory (don't use temp_project fixture which has 2 .py files)
        temp_dir = tempfile.mkdtemp()
        try:
            # Create supported and unsupported files with actual code
            (Path(temp_dir) / "script.py").write_text("x = 1")
            (Path(temp_dir) / "app.js").write_text("const x = 1;")
            (Path(temp_dir) / "data.json").write_text('{"key": "value"}')
            (Path(temp_dir) / "readme.txt").write_text("README")

            result_json = await analyze_codebase(directory=str(temp_dir))
            result = json.loads(result_json)

            # Should only count .py and .js files
            assert result['summary']['filesAnalyzed'] == 2
        finally:
            shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_analyze_calculates_average_file_size(self):
        """Test that average file size is calculated correctly."""
        # Create a fresh temp directory (don't use temp_project fixture)
        temp_dir = tempfile.mkdtemp()
        try:
            # Create files with known sizes using actual code
            code1 = "\n".join(["x" + str(i) + " = " + str(i) for i in range(100)])  # 100 lines
            code2 = "\n".join(["y" + str(i) + " = " + str(i) for i in range(200)])  # 200 lines
            (Path(temp_dir) / "file1.py").write_text(code1)
            (Path(temp_dir) / "file2.py").write_text(code2)
            
            result_json = await analyze_codebase(directory=str(temp_dir))
            result = json.loads(result_json)
            
            # Average should be around 150
            average = result['summary']['averageFileSize']
            assert 140 <= average <= 160
        finally:
            shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_analyze_violations_sorted_by_size(self, temp_project):
        """Test that violations are sorted by line count (largest first)."""
        # Create files of different sizes with actual code
        code_small = "\n".join(["a = " + str(i) for i in range(60)])  # 60 lines
        code_medium = "\n".join(["b = " + str(i) for i in range(80)])  # 80 lines
        code_large = "\n".join(["c = " + str(i) for i in range(100)])  # 100 lines
        (Path(temp_project) / "small.py").write_text(code_small)
        (Path(temp_project) / "medium.py").write_text(code_medium)
        (Path(temp_project) / "large.py").write_text(code_large)
        
        result_json = await analyze_codebase(
            directory=str(temp_project),
            threshold_lines=50
        )
        result = json.loads(result_json)
        
        violations = result['violations']
        
        # Should be sorted largest first
        assert len(violations) == 3
        assert violations[0]['lines'] >= violations[1]['lines']
        assert violations[1]['lines'] >= violations[2]['lines']
    
    @pytest.mark.asyncio
    async def test_analyze_handles_file_errors_gracefully(self, temp_project):
        """Test that errors in individual files don't stop analysis."""
        # Create normal file
        (Path(temp_project) / "good.py").write_text("print('hello')")
        
        # Create file that might cause parsing issues (but should still count lines)
        (Path(temp_project) / "weird.py").write_text("# Valid Python\nprint('ok')")
        
        result_json = await analyze_codebase(directory=str(temp_project))
        result = json.loads(result_json)
        
        # Should still analyze successfully
        assert result['summary']['filesAnalyzed'] >= 1
        assert result['status'] != 'error' if 'status' in result else True


class TestCalculateSeverity:
    """Tests for the _calculate_severity helper function."""
    
    def test_no_violation(self):
        """Test severity when file is under threshold."""
        severity = _calculate_severity(lines=100, threshold=150)
        assert severity == 'none'
    
    def test_low_severity(self):
        """Test low severity (up to 50% over threshold)."""
        # 150 is 50% over 100
        severity = _calculate_severity(lines=150, threshold=100)
        assert severity == 'low'
    
    def test_medium_severity(self):
        """Test medium severity (50-100% over threshold)."""
        # 180 is 80% over 100
        severity = _calculate_severity(lines=180, threshold=100)
        assert severity == 'medium'
    
    def test_high_severity(self):
        """Test high severity (100-200% over threshold)."""
        # 250 is 150% over 100
        severity = _calculate_severity(lines=250, threshold=100)
        assert severity == 'high'
    
    def test_critical_severity(self):
        """Test critical severity (more than 200% over threshold)."""
        # 400 is 300% over 100
        severity = _calculate_severity(lines=400, threshold=100)
        assert severity == 'critical'


class TestGenerateRecommendations:
    """Tests for the _generate_recommendations helper function."""
    
    def test_recommendations_for_large_python_file(self):
        """Test recommendations for a large Python file."""
        recommendations = _generate_recommendations(
            lines=3500,
            functions=60,
            complexity=25,
            language='python'
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert len(recommendations) <= 3  # Should return max 3
        
        # Should suggest splitting
        recommendations_text = ' '.join(recommendations).lower()
        assert 'split' in recommendations_text or 'package' in recommendations_text
    
    def test_recommendations_for_complex_file(self):
        """Test recommendations for a file with high complexity."""
        recommendations = _generate_recommendations(
            lines=1800,
            functions=20,
            complexity=25,
            language='javascript'
        )
        
        recommendations_text = ' '.join(recommendations).lower()
        assert 'complexity' in recommendations_text or 'simplif' in recommendations_text
    
    def test_recommendations_for_many_functions(self):
        """Test recommendations for a file with many functions."""
        recommendations = _generate_recommendations(
            lines=1800,
            functions=55,
            complexity=10,
            language='python'
        )
        
        recommendations_text = ' '.join(recommendations).lower()
        assert 'function' in recommendations_text or 'class' in recommendations_text
    
    def test_language_specific_recommendations_python(self):
        """Test that Python-specific recommendations are included."""
        recommendations = _generate_recommendations(
            lines=2500,
            functions=30,
            complexity=12,
            language='python'
        )
        
        recommendations_text = ' '.join(recommendations).lower()
        # Should mention Python-specific patterns
        assert 'python' in recommendations_text or 'package' in recommendations_text or 'dataclass' in recommendations_text
    
    def test_language_specific_recommendations_javascript(self):
        """Test that JavaScript-specific recommendations are included."""
        recommendations = _generate_recommendations(
            lines=2500,
            functions=30,
            complexity=12,
            language='javascript'
        )
        
        recommendations_text = ' '.join(recommendations).lower()
        # Should mention JS-specific patterns
        assert 'module' in recommendations_text or 'component' in recommendations_text or 'composition' in recommendations_text
    
    def test_returns_maximum_three_recommendations(self):
        """Test that no more than 3 recommendations are returned."""
        # Extreme values that would trigger many recommendations
        recommendations = _generate_recommendations(
            lines=5000,
            functions=100,
            complexity=50,
            language='python'
        )
        
        assert len(recommendations) <= 3


# Fixtures

@pytest.fixture
def temp_project():
    """Create a temporary project directory with some Python files."""
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir)
    
    # Create a basic Python file
    main_file = project_path / "main.py"
    main_file.write_text("""
def hello():
    print("Hello, World!")

def goodbye():
    print("Goodbye!")

if __name__ == "__main__":
    hello()
    goodbye()
""")
    
    # Create another file
    utils_file = project_path / "utils.py"
    utils_file.write_text("""
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
""")
    
    yield str(project_path)
    
    # Cleanup
    shutil.rmtree(temp_dir)
