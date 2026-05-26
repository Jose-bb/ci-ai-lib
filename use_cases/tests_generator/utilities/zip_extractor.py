import zipfile
import io
from typing import Dict

class ZipExtractor:
    """
    Utility class to handle in-memory extraction of ZIP files.
    Filters out non-essential files and directories to keep the LLM context clean.
    """

    # Directories and file extensions to ignore during extraction to save tokens
    EXCLUDED_DIRS = {'.git', '__pycache__', '.venv', 'venv', 'env', '.pytest_cache', 'node_modules'}
    
    # Allowed file extensions and specific context files
    ALLOWED_EXTENSIONS = {'.py'}
    CONTEXT_FILES = {'README.md', 'requirements.txt', '.env.example', 'pyproject.toml'}

    @staticmethod
    def extract_python_files(zip_bytes: bytes) -> Dict[str, str]:
        """
        Extracts a ZIP archive in memory and returns the content of valid Python files
        and project context files.

        Args:
            zip_bytes (bytes): The raw bytes of the uploaded ZIP file.

        Returns:
            Dict[str, str]: A dictionary where keys are file paths and values are the file contents.
        """
        extracted_files = {}

        # Use io.BytesIO to read the ZIP file directly from memory without saving to disk
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
            for file_info in archive.infolist():
                # Skip directories entirely
                if file_info.is_dir():
                    continue

                file_path = file_info.filename
                
                path_parts = file_path.split('/')
                file_name = path_parts[-1]

                # Skip files located inside excluded directories
                if any(excluded_dir in path_parts for excluded_dir in ZipExtractor.EXCLUDED_DIRS):
                    continue

                # Check if the file is a Python file or a recognized context file
                is_python_file = any(file_name.endswith(ext) for ext in ZipExtractor.ALLOWED_EXTENSIONS)
                is_context_file = file_name in ZipExtractor.CONTEXT_FILES

                # Process only allowed files
                if not (is_python_file or is_context_file):
                    continue

                # Read and decode the file content safely
                try:
                    content = archive.read(file_info.filename).decode('utf-8')
                    extracted_files[file_path] = content
                except UnicodeDecodeError:
                    # Skip files that cannot be decoded as UTF-8 (e.g., binaries)
                    continue

        return extracted_files