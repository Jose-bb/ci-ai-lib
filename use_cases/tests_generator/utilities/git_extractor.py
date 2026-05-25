import os
import subprocess
import tempfile
from typing import Dict

class GitExtractor:
    """
    Utility class to handle cloning and extracting context from Git repositories.
    Filters out non-essential files to keep the LLM context clean, while pulling
    both Python code and project metadata.
    """

    # Directories to ignore during extraction to save tokens
    EXCLUDED_DIRS = {'.git', '__pycache__', '.venv', 'venv', 'env', '.pytest_cache', 'node_modules'}
    
    # Allowed file extensions and specific context files
    ALLOWED_EXTENSIONS = {'.py'}
    CONTEXT_FILES = {'README.md', 'requirements.txt', '.env.example', 'pyproject.toml'}

    @staticmethod
    def extract_repository(repo_url: str) -> Dict[str, str]:
        """
        Clones a Git repository into an ephemeral temporary directory, extracts
        relevant source code and context files, and returns their contents.

        Args:
            repo_url (str): The HTTPS URL of the Git repository.

        Returns:
            Dict[str, str]: A dictionary where keys are relative file paths 
                            and values are the file contents.
        
        Raises:
            RuntimeError: If the git clone command fails (e.g., invalid URL).
        """
        extracted_files = {}

        # Create an ephemeral temporary directory that automatically cleans up
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Execute a shallow clone (--depth 1) to save bandwidth and time
                subprocess.run(
                    ['git', 'clone', '--depth', '1', repo_url, temp_dir],
                    check=True,
                    capture_output=True,
                    text=True
                )
            except subprocess.CalledProcessError as e:
                # Capture the standard error from Git and raise it for the API to handle
                raise RuntimeError(f"Failed to clone repository. Error: {e.stderr}")

            # Walk through the downloaded repository
            for root, dirs, files in os.walk(temp_dir):
                # Modify 'dirs' in-place to skip excluded directories entirely
                dirs[:] = [d for d in dirs if d not in GitExtractor.EXCLUDED_DIRS]

                for file in files:
                    # Check if the file is a Python file or a recognized context file
                    is_python_file = any(file.endswith(ext) for ext in GitExtractor.ALLOWED_EXTENSIONS)
                    is_context_file = file in GitExtractor.CONTEXT_FILES

                    if not (is_python_file or is_context_file):
                        continue

                    # Construct the absolute path to read the file
                    absolute_path = os.path.join(root, file)
                    # Construct a clean relative path to use as the dictionary key
                    relative_path = os.path.relpath(absolute_path, temp_dir)

                    # Read and decode the file content safely
                    try:
                        with open(absolute_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            extracted_files[relative_path] = content
                    except UnicodeDecodeError:
                        # Skip binary files or unrecognized encodings
                        continue

        # The temporary directory (and all its contents) is automatically deleted as soon as the execution exits the 'with' block.
        return extracted_files