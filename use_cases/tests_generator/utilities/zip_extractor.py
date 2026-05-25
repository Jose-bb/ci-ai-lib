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
    ALLOWED_EXTENSIONS = {'.py'}

    @staticmethod
    def extract_python_files(zip_bytes: bytes) -> Dict[str, str]:
        """
        Extracts a ZIP archive in memory and returns the content of valid Python files.

        Args:
            zip_bytes (bytes): The raw bytes of the uploaded ZIP file.

        Returns:
            Dict[str, str]: A dictionary where keys are file paths and values are the source code.
        """
        extracted_files = {}

        # Use io.BytesIO to read the ZIP file directly from memory without saving to disk
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
            for file_info in archive.infolist():
                # Skip directories entirely
                if file_info.is_dir():
                    continue

                file_path = file_info.filename

                # Skip files located inside excluded directories
                if any(excluded_dir in file_path.split('/') for excluded_dir in ZipExtractor.EXCLUDED_DIRS):
                    continue

                # Process only files with allowed extensions
                if not any(file_path.endswith(ext) for ext in ZipExtractor.ALLOWED_EXTENSIONS):
                    continue

                # Read and decode the file content safely
                try:
                    content = archive.read(file_info.filename).decode('utf-8')
                    extracted_files[file_path] = content
                except UnicodeDecodeError:
                    # Skip files that cannot be decoded as UTF-8 (e.g., binaries)
                    continue

        return extracted_files