"""
Confirmation handlers for execution decisions.

This module provides a unified interface for determining whether actions
should be executed, consolidating the logic previously scattered across
multiple strategy hierarchies. It supports dry-run, automatic, and interactive
modes with proper caching for interactive sessions.
"""

from abc import ABC, abstractmethod

from ..commons import get_logger

logger = get_logger()


class ConfirmationHandler(ABC):
    """
    Abstract base class for determining if an action should be executed.

    This handler centralizes the decision logic for execution modes,
    replacing the previous separate hierarchies for organize and delete-unpacked.
    """

    @abstractmethod
    def should_execute(
        self,
        context_info: str,
        prompt_template: str,
        cache_key: str | None = None,
        action_type: str | None = None,
    ) -> bool:
        """
        Determine if an action should be executed based on the context and mode.

        Args:
            context_info (str): Description of the action context (e.g., file path).
            prompt_template (str): Template for interactive prompts, with {context}.
            cache_key (Optional[str]): Key for caching interactive responses.
            action_type (Optional[str]): Type of action (e.g., 'delete', 'move').
                                       If None, defaults to delete-like behavior.

        Returns:
            bool: True if the action should proceed, False otherwise.
        """
        pass


class DryRunConfirmationHandler(ConfirmationHandler):
    """Handler for dry-run mode - logs actions but never executes them."""

    def should_execute(
        self,
        context_info: str,
        prompt_template: str,
        cache_key: str | None = None,
        action_type: str | None = None,
    ) -> bool:
        """
        Always returns False in dry-run mode, logging the intended action.

        Args:
            context_info (str): Description of the action context.
            prompt_template (str): Unused in dry-run.
            cache_key (Optional[str]): Unused in dry-run.
            action_type (Optional[str]): Type of action for descriptive logging.

        Returns:
            bool: Always False in dry-run mode.
        """
        action_desc = action_type if action_type else "execute action"
        logger.info(f"[DRY RUN] Would {action_desc} for {context_info}")
        return False


class AutomaticConfirmationHandler(ConfirmationHandler):
    """Handler for automatic execution without user interaction."""

    def __init__(self, always_confirm: bool = False):
        """
        Initialize automatic handler.

        Args:
            always_confirm (bool): If True, always confirm delete actions.
                                 For non-delete actions, this is ignored (always True).
        """
        self.always_confirm = always_confirm

    def should_execute(
        self,
        context_info: str,
        prompt_template: str,
        cache_key: str | None = None,
        action_type: str | None = None,
    ) -> bool:
        """
        Determine execution based on action type and configuration.

        Non-delete actions always proceed. Delete actions depend on always_confirm.

        Args:
            context_info (str): Description of the action context.
            prompt_template (str): Unused in automatic mode.
            cache_key (Optional[str]): Unused in automatic mode.
            action_type (Optional[str]): Type of action to evaluate.

        Returns:
            bool: True if action should proceed, False otherwise.
        """
        # Non-delete actions always execute in automatic mode
        if action_type != "delete":
            return True

        # For delete actions, use the configured preference
        if not self.always_confirm:
            logger.info(f"Skipping delete action for {context_info} (automatic mode)")
        return self.always_confirm


class InteractiveConfirmationHandler(ConfirmationHandler):
    """Handler for interactive execution with user prompts and response caching."""

    def __init__(self):
        """Initialize interactive handler with empty response cache."""
        self._responses: dict[str, str] = {}

    def should_execute(
        self,
        context_info: str,
        prompt_template: str,
        cache_key: str | None = None,
        action_type: str | None = None,
    ) -> bool:
        """
        Handle user interaction for delete actions, with caching.

        Non-delete actions always proceed without prompting.

        Args:
            context_info (str): Description of the action context.
            prompt_template (str): Template for the prompt, with {context}.
            cache_key (Optional[str]): Key for caching responses (e.g., rule ID).
            action_type (Optional[str]): Type of action to evaluate.

        Returns:
            bool: True if user confirms or action is non-delete, False otherwise.
        """
        # Non-delete actions always execute without prompting
        if action_type != "delete":
            return True

        # Check cache for previously stored responses
        if cache_key and cache_key in self._responses:
            cached_response = self._responses[cache_key]
            if cached_response == "a":  # Apply to all
                return True
            elif cached_response == "never":
                return False
            # For individual responses, fall through to prompt again

        # Generate and show prompt
        prompt = prompt_template.format(context=context_info)
        valid_responses = {"y", "n", "a", "never"}
        default_response = "y"

        while True:
            try:
                response = input(prompt).strip().lower() or default_response
                if response in valid_responses:
                    break
                print("Invalid response. Please try again.")
            except (EOFError, KeyboardInterrupt):
                print("\nOperation cancelled by user.")
                raise

        # Handle special responses that should be cached
        if response in ("a", "never") and cache_key:
            self._responses[cache_key] = response

        # Return True for affirmative responses
        return response in ("y", "a")
