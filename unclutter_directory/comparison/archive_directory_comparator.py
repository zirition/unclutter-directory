"""
Archive Directory Comparator - Compares compressed files with their corresponding directories.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple

from ..commons import get_logger
from ..entities.compressed_archive import get_archive_manager
from ..entities.file import File
from .directory_analyzer import DirectoryAnalyzer

logger = get_logger()


class ComparisonResult:
    """Result of comparing an archive with its corresponding directory."""

    def __init__(
        self,
        archive_path: Path,
        directory_path: Path,
        identical: bool,
        archive_files: List[File],
        directory_files: List[File],
        differences: List[str] = None,
    ):
        self.archive_path = archive_path
        self.directory_path = directory_path
        self.identical = identical
        self.archive_files = archive_files
        self.directory_files = directory_files
        self.differences = differences or []

    def __str__(self) -> str:
        status = "IDENTICAL" if self.identical else "DIFFERENT"
        return f"Comparison: {self.archive_path} vs {self.directory_path} [{status}]"


class ArchiveDirectoryComparator:
    """
    Compares compressed archive files (ZIP, RAR, 7Z) with their corresponding directories
    to determine if they contain identical file structures.
    """

    def __init__(self, include_hidden: bool = False):
        """
        Initialize comparator instance

        Args:
            include_hidden: Whether to include hidden files in comparison
        """
        self.include_hidden = include_hidden
        self.directory_analyzer = DirectoryAnalyzer(include_hidden=include_hidden)

    def find_potential_duplicates(self, target_dir: Path) -> List[Tuple[Path, Path]]:
        """
        Find potential archive-directory duplicates in target directory.

        Args:
            target_dir: Directory to scan for archives and corresponding directories

        Returns:
            List of tuples (archive_path, directory_path) where directory might be duplicate of archive
        """
        potential_duplicates = []

        try:
            # Walk through all files in target directory
            for root, _dirs, files in os.walk(target_dir):
                root_path = Path(root)

                for file_name in files:
                    file_path = root_path / file_name

                    # Check if it's a supported archive file
                    archive_file = File.from_path(file_path)
                    if get_archive_manager(archive_file):
                        # Extract directory name (remove extension)
                        dir_name = file_path.stem

                        # Check if corresponding directory exists
                        expected_dir_path = file_path.parent / dir_name
                        if expected_dir_path.exists() and expected_dir_path.is_dir():
                            potential_duplicates.append((file_path, expected_dir_path))

        except OSError as e:
            logger.error(f"Error scanning directory {target_dir}: {e}")

        logger.info(
            f"Found {len(potential_duplicates)} potential archive-directory pairs for comparison"
        )
        return potential_duplicates

    def compare_archive_and_directory(
        self, archive_path: Path, directory_path: Path
    ) -> ComparisonResult:
        """
        Compare an archive file with its corresponding directory.

        Args:
            archive_path: Path to the archive file
            directory_path: Path to the directory to compare

        Returns:
            ComparisonResult object with details of the comparison
        """
        try:
            # Get archive manager based on file type
            archive_manager = self._get_archive_manager(archive_path)
            if not archive_manager:
                return ComparisonResult(
                    archive_path,
                    directory_path,
                    False,
                    [],
                    [],
                    [f"Unsupported archive format: {archive_path.suffix}"],
                )

            # Get files from archive
            archive_files = archive_manager.get_files(File.from_path(archive_path))

            # Check if the archive contains directory entries
            archive_has_directories = any(f.name.endswith("/") for f in archive_files)

            # Get files from directory (always include directories initially)
            directory_files = self.directory_analyzer.get_files(directory_path)

            # If archive doesn't have directories, filter them out from directory files
            if not archive_has_directories:
                directory_files = [
                    f for f in directory_files if not f.name.endswith("/")
                ]

            # Compare structures
            differences = self._compare_file_structures(archive_files, directory_files)

            # Structures are identical if there are no differences
            identical = len(differences) == 0

            return ComparisonResult(
                archive_path,
                directory_path,
                identical,
                archive_files,
                directory_files,
                differences,
            )

        except Exception as e:
            logger.error(f"Error comparing {archive_path} with {directory_path}: {e}")
            return ComparisonResult(
                archive_path,
                directory_path,
                False,
                [],
                [],
                [f"Comparison failed: {str(e)}"],
            )

    def _get_archive_manager(self, archive_path: Path):
        """
        Get the appropriate archive manager for a file.

        Uses Chain of Responsibility pattern to determine the correct archive manager
        based on the file extension.

        Args:
            archive_path: Path to archive file

        Returns:
            Archive manager instance or None if unsupported format
        """
        # Convert Path to File object for the new API
        archive_file = File.from_path(archive_path)
        return get_archive_manager(archive_file)

    def _compare_file_structures(
        self, archive_files: List[File], directory_files: List[File]
    ) -> List[str]:
        """
        Compare file structures from archive and directory.

        Args:
            archive_files: Files from archive
            directory_files: Files from directory

        Returns:
            List of differences found
        """
        differences = []

        # Create sets of file paths for comparison
        archive_paths = {file.name for file in archive_files}
        directory_paths = {file.name for file in directory_files}

        # Find files that are in archive but not in directory
        missing_in_directory = archive_paths - directory_paths
        if missing_in_directory:
            differences.extend(
                [
                    f"Missing in directory: {path}"
                    for path in sorted(missing_in_directory)
                ]
            )

        # Find files that are in directory but not in archive
        extra_in_directory = directory_paths - archive_paths
        if extra_in_directory:
            differences.extend(
                [f"Extra in directory: {path}" for path in sorted(extra_in_directory)]
            )

        # Compare file sizes and modification times for common files
        common_files = archive_paths & directory_paths
        for file_path in common_files:
            archive_file = next(f for f in archive_files if f.name == file_path)
            directory_file = next(f for f in directory_files if f.name == file_path)

            # Compare sizes
            if archive_file.size != directory_file.size:
                differences.append(
                    f"Size mismatch for {file_path}: "
                    f"archive={archive_file.size}, directory={directory_file.size}"
                )

        return differences

    def get_comparison_summary(self, results: List[ComparisonResult]) -> Dict:
        """
        Generate summary statistics from comparison results.

        Args:
            results: List of comparison results

        Returns:
            Dictionary with summary statistics
        """
        total = len(results)
        identical = sum(1 for r in results if r.identical)
        different = total - identical

        return {
            "total_comparisons": total,
            "identical": identical,
            "different": different,
            "identical_percentage": (identical / total * 100) if total > 0 else 0,
        }
