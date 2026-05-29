import ast
from typing import Dict, Any

class CodeParser:
    """
    Utility class to parse Python source code and extract its structure.
    This provides the LLM with a clear map of what needs to be tested across an entire project.
    """

    @staticmethod
    def extract_project_structure(project_files: Dict[str, str]) -> Dict[str, Any]:
        """
        Parses multiple files. Extracts classes and methods for Python files,
        and passes context files directly as raw content.
        
        Args:
            project_files (Dict[str, str]): Dictionary mapping file paths to their raw source code.
            
        Returns:
            Dict[str, Any]: A nested dictionary containing the structural metadata and context.
                            If a syntax error occurs in any Python file, returns a dict with the 'error' key.
        """
        project_structure = {}

        for file_path, source_code in project_files.items():
            
            # Handle Context Files (Non-Python)
            if not file_path.endswith('.py'):
                project_structure[file_path] = {
                    "type": "context_file",
                    "content": source_code
                }
                continue

            # Handle Python Files (AST Parsing)
            try:
                # Analyze the code safely without executing it
                tree = ast.parse(source_code)
            except SyntaxError as e:
                # Fail-fast: If one file is broken, we abort and report exactly which file failed
                return {"error": f"Failed to parse '{file_path}'. Syntax error: {str(e)}"}

            file_structure = {
                "type": "python_module",
                "classes": {},
                "standalone_functions": []
            }

            # Iterate through top-level nodes for the current file
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    # Check for both standard and async functions
                    methods = [
                        n.name for n in node.body 
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    ]
                    
                    file_structure["classes"][node.name] = {
                        "methods": methods,
                        "has_docstring": ast.get_docstring(node) is not None
                    }
                    
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    file_structure["standalone_functions"].append({
                        "name": node.name,
                        "has_docstring": ast.get_docstring(node) is not None
                    })

            # Append this file's structure to the global project map
            project_structure[file_path] = file_structure

        return project_structure