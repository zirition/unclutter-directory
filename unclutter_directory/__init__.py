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

__version__ = "0.9.4"

from .cli import cli
from .entities.file import File, CompressedArchive, ZipArchive, RarArchive
from .file_operations.file_matcher import FileMatcher
from .execution.action_executor import ActionExecutor
from .execution.action_strategies import MoveStrategy, DeleteStrategy, CompressStrategy
from .execution.action_strategy_factory import ActionStrategyFactory
from .commands.organize_command import OrganizeCommand
from .config.organize_config import OrganizeConfig

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

    # Version
    "__version__",
]