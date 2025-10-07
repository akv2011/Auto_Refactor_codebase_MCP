"""
Codebase analysis orchestrator for TaskMaster MCP Server.

This module provides the analyze_codebase MCP tool that orchestrates file scanning
and metrics calculation to generate comprehensive codebase analysis reports.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

from .scanner import FileScanner
from .metrics_engine import MetricsEngine
from .config import RefactorConfig


class CodebaseAnalysisError(Exception):
    """Raised when codebase analysis fails."""
    pass


async def analyze_codebase(
    directory: str,
    threshold_lines: int = 1500,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None
) -> str:
    """
    Analyze codebase and identify files requiring refactoring.
    
    This is the main MCP tool for TaskMaster that scans a directory, calculates
    metrics for all supported files, and generates a JSON report identifying
    files that exceed configured thresholds.
    
    Args:
        directory: Root directory to analyze
        threshold_lines: Maximum lines per file (default: 1500)
        include_patterns: File patterns to include (e.g., ["*.py", "*.js"])
        exclude_patterns: Patterns to exclude (e.g., ["**/test/**"])
    
    Returns:
        JSON string with analysis report including files exceeding thresholds
        
    Raises:
        CodebaseAnalysisError: If analysis fails
        
    Example:
        >>> result = await analyze_codebase(
        ...     directory="/path/to/project",
        ...     threshold_lines=1500,
        ...     include_patterns=["*.py"],
        ...     exclude_patterns=["**/test/**"]
        ... )
        >>> report = json.loads(result)
        >>> print(f"Files exceeding threshold: {report['summary']['filesExceedingThreshold']}")
    """
    try:
        # Validate directory
        dir_path = Path(directory).resolve()
        if not dir_path.exists():
            raise CodebaseAnalysisError(f"Directory not found: {directory}")
        if not dir_path.is_dir():
            raise CodebaseAnalysisError(f"Path is not a directory: {directory}")
        
        # Load or create configuration
        config = _create_analysis_config(
            dir_path,
            threshold_lines,
            include_patterns,
            exclude_patterns
        )
        
        # Initialize scanner and metrics engine
        scanner = FileScanner(dir_path, config)
        metrics_engine = MetricsEngine()
        
        # Scan files
        all_files: List[Path] = []
        for file_path in scanner.walk():
            # Only include supported file types
            if metrics_engine.is_supported(file_path):
                all_files.append(file_path)
        
        # Calculate metrics for all files
        files_with_metrics: List[Dict[str, Any]] = []
        violations: List[Dict[str, Any]] = []
        total_lines = 0
        
        for file_path in all_files:
            try:
                # Calculate metrics for this file
                metric_report = metrics_engine.calculate(file_path)
                
                if metric_report['status'] == 'success':
                    metrics = metric_report['metrics']
                    loc = metrics.get('loc', 0) or 0
                    total_lines += loc
                    
                    file_info = {
                        'file': str(file_path.relative_to(dir_path)),
                        'absolute_path': str(file_path),
                        'language': metric_report['language'],
                        'lines': loc,
                        'functions': metrics.get('function_count', 0) or 0,
                        'complexity': metrics.get('cyclomatic_complexity', 0) or 0
                    }
                    
                    files_with_metrics.append(file_info)
                    
                    # Check if file exceeds threshold
                    if loc > threshold_lines:
                        violation = {
                            'file': str(file_path.relative_to(dir_path)),
                            'lines': loc,
                            'functions': metrics.get('function_count', 0) or 0,
                            'complexity': metrics.get('cyclomatic_complexity', 0) or 0,
                            'severity': _calculate_severity(loc, threshold_lines),
                            'recommendations': _generate_recommendations(
                                loc,
                                metrics.get('function_count', 0) or 0,
                                metrics.get('cyclomatic_complexity', 0) or 0,
                                metric_report['language']
                            )
                        }
                        violations.append(violation)
                        
            except Exception as e:
                # Log error but continue with other files
                # In production, you might want to log this
                continue
        
        # Build summary
        summary = {
            'totalFiles': len(all_files),
            'filesAnalyzed': len(files_with_metrics),
            'filesExceedingThreshold': len(violations),
            'totalLines': total_lines,
            'averageFileSize': round(total_lines / len(files_with_metrics)) if files_with_metrics else 0
        }
        
        # Build final report
        report = {
            'timestamp': datetime.now().isoformat() + 'Z',
            'projectPath': str(dir_path),
            'thresholds': {
                'maxLines': threshold_lines
            },
            'summary': summary,
            'violations': sorted(violations, key=lambda x: x['lines'], reverse=True)
        }
        
        # Return as JSON string
        return json.dumps(report, indent=2)
        
    except CodebaseAnalysisError:
        raise
    except Exception as e:
        raise CodebaseAnalysisError(f"Analysis failed: {e}") from e


def _create_analysis_config(
    dir_path: Path,
    threshold_lines: int,
    include_patterns: Optional[List[str]],
    exclude_patterns: Optional[List[str]]
) -> RefactorConfig:
    """
    Create a RefactorConfig for analysis.
    
    Args:
        dir_path: Root directory being analyzed
        threshold_lines: Line count threshold
        include_patterns: Patterns to include (currently not used, reserved for future)
        exclude_patterns: Additional patterns to exclude
    
    Returns:
        RefactorConfig instance
    """
    # Default exclude patterns
    default_excludes = [
        "**/node_modules/**",
        "**/venv/**",
        "**/.venv/**",
        "**/dist/**",
        "**/build/**",
        "**/__pycache__/**",
        "**/.git/**",
        "**/*.pyc",
        "**/*.min.js",
        "**/*.bundle.js"
    ]
    
    # Merge with user-provided excludes
    if exclude_patterns:
        all_excludes = default_excludes + exclude_patterns
    else:
        all_excludes = default_excludes
    
    # Create configuration with thresholds
    from config import ThresholdsConfig
    
    config = RefactorConfig(
        thresholds=ThresholdsConfig(maxLines=threshold_lines),
        exclude_patterns=all_excludes
    )
    
    return config
def _calculate_severity(lines: int, threshold: int) -> str:
    """
    Calculate violation severity based on how much the file exceeds the threshold.
    
    Args:
        lines: Actual line count
        threshold: Threshold line count
        
    Returns:
        Severity level: 'low', 'medium', 'high', or 'critical'
    """
    if lines <= threshold:
        return 'none'
    
    excess_ratio = (lines - threshold) / threshold
    
    if excess_ratio <= 0.5:  # Up to 50% over
        return 'low'
    elif excess_ratio <= 1.0:  # 50-100% over
        return 'medium'
    elif excess_ratio <= 2.0:  # 100-200% over
        return 'high'
    else:  # More than 200% over
        return 'critical'


def _generate_recommendations(
    lines: int,
    functions: int,
    complexity: float,
    language: str
) -> List[str]:
    """
    Generate refactoring recommendations based on metrics.
    
    Args:
        lines: Line count
        functions: Function count
        complexity: Cyclomatic complexity
        language: Programming language
        
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    # Basic size recommendation
    if lines > 3000:
        recommendations.append("Consider splitting into multiple modules")
    elif lines > 2000:
        recommendations.append("Split into logical components")
    else:
        recommendations.append("Extract utility functions to separate file")
    
    # Function count recommendation
    if functions > 50:
        recommendations.append("Group related functions into classes or modules")
    elif functions > 30:
        recommendations.append("Extract some functions to utility modules")
    
    # Complexity recommendation
    if complexity > 20:
        recommendations.append("Reduce complexity by simplifying control flow")
    elif complexity > 15:
        recommendations.append("Refactor complex functions into smaller ones")
    
    # Language-specific recommendations
    if language == 'python':
        if lines > 2000:
            recommendations.append("Create a Python package structure")
        recommendations.append("Consider using dataclasses or Pydantic models")
    elif language in ['javascript', 'typescript']:
        if lines > 2000:
            recommendations.append("Split into ES modules")
        recommendations.append("Use composition to break down large components")
    
    return recommendations[:3]  # Return top 3 recommendations
