"""
AST Wrapper for standardized parsing interface.

This module provides a wrapper class that encapsulates tree-sitter parsing logic,
offering a consistent interface for working with Abstract Syntax Trees across
multiple programming languages.
"""

from pathlib import Path
from typing import Union, Optional, List, Dict, Any

from .parser_factory import ParserFactory, ParserNotAvailableError
from .code_node import CodeNode, CodeNodeCollection


class ASTParsingError(Exception):
    """Raised when AST parsing fails."""
    pass


# Language-specific query patterns for common constructs
QUERY_PATTERNS = {
    "python": {
        "function": """
            (function_definition
                name: (identifier) @name
                parameters: (parameters) @parameters
                body: (block) @body) @definition
            
            (decorated_definition
                (function_definition
                    name: (identifier) @name
                    parameters: (parameters) @parameters
                    body: (block) @body) @definition
                decorators: (decorator)+ @decorators)
        """,
        "class": """
            (class_definition
                name: (identifier) @name
                superclasses: (argument_list)? @superclasses
                body: (block) @body) @definition
            
            (decorated_definition
                (class_definition
                    name: (identifier) @name
                    superclasses: (argument_list)? @superclasses
                    body: (block) @body) @definition
                decorators: (decorator)+ @decorators)
        """,
    },
    "javascript": {
        "function": """
            (function_declaration
                name: (identifier) @name
                parameters: (formal_parameters) @parameters
                body: (statement_block) @body) @definition
            
            (lexical_declaration
                (variable_declarator
                    name: (identifier) @name
                    value: (arrow_function
                        parameters: (formal_parameters)? @parameters
                        body: (_) @body))) @definition
            
            (method_definition
                name: (property_identifier) @name
                parameters: (formal_parameters) @parameters
                body: (statement_block) @body) @definition
            
            (export_statement
                declaration: (function_declaration
                    name: (identifier) @name
                    parameters: (formal_parameters) @parameters
                    body: (statement_block) @body) @definition)
        """,
        "class": """
            (class_declaration
                name: (identifier) @name
                heritage: (class_heritage)? @heritage
                body: (class_body) @body) @definition
            
            (export_statement
                declaration: (class_declaration
                    name: (identifier) @name
                    heritage: (class_heritage)? @heritage
                    body: (class_body) @body) @definition)
        """,
    },
    "typescript": {
        "function": """
            (function_declaration
                name: (identifier) @name
                parameters: (formal_parameters) @parameters
                body: (statement_block) @body) @definition
            
            (lexical_declaration
                (variable_declarator
                    name: (identifier) @name
                    value: (arrow_function
                        parameters: (formal_parameters)? @parameters
                        body: (_) @body))) @definition
            
            (method_definition
                name: (property_identifier) @name
                parameters: (formal_parameters) @parameters
                body: (statement_block) @body) @definition
            
            (export_statement
                declaration: (function_declaration
                    name: (identifier) @name
                    parameters: (formal_parameters) @parameters
                    body: (statement_block) @body) @definition)
        """,
        "class": """
            (class_declaration
                name: [(identifier) @name (type_identifier) @name]
                heritage: (class_heritage)? @heritage
                body: (class_body) @body) @definition
            
            (export_statement
                declaration: (class_declaration
                    name: [(identifier) @name (type_identifier) @name]
                    heritage: (class_heritage)? @heritage
                    body: (class_body) @body) @definition)
        """,
    },
    "java": {
        "function": """
            (method_declaration
                name: (identifier) @name
                parameters: (formal_parameters) @parameters
                body: (block) @body) @definition
            
            (constructor_declaration
                name: (identifier) @name
                parameters: (formal_parameters) @parameters
                body: (constructor_body) @body) @definition
        """,
        "class": """
            (class_declaration
                name: (identifier) @name
                superclass: (_)? @superclass
                interfaces: (_)? @interfaces
                body: (class_body) @body) @definition
            
            (interface_declaration
                name: (identifier) @name
                extends_interfaces: (_)? @interfaces
                body: (interface_body) @body) @definition
        """,
    },
    "csharp": {
        "function": """
            (method_declaration
                name: (identifier) @name
                parameters: (parameter_list) @parameters
                body: (block) @body) @definition
            
            (constructor_declaration
                (identifier) @name
                (parameter_list) @parameters
                body: (block) @body) @definition
        """,
        "class": """
            (class_declaration
                name: (identifier) @name
                base_list: (_)? @base
                body: (_)) @definition
            
            (interface_declaration
                name: (identifier) @name
                base_list: (_)? @base
                body: (_)) @definition
        """,
    },
    "sql": {
        "function": """
            (create_function_statement
                (function_name) @name) @definition
            
            (create_procedure_statement
                (procedure_name) @name) @definition
        """,
        "class": """
            (create_table_statement
                (table_name) @name) @definition
        """,
    },
}


