"""
Entities module for file and archive representations.
"""

from .compressed_archive import (
    ArchiveHandler,
    ArchiveHandlerChain,
    CompressedArchive,
    GzipArchive,
    GzipHandler,
    TarGzArchive,
    TarGzHandler,
    RarArchive,
    RarHandler,
    SevenZipArchive,
    SevenZipHandler,
    ZipArchive,
    ZipHandler,
    get_archive_manager,
)
from .file import File

__all__ = [
    "File",
    "CompressedArchive",
    "ZipArchive",
    "GzipArchive",
    "TarGzArchive",
    "RarArchive",
    "SevenZipArchive",
    "ArchiveHandler",
    "ZipHandler",
    "GzipHandler",
    "TarGzHandler",
    "RarHandler",
    "SevenZipHandler",
    "ArchiveHandlerChain",
    "get_archive_manager",
]
