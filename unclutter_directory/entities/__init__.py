"""
Entities module for file and archive representations.
"""

from .file import File
from .compressed_archive import (
    CompressedArchive,
    ZipArchive,
    RarArchive,
    SevenZipArchive,
    ArchiveHandler,
    ZipHandler,
    RarHandler,
    SevenZipHandler,
    ArchiveHandlerChain,
    get_archive_manager,
)

__all__ = [
    "File",
    "CompressedArchive",
    "ZipArchive",
    "RarArchive",
    "SevenZipArchive",
    "ArchiveHandler",
    "ZipHandler",
    "RarHandler",
    "SevenZipHandler",
    "ArchiveHandlerChain",
    "get_archive_manager",
]