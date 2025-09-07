"""
Delete strategy for the check-duplicates command.
Provides both interactive and non-interactive deletion of duplicate directories.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from ..commons import get_logger
from .confirmation_strategies import (
    AutomaticConfirmationStrategy,
    DryRunConfirmationStrategy,
    InteractiveConfirmationStrategy,
)

logger = get_logger()


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

    def perform_deletion(
        self, directory_path: Path, archive_path: Path, dry_run: bool = False
    ) -> bool:
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
        self.confirmation_strategy = InteractiveConfirmationStrategy(
            prompt_template="Delete duplicate directory '{context}'? [Y(es)/N(o)]: ",
            valid_responses={"y", "n"},
            default_response="n",
            caching_enabled=False,
        )

    def should_delete_directory(self, directory_path: Path, archive_path: Path) -> bool:
        """
        Prompt user for confirmation to delete directory.

        Args:
            directory_path: Path to directory to delete
            archive_path: Path to corresponding archive

        Returns:
            True if user confirms deletion, False otherwise
        """
        context_info = f"'{directory_path.name}' (identical to '{archive_path.name}')"
        return self.confirmation_strategy.get_confirmation(context_info)


class AutomaticDeleteStrategy(DeleteConfirmationStrategy):
    """Strategy for automatic deletion without user interaction."""

    def __init__(self, always_delete: bool = False):
        """
        Initialize automatic delete strategy.

        Args:
            always_delete: If True, always delete duplicate directories
        """
        self.confirmation_strategy = AutomaticConfirmationStrategy(
            always_execute=always_delete,
            never_execute=not always_delete,  # Default to never if not always
        )

    def should_delete_directory(self, directory_path: Path, archive_path: Path) -> bool:
        """
        Determine deletion based on configured flags.

        Args:
            directory_path: Path to directory to consider for deletion
            archive_path: Path to corresponding archive

        Returns:
            True if directory should be deleted, False otherwise
        """
        context_info = f"delete directory {directory_path.name}"
        return self.confirmation_strategy.get_confirmation(context_info)


class DryRunDeleteStrategy(DeleteConfirmationStrategy):
    """Strategy for dry run mode - logs actions but doesn't actually delete."""

    def __init__(self):
        """Initialize dry run delete strategy."""
        self.dry_run_confirmation = DryRunConfirmationStrategy()

    def should_delete_directory(self, directory_path: Path, archive_path: Path) -> bool:
        """Always returns False in dry run mode."""
        return False

    def perform_deletion(
        self, directory_path: Path, archive_path: Path, dry_run: bool = False
    ) -> bool:
        """Override to ensure dry run behavior is always true."""
        logger.info(
            f"[DRY RUN] Would delete duplicate directory: {directory_path.name} "
            f"(identical to {archive_path.name})"
        )
        return True  # Always successful in dry run


def create_delete_strategy(
    always_delete: bool = False,
    never_delete: bool = False,
    interactive: bool = True,
):
    """
    Factory function to create the appropriate delete strategy.

    Args:
        always_delete: If True, use automatic strategy with always delete
        never_delete: If True, use automatic strategy with never delete
        interactive: If True, use interactive strategy when not in other modes

    Returns:
        DeleteConfirmationStrategy instance
    """
    if never_delete:
        return DryRunDeleteStrategy()
    elif always_delete:
        return AutomaticDeleteStrategy(always_delete=always_delete)
    elif interactive:
        return InteractiveDeleteStrategy()
    else:
        # Default to automatic never delete for safety
        logger.warning(
            "No explicit delete strategy specified, defaulting to automatic never delete mode"
        )
        return AutomaticDeleteStrategy(always_delete=False)
