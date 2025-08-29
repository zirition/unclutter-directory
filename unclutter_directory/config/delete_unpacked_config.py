"""
Configuration class for the check-duplicates command.
"""

from pathlib import Path

from ..commons import validations

logger = validations.get_logger()


class DeleteUnpackedConfig:
    """Configuration for the delete-unpacked operation."""

    def __init__(self,
                 target_dir: Path,
                 dry_run: bool = True,  # Default to True for safety
                 always_delete: bool = False,
                 never_delete: bool = False,
                 include_hidden: bool = False):
        """
        Initialize check duplicates configuration

        Args:
            target_dir: Directory to scan for archive-directory duplicates
            dry_run: If True, only show what would be deleted without actually deleting
            always_delete: If True, delete duplicate directories without confirmation
            never_delete: If True, never delete directories (only report)
            include_hidden: Whether to include hidden files and directories
        """
        self.target_dir = target_dir
        self.dry_run = dry_run
        self.always_delete = always_delete
        self.never_delete = never_delete
        self.include_hidden = include_hidden

        # Computed properties
        self._target_dir_path = None

        # Validate configuration
        self._validate_config()

    def _validate_config(self):
        """Validate configuration parameters"""
        errors = []

        # Validate target directory
        if not self.target_dir.exists():
            errors.append(f"TTarget directory does not exist: {self.target_dir}")

        if not self.target_dir.is_dir():
            errors.append(f"Target path is not a directory: {self.target_dir}")

        if not self.target_dir.is_absolute():
            errors.append("Target directory path must be absolute")

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

        flag_str = f" [{', '.join(flags)}]" if flags else ""
        return f"{self.__class__.__name__}(target_dir={self.target_dir}{flag_str})"