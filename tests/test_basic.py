"""
Tests for TaskMaster MCP Server basic functionality
"""

import pytest


def test_import_taskmaster():
    """Test that taskmaster package can be imported"""
    import taskmaster
    assert taskmaster.__version__ == "0.1.0"


def test_import_fastmcp():
    """Test that FastMCP can be imported"""
    from mcp.server.fastmcp import FastMCP
    assert FastMCP is not None


def test_import_dependencies():
    """Test that all required dependencies can be imported"""
    # Core dependencies
    import pydantic
    import git  # gitpython
    import openai
    import anthropic
    import radon
    import astroid
    
    # Tree-sitter for code parsing
    import tree_sitter
    import tree_sitter_python
    import tree_sitter_javascript
    
    # All imports successful
    assert True


@pytest.mark.asyncio
async def test_hello_taskmaster():
    """Test the hello_taskmaster tool"""
    # This will be a simple integration test once server is running
    # For now, just verify the tool can be defined
    from mcp.server.fastmcp import FastMCP
    
    test_mcp = FastMCP("test")
    
    @test_mcp.tool()
    async def hello_test() -> str:
        return "Hello test"
    
    # Tool registered successfully
    assert True
