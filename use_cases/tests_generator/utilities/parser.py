import ast
from typing import Dict, Any

class CodeParser:
    """
    Utility class to parse Python source code and extract its structure.
    This provides the LLM with a clear map of what needs to be tested.
    """

    @staticmethod
    def extract_structure(source_code: str) -> Dict[str, Any]:
        """
        Parses a raw string of Python code and extracts classes, methods, and top-level functions.
        
        Args:
            source_code (str): The raw Python code received from the API endpoint.
            
        Returns:
            Dict[str, Any]: A dictionary containing the structural metadata of the code.
                            If a syntax error occurs, returns a dictionary with the 'error' key.
        """
        try:
            # Analyze the code without running it
            tree = ast.parse(source_code)
        except SyntaxError as e:
            return {"error": f"Failed to parse source code. Syntax error: {str(e)}"}

        structure = {
            "classes": {},
            "standalone_functions": []
        }

        # Iterate only through top-level nodes to cleanly separate class boundaries from global functions
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                # We check for both standard and async functions to ensure full coverage
                methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                
                structure["classes"][node.name] = {
                    "methods": methods,
                    "has_docstring": ast.get_docstring(node) is not None
                }
                
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                structure["standalone_functions"].append({
                    "name": node.name,
                    "has_docstring": ast.get_docstring(node) is not None
                })

        return structure