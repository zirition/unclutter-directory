import zipfile
import rarfile
from rarfile import RarFile

from abc import ABC, abstractmethod
from typing import List, Optional

from unclutter_directory.commons import validations
from unclutter_directory.entities.file import File

logger = validations.get_logger()

class CompressedArchive(ABC):
    @abstractmethod
    def get_files(self, file: File) -> List[File]:
        pass


class ZipArchive(CompressedArchive):
    def __init__(self):
        pass

    def get_files(self, file: File) -> List[File]:
        archive_path = file.path / file.name
        try:
            with zipfile.ZipFile(archive_path, "r") as zipf:
                return [
                    File(
                        file.path,
                        name,
                        zipf.getinfo(name).date_time,
                        zipf.getinfo(name).file_size,
                    )
                    for name in zipf.namelist()
                ]
        except zipfile.BadZipFile:
            logger.error(f"❌ Error reading zip file: {archive_path}")
            return []

class RarArchive(CompressedArchive):
    def __init__(self):
        pass

    def get_files(self, file: File) -> List[File]:
        archive_path = file.path / file.name
        try:
            with RarFile(archive_path) as rarf:
                return [
                    File(
                        file.path,
                        name,
                        rarf.getinfo(name).date_time,
                        rarf.getinfo(name).file_size,
                    )
                    for name in rarf.namelist()
                ]
        except rarfile.Error:
            logger.error(f"❌ Error reading rar file: {archive_path}")
            return []

# Chain of Responsibility Pattern Implementation

class ArchiveHandler(ABC):
    """Abstract base class for archive handlers in the chain"""

    @abstractmethod
    def can_handle(self, file: File) -> bool:
        """
        Check if this handler can process the given file.

        Args:
            file: File to check

        Returns:
            True if this handler can process the file, False otherwise
        """
        pass

    @abstractmethod
    def create_instance(self) -> CompressedArchive:
        """
        Create an instance of the appropriate archive handler.

        Returns:
            CompressedArchive instance
        """
        pass


class ZipHandler(ArchiveHandler):
    """Handler for ZIP archive files."""

    def can_handle(self, file: File) -> bool:
        return file.name.lower().endswith('.zip')

    def create_instance(self) -> CompressedArchive:
        return ZipArchive()


class RarHandler(ArchiveHandler):
    """Handler for RAR archive files."""

    def can_handle(self, file: File) -> bool:
        return file.name.lower().endswith('.rar')

    def create_instance(self) -> CompressedArchive:
        return RarArchive()


class ArchiveHandlerChain:
    """
    Chain of responsibility pattern for archive file handling.
    Runs all handlers and returns the first one that can handle the file.
    """

    def __init__(self):
        """Initialize archive handler chain with default handlers"""
        self.handlers: List[ArchiveHandler] = [
            ZipHandler(),
            RarHandler(),
        ]

    def add_handler(self, handler: ArchiveHandler) -> None:
        """
        Add a custom handler to the chain.

        Args:
            handler: ArchiveHandler instance to add
        """
        self.handlers.append(handler)

    def get_archive_handler(self, file: File) -> Optional[CompressedArchive]:
        """
        Get the appropriate archive handler for the given file.

        Args:
            file: File to get a handler for

        Returns:
            CompressedArchive instance or None if no handler can process the file
        """
        for handler in self.handlers:
            try:
                if handler.can_handle(file):
                    return handler.create_instance()
            except Exception as e:
                logger.error(f"Handler {handler.__class__.__name__} failed: {e}")
                continue

        return None


# Factory function using Chain of Responsibility
def get_archive_manager(file: File) -> Optional[CompressedArchive]:
    """
    Factory function that uses Chain of Responsibility to get the appropriate archive manager.

    This function replaces the hard-coded if-elif logic in FileMatcher and ArchiveDirectoryComparator
    and provides a cleaner, more extensible way to handle different archive formats.

    Args:
        file: The file to get an archive manager for

    Returns:
        CompressedArchive instance or None if unsupported format

    Example:
        >>> file = File.from_path(Path("document.zip"))
        >>> manager = get_archive_manager(file)
        >>> if manager:
        ...     files = manager.get_files(file)
    """
    handler_chain = ArchiveHandlerChain()
    return handler_chain.get_archive_handler(file)


# Convenience function for backward compatibility
def create_archive_manager(file_extension: str) -> Optional[CompressedArchive]:
    """
    Create an archive manager based on file extension.
    Useful for cases where you only have the extension.

    Args:
        file_extension: File extension (e.g., '.zip', '.rar')

    Returns:
        CompressedArchive instance or None if unsupported
    """
    # Create a dummy file just to use the chain logic
    class DummyFile:
        def __init__(self, name: str):
            self.name = name

    dummy_file = DummyFile(f"dummy{file_extension.lower()}")
    return get_archive_manager(dummy_file)
