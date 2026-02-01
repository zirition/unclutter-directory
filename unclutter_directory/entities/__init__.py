"""
Entities module for file and archive representations.
"""

from .compressed_archive import (
    ArchiveHandler,
    ArchiveHandlerChain,
    CompressedArchive,
    GzipArchive,
    GzipHandler,
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
    "RarArchive",
    "SevenZipArchive",
    "ArchiveHandler",
    "ZipHandler",
    "GzipHandler",
    "RarHandler",
    "SevenZipHandler",
    "ArchiveHandlerChain",
    "get_archive_manager",
]
