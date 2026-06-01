import os
import subprocess
import tempfile
from typing import Dict, Optional

class GitExtractor:
    """
    Utility class to handle cloning and extracting context from Git repositories.
    Filters out non-essential files to keep the LLM context clean, while pulling both Python code and project metadata.
    """

    # Directories to ignore during extraction to save tokens
    EXCLUDED_DIRS = {'.git', '__pycache__', '.venv', 'venv', 'env', '.pytest_cache', 'node_modules'}
    
    # Allowed file extensions and specific context files
    ALLOWED_EXTENSIONS = {'.py'}
    CONTEXT_FILES = {'README.md', 'requirements.txt', '.env.example', 'pyproject.toml'}

    @staticmethod
    def extract_repository(repo_url: str, github_token: Optional[str] = None) -> Dict[str, str]:
        """
        Clones a Git repository into an ephemeral temporary directory, extracts
        relevant source code and context files, and returns their contents.

        Args:
            repo_url (str): The HTTPS URL of the Git repository.
            github_token (str, optional): The GitHub token for private repositories.

        Returns:
            Dict[str, str]: A dictionary where keys are relative file paths 
                            and values are the file contents.
        
        Raises:
            RuntimeError: If the git clone command fails (e.g., invalid URL or unauthorized access).
        """
        extracted_files = {}
        cmd = ['git', 'clone', '--depth', '1']

        # Create an ephemeral temporary directory that automatically cleans up
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Execute a shallow clone (--depth 1) to save bandwidth and time
                if github_token:
                    auth_url = repo_url.replace("https://", f"https://x-access-token:{github_token}@")
                    cmd.append(auth_url)
                else:
                    cmd.append(repo_url)
                
                cmd.append(temp_dir)
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                
            except subprocess.CalledProcessError as e:
                error_output = e.stderr or str(e)
                # Mask the user's PAT token in the exception message before raising it to the API layer
                if github_token and github_token in error_output:
                    error_output = error_output.replace(github_token, "***MASKED_TOKEN***")
                
                raise RuntimeError(f"Failed to clone repository. Error: {error_output}")

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

        return extracted_files