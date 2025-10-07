"""
Tests for CodeNode data structures.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from src.code_node import CodeNode, CodeNodeCollection


class TestCodeNode:
    """Test CodeNode dataclass."""
    
    def test_basic_initialization(self):
        """Test basic CodeNode creation."""
        node = CodeNode(
            type="function",
            name="my_function",
            start_line=1,
            end_line=10,
            source_text="def my_function():\n    pass"
        )
        
        assert node.type == "function"
        assert node.name == "my_function"
        assert node.start_line == 1
        assert node.end_line == 10
        assert node.line_count == 10
    
    def test_initialization_with_optional_fields(self):
        """Test CodeNode with all optional fields."""
        file_path = Path("test.py")
        tree_node = Mock()
        
        node = CodeNode(
            type="class",
            name="MyClass",
            start_line=5,
            end_line=20,
            source_text="class MyClass:\n    pass",
            file_path=file_path,
            language="python",
            node=tree_node,
            metadata={"decorators": "@dataclass"}
        )
        
        assert node.file_path == file_path
        assert node.language == "python"
        assert node.node is tree_node
        assert node.metadata["decorators"] == "@dataclass"
    
    def test_validation_start_line_must_be_positive(self):
        """Test that start_line must be >= 1."""
        with pytest.raises(ValueError, match="start_line must be >= 1"):
            CodeNode(
                type="function",
                name="test",
                start_line=0,
                end_line=5,
                source_text="code"
            )
    
    def test_validation_end_line_must_be_after_start(self):
        """Test that end_line must be >= start_line."""
        with pytest.raises(ValueError, match="end_line .* must be >= start_line"):
            CodeNode(
                type="function",
                name="test",
                start_line=10,
                end_line=5,
                source_text="code"
            )
    
    def test_validation_name_cannot_be_empty(self):
        """Test that name cannot be empty."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            CodeNode(
                type="function",
                name="",
                start_line=1,
                end_line=5,
                source_text="code"
            )
    
    def test_validation_type_cannot_be_empty(self):
        """Test that type cannot be empty."""
        with pytest.raises(ValueError, match="type cannot be empty"):
            CodeNode(
                type="",
                name="test",
                start_line=1,
                end_line=5,
                source_text="code"
            )
    
    def test_line_count_property(self):
        """Test line_count calculation."""
        node = CodeNode(
            type="function",
            name="test",
            start_line=5,
            end_line=15,
            source_text="code"
        )
        
        assert node.line_count == 11
    
    def test_is_function_property(self):
        """Test is_function property."""
        function_node = CodeNode(type="function", name="f", start_line=1, end_line=5, source_text="")
        method_node = CodeNode(type="method", name="m", start_line=1, end_line=5, source_text="")
        constructor_node = CodeNode(type="constructor", name="c", start_line=1, end_line=5, source_text="")
        class_node = CodeNode(type="class", name="C", start_line=1, end_line=5, source_text="")
        
        assert function_node.is_function is True
        assert method_node.is_function is True
        assert constructor_node.is_function is True
        assert class_node.is_function is False
    
    def test_is_class_property(self):
        """Test is_class property."""
        class_node = CodeNode(type="class", name="C", start_line=1, end_line=5, source_text="")
        interface_node = CodeNode(type="interface", name="I", start_line=1, end_line=5, source_text="")
        struct_node = CodeNode(type="struct", name="S", start_line=1, end_line=5, source_text="")
        function_node = CodeNode(type="function", name="f", start_line=1, end_line=5, source_text="")
        
        assert class_node.is_class is True
        assert interface_node.is_class is True
        assert struct_node.is_class is True
        assert function_node.is_class is False
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        node = CodeNode(
            type="function",
            name="test",
            start_line=1,
            end_line=10,
            source_text="code",
            file_path=Path("test.py"),
            language="python",
            metadata={"params": "x, y"}
        )
        
        result = node.to_dict()
        
        assert result["type"] == "function"
        assert result["name"] == "test"
        assert result["start_line"] == 1
        assert result["end_line"] == 10
        assert result["source_text"] == "code"
        assert result["file_path"] == "test.py"
        assert result["language"] == "python"
        assert result["line_count"] == 10
        assert result["metadata"]["params"] == "x, y"
        assert "node" not in result  # tree-sitter node excluded
    
    def test_str_representation(self):
        """Test string representation."""
        node = CodeNode(
            type="function",
            name="my_func",
            start_line=5,
            end_line=15,
            source_text="code",
            file_path=Path("test.py")
        )
        
        result = str(node)
        
        assert "function" in result
        assert "my_func" in result
        assert "test.py:5" in result
        assert "11 lines" in result


