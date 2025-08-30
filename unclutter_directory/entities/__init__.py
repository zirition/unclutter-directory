"""
Entities module for file and archive representations.
"""

from .compressed_archive import (
    ArchiveHandler,
    ArchiveHandlerChain,
    CompressedArchive,
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
    "RarArchive",
    "SevenZipArchive",
    "ArchiveHandler",
    "ZipHandler",
    "RarHandler",
    "SevenZipHandler",
    "ArchiveHandlerChain",
    "get_archive_manager",
]