class ASTWrapper:
    """
    Wrapper class for Abstract Syntax Trees.
    
    This class encapsulates the parsing logic and provides a standardized
    interface for interacting with parsed ASTs across multiple languages.
    """
    
    def __init__(
        self,
        source_code: Union[str, bytes],
        file_path: Union[str, Path],
        parser_factory: Optional[ParserFactory] = None
    ):
        """
        Initialize the AST wrapper and parse the source code.
        
        Args:
            source_code: Source code to parse (string or bytes)
            file_path: Path to the source file (used to determine language)
            parser_factory: ParserFactory instance. If None, creates a new one.
        
        Raises:
            ASTParsingError: If parsing fails
            ParserNotAvailableError: If language/extension not supported
        """
        self._source_code = source_code
        self._file_path = Path(file_path)
        self._parser_factory = parser_factory if parser_factory is not None else ParserFactory()
        self._root_node = None
        self._tree = None
        
        # Parse immediately on initialization
        self._parse()
    
    def _parse(self) -> None:
        """
        Parse the source code using the appropriate parser.
        
        Raises:
            ASTParsingError: If parsing fails
            ParserNotAvailableError: If parser not available for file type
        """
        try:
            # Get parser for file type
            parser = self._parser_factory.get_parser_for_file(self._file_path)
            
            # Convert source code to bytes if needed
            source_bytes = self._source_code
            if isinstance(source_bytes, str):
                source_bytes = source_bytes.encode('utf-8')
            
            # Parse the code
            self._tree = parser.parse(source_bytes)
            
            if self._tree is None:
                raise ASTParsingError(
                    f"Failed to parse {self._file_path}: Parser returned None"
                )
            
            self._root_node = self._tree.root_node
            
            if self._root_node is None:
                raise ASTParsingError(
                    f"Failed to parse {self._file_path}: No root node in parse tree"
                )
            
            # Check for parse errors
            if self._root_node.has_error:
                raise ASTParsingError(
                    f"Parse errors detected in {self._file_path}"
                )
                
        except ParserNotAvailableError:
            # Re-raise parser availability errors as-is
            raise
        except ASTParsingError:
            # Re-raise parsing errors as-is
            raise
        except Exception as e:
            raise ASTParsingError(
                f"Unexpected error parsing {self._file_path}: {e}"
            ) from e
    
    @property
    def root_node(self):
        """
        Get the root node of the AST.
        
        Returns:
            tree_sitter.Node: Root node of the parsed tree
        """
        return self._root_node
    
    @property
    def tree(self):
        """
        Get the complete parse tree.
        
        Returns:
            tree_sitter.Tree: Complete parse tree
        """
        return self._tree
    
    @property
    def source_code(self) -> Union[str, bytes]:
        """
        Get the original source code.
        
        Returns:
            Original source code as provided to constructor
        """
        return self._source_code
    
    @property
    def file_path(self) -> Path:
        """
        Get the file path.
        
        Returns:
            Path object for the source file
        """
        return self._file_path
    
    @property
    def language(self) -> str:
        """
        Get the detected language for the source code.
        
        Returns:
            Language identifier (e.g., 'python', 'javascript')
        """
        extension = self._file_path.suffix
        return self._parser_factory.setup.get_language_for_extension(extension)
    
    def has_errors(self) -> bool:
        """
        Check if the parsed tree contains any errors.
        
        Returns:
            True if parse errors exist, False otherwise
        """
        return self._root_node.has_error if self._root_node else True
    
    def get_node_text(self, node) -> str:
        """
        Get the source code text for a specific node.
        
        Args:
            node: tree_sitter.Node to extract text from
        
        Returns:
            Source code text for the node
        """
        if node is None:
            return ""
        
        source_bytes = self._source_code
        if isinstance(source_bytes, str):
            source_bytes = source_bytes.encode('utf-8')
        
        return source_bytes[node.start_byte:node.end_byte].decode('utf-8')
    
    def query(self, query_string: str) -> List[tuple]:
        """
        Execute a generic tree-sitter query on the AST.
        
        Args:
            query_string: S-expression query string in tree-sitter query language
        
        Returns:
            List of (node, capture_name) tuples from the query
        
        Raises:
            ASTParsingError: If query execution fails
        """
        try:
            from tree_sitter import Language
            
            # Get language object
            grammar_path = self._parser_factory.setup.get_grammar_path(self.language)
            lang = Language(str(grammar_path), self.language)
            
            # Create and execute query
            query = lang.query(query_string)
            captures = query.captures(self._root_node)
            
            return captures
            
        except Exception as e:
            raise ASTParsingError(
                f"Failed to execute query: {e}"
            ) from e
    
    def _group_captures(self, captures: List[tuple]) -> List[Dict[str, Any]]:
        """
        Group query captures by definition node.
        
        Args:
            captures: List of (node, capture_name) tuples
        
        Returns:
            List of dictionaries with grouped captures
        """
        grouped = {}
        
        for node, capture_name in captures:
            # Find the definition node (marked with @definition in queries)
            if capture_name == "definition":
                def_id = id(node)
                if def_id not in grouped:
                    grouped[def_id] = {
                        "definition_node": node,
                        "captures": {}
                    }
            else:
                # Find parent definition for this capture
                current = node
                while current:
                    def_id = id(current)
                    if def_id in grouped:
                        grouped[def_id]["captures"][capture_name] = node
                        break
                    current = current.parent
        
        return list(grouped.values())
    
    def find_function_definitions(self) -> CodeNodeCollection:
        """
        Find all function definitions in the parsed code.
        
        Returns:
            CodeNodeCollection containing CodeNode objects for each function.
            Each CodeNode has type='function' (or 'method' for class methods).
        
        Raises:
            ASTParsingError: If query fails or language not supported
        """
        language = self.language
        
        if language not in QUERY_PATTERNS:
            raise ASTParsingError(
                f"Function queries not supported for language: {language}"
            )
        
        query_string = QUERY_PATTERNS[language].get("function")
        if not query_string:
            return CodeNodeCollection()
        
        captures = self.query(query_string)
        grouped = self._group_captures(captures)
        
        nodes = []
        for group in grouped:
            def_node = group["definition_node"]
            captures_dict = group["captures"]
            
            # Extract name from captures
            name_node = captures_dict.get("name")
            name = self.get_node_text(name_node) if name_node else "<anonymous>"
            
            # Determine type based on node type or context
            node_type = "function"
            if def_node.type in ("method_definition", "method_declaration"):
                node_type = "method"
            elif def_node.type in ("constructor_declaration", "constructor_body"):
                node_type = "constructor"
            
            # Extract metadata
            metadata = {}
            if "parameters" in captures_dict:
                metadata["parameters"] = self.get_node_text(captures_dict["parameters"])
            if "decorators" in captures_dict:
                metadata["decorators"] = self.get_node_text(captures_dict["decorators"])
            if "body" in captures_dict:
                metadata["body_start_line"] = captures_dict["body"].start_point[0] + 1
            
            code_node = CodeNode(
                type=node_type,
                name=name,
                start_line=def_node.start_point[0] + 1,  # tree-sitter is 0-indexed
                end_line=def_node.end_point[0] + 1,
                source_text=self.get_node_text(def_node),
                file_path=self._file_path,
                language=language,
                node=def_node,
                metadata=metadata
            )
            nodes.append(code_node)
        
        return CodeNodeCollection(nodes)
    
    def find_class_declarations(self) -> CodeNodeCollection:
        """
        Find all class declarations in the parsed code.
        
        Returns:
            CodeNodeCollection containing CodeNode objects for each class.
            Each CodeNode has type='class', 'interface', or 'struct'.
        
        Raises:
            ASTParsingError: If query fails or language not supported
        """
        language = self.language
        
        if language not in QUERY_PATTERNS:
            raise ASTParsingError(
                f"Class queries not supported for language: {language}"
            )
        
        query_string = QUERY_PATTERNS[language].get("class")
        if not query_string:
            return CodeNodeCollection()
        
        captures = self.query(query_string)
        grouped = self._group_captures(captures)
        
        nodes = []
        for group in grouped:
            def_node = group["definition_node"]
            captures_dict = group["captures"]
            
            # Extract name from captures
            name_node = captures_dict.get("name")
            name = self.get_node_text(name_node) if name_node else "<anonymous>"
            
            # Determine type based on node type
            node_type = "class"
            if def_node.type == "interface_declaration":
                node_type = "interface"
            elif def_node.type == "struct_declaration":
                node_type = "struct"
            elif def_node.type == "create_table_statement":
                node_type = "table"  # SQL tables
            
            # Extract metadata
            metadata = {}
            if "superclass" in captures_dict or "superclasses" in captures_dict:
                superclass_node = captures_dict.get("superclass") or captures_dict.get("superclasses")
                metadata["superclass"] = self.get_node_text(superclass_node)
            if "interfaces" in captures_dict:
                metadata["interfaces"] = self.get_node_text(captures_dict["interfaces"])
            if "heritage" in captures_dict:
                metadata["heritage"] = self.get_node_text(captures_dict["heritage"])
            if "base" in captures_dict:
                metadata["base"] = self.get_node_text(captures_dict["base"])
            if "decorators" in captures_dict:
                metadata["decorators"] = self.get_node_text(captures_dict["decorators"])
            if "body" in captures_dict:
                metadata["body_start_line"] = captures_dict["body"].start_point[0] + 1
            
            code_node = CodeNode(
                type=node_type,
                name=name,
                start_line=def_node.start_point[0] + 1,
                end_line=def_node.end_point[0] + 1,
                source_text=self.get_node_text(def_node),
                file_path=self._file_path,
                language=language,
                node=def_node,
                metadata=metadata
            )
            nodes.append(code_node)
        
        return CodeNodeCollection(nodes)
    
    def __repr__(self) -> str:
        """String representation of the wrapper."""
        status = "parsed" if self._root_node and not self.has_errors() else "error"
        return f"ASTWrapper(file={self._file_path.name}, language={self.language}, status={status})"
