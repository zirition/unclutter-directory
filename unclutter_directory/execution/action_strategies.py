"""Action Strategy Pattern Implementation

This module implements the Strategy pattern for action execution.
It provides a clean, extensible way to handle different types of file organization actions.

Classes:
    ActionStrategy: Abstract base class for all action strategies
    MoveStrategy: Strategy for moving files and directories
    DeleteStrategy: Strategy for deleting files and directories
    CompressStrategy: Strategy for compressing files and directories

The strategy pattern allows for:
- Easy addition of new action types without modifying existing code
- Better testability through isolated strategies
- Cleaner separation of concerns
- More maintainable code structure
"""

import shutil
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..commons import validations

logger = validations.get_logger()


class ActionExecutionError(Exception):
    """Exception raised when an action fails but recovery is possible"""

    pass


class ActionExecutionFatalError(Exception):
    """Exception raised when an action fails critically and execution should stop"""

    pass


class ActionStrategy(ABC):
    """Abstract base class for action execution strategies.

    This class defines the interface that all action strategies must implement.
    Each concrete strategy handles a specific type of file organization action.

    Attributes:
        _logger: Logger instance for strategy-specific logging
    """

    def __init__(self, logger_instance: Any):
        """Initialize strategy with logger.

        Args:
            logger_instance: Logger instance for this strategy
        """
        self._logger = logger_instance

    @abstractmethod
    def execute(self, file_path: Path, parent_path: Path, target: str) -> None:
        """Execute the specific action.

        Args:
            file_path: Path to file/directory to process
            parent_path: Base directory for relative path calculations
            target: Target specification (can be path or empty for delete)

        Raises:
            ActionExecutionError: When action fails but could be recoverable
            ActionExecutionFatalError: When action fails critically
        """
        pass

    @abstractmethod
    def validate(self, file_path: Path, target: str) -> bool:
        """Validate if action can be executed with given parameters.

        Args:
            file_path: Path to file/directory to process
            target: Target specification to validate

        Returns:
            bool: True if action can be executed, False otherwise
        """
        pass

    def _resolve_conflict(self, target_path: Path) -> Path:
        """Resolve filename conflicts by adding numerical suffix.

        This method is shared across strategies that may create files.

        Args:
            target_path: Original target path that may conflict

        Returns:
            Path: Unique path that doesn't exist
        """
        if not target_path.exists():
            return target_path

        base_name = target_path.stem
        suffix = 1
        while True:
            new_name = f"{base_name}_{suffix}{target_path.suffix}"
            new_path = target_path.with_name(new_name)
            if not new_path.exists():
                return new_path
            suffix += 1


class MoveStrategy(ActionStrategy):
    """Strategy for moving files and directories.

    This strategy handles the relocation of files and directories while preserving
    their relative path structure and handling filename conflicts.
    """

    def validate(self, file_path: Path, target: str) -> bool:
        """Validate move operation parameters.

        Args:
            file_path: Path to source file/directory
            target: Target directory path

        Returns:
            bool: True if move can be executed
        """
        if not target or target.strip() == "":
            self._logger.warning("Missing target for move action")
            return False

        if not file_path.exists():
            self._logger.warning(f"Source path does not exist: {file_path}")
            return False

        # For compatibility with existing tests, delay validation
        # to maintain original behavior
        return True

    def execute(self, file_path: Path, parent_path: Path, target: str) -> None:
        """Execute move operation.

        Args:
            file_path: Path to source file/directory
            parent_path: Base directory for relative calculations
            target: Target directory path

        Raises:
            ActionExecutionError: When move fails
        """
        try:
            # Calculate target path
            target_dir = self._get_target_directory(target, parent_path)
            rel_path = file_path.relative_to(parent_path)
            target_path = target_dir / rel_path

            # Resolve filename conflicts if needed
            target_path = self._resolve_conflict(target_path)

            # Ensure parent directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Perform the move
            shutil.move(str(file_path), str(target_path))
            self._logger.info(f"Moved {file_path} to {target_path}")

        except Exception as e:
            self._logger.error(f"❌ Unexpected error processing {file_path}: {e}")
            raise

    def _get_target_directory(self, target: str, parent_path: Path) -> Path:
        """Resolve target directory path from string specification.

        Args:
            target: Target directory as string (absolute or relative)
            parent_path: Base directory for relative resolution

        Returns:
            Path: Resolved directory path
        """
        target_path = Path(target)
        if target_path.is_absolute():
            return target_path
        return parent_path / target


