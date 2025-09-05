from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional

from unclutter_directory.commons.aliases import Rule

from ..commons import get_logger

logger = get_logger()

# Type aliases
RuleResponses = Dict[int, str]


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

    def should_execute_action(
        self,
        file_path: Path,
        action_type: str,
        rule: Rule,
        rule_responses: RuleResponses,
    ) -> bool:
        """Determine execution based on configured flags"""
        if action_type == "delete":
            if self.never_delete:
                logger.info(f"Skipping deletion of {file_path} (never-delete mode)")
                return False
            elif self.always_delete:
                return True
            else:
                # This shouldn't happen with proper configuration validation
                logger.warning(
                    f"Automatic strategy without delete preference for {file_path}"
                )
                return False

        # For non-delete actions, always execute
        return True


class InteractiveStrategy(ExecutionStrategy):
    """Strategy for interactive execution with user prompts for deletion"""

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

        rule_id = id(rule)

        # Check if we already have a response for this rule
        if rule_id in rule_responses:
            cached_response = rule_responses[rule_id]
            if cached_response == "a":  # Apply to all for this rule
                return True
            elif cached_response == "never":  # Never for this rule
                return False
            # If other response cached (shouldn't happen), fall through to ask again

        # Get user response (and cache only special responses)
        response = self._prompt_user_for_action(file_path)

        # Handle special responses that should be cached
        if response == "a":  # Apply to all (for this rule)
            rule_responses[rule_id] = "a"
            return True
        elif response == "never":  # Never for this rule
            rule_responses[rule_id] = "never"
            return False
        else:
            # Don't cache individual Y/N responses - ask each time
            return response == "y"

    def _prompt_user_for_action(self, file_path: Path) -> str:
        """
        Prompt user for deletion confirmation

        Args:
            file_path: Path to file that would be deleted

        Returns:
            User's response (normalized to lowercase)
        """
        valid_responses = {"y", "n", "a", "never"}
        prompt = f"Do you want to delete {file_path}? [Y(es)/N(o)/A(ll)/Never]: "

        while True:
            try:
                response = input(prompt).strip().lower() or "y"
                if response in valid_responses:
                    return response
                print("Invalid option. Please choose Y(es), N(o), A(ll), or Never.")
            except (EOFError, KeyboardInterrupt):
                # Handle Ctrl+C or EOF gracefully
                print("\nOperation cancelled by user.")
                raise KeyboardInterrupt from None
