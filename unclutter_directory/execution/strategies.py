from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional

from unclutter_directory.commons.aliases import Rule

from ..commons import get_logger
from .confirmation_strategies import (
    AutomaticConfirmationStrategy,
    DryRunConfirmationStrategy,
    InteractiveConfirmationStrategy,
)

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
            # Handle the special cases for logging
            if self.never_delete:
                logger.info(f"Skipping action for {file_path} (never-execute mode)")
                return False
            elif not self.always_delete and not self.never_delete:
                logger.warning(
                    f"Automatic strategy without execution preference for {file_path}"
                )
                return False
            # For always_delete case, delegate to confirmation strategy
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
