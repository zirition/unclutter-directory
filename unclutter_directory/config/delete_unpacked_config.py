from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..commons import get_logger

"""
Configuration class for the check-duplicates command.
"""

logger = get_logger()


@dataclass
class DeleteUnpackedConfig:
    """Configuration for the delete-unpacked operation."""

    target_dir: Path
    dry_run: bool = False  # Default to False for interactive mode
    always_delete: bool = False
    never_delete: bool = False
    include_hidden: bool = False
    quiet: bool = False
    _target_dir_path: Path | None = field(init=False, default=None)

    def __post_init__(self):
        """Validate configuration after initialization"""
        errors = []

        # Validate target directory
        if not self.target_dir.exists():
            errors.append(f"Target directory does not exist: {self.target_dir}")

        if not self.target_dir.is_dir():
            errors.append(f"Target path is not a directory: {self.target_dir}")

        # Validate conflicting flags
        if self.always_delete and self.never_delete:
            errors.append("Cannot specify both --always-delete and --never-delete")

        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            raise ValueError("Invalid configuration: " + "; ".join(errors))

    @property
    def target_dir_path(self) -> Path:
        """Get the resolved target directory path"""
        if self._target_dir_path is None:
            self._target_dir_path = self.target_dir.resolve()
        return self._target_dir_path

    def should_interactive_prompt(self) -> bool:
        """
        Determine if user should be prompted for deletion confirmation.

        Returns:
            True if interactive prompt should be shown, False otherwise
        """
        return not (self.dry_run or self.always_delete or self.never_delete)

    def should_delete(self) -> bool:
        """
        Determine if directories should be deleted (used for non-interactive modes).

        Returns:
            True if directories should be deleted, False otherwise
        """
        if self.never_delete:
            return False
        if self.always_delete:
            return True
        if self.dry_run:
            return False  # Never actually delete in dry run mode
        return False  # Default to not delete

    def __str__(self) -> str:
        """String representation for logging"""
        flags = []
        if self.dry_run:
            flags.append("dry-run")
        if self.always_delete:
            flags.append("always-delete")
        if self.never_delete:
            flags.append("never-delete")
        if self.include_hidden:
            flags.append("include-hidden")
        if self.quiet:
            flags.append("quiet")

        flag_str = f" [{', '.join(flags)}]" if flags else ""
        return f"{self.__class__.__name__}(target_dir={self.target_dir}{flag_str})"
