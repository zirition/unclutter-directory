from pathlib import Path
from typing import Dict, List

from ..config.organize_config import OrganizeConfig
from ..entities.file import File
from ..file_operations.file_matcher import FileMatcher
from .action_executor import ActionExecutor
from .strategies import ExecutionStrategy, RuleResponses


class FileProcessor:
    """
    Processes individual files according to matched rules.
    Coordinates between FileMatcher, ExecutionStrategy, and ActionExecutor.
    """

    def __init__(
        self,
        matcher: FileMatcher,
        strategy: ExecutionStrategy,
        rule_responses: RuleResponses,
        config: OrganizeConfig,
    ):
        """
        Initialize file processor
        Args:
            matcher: FileMatcher instance for rule matching
            strategy: ExecutionStrategy for determining execution behavior
            rule_responses: Dictionary to track user responses for rules
            config: OrganizeConfig instance
        """
        self.matcher = matcher
        self.strategy = strategy
        self.rule_responses = rule_responses
        self.config = config

    def process_file(self, file_path: Path, target_dir: Path) -> bool:
        """
        Process a single file according to matching rules

        Args:
            file_path: Path to file to process
            target_dir: Base directory for relative path calculations

        Returns:
            True if file was processed (rule matched), False otherwise
        """
        # Convert to File object for matching
        file_obj = File.from_path(file_path)

        # Find matching rule
        rule = self.matcher.match(file_obj)
        if not rule:
            return False

        # Extract action information
        action = rule.get("action", {})
        action_type = action.get("type")

        # Log the match
        self.strategy.log_match(file_path, action_type, action.get("target"))

        # Determine if we should execute the action
        should_execute = self.strategy.should_execute_action(
            file_path, action_type, rule, self.rule_responses
        )

        # Execute action if determined
        if should_execute:
            executor = ActionExecutor(action, strategy_factory=None)
            executor.execute_action(file_path, target_dir, rule, self.config)

        return True

    def process_files(self, file_paths: List[Path], target_dir: Path) -> Dict[str, int]:
        """
        Process multiple files and return statistics

        Args:
            file_paths: List of file paths to process
            target_dir: Base directory for relative path calculations

        Returns:
            Dictionary with processing statistics
        """
        stats = {
            "total_files": len(file_paths),
            "processed_files": 0,
            "skipped_files": 0,
            "errors": 0,
        }

        for file_path in file_paths:
            try:
                if self.process_file(file_path, target_dir):
                    stats["processed_files"] += 1
                else:
                    stats["skipped_files"] += 1
            except Exception:
                stats["errors"] += 1
                # Let ActionExecutor handle error logging
                continue

        return stats