class DeleteStrategy(ActionStrategy):
    """Strategy for deleting files and directories.

    This strategy handles safe deletion of files and directories,
    using appropriate methods for each type.
    """

    def validate(self, file_path: Path, target: str) -> bool:
        """Validate delete operation parameters.

        Args:
            file_path: Path to file/directory to delete
            target: Not used for delete operations (should be empty)

        Returns:
            bool: True if delete can be executed
        """
        if not file_path.exists():
            self._logger.warning(f"Path does not exist: {file_path}")
            return False

        # For delete, we don't need target validation as it's not used
        return True

    def execute(self, file_path: Path, parent_path: Path, target: str) -> None:
        """Execute delete operation.

        Args:
            file_path: Path to file/directory to delete
            parent_path: Not used for delete operations
            target: Not used for delete operations

        Raises:
            ActionExecutionError: When delete fails
        """
        try:
            if file_path.is_dir():
                # Delete directory and all contents
                shutil.rmtree(file_path)
                self._logger.info(f"Deleted directory: {file_path}")
            else:
                # Delete single file
                file_path.unlink()
                self._logger.info(f"Deleted file: {file_path}")

        except Exception as e:
            self._logger.error(f"❌ Error deleting {file_path}: {e}")
            raise


class CompressStrategy(ActionStrategy):
    """Strategy for compressing files and directories into ZIP archives.

    This strategy creates ZIP archives while preserving directory structure
    and handling various edge cases like empty directories and existing archives.
    """

    # Extensions that are already compressed and should be skipped
    COMPRESSED_EXTENSIONS = {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"}

    def validate(self, file_path: Path, target: str) -> bool:
        """Validate compression operation parameters.

        Args:
            file_path: Path to file/directory to compress
            target: Target directory for ZIP file

        Returns:
            bool: True if compression can be executed
        """
        if not target or target.strip() == "":
            self._logger.warning("Compress action requires non-empty target parameter")
            return False

        if not file_path.exists():
            self._logger.warning(f"Source path does not exist: {file_path}")
            return False

        # Skip if file is already compressed
        if (
            file_path.is_file()
            and file_path.suffix.lower() in self.COMPRESSED_EXTENSIONS
        ):
            # Return True to allow execution, but CompressStrategy will skip it
            return True

        # Validate target directory is accessible
        try:
            target_path = Path(target) if Path(target).is_absolute() else Path(".")
            if target_path.exists() and not target_path.is_dir():
                self._logger.warning(f"Target is not a directory: {target_path}")
                return False
        except Exception as e:
            self._logger.warning(f"Invalid target path '{target}': {e}")
            return False

        return True

    def execute(self, file_path: Path, parent_path: Path, target: str) -> None:
        """Execute compression operation.

        Args:
            file_path: Path to file/directory to compress
            parent_path: Base directory for relative calculations
            target: Target directory for ZIP file

        Raises:
            ActionExecutionError: When compression fails
        """
        # Skip compression for already compressed files
        if (
            file_path.is_file()
            and file_path.suffix.lower() in self.COMPRESSED_EXTENSIONS
        ):
            self._logger.info(f"Skipping compression for archive file: {file_path}")
            return

        try:
            target_dir = self._get_target_directory(target, parent_path)
            target_dir.mkdir(parents=True, exist_ok=True)

            # Generate ZIP filename
            zip_name = (
                file_path.stem if file_path.is_file() else file_path.name
            ) + ".zip"
            target_path = target_dir / zip_name

            # Resolve filename conflicts
            target_path = self._resolve_conflict(target_path)

            # Create ZIP archive
            self._create_zip_archive(file_path, target_path)

            # Remove original file/directory after successful compression
            if file_path.is_dir():
                shutil.rmtree(file_path)
            else:
                file_path.unlink()

            self._logger.info(f"Compressed {file_path} to {target_path}")

        except Exception as e:
            self._logger.error(f"❌ Error compressing {file_path}: {e}")
            raise

    def _create_zip_archive(self, source_path: Path, target_path: Path) -> None:
        """Create ZIP archive from source path.

        Args:
            source_path: File or directory to compress
            target_path: Path for the resulting ZIP file
        """
        with zipfile.ZipFile(target_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            if source_path.is_dir():
                self._add_directory_to_zip(zipf, source_path)
            else:
                zipf.write(source_path, source_path.name)

    def _add_directory_to_zip(self, zipf: zipfile.ZipFile, source_path: Path) -> None:
        """Add directory contents to ZIP archive recursively.

        Args:
            zipf: ZIP file handle
            source_path: Directory to add to archive
        """
        for file_path in source_path.rglob("*"):
            if file_path.is_file():
                # Calculate relative path from parent directory for proper structure
                arcname = file_path.relative_to(source_path.parent)
                zipf.write(file_path, arcname)
            elif file_path.is_dir():
                # Add directory entry only if it's empty (to preserve structure)
                if not list(file_path.iterdir()):
                    arcname = file_path.relative_to(source_path.parent)
                    zipf.writestr(str(arcname) + "/", "")

    def _get_target_directory(self, target: str, parent_path: Path) -> Path:
        """Resolve target directory path for compression.

        Args:
            target: Target directory as string
            parent_path: Base directory for relative resolution

        Returns:
            Path: Resolved directory path
        """
        target_path = Path(target)
        if target_path.is_absolute():
            return target_path
        return parent_path / target
