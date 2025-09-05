"""
Delete strategy for the check-duplicates command.
Provides both interactive and non-interactive deletion of duplicate directories.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Set

from ..commons import get_logger

logger = get_logger()


class ConfirmationStrategy(ABC):
    """Base class for configurable confirmation strategies"""

    @abstractmethod
    def get_confirmation(
        self, context_info: str, cache_key: Optional[str] = None
    ) -> bool:
        """
        Get user confirmation for an action.

        Args:
            context_info: Information about the action for the prompt
            cache_key: Optional key for caching responses

        Returns:
            True if action should proceed, False otherwise
        """
        pass


class AutomaticConfirmationStrategy(ConfirmationStrategy):
    """Strategy for automatic confirmation without user interaction"""

    def __init__(self, always_execute: bool = False, never_execute: bool = False):
        self.always_execute = always_execute
        self.never_execute = never_execute

    def get_confirmation(
        self, context_info: str, cache_key: Optional[str] = None
    ) -> bool:
        """Determine confirmation based on flags"""
        if self.never_execute:
            logger.info(f"Skipping action for {context_info} (never-execute mode)")
            return False
        elif self.always_execute:
            return True
        else:
            logger.warning(
                f"Automatic strategy without execution preference for {context_info}"
            )
            return False


class InteractiveConfirmationStrategy(ConfirmationStrategy):
    """Strategy for interactive confirmation with user prompts"""

    def __init__(
        self,
        prompt_template: str,
        valid_responses: Set[str],
        default_response: str = "n",
        caching_enabled: bool = False,
        responses_dict: Optional[dict] = None,
    ):
        """
        Initialize interactive confirmation strategy.

        Args:
            prompt_template: Template string for the prompt (e.g., "Delete {context}? [Y/N]: ")
            valid_responses: Set of valid response strings
            default_response: Default response for empty input
            caching_enabled: Whether to cache responses
            responses_dict: Dictionary to store cached responses
        """
        self.prompt_template = prompt_template
        self.valid_responses = valid_responses
        self.default_response = default_response
        self.caching_enabled = caching_enabled
        self.responses_dict = responses_dict or {}

    def get_confirmation(
        self, context_info: str, cache_key: Optional[str] = None
    ) -> bool:
        """Get confirmation from user, with optional caching"""
        if self.caching_enabled and cache_key and cache_key in self.responses_dict:
            cached = self.responses_dict[cache_key]
            if cached == "a":  # Apply to all
                return True
            elif cached == "never":
                return False
            # If other response cached, fall through to ask again

        # Get response from user
        response = self._prompt_user(context_info)

        # Handle special responses that should be cached
        if response == "a":  # Apply to all
            if self.caching_enabled and cache_key:
                self.responses_dict[cache_key] = "a"
            return True
        elif response == "never":
            if self.caching_enabled and cache_key:
                self.responses_dict[cache_key] = "never"
            return False
        else:
            # Don't cache individual Y/N responses - ask each time
            return response == "y"

    def _prompt_user(self, context_info: str) -> str:
        """Prompt user and return normalized response"""
        prompt = self.prompt_template.format(context=context_info)
        while True:
            try:
                response = input(prompt).strip().lower() or self.default_response
                if response in self.valid_responses:
                    return response
                print("Invalid response. Please try again.")
            except (EOFError, KeyboardInterrupt):
                print("\nOperation cancelled by user.")
                raise KeyboardInterrupt from None


class DryRunConfirmationStrategy(ConfirmationStrategy):
    """Strategy for dry run mode - always returns False"""

    def get_confirmation(
        self, context_info: str, cache_key: Optional[str] = None
    ) -> bool:
        """Always return False in dry run mode"""
        logger.info(f"[DRY RUN] Would confirm action for {context_info}")
        return False


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
        never_delete: If True, use automatic strategy with never delete (dry run)
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
        # Default to never delete (dry run) for safety
        logger.warning(
            "No explicit delete strategy specified, defaulting to dry run mode"
        )
        return DryRunDeleteStrategy()
