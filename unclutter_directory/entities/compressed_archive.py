import bz2
import lzma
import struct
import tarfile
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path

import py7zr
import rarfile
from rarfile import RarFile

from unclutter_directory.commons import get_logger
from unclutter_directory.entities.file import File

logger = get_logger()


class CompressedArchive(ABC):
    @abstractmethod
    def get_files(self, file: File) -> list[File]:
        pass


class ZipArchive(CompressedArchive):
    def __init__(self):
        pass

    def get_files(self, file: File) -> list[File]:
        archive_path = file.path / file.name
        try:
            # Try with UTF-8 encoding first (handles most modern ZIP files correctly)
            try:
                with zipfile.ZipFile(
                    archive_path, "r", metadata_encoding="utf-8"
                ) as zipf:
                    return [
                        File(
                            file.path,
                            name,
                            zipf.getinfo(name).date_time,
                            zipf.getinfo(name).file_size,
                        )
                        for name in zipf.namelist()
                    ]
            except (TypeError, UnicodeDecodeError):
                # Fallback for older Python versions or if metadata_encoding is not supported
                # Also handles cases where the ZIP file metadata is not UTF-8 encoded
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

    def get_files(self, file: File) -> list[File]:
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


class SevenZipArchive(CompressedArchive):
    def __init__(self):
        pass

    def get_files(self, file: File) -> list[File]:
        archive_path = file.path / file.name
        try:
            with py7zr.SevenZipFile(archive_path, mode="r") as szf:
                files = []
                for name in szf.getnames():
                    file_info = szf.getinfo(name)
                    # Add trailing slash to directory names for consistency with ZIP/RAR
                    if file_info.is_directory and not name.endswith("/"):
                        name = name + "/"
                    timestamp = self._get_fileinfo_timestamp(file_info)
                    if timestamp is None:
                        timestamp = file.date if file.date is not None else 0
                    size = (
                        file_info.uncompressed
                        if hasattr(file_info, "uncompressed")
                        else getattr(file_info, "size", 0)
                    )
                    files.append(
                        File(
                            file.path,
                            name,
                            timestamp,
                            size,
                        )
                    )
                return files
        except py7zr.Bad7zFile as e:
            logger.error(f"❌ Error reading 7z file {archive_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error reading 7z file {archive_path}: {e}")
            return []

    @staticmethod
    def _get_fileinfo_timestamp(file_info):
        for attr in ("lastwritetime", "mtime", "modified", "date_time"):
            value = getattr(file_info, attr, None)
            if value is None:
                continue
            if hasattr(value, "timestamp"):
                return value.timestamp()
            return value
        return None


class GzipArchive(CompressedArchive):
    def __init__(self):
        pass

    def get_files(self, file: File) -> list[File]:
        archive_path = file.path / file.name
        try:
            name, mtime = self._read_header_name_and_mtime(archive_path)
            if not name:
                name = self._default_name(archive_path)
            size = self._read_uncompressed_size(archive_path)
            timestamp = mtime if mtime else file.date
            return [File(file.path, name, timestamp, size)]
        except OSError as e:
            logger.error(f"❌ Error reading gzip file {archive_path}: {e}")
            return []

    @staticmethod
    def _default_name(archive_path: Path) -> str:
        name = archive_path.name
        if name.lower().endswith(".gz"):
            return name[:-3]
        return name

    @staticmethod
    def _read_header_name_and_mtime(
        archive_path: Path,
    ) -> tuple[str | None, int | None]:
        try:
            with archive_path.open("rb") as handle:
                header = handle.read(10)
                if len(header) < 10 or header[0:2] != b"\x1f\x8b":
                    return None, None
                flags = header[3]
                mtime = struct.unpack("<I", header[4:8])[0] or None

                # Extra field
                if flags & 0x04:
                    extra_len_bytes = handle.read(2)
                    if len(extra_len_bytes) < 2:
                        return None, mtime
                    extra_len = struct.unpack("<H", extra_len_bytes)[0]
                    handle.seek(extra_len, 1)

                # Original filename
                name = None
                if flags & 0x08:
                    name_bytes = bytearray()
                    while True:
                        chunk = handle.read(1)
                        if not chunk:
                            return None, mtime
                        if chunk == b"\x00":
                            break
                        name_bytes.extend(chunk)
                    try:
                        name = name_bytes.decode("utf-8")
                    except UnicodeDecodeError:
                        name = name_bytes.decode("latin-1", errors="replace")

                return Path(name).name if name else None, mtime
        except OSError:
            return None, None

    @staticmethod
    def _read_uncompressed_size(archive_path: Path) -> int:
        try:
            file_size = archive_path.stat().st_size
            if file_size < 4:
                return 0
            with archive_path.open("rb") as handle:
                handle.seek(-4, 2)
                size_bytes = handle.read(4)
            if len(size_bytes) < 4:
                return 0
            return struct.unpack("<I", size_bytes)[0]
        except OSError:
            return 0


