"""Unclutter Directory - Tool to easily organize directories.

This library provides a comprehensive interface to organize files and folders
based on user-defined rules. It supports automatic moves,
compression, deletion, and other organizational actions.

Basic usage:
    from unclutter_directory import cli, File, FileMatcher, OrganizeCommand

    # Run CLI
    cli()

    # Use components programmatically
    file = File.from_path(Path("document.txt"))
    matcher = FileMatcher(rules)
"""

try:
    from importlib.metadata import version

    __version__ = version("unclutter-directory")
except ImportError:
    # Fallback for pre-3.8 and development
    __version__ = "unknown"

from .cli import cli
from .commands.organize_command import OrganizeCommand
from .config.organize_config import OrganizeConfig
from .entities.compressed_archive import (
    ArchiveHandler,
    ArchiveHandlerChain,
    CompressedArchive,
    RarArchive,
    RarHandler,
    ZipArchive,
    ZipHandler,
    get_archive_manager,
)
from .entities.file import File
from .execution.action_executor import ActionExecutor
from .execution.action_strategies import CompressStrategy, DeleteStrategy, MoveStrategy
from .execution.action_strategy_factory import ActionStrategyFactory
from .file_operations.file_matcher import FileMatcher

__all__ = [
    # CLI
    "cli",
    # Main classes
    "File",
    "FileMatcher",
    "ActionExecutor",
    "OrganizeCommand",
    "OrganizeConfig",
    # Strategy Pattern Classes
    "MoveStrategy",
    "DeleteStrategy",
    "CompressStrategy",
    "ActionStrategyFactory",
    # Compressed file handling
    "CompressedArchive",
    "ZipArchive",
    "RarArchive",
    "ArchiveHandler",
    "ZipHandler",
    "RarHandler",
    "ArchiveHandlerChain",
    "get_archive_manager",
    # Version
    "__version__",
]
