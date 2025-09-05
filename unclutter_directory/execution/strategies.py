from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Set

from unclutter_directory.commons.aliases import Rule

from ..commons import get_logger

logger = get_logger()

# Type aliases
RuleResponses = Dict[int, str]


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
        responses_dict: Optional[Dict[str, str]] = None,
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


class ExecutionStrategy(ABC):
    """Abstract strategy for file processing execution"""

    @abstractmethod
    def should_execute_action(
        self,
        file_path: Path,
        action_type: str,
        rule: Rule,
        rule_responses: RuleResponses,
    ) -> bool:
        """
        Determine if action should be executed

        Args:
            file_path: Path to the file being processed
            action_type: Type of action (move, delete, compress)
            rule: The matched rule
            rule_responses: Dictionary storing user responses for rules

        Returns:
            True if action should be executed, False otherwise
        """
        pass

    def log_match(
        self, file_path: Path, action_type: str, target: Optional[str] = None
    ):
        """
        Log matched file information

        Args:
            file_path: Path to matched file
            action_type: Type of action to perform
            target: Target location for move/compress actions
        """
        target_info = f" | Target: {target}" if target else ""
        logger.info(f"Matched file: {file_path} | Action: {action_type}{target_info}")


class DryRunStrategy(ExecutionStrategy):
    """Strategy for dry run mode - logs actions but doesn't execute them"""

    def __init__(self):
        """Initialize dry run strategy"""
        self.dry_run_confirmation = DryRunConfirmationStrategy()

    def should_execute_action(
        self,
        file_path: Path,
        action_type: str,
        rule: Rule,
        rule_responses: RuleResponses,
    ) -> bool:
        """Always returns False for dry run mode"""
        return False

    def log_match(
        self, file_path: Path, action_type: str, target: Optional[str] = None
    ):
        """Override to add dry run indication"""
        target_info = f" | Target: {target}" if target else ""
        logger.info(
            f"[DRY RUN] Would execute: {file_path} | Action: {action_type}{target_info}"
        )


class AutomaticStrategy(ExecutionStrategy):
    """Strategy for automatic execution without user interaction"""

    def __init__(self, always_delete: bool, never_delete: bool):
        """
        Initialize automatic strategy

        Args:
            always_delete: If True, always delete without prompting
            never_delete: If True, never delete files
        """
        self.always_delete = always_delete
        self.never_delete = never_delete
        self.confirmation_strategy = AutomaticConfirmationStrategy(
            always_execute=always_delete, never_execute=never_delete
        )

    def should_execute_action(
        self,
        file_path: Path,
        action_type: str,
        rule: Rule,
        rule_responses: RuleResponses,
    ) -> bool:
        """Determine execution based on configured flags"""
        if action_type == "delete":
            return self.confirmation_strategy.get_confirmation(
                context_info=str(file_path), cache_key=None
            )

        # For non-delete actions, always execute
        return True


class InteractiveStrategy(ExecutionStrategy):
    """Strategy for interactive execution with user prompts for deletion"""

    def __init__(self):
        """Initialize interactive strategy"""
        self.confirmation_strategy = InteractiveConfirmationStrategy(
            prompt_template="Do you want to delete {context}? [Y(es)/N(o)/A(ll)/Never]: ",
            valid_responses={"y", "n", "a", "never"},
            default_response="y",
            caching_enabled=True,
            responses_dict={},
        )

    def should_execute_action(
        self,
        file_path: Path,
        action_type: str,
        rule: Rule,
        rule_responses: RuleResponses,
    ) -> bool:
        """Handle user interaction for delete actions"""
        if action_type != "delete":
            return True

        rule_id = str(id(rule))

        # Use rule_responses as our responses_dict for caching
        self.confirmation_strategy.responses_dict = rule_responses

        # Map responses to expected format
        response = self.confirmation_strategy.get_confirmation(
            context_info=str(file_path), cache_key=rule_id
        )

        return response