class Bzip2Archive(CompressedArchive):
    def __init__(self):
        pass

    def get_files(self, file: File) -> list[File]:
        archive_path = file.path / file.name
        try:
            name = self._default_name(archive_path)
            size = self._read_uncompressed_size(archive_path)
            return [File(file.path, name, file.date, size)]
        except OSError as e:
            logger.error(f"❌ Error reading bzip2 file {archive_path}: {e}")
            return []

    @staticmethod
    def _default_name(archive_path: Path) -> str:
        name = archive_path.name
        for suffix in (".bz2", ".bz"):
            if name.lower().endswith(suffix):
                return name[: -len(suffix)]
        return name

    @staticmethod
    def _read_uncompressed_size(archive_path: Path) -> int:
        try:
            with bz2.BZ2File(archive_path, "rb") as handle:
                size = 0
                while True:
                    chunk = handle.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                return size
        except OSError:
            return 0


class XzArchive(CompressedArchive):
    def __init__(self):
        pass

    def get_files(self, file: File) -> list[File]:
        archive_path = file.path / file.name
        try:
            name = self._default_name(archive_path)
            size = self._read_uncompressed_size(archive_path)
            return [File(file.path, name, file.date, size)]
        except OSError as e:
            logger.error(f"❌ Error reading xz file {archive_path}: {e}")
            return []

    @staticmethod
    def _default_name(archive_path: Path) -> str:
        name = archive_path.name
        if name.lower().endswith(".xz"):
            return name[:-3]
        return name

    @staticmethod
    def _read_uncompressed_size(archive_path: Path) -> int:
        try:
            with lzma.open(archive_path, "rb") as handle:
                size = 0
                while True:
                    chunk = handle.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                return size
        except OSError:
            return 0


class TarGzArchive(CompressedArchive):
    def __init__(self):
        pass

    def get_files(self, file: File) -> list[File]:
        archive_path = file.path / file.name
        try:
            with tarfile.open(archive_path, mode="r:gz") as tarf:
                files: list[File] = []
                for member in tarf.getmembers():
                    name = member.name
                    if member.isdir() and not name.endswith("/"):
                        name = name + "/"
                    files.append(
                        File(
                            file.path,
                            name,
                            member.mtime,
                            member.size,
                        )
                    )
                return files
        except (tarfile.TarError, OSError) as e:
            logger.error(f"❌ Error reading tar.gz file {archive_path}: {e}")
            return []


class TarBz2Archive(CompressedArchive):
    def __init__(self):
        pass

    def get_files(self, file: File) -> list[File]:
        archive_path = file.path / file.name
        try:
            with tarfile.open(archive_path, mode="r:bz2") as tarf:
                files: list[File] = []
                for member in tarf.getmembers():
                    name = member.name
                    if member.isdir() and not name.endswith("/"):
                        name = name + "/"
                    files.append(
                        File(
                            file.path,
                            name,
                            member.mtime,
                            member.size,
                        )
                    )
                return files
        except (tarfile.TarError, OSError) as e:
            logger.error(f"❌ Error reading tar.bz2 file {archive_path}: {e}")
            return []


class TarXzArchive(CompressedArchive):
    def __init__(self):
        pass

    def get_files(self, file: File) -> list[File]:
        archive_path = file.path / file.name
        try:
            with tarfile.open(archive_path, mode="r:xz") as tarf:
                files: list[File] = []
                for member in tarf.getmembers():
                    name = member.name
                    if member.isdir() and not name.endswith("/"):
                        name = name + "/"
                    files.append(
                        File(
                            file.path,
                            name,
                            member.mtime,
                            member.size,
                        )
                    )
                return files
        except (tarfile.TarError, OSError) as e:
            logger.error(f"❌ Error reading tar.xz file {archive_path}: {e}")
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
        return file.name.lower().endswith(".zip")

    def create_instance(self) -> CompressedArchive:
        return ZipArchive()


class RarHandler(ArchiveHandler):
    """Handler for RAR archive files."""

    def can_handle(self, file: File) -> bool:
        return file.name.lower().endswith(".rar")

    def create_instance(self) -> CompressedArchive:
        return RarArchive()


class SevenZipHandler(ArchiveHandler):
    """Handler for 7Z archive files."""

    def can_handle(self, file: File) -> bool:
        return file.name.lower().endswith(".7z")

    def create_instance(self) -> CompressedArchive:
        return SevenZipArchive()


class GzipHandler(ArchiveHandler):
    """Handler for GZIP archive files (single-file)."""

    def can_handle(self, file: File) -> bool:
        lower_name = file.name.lower()
        return (
            lower_name.endswith(".gz")
            and not lower_name.endswith(".tar.gz")
            and not lower_name.endswith(".tgz")
        )

    def create_instance(self) -> CompressedArchive:
        return GzipArchive()


class Bzip2Handler(ArchiveHandler):
    """Handler for BZ2/BZ single-file archives (excludes .tar.bz2/.tbz*)."""

    def can_handle(self, file: File) -> bool:
        lower_name = file.name.lower()
        if (
            lower_name.endswith(".tar.bz2")
            or lower_name.endswith(".tbz2")
            or lower_name.endswith(".tbz")
        ):
            return False
        return lower_name.endswith(".bz2") or lower_name.endswith(".bz")

    def create_instance(self) -> CompressedArchive:
        return Bzip2Archive()


class XzHandler(ArchiveHandler):
    """Handler for XZ single-file archives (excludes .tar.xz/.txz)."""

    def can_handle(self, file: File) -> bool:
        lower_name = file.name.lower()
        if lower_name.endswith(".tar.xz") or lower_name.endswith(".txz"):
            return False
        return lower_name.endswith(".xz")

    def create_instance(self) -> CompressedArchive:
        return XzArchive()


class TarGzHandler(ArchiveHandler):
    """Handler for TAR.GZ / TGZ archive files."""

    def can_handle(self, file: File) -> bool:
        lower_name = file.name.lower()
        return lower_name.endswith(".tar.gz") or lower_name.endswith(".tgz")

    def create_instance(self) -> CompressedArchive:
        return TarGzArchive()


class TarBz2Handler(ArchiveHandler):
    """Handler for TAR.BZ2 / TBZ2 / TBZ archive files."""

    def can_handle(self, file: File) -> bool:
        lower_name = file.name.lower()
        return (
            lower_name.endswith(".tar.bz2")
            or lower_name.endswith(".tbz2")
            or lower_name.endswith(".tbz")
        )

    def create_instance(self) -> CompressedArchive:
        return TarBz2Archive()


class TarXzHandler(ArchiveHandler):
    """Handler for TAR.XZ / TXZ archive files."""

    def can_handle(self, file: File) -> bool:
        lower_name = file.name.lower()
        return lower_name.endswith(".tar.xz") or lower_name.endswith(".txz")

    def create_instance(self) -> CompressedArchive:
        return TarXzArchive()


class ArchiveHandlerChain:
    """
    Chain of responsibility pattern for archive file handling.
    Runs all handlers and returns the first one that can handle the file.
    """

    def __init__(self):
        """Initialize archive handler chain with default handlers"""
        self.handlers: list[ArchiveHandler] = [
            ZipHandler(),
            RarHandler(),
            SevenZipHandler(),
            TarGzHandler(),
            TarBz2Handler(),
            TarXzHandler(),
            Bzip2Handler(),
            XzHandler(),
            GzipHandler(),
        ]

    def add_handler(self, handler: ArchiveHandler) -> None:
        """
        Add a custom handler to the chain.

        Args:
            handler: ArchiveHandler instance to add
        """
        self.handlers.append(handler)

    def get_archive_handler(self, file: File) -> CompressedArchive | None:
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
def get_archive_manager(file: File) -> CompressedArchive | None:
    """
    Factory function that uses Chain of Responsibility to get the appropriate archive manager.

    This function replaces the hard-coded if-elif logic in FileMatcher and ArchiveDirectoryComparator
    and provides a cleaner, more extensible way to handle different archive formats
    such as ZIP, RAR, 7Z, and GZ.

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
