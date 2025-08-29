"""
Delete strategy for the check-duplicates command.
Provides both interactive and non-interactive deletion of duplicate directories.
"""

from pathlib import Path
from abc import ABC, abstractmethod

from ..commons import validations

logger = validations.get_logger()


class DeleteConfirmationStrategy(ABC):
    """Abstract base class for directory deletion confirmation strategies."""

    @abstractmethod
    def should_delete_directory(self, directory_path: Path, archive_path: Path) -> bool:
        """
        Determine if a directory should be deleted.

        Args:
            directory_path: Path to the directory to potentially delete
            archive_path: Path to the corresponding archive file

        Returns:
            True if directory should be deleted, False otherwise
        """
        pass

    def perform_deletion(self, directory_path: Path, archive_path: Path, dry_run: bool = False) -> bool:
        """
        Perform the actual directory deletion.

        Args:
            directory_path: Path to directory to delete
            archive_path: Path to corresponding archive
            dry_run: If True, only log what would be deleted

        Returns:
            True if deletion was successful or would be successful (dry run), False otherwise
        """
        if dry_run:
            logger.info(f"[DRY RUN] Would delete directory: {directory_path}")
            return True

        try:
            import shutil
            shutil.rmtree(directory_path)
            logger.info(f"✅ Deleted duplicate directory: {directory_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete directory {directory_path}: {e}")
            return False


class InteractiveDeleteStrategy(DeleteConfirmationStrategy):
    """Strategy that prompts user for confirmation before deleting directories."""

    def __init__(self):
        """Initialize interactive delete strategy."""
        pass

    def should_delete_directory(self, directory_path: Path, archive_path: Path) -> bool:
        """
        Prompt user for confirmation to delete directory.

        Args:
            directory_path: Path to directory to delete
            archive_path: Path to corresponding archive

        Returns:
            True if user confirms deletion, False otherwise
        """
        return self._prompt_user_for_deletion(directory_path, archive_path)

    def _prompt_user_for_deletion(self, directory_path: Path, archive_path: Path) -> str:
        """
        Prompt user for directory deletion confirmation.

        Args:
            directory_path: Path to directory that would be deleted
            archive_path: Path to corresponding archive file

        Returns:
            'y' for yes/accept, 'n' for no/skip
        """
        valid_responses = {"y", "n"}
        archive_name = archive_path.name

        prompt = f"Delete duplicate directory '{directory_path.name}' (identical to '{archive_name}')? [Y(es)/N(o)]: "

        while True:
            try:
                response = input(prompt).strip().lower() or "n"  # Default to no
                if response in valid_responses:
                    return response == "y"
                print("Invalid option. Please choose Y(es) or N(o).")
            except (EOFError, KeyboardInterrupt):
                print("\nOperation cancelled by user.")
                raise KeyboardInterrupt


class AutomaticDeleteStrategy(DeleteConfirmationStrategy):
    """Strategy for automatic deletion without user interaction."""

    def __init__(self, always_delete: bool = False, never_delete: bool = False):
        """
        Initialize automatic delete strategy.

        Args:
            always_delete: If True, always delete duplicate directories
            never_delete: If True, never delete directories (report only)
        """
        self.always_delete = always_delete
        self.never_delete = never_delete

    def should_delete_directory(self, directory_path: Path, archive_path: Path) -> bool:
        """
        Determine deletion based on configured flags.

        Args:
            directory_path: Path to directory to consider for deletion
            archive_path: Path to corresponding archive

        Returns:
            True if directory should be deleted, False otherwise
        """
        if self.never_delete:
            logger.info(f"Skipping deletion of {directory_path} (never-delete mode)")
            return False

        if self.always_delete:
            return True

        # Default behavior: never delete (report only)
        return False


class DryRunDeleteStrategy(DeleteConfirmationStrategy):
    """Strategy for dry run mode - logs actions but doesn't actually delete."""

    def should_delete_directory(self, directory_path: Path, archive_path: Path) -> bool:
        """Always returns False in dry run mode."""
        return False

    def perform_deletion(self, directory_path: Path, archive_path: Path, dry_run: bool = False) -> bool:
        """Override to ensure dry run behavior is always true."""
        logger.info(f"[DRY RUN] Would delete duplicate directory: {directory_path.name} "
                   f"(identical to {archive_path.name})")
        return True  # Always successful in dry run


def create_delete_strategy(dry_run: bool = False, always_delete: bool = False,
                          never_delete: bool = False, interactive: bool = True):
    """
    Factory function to create the appropriate delete strategy.

    Args:
        dry_run: If True, use dry run strategy
        always_delete: If True, use automatic strategy with always delete
        never_delete: If True, use automatic strategy with never delete
        interactive: If True, use interactive strategy when not in other modes

    Returns:
        DeleteConfirmationStrategy instance
    """
    if dry_run:
        return DryRunDeleteStrategy()
    elif always_delete or never_delete:
        return AutomaticDeleteStrategy(always_delete=always_delete, never_delete=never_delete)
    elif interactive:
        return InteractiveDeleteStrategy()
    else:
        # Default to never delete for safety
        logger.warning("No explicit delete strategy specified, defaulting to never delete")
        return AutomaticDeleteStrategy(always_delete=False, never_delete=True)