"""
Refactoring Execution Engine for applying code transformations.

This module provides the core logic for applying refactoring operations
to source code files using AST manipulation and text-based transformations.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from .parser_factory import ParserFactory, ParserNotAvailableError
from .parser_setup import TreeSitterSetup


class RefactoringError(Exception):
    """Base exception for refactoring errors."""
    pass


class UnsupportedOperationError(RefactoringError):
    """Raised when an unsupported refactoring operation is requested."""
    pass


class RefactoringValidationError(RefactoringError):
    """Raised when refactoring operation parameters are invalid."""
    pass


class ParsingError(RefactoringError):
    """Raised when AST parsing fails."""
    pass


class CodeGenerationError(RefactoringError):
    """Raised when code generation from AST fails."""
    pass


class RefactoringEngine:
    """
    Core engine for applying refactoring transformations to source code.
    
    This engine supports various refactoring operations including:
    - Function extraction (extract_function)
    - File splitting (split_file)
    - Diff application (apply_diff)
    - And more to be added
    
    The engine uses tree-sitter for AST-based transformations and supports
    both structured code manipulation and text-based operations.
    
    Example:
        >>> engine = RefactoringEngine()
        >>> operation = {
        ...     'type': 'extract_function',
        ...     'source_file': 'module.py',
        ...     'target_file': 'helpers.py',
        ...     'function_name': 'helper_function'
        ... }
        >>> result = engine.apply(operation)
    """
    
    def __init__(self):
        """
        Initialize the RefactoringEngine.
        
        Sets up the operation handlers and prepares the engine for
        refactoring operations.
        """
        self._operation_handlers = {
            'extract_function': self._handle_extract_function,
            'split_file': self._handle_split_file,
            'apply_diff': self._handle_apply_diff,
            'rename_symbol': self._handle_rename_symbol,
            'inline_function': self._handle_inline_function,
        }
        # Initialize parser factory for AST operations
        self._parser_factory = ParserFactory()
        # Initialize tree-sitter setup for modern AST parsing
        self.ts_setup = TreeSitterSetup()
    
    def apply(self, operation_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a refactoring operation based on the provided details.
        
        This is the main entry point for all refactoring operations. It validates
        the operation details and delegates to the appropriate handler.
        
        Args:
            operation_details: Dictionary containing:
                - type: Operation type (required)
                - Additional parameters specific to the operation
                
        Returns:
            Dictionary containing:
                - status: 'success' or 'error'
                - modified_files: List of files that were modified
                - created_files: List of files that were created
                - message: Description of the result
                - error: Error message if status is 'error'
                
        Raises:
            RefactoringValidationError: If operation_details is invalid
            UnsupportedOperationError: If operation type is not supported
            
        Example:
            >>> engine = RefactoringEngine()
            >>> operation = {
            ...     'type': 'extract_function',
            ...     'source_file': 'app.py',
            ...     'function_name': 'helper'
            ... }
            >>> result = engine.apply(operation)
            >>> print(result['status'])
            success
        """
        # Validate operation details
        if not isinstance(operation_details, dict):
            raise RefactoringValidationError(
                "operation_details must be a dictionary"
            )
        
        if 'type' not in operation_details:
            raise RefactoringValidationError(
                "operation_details must include 'type' field"
            )
        
        operation_type = operation_details['type']
        
        # Check if operation is supported
        if operation_type not in self._operation_handlers:
            raise UnsupportedOperationError(
                f"Unsupported operation type: '{operation_type}'. "
                f"Supported operations: {', '.join(self._operation_handlers.keys())}"
            )
        
        # Get the handler
        handler = self._operation_handlers[operation_type]
        
        # Execute the operation
        try:
            result = handler(operation_details)
            return result
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'modified_files': [],
                'created_files': [],
                'message': f"Operation failed: {e}"
            }
    
    def get_supported_operations(self) -> list[str]:
        """
        Get list of supported refactoring operations.
        
        Returns:
            List of operation type strings
            
        Example:
            >>> engine = RefactoringEngine()
            >>> ops = engine.get_supported_operations()
            >>> print(ops)
            ['extract_function', 'split_file', 'apply_diff', ...]
        """
        return list(self._operation_handlers.keys())
    
    def is_operation_supported(self, operation_type: str) -> bool:
        """
        Check if a specific operation type is supported.
        
        Args:
            operation_type: Type of operation to check
            
        Returns:
            True if operation is supported, False otherwise
            
        Example:
            >>> engine = RefactoringEngine()
            >>> if engine.is_operation_supported('extract_function'):
            ...     print("Supported")
        """
        return operation_type in self._operation_handlers
    
    # AST Parsing and Code Generation Methods
    
    def _parse_file_to_ast(self, file_path: str):
        """
        Parse a source code file to an Abstract Syntax Tree (AST).
        
        This method reads a file, detects its language based on the file extension,
        and uses the appropriate tree-sitter parser to generate an AST.
        
        Args:
            file_path: Path to the source code file to parse
            
        Returns:
            tree_sitter.Tree object representing the parsed AST
            
        Raises:
            ParsingError: If file cannot be read or parsed
            ParserNotAvailableError: If no parser available for the file type
            
        Example:
            >>> engine = RefactoringEngine()
            >>> ast = engine._parse_file_to_ast('module.py')
            >>> print(ast.root_node.type)
            module
        """
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            raise ParsingError(f"File not found: {file_path}")
        
        # Check if it's a file (not directory)
        if not path.is_file():
            raise ParsingError(f"Path is not a file: {file_path}")
        
        try:
            # Read file content
            with open(path, 'rb') as f:
                source_code = f.read()
        except Exception as e:
            raise ParsingError(f"Failed to read file {file_path}: {e}") from e
        
        try:
            # Get language for file extension
            extension = path.suffix
            language = TreeSitterSetup.get_language_for_extension(extension)
            
            if not language:
                raise ParserNotAvailableError(
                    f"Unsupported file extension: {extension}"
                )
            
            # Get parser for the language using tree-sitter setup
            parser = self.ts_setup.get_parser(language)
        except (ParserNotAvailableError, Exception) as e:
            raise ParsingError(
                f"Cannot parse {file_path}: {e}"
            ) from e
        
        try:
            # Parse the source code
            tree = parser.parse(source_code)
            
            if tree is None:
                raise ParsingError(f"Parser returned None for {file_path}")
            
            # Check for parsing errors
            if tree.root_node.has_error:
                raise ParsingError(
                    f"Syntax errors detected in {file_path}. "
                    f"The file may contain invalid syntax."
                )
            
            return tree
            
        except Exception as e:
            if isinstance(e, ParsingError):
                raise
            raise ParsingError(f"Failed to parse {file_path}: {e}") from e
    
    def _generate_code_from_ast(self, ast, original_source: Optional[bytes] = None) -> str:
        """
        Generate source code from an Abstract Syntax Tree (AST).
        
        This method converts a tree-sitter AST back into formatted source code.
        It preserves the original formatting by extracting text from the tree nodes.
        
        Args:
            ast: tree_sitter.Tree object to convert to source code
            original_source: Original source code bytes (optional, for better formatting)
            
        Returns:
            String containing the generated source code
            
        Raises:
            CodeGenerationError: If code generation fails
            
        Example:
            >>> engine = RefactoringEngine()
            >>> ast = engine._parse_file_to_ast('module.py')
            >>> code = engine._generate_code_from_ast(ast)
            >>> print(code)
            # ... source code ...
        """
        if ast is None:
            raise CodeGenerationError("AST is None, cannot generate code")
        
        try:
            # Get the root node
            root_node = ast.root_node
            
            # If we have the original source, use it to extract text
            # This preserves original formatting
            if original_source is not None:
                if isinstance(original_source, str):
                    original_source = original_source.encode('utf-8')
                
                # Extract text from the root node using original source
                code_bytes = original_source[root_node.start_byte:root_node.end_byte]
                return code_bytes.decode('utf-8')
            
            # If no original source, we need to traverse the tree
            # and reconstruct the code from node text
            # This is a fallback and may not preserve all formatting
            def extract_text(node) -> str:
                """Recursively extract text from nodes."""
                if node.child_count == 0:
                    # Leaf node - return its text representation
                    # Note: Without original source, we can't get the actual text
                    # This is a limitation of tree-sitter
                    return ""
                
                # Non-leaf node - concatenate children
                result = []
                for child in node.children:
                    result.append(extract_text(child))
                return "".join(result)
            
            # Without original source, we cannot reliably reconstruct code
            # tree-sitter AST nodes don't store the actual text
            raise CodeGenerationError(
                "Cannot generate code without original source. "
                "Please provide original_source parameter."
            )
            
        except Exception as e:
            if isinstance(e, CodeGenerationError):
                raise
            raise CodeGenerationError(f"Failed to generate code from AST: {e}") from e
    
    # Private handler methods (to be implemented in subsequent subtasks)
    
    def _handle_extract_function(
        self, 
        operation_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle function extraction refactoring.
        
        Args:
            operation_details: Details including:
                - source_file: Source file path
                - target_file: Target file path (where to extract to)
                - function_name: Name of function to extract
                
        Returns:
            Result dictionary with status and affected files
        
        Raises:
            RefactoringValidationError: If required parameters are missing
            RefactoringError: If extraction fails
        """
        # Validate parameters
        required_params = ['source_file', 'target_file', 'function_name']
        for param in required_params:
            if param not in operation_details:
                raise RefactoringValidationError(
                    f"Missing required parameter: {param}"
                )
        
        source_file = Path(operation_details['source_file'])
        target_file = Path(operation_details['target_file'])
        function_name = operation_details['function_name']
        
        try:
            # Parse source file to AST
            with open(source_file, 'rb') as f:
                source_bytes = f.read()
            
            source_tree = self._parse_file_to_ast(str(source_file))
            
            if not source_tree:
                raise RefactoringError(
                    f"Failed to parse source file: {source_file}"
                )
            
            # Find the function definition node using tree-sitter query
            function_node = self._find_function_node(
                source_tree, function_name, source_bytes
            )
            
            if not function_node:
                raise RefactoringError(
                    f"Function '{function_name}' not found in {source_file}"
                )
            
            # Extract the function text
            function_text = source_bytes[
                function_node.start_byte:function_node.end_byte
            ].decode('utf-8')
            
            # Create modified source without the function
            modified_source_bytes = self._remove_function_and_add_call(
                source_bytes, function_node, function_name
            )
            
            # Add import for the extracted function in the source file
            # Calculate the relative import path from source to target
            target_module = self._get_module_name_from_path(source_file, target_file)
            
            # Re-parse the modified source to add import
            parser = self.ts_setup.get_parser('python')
            modified_tree = parser.parse(modified_source_bytes)
            
            # Add import statement for the extracted function
            modified_source_with_import = self._add_import_to_ast(
                modified_tree,
                modified_source_bytes,
                target_module,
                [function_name]
            )
            
            # Handle target file
            # Check if target file exists
            if target_file.exists():
                # Target file exists, append to it
                with open(target_file, 'rb') as f:
                    target_bytes = f.read()
                target_tree = self._parse_file_to_ast(str(target_file))
            else:
                # Target file doesn't exist, create empty structure
                target_bytes = b''
                # Create minimal Python file
                target_bytes = b'"""Extracted functions."""\n\n'
                target_tree = parser.parse(target_bytes)
            
            # Add export to __all__ in target file
            target_with_export = self._add_export_to_ast(
                target_tree,
                target_bytes,
                function_name
            )
            
            # Re-parse after adding export
            target_tree = parser.parse(target_with_export)
            
            # Find imports used in the extracted function
            function_imports = self._find_function_dependencies(
                function_node, source_bytes, source_tree
            )
            
            # Add necessary imports to target file
            target_final = target_with_export
            for imp_module, imp_symbols in function_imports.items():
                target_tree = parser.parse(target_final)
                target_final = self._add_import_to_ast(
                    target_tree,
                    target_final,
                    imp_module,
                    imp_symbols if imp_symbols else None
                )
            
            # Append the extracted function to the target file
            target_final = target_final + b'\n\n' + function_text.encode('utf-8') + b'\n'
            
            # Write modified source back
            with open(source_file, 'wb') as f:
                f.write(modified_source_with_import)
            
            # Write target file
            with open(target_file, 'wb') as f:
                f.write(target_final)
            
            return {
                'status': 'success',
                'affected_files': [str(source_file), str(target_file)],
                'message': f"Successfully extracted function '{function_name}' to {target_file.name}"
            }
            
        except Exception as e:
            if isinstance(e, (RefactoringValidationError, RefactoringError)):
                raise
            raise RefactoringError(
                f"Failed to extract function: {e}"
            ) from e
    
    def _find_function_node(self, tree: Any, function_name: str, source_bytes: bytes):
        """
        Find a function definition node by name using tree-sitter query.
        
        Args:
            tree: Tree-sitter Tree object
            function_name: Name of function to find
            source_bytes: Original source code as bytes
        
        Returns:
            Function definition node or None if not found
        """
        from tree_sitter import Query, QueryCursor
        
        # Get language from parser setup
        language = self.ts_setup.get_language('python')
        
        # Create query to find function definitions
        query = Query(
            language,
            """
            (function_definition
              name: (identifier) @function.name
            ) @function.def
            """
        )
        
        cursor = QueryCursor(query)
        captures = cursor.captures(tree.root_node)
        
        # Find the function with matching name
        for capture_name, nodes in captures.items():
            if capture_name == "function.name":
                for captured_node in nodes:
                    # Extract the function name text
                    name_text = source_bytes[
                        captured_node.start_byte:captured_node.end_byte
                    ].decode('utf-8')
                    
                    if name_text == function_name:
                        # Return the parent function_definition node
                        return captured_node.parent
        
        return None
    
    def _remove_function_and_add_call(
        self, 
        source_bytes: bytes,
        function_node: Any,
        function_name: str
    ) -> bytes:
        """
        Remove function from source and replace with a call.
        
        Args:
            source_bytes: Original source code
            function_node: Function definition node to remove
            function_name: Name of the function
        
        Returns:
            Modified source code as bytes
        """
        # Simple implementation: remove the function and add a comment
        # A proper implementation would add an actual function call
        before = source_bytes[:function_node.start_byte]
        after = source_bytes[function_node.end_byte:]
        
        # Add a placeholder comment where the function was
        placeholder = f"# Function '{function_name}' extracted\n".encode('utf-8')
        
        return before + placeholder + after
    
    def _get_module_name_from_path(
        self,
        source_file: Path,
        target_file: Path
    ) -> str:
        """
        Calculate the module name for importing from target into source.
        
        This calculates the relative module path between two Python files.
        
        Args:
            source_file: Path to the source file (where import will be added)
            target_file: Path to the target file (module being imported)
            
        Returns:
            Module name as a string (e.g., 'helpers', '.helpers', '..utils.helpers')
            
        Example:
            >>> source = Path('src/main.py')
            >>> target = Path('src/helpers.py')
            >>> _get_module_name_from_path(source, target)
            '.helpers'
        """
        # Convert to absolute paths
        source_abs = source_file.resolve()
        target_abs = target_file.resolve()
        
        # Get parent directories
        source_dir = source_abs.parent
        target_dir = target_abs.parent
        
        # Get module name (filename without .py extension)
        target_module_name = target_abs.stem
        
        # If in the same directory, use relative import
        if source_dir == target_dir:
            return f".{target_module_name}"
        
        # Try to find relative path
        try:
            # Get relative path from source dir to target dir
            rel_path = target_dir.relative_to(source_dir)
            # Build module path with dots
            module_parts = list(rel_path.parts) + [target_module_name]
            return '.' + '.'.join(module_parts)
        except ValueError:
            # target_dir is not relative to source_dir
            pass
        
        try:
            # Try the other direction (going up from source)
            rel_path = source_dir.relative_to(target_dir)
            # Count levels up
            levels_up = len(rel_path.parts)
            dots = '.' * (levels_up + 1)
            return f"{dots}{target_module_name}"
        except ValueError:
            # Not in a simple relative path
            pass
        
        # Fallback: use absolute import (just the target module name)
        # This assumes both files are in the same Python package
        return target_module_name
    
    def _find_function_dependencies(
        self,
        function_node: Any,
        source_bytes: bytes,
        source_tree: Any
    ) -> Dict[str, Optional[list[str]]]:
        """
        Find imports that a function depends on.
        
        This analyzes the function body to find all identifiers used,
        then matches them against imports in the source file.
        
        Args:
            function_node: AST node for the function definition
            source_bytes: Source code as bytes
            source_tree: Full source tree
            
        Returns:
            Dictionary mapping module names to lists of imported symbols.
            For regular imports (import x), symbols list is None.
            For from-imports (from x import y), symbols list contains the names.
            
        Example:
            >>> deps = _find_function_dependencies(func_node, source, tree)
            >>> print(deps)
            {'pathlib': ['Path'], 'os': None}
        """
        from tree_sitter import Query, QueryCursor
        
        # Find all imports in the source file
        all_imports = self._find_imports(source_tree, source_bytes)
        
        # Create a map of symbol names to their import info
        symbol_to_import = {}
        
        for imp in all_imports:
            if imp['type'] == 'import':
                # Regular import: import os, import json as js
                module = imp['module']
                alias = imp['alias']
                # The accessible name is the alias if present, otherwise the module name
                accessible_name = alias if alias else module.split('.')[0]
                symbol_to_import[accessible_name] = {
                    'module': module,
                    'symbols': None,  # Regular import
                    'alias': alias
                }
            elif imp['type'] == 'from_import':
                # From-import: from pathlib import Path
                module = imp['module']
                for symbol in imp['symbols']:
                    # Handle "symbol as alias" case
                    if ' as ' in symbol:
                        sym_name, sym_alias = symbol.split(' as ', 1)
                        accessible_name = sym_alias.strip()
                        actual_symbol = sym_name.strip()
                    else:
                        accessible_name = symbol
                        actual_symbol = symbol
                    
                    symbol_to_import[accessible_name] = {
                        'module': module,
                        'symbols': [actual_symbol],
                        'alias': None
                    }
        
        # Find all identifiers used in the function
        identifier_query = Query(
            self.ts_setup.get_language('python'),
            "(identifier) @id"
        )
        
        cursor = QueryCursor(identifier_query)
        captures = cursor.captures(function_node)
        
        used_identifiers = set()
        for capture_name, nodes in captures.items():
            for node in nodes:
                identifier = source_bytes[node.start_byte:node.end_byte].decode('utf-8')
                used_identifiers.add(identifier)
        
        # Match used identifiers against imports
        required_imports = {}
        for identifier in used_identifiers:
            if identifier in symbol_to_import:
                imp_info = symbol_to_import[identifier]
                module = imp_info['module']
                symbols = imp_info['symbols']
                
                if module not in required_imports:
                    if symbols is None:
                        # Regular import
                        required_imports[module] = None
                    else:
                        # From-import
                        required_imports[module] = symbols.copy()
                else:
                    # Module already in required imports
                    if symbols and required_imports[module] is not None:
                        # Add to the symbol list
                        for sym in symbols:
                            if sym not in required_imports[module]:
                                required_imports[module].append(sym)
        
        return required_imports
    
    def _find_imports(self, tree: Any, source_bytes: bytes) -> list[Dict[str, Any]]:
        """
        Find all import statements in the AST.
        
        This method locates both regular imports (import x) and from-imports
        (from x import y) in a Python AST.
        
        Args:
            tree: tree_sitter.Tree object
            source_bytes: Source code as bytes
            
        Returns:
            List of dictionaries, each containing:
                - type: 'import' or 'from_import'
                - module: Module name being imported
                - symbols: List of imported symbols (for from-imports)
                - alias: Alias if using 'as' (optional)
                - node: The AST node for the import statement
                
        Example:
            >>> tree = engine._parse_file_to_ast('module.py')
            >>> with open('module.py', 'rb') as f:
            ...     source = f.read()
            >>> imports = engine._find_imports(tree, source)
            >>> print(imports[0])
            {'type': 'from_import', 'module': 'pathlib', 'symbols': ['Path'], ...}
        """
        from tree_sitter import Query, QueryCursor
        
        imports = []
        
        # Query for all import statements
        import_query = Query(
            self.ts_setup.get_language('python'),
            "(import_statement) @import"
        )
        
        cursor = QueryCursor(import_query)
        captures = cursor.captures(tree.root_node)
        
        # Process regular imports
        for capture_name, nodes in captures.items():
            for import_stmt in nodes:
                # Process each import within the statement
                # An import_statement can have multiple imports: import a, b, c
                for child in import_stmt.named_children:
                    module_name = None
                    alias = None
                    
                    if child.type == 'dotted_name':
                        # Simple import: import x
                        module_name = source_bytes[child.start_byte:child.end_byte].decode('utf-8')
                    elif child.type == 'aliased_import':
                        # Import with alias: import x as y
                        name_node = child.child_by_field_name('name')
                        alias_node = child.child_by_field_name('alias')
                        if name_node:
                            module_name = source_bytes[
                                name_node.start_byte:name_node.end_byte
                            ].decode('utf-8')
                        if alias_node:
                            alias = source_bytes[
                                alias_node.start_byte:alias_node.end_byte
                            ].decode('utf-8')
                    
                    if module_name:
                        imports.append({
                            'type': 'import',
                            'module': module_name,
                            'symbols': [],
                            'alias': alias,
                            'node': import_stmt
                        })
        
        # Query for from-import statements
        from_import_query = Query(
            self.ts_setup.get_language('python'),
            "(import_from_statement) @from_import"
        )
        
        cursor2 = QueryCursor(from_import_query)
        captures2 = cursor2.captures(tree.root_node)
        
        # Process from-imports
        for capture_name, nodes in captures2.items():
            for import_stmt in nodes:
                # Find the module name
                module_name = None
                module_node = import_stmt.child_by_field_name('module_name')
                if module_node:
                    module_name = source_bytes[
                        module_node.start_byte:module_node.end_byte
                    ].decode('utf-8')
                
                # Find imported symbols
                symbols = []
                for child in import_stmt.named_children:
                    if child.type == 'dotted_name' and child != module_node:
                        # This is an imported symbol
                        symbol = source_bytes[child.start_byte:child.end_byte].decode('utf-8')
                        symbols.append(symbol)
                    elif child.type == 'aliased_import':
                        # Import with alias
                        name_node = child.child_by_field_name('name')
                        alias_node = child.child_by_field_name('alias')
                        if name_node:
                            symbol = source_bytes[
                                name_node.start_byte:name_node.end_byte
                            ].decode('utf-8')
                            if alias_node:
                                alias_text = source_bytes[
                                    alias_node.start_byte:alias_node.end_byte
                                ].decode('utf-8')
                                symbols.append(f"{symbol} as {alias_text}")
                            else:
                                symbols.append(symbol)
                    elif child.type == 'wildcard_import':
                        symbols.append('*')
                
                if module_name:
                    imports.append({
                        'type': 'from_import',
                        'module': module_name,
                        'symbols': symbols,
                        'alias': None,
                        'node': import_stmt
                    })
        
        return imports
    
    def _add_import_to_ast(
        self, 
        tree: Any,
        source_bytes: bytes,
        module_path: str,
        symbols: Optional[list[str]] = None
    ) -> bytes:
        """
        Add an import statement to the source code.
        
        This method intelligently inserts a new import statement at the
        appropriate location (typically after existing imports, before
        the main code).
        
        Args:
            tree: tree_sitter.Tree object
            source_bytes: Source code as bytes
            module_path: Module to import (e.g., 'os', 'pathlib.Path')
            symbols: List of symbols to import (for from-imports). If None,
                    creates regular import. If provided, creates from-import.
                    
        Returns:
            Modified source code as bytes with the new import added
            
        Example:
            >>> tree = engine._parse_file_to_ast('module.py')
            >>> with open('module.py', 'rb') as f:
            ...     source = f.read()
            >>> # Add: from pathlib import Path
            >>> new_source = engine._add_import_to_ast(tree, source, 'pathlib', ['Path'])
        """
        # Find existing imports to determine insertion point
        existing_imports = self._find_imports(tree, source_bytes)
        
        # Generate the new import statement
        if symbols is None or len(symbols) == 0:
            # Regular import: import module_path
            new_import = f"import {module_path}\n"
        else:
            # From-import: from module_path import symbol1, symbol2
            symbols_str = ', '.join(symbols)
            new_import = f"from {module_path} import {symbols_str}\n"
        
        # Determine insertion position
        if existing_imports:
            # Insert after the last import
            last_import_node = existing_imports[-1]['node']
            insert_pos = last_import_node.end_byte
            
            # Check if there's a newline at the insertion point
            # If yes, move past it; if no, add one before our import
            if insert_pos < len(source_bytes) and source_bytes[insert_pos:insert_pos+1] == b'\n':
                # There's a newline, insert after it
                insert_pos += 1
            else:
                # No newline after the last import, add one before our new import
                new_import = '\n' + new_import
        else:
            # No existing imports, insert at the beginning
            # Skip any module docstring first
            insert_pos = 0
            root = tree.root_node
            
            # Check if first statement is a docstring
            if root.named_children:
                first_child = root.named_children[0]
                if first_child.type == 'expression_statement':
                    # Check if it's a string (docstring)
                    if first_child.named_children and first_child.named_children[0].type == 'string':
                        insert_pos = first_child.end_byte
                        new_import = '\n' + new_import
        
        # Insert the new import
        new_source = (
            source_bytes[:insert_pos] +
            new_import.encode('utf-8') +
            source_bytes[insert_pos:]
        )
        
        return new_source
    
    def _add_export_to_ast(
        self,
        tree: Any,
        source_bytes: bytes,
        symbol_name: str
    ) -> bytes:
        """
        Add a symbol to the module's public API exports.
        
        In Python, this typically means adding the symbol to __all__.
        If __all__ doesn't exist, this method creates it.
        
        Args:
            tree: tree_sitter.Tree object
            source_bytes: Source code as bytes
            symbol_name: Name of the symbol to export
            
        Returns:
            Modified source code as bytes with the symbol added to exports
            
        Example:
            >>> tree = engine._parse_file_to_ast('module.py')
            >>> with open('module.py', 'rb') as f:
            ...     source = f.read()
            >>> new_source = engine._add_export_to_ast(tree, source, 'my_function')
        """
        from tree_sitter import Query, QueryCursor
        
        # Find existing __all__ definition
        all_query = Query(
            self.ts_setup.get_language('python'),
            """
            (assignment
                left: (identifier) @var.name
                (#eq? @var.name "__all__"))
            """
        )
        
        cursor = QueryCursor(all_query)
        captures = cursor.captures(tree.root_node)
        
        # Check if __all__ exists
        all_node = None
        for capture_name, nodes in captures.items():
            if nodes:
                all_node = nodes[0].parent  # Get the assignment node
                break
        
        if all_node is not None:
            # __all__ exists, add the symbol to it
            # Find the list node
            list_node = None
            for child in all_node.named_children:
                if child.type == 'list':
                    list_node = child
                    break
            
            if list_node:
                # Add symbol to the list
                # Insert before the closing bracket
                insert_pos = list_node.end_byte - 1
                
                # Check if list is empty or has items
                if len(list_node.named_children) > 0:
                    # Has items, add comma and new item
                    new_item = f", '{symbol_name}'"
                else:
                    # Empty list
                    new_item = f"'{symbol_name}'"
                
                new_source = (
                    source_bytes[:insert_pos] +
                    new_item.encode('utf-8') +
                    source_bytes[insert_pos:]
                )
                
                return new_source
        
        # __all__ doesn't exist, create it
        # Find where to insert it (after imports, after docstring)
        existing_imports = self._find_imports(tree, source_bytes)
        
        if existing_imports:
            # Insert after last import
            insert_pos = existing_imports[-1]['node'].end_byte
            new_all = f"\n__all__ = ['{symbol_name}']\n"
        else:
            # No imports, insert at beginning (after docstring if any)
            insert_pos = 0
            root = tree.root_node
            
            if root.named_children:
                first_child = root.named_children[0]
                if first_child.type == 'expression_statement':
                    if first_child.named_children and first_child.named_children[0].type == 'string':
                        insert_pos = first_child.end_byte
            
            new_all = f"\n__all__ = ['{symbol_name}']\n"
        
        new_source = (
            source_bytes[:insert_pos] +
            new_all.encode('utf-8') +
            source_bytes[insert_pos:]
        )
        
        return new_source
    
    def _handle_split_file(
        self, 
        operation_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle file splitting refactoring.
        
        Args:
            operation_details: Details including:
                - source_file: File to split
                - split_criteria: How to split the file
                
        Returns:
            Result dictionary with status and affected files
        """
        # Placeholder for future implementation
        raise NotImplementedError(
            "split_file operation is not yet implemented"
        )
    
    def _handle_apply_diff(
        self, 
        operation_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle text-based diff application using the patch utility.
        
        This method applies unified diff patches to files. It supports standard
        unified diff format as generated by git diff or similar tools.
        
        Args:
            operation_details: Details including:
                - file: File path to apply diff to (required)
                - diff: Unified diff content to apply (required)
                
        Returns:
            Result dictionary with:
                - status: 'success' or 'error'
                - modified_files: List of files that were modified
                - message: Description of the result
                
        Raises:
            RefactoringValidationError: If required parameters are missing
            RefactoringError: If diff application fails
        """
        import subprocess
        import tempfile
        
        # Validate required parameters
        if 'file' not in operation_details:
            raise RefactoringValidationError(
                "apply_diff operation requires 'file' parameter"
            )
        if 'diff' not in operation_details:
            raise RefactoringValidationError(
                "apply_diff operation requires 'diff' parameter"
            )
        
        file_path = Path(operation_details['file'])
        diff_content = operation_details['diff']
        
        # Validate file exists
        if not file_path.exists():
            raise RefactoringError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise RefactoringError(f"Path is not a file: {file_path}")
        
        # Create temporary file for the diff
        try:
            with tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.patch',
                delete=False,
                encoding='utf-8'
            ) as diff_file:
                diff_file.write(diff_content)
                diff_file_path = diff_file.name
            
            # Apply the patch using the patch command
            # Try 'patch' command first (Unix-like systems)
            try:
                result = subprocess.run(
                    ['patch', '-p0', str(file_path)],
                    stdin=open(diff_file_path, 'r'),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    return {
                        'status': 'success',
                        'modified_files': [str(file_path)],
                        'message': f'Successfully applied diff to {file_path.name}'
                    }
                
                # Patch failed, try git apply as fallback
                result = subprocess.run(
                    ['git', 'apply', '--reject', '--whitespace=fix', diff_file_path],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=str(file_path.parent)
                )
                
                if result.returncode == 0:
                    return {
                        'status': 'success',
                        'modified_files': [str(file_path)],
                        'message': f'Successfully applied diff to {file_path.name}'
                    }
                
                # Both patch and git apply failed, fall back to manual application
                return self._apply_diff_manually(file_path, diff_content)
                
            except FileNotFoundError:
                # Neither patch nor git is available, fall back to manual application
                return self._apply_diff_manually(file_path, diff_content)
                
        except Exception as e:
            raise RefactoringError(
                f"Error applying diff to {file_path}: {str(e)}"
            ) from e
        finally:
            # Clean up temporary diff file
            try:
                Path(diff_file_path).unlink()
            except Exception:
                pass  # Ignore cleanup errors
    
    def _apply_diff_manually(
        self, 
        file_path: Path, 
        diff_content: str
    ) -> Dict[str, Any]:
        """
        Manually apply a simple unified diff when patch/git tools aren't available.
        
        This is a fallback method that handles basic unified diff format.
        It's not as robust as the patch command but works for simple cases.
        
        Args:
            file_path: Path to the file to patch
            diff_content: Unified diff content
            
        Returns:
            Result dictionary
            
        Raises:
            RefactoringError: If manual application fails
        """
        try:
            # Read the current file content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_lines = f.readlines()
            
            # Parse the diff to extract changes
            # This is a simplified parser for basic unified diffs
            modified_lines = original_lines.copy()
            
            # Split diff into lines
            diff_lines = diff_content.split('\n')
            
            # Find the hunk headers (@@  -x,y +a,b @@)
            import re
            hunks = []
            current_hunk = None
            
            for line in diff_lines:
                if line.startswith('@@'):
                    # Parse hunk header
                    match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
                    if match:
                        old_start = int(match.group(1))
                        old_count = int(match.group(2)) if match.group(2) else 1
                        new_start = int(match.group(3))
                        new_count = int(match.group(4)) if match.group(4) else 1
                        
                        if current_hunk:
                            hunks.append(current_hunk)
                        
                        current_hunk = {
                            'old_start': old_start,
                            'old_count': old_count,
                            'new_start': new_start,
                            'new_count': new_count,
                            'lines': []
                        }
                elif current_hunk is not None:
                    current_hunk['lines'].append(line)
            
            if current_hunk:
                hunks.append(current_hunk)
            
            if not hunks:
                raise RefactoringError("No valid hunks found in diff")
            
            # Apply hunks in reverse order to maintain line numbers
            for hunk in reversed(hunks):
                old_start = hunk['old_start'] - 1  # Convert to 0-based
                old_end = old_start + hunk['old_count']
                
                # Extract the new content from the hunk
                new_content = []
                for line in hunk['lines']:
                    if line.startswith('+') and not line.startswith('+++'):
                        new_content.append(line[1:] + '\n')
                    elif line.startswith(' '):
                        new_content.append(line[1:] + '\n')
                
                # Replace the old content with new content
                modified_lines[old_start:old_end] = new_content
            
            # Write the modified content back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(modified_lines)
            
            return {
                'status': 'success',
                'modified_files': [str(file_path)],
                'message': f'Successfully applied diff manually to {file_path.name}'
            }
            
        except Exception as e:
            raise RefactoringError(
                f"Failed to manually apply diff to {file_path}: {str(e)}"
            ) from e
    
    def _handle_rename_symbol(
        self, 
        operation_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle symbol renaming refactoring.
        
        Args:
            operation_details: Details including:
                - file: File containing the symbol
                - old_name: Current symbol name
                - new_name: New symbol name
                
        Returns:
            Result dictionary with status and affected files
        """
        # Placeholder for future implementation
        raise NotImplementedError(
            "rename_symbol operation is not yet implemented"
        )
    
    def _handle_inline_function(
        self, 
        operation_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle function inlining refactoring.
        
        Args:
            operation_details: Details including:
                - file: File containing the function
                - function_name: Function to inline
                
        Returns:
            Result dictionary with status and affected files
        """
        # Placeholder for future implementation
        raise NotImplementedError(
            "inline_function operation is not yet implemented"
        )
