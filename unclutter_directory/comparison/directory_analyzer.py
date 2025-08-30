"""
Directory analysis utility for comparing directory structures with compressed archives.
"""

import os
from pathlib import Path
from typing import Dict, List

from ..commons import validations
from ..entities.file import File

logger = validations.get_logger()


class DirectoryAnalyzer:
    """
    Analyzes directory structure to extract file information for comparison with archives.
    """

    def __init__(self, include_hidden: bool = False):
        """
        Initialize directory analyzer

        Args:
            include_hidden: Whether to include hidden files and directories
        """
        self.include_hidden = include_hidden

    def get_files(self, directory_path: Path) -> List[File]:
        """
        Get all files in a directory, similar to how CompressedArchive.get_files() works.

        Args:
            directory_path: Path to the directory to analyze

        Returns:
            List of File objects representing all files in the directory structure
        """
        if not directory_path.is_dir():
            logger.error(f"Path is not a directory: {directory_path}")
            return []

        try:
            all_files = []
            # Walk through all files in the directory tree
            for root, dirs, files in os.walk(directory_path):
                root_path = Path(root)

                # Filter hidden directories if not included
                if not self.include_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith(".")]

                # Process each file
                for file_name in files:
                    # Skip hidden files if not included
                    if not self.include_hidden and file_name.startswith("."):
                        continue

                    file_path = root_path / file_name

                    try:
                        # Get file stats
                        stat = file_path.stat()

                        # Create relative path for comparison (similar to zip namelist format)
                        relative_path = file_path.relative_to(directory_path)

                        # Create File object
                        file_obj = File(
                            path=root_path,  # Parent directory
                            name=str(relative_path),  # Relative path as filename
                            date=int(stat.st_mtime),  # Modification time
                            size=stat.st_size,  # File size
                        )

                        all_files.append(file_obj)

                    except OSError as e:
                        logger.warning(f"Could not access file {file_path}: {e}")
                        continue

            return all_files

        except OSError as e:
            logger.error(f"Error analyzing directory {directory_path}: {e}")
            return []

    def get_file_list(self, directory_path: Path) -> List[str]:
        """
        Get simple list of relative file paths for quick comparison.

        Args:
            directory_path: Path to the directory to analyze

        Returns:
            List of relative file paths as strings
        """
        files = self.get_files(directory_path)
        return [file.name for file in files]

    def get_file_details(self, directory_path: Path) -> Dict[str, Dict]:
        """
        Get detailed file information including sizes and modification times.

        Args:
            directory_path: Path to the directory to analyze

        Returns:
            Dictionary mapping relative paths to file details
        """
        files = self.get_files(directory_path)
        details = {}

        for file in files:
            details[file.name] = {
                "size": file.size,
                "date": file.date,
                "path": str(file.path / file.name),
            }

        return details