class TestCodeNodeCollection:
    """Test CodeNodeCollection."""
    
    def test_empty_collection(self):
        """Test empty collection."""
        collection = CodeNodeCollection()
        
        assert len(collection) == 0
        assert list(collection) == []
    
    def test_collection_with_nodes(self):
        """Test collection with nodes."""
        nodes = [
            CodeNode(type="function", name="f1", start_line=1, end_line=5, source_text=""),
            CodeNode(type="function", name="f2", start_line=10, end_line=15, source_text="")
        ]
        collection = CodeNodeCollection(nodes)
        
        assert len(collection) == 2
        assert collection[0].name == "f1"
        assert collection[1].name == "f2"
    
    def test_filter_by_type(self):
        """Test filtering by type."""
        nodes = [
            CodeNode(type="function", name="f1", start_line=1, end_line=5, source_text=""),
            CodeNode(type="class", name="C1", start_line=10, end_line=20, source_text=""),
            CodeNode(type="function", name="f2", start_line=25, end_line=30, source_text="")
        ]
        collection = CodeNodeCollection(nodes)
        
        functions = collection.filter_by_type("function")
        
        assert len(functions) == 2
        assert functions[0].name == "f1"
        assert functions[1].name == "f2"
    
    def test_filter_by_language(self):
        """Test filtering by language."""
        nodes = [
            CodeNode(type="function", name="f1", start_line=1, end_line=5, source_text="", language="python"),
            CodeNode(type="function", name="f2", start_line=1, end_line=5, source_text="", language="javascript"),
            CodeNode(type="function", name="f3", start_line=1, end_line=5, source_text="", language="python")
        ]
        collection = CodeNodeCollection(nodes)
        
        python_nodes = collection.filter_by_language("python")
        
        assert len(python_nodes) == 2
        assert python_nodes[0].name == "f1"
        assert python_nodes[1].name == "f3"
    
    def test_filter_by_name_exact(self):
        """Test filtering by exact name."""
        nodes = [
            CodeNode(type="function", name="foo", start_line=1, end_line=5, source_text=""),
            CodeNode(type="function", name="bar", start_line=1, end_line=5, source_text=""),
            CodeNode(type="function", name="foo_bar", start_line=1, end_line=5, source_text="")
        ]
        collection = CodeNodeCollection(nodes)
        
        result = collection.filter_by_name("foo", exact=True)
        
        assert len(result) == 1
        assert result[0].name == "foo"
    
    def test_filter_by_name_substring(self):
        """Test filtering by substring."""
        nodes = [
            CodeNode(type="function", name="foo", start_line=1, end_line=5, source_text=""),
            CodeNode(type="function", name="bar", start_line=1, end_line=5, source_text=""),
            CodeNode(type="function", name="foo_bar", start_line=1, end_line=5, source_text="")
        ]
        collection = CodeNodeCollection(nodes)
        
        result = collection.filter_by_name("foo", exact=False)
        
        assert len(result) == 2
        assert "foo" in result[0].name
        assert "foo" in result[1].name
    
    def test_get_functions(self):
        """Test getting all function-like nodes."""
        nodes = [
            CodeNode(type="function", name="f1", start_line=1, end_line=5, source_text=""),
            CodeNode(type="method", name="m1", start_line=1, end_line=5, source_text=""),
            CodeNode(type="class", name="C1", start_line=1, end_line=5, source_text=""),
            CodeNode(type="constructor", name="init", start_line=1, end_line=5, source_text="")
        ]
        collection = CodeNodeCollection(nodes)
        
        functions = collection.get_functions()
        
        assert len(functions) == 3  # function, method, constructor
        assert all(node.is_function for node in functions)
    
    def test_get_classes(self):
        """Test getting all class-like nodes."""
        nodes = [
            CodeNode(type="function", name="f1", start_line=1, end_line=5, source_text=""),
            CodeNode(type="class", name="C1", start_line=1, end_line=5, source_text=""),
            CodeNode(type="interface", name="I1", start_line=1, end_line=5, source_text=""),
            CodeNode(type="struct", name="S1", start_line=1, end_line=5, source_text="")
        ]
        collection = CodeNodeCollection(nodes)
        
        classes = collection.get_classes()
        
        assert len(classes) == 3  # class, interface, struct
        assert all(node.is_class for node in classes)
    
    def test_group_by_file(self):
        """Test grouping by file."""
        file1 = Path("test1.py")
        file2 = Path("test2.py")
        
        nodes = [
            CodeNode(type="function", name="f1", start_line=1, end_line=5, source_text="", file_path=file1),
            CodeNode(type="function", name="f2", start_line=1, end_line=5, source_text="", file_path=file1),
            CodeNode(type="function", name="f3", start_line=1, end_line=5, source_text="", file_path=file2)
        ]
        collection = CodeNodeCollection(nodes)
        
        grouped = collection.group_by_file()
        
        assert len(grouped) == 2
        assert len(grouped[file1]) == 2
        assert len(grouped[file2]) == 1
    
    def test_group_by_type(self):
        """Test grouping by type."""
        nodes = [
            CodeNode(type="function", name="f1", start_line=1, end_line=5, source_text=""),
            CodeNode(type="function", name="f2", start_line=1, end_line=5, source_text=""),
            CodeNode(type="class", name="C1", start_line=1, end_line=5, source_text="")
        ]
        collection = CodeNodeCollection(nodes)
        
        grouped = collection.group_by_type()
        
        assert len(grouped) == 2
        assert len(grouped["function"]) == 2
        assert len(grouped["class"]) == 1
    
    def test_to_list(self):
        """Test converting to list of dictionaries."""
        nodes = [
            CodeNode(type="function", name="f1", start_line=1, end_line=5, source_text=""),
            CodeNode(type="class", name="C1", start_line=1, end_line=5, source_text="")
        ]
        collection = CodeNodeCollection(nodes)
        
        result = collection.to_list()
        
        assert len(result) == 2
        assert result[0]["name"] == "f1"
        assert result[1]["name"] == "C1"
        assert all(isinstance(item, dict) for item in result)
