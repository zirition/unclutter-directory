"""
Entities module for file and archive representations.
"""

from .compressed_archive import (
    ArchiveHandler,
    ArchiveHandlerChain,
    CompressedArchive,
    GzipArchive,
    GzipHandler,
    TarBz2Archive,
    TarBz2Handler,
    TarGzArchive,
    TarGzHandler,
    TarXzArchive,
    TarXzHandler,
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
    "TarBz2Archive",
    "TarXzArchive",
    "RarArchive",
    "SevenZipArchive",
    "ArchiveHandler",
    "ZipHandler",
    "GzipHandler",
    "TarGzHandler",
    "TarBz2Handler",
    "TarXzHandler",
    "RarHandler",
    "SevenZipHandler",
    "ArchiveHandlerChain",
    "get_archive_manager",
]
