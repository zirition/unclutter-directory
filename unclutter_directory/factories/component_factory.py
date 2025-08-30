import yaml

from unclutter_directory.commons.aliases import Rules

from ..commons import validations
from ..config.organize_config import ExecutionMode, OrganizeConfig
from ..execution.strategies import (
    AutomaticStrategy,
    DryRunStrategy,
    ExecutionStrategy,
    InteractiveStrategy,
)
from ..file_operations.file_collector import FileCollector
from ..file_operations.file_matcher import FileMatcher

logger = validations.get_logger()


class ComponentFactory:
    """
    Factory for creating configured components.
    Centralizes object creation and configuration logic.
    """

    @staticmethod
    def create_file_matcher(config: OrganizeConfig) -> FileMatcher:
        """
        Create configured FileMatcher with loaded rules

        Args:
            config: Configuration containing rules file path

        Returns:
            Configured FileMatcher instance

        Raises:
            RuntimeError: If rules cannot be loaded
        """
        rules = ComponentFactory._load_rules(config.rules_file)
        if rules is None:
            raise RuntimeError(f"Failed to load rules from {config.rules_file}")

        return FileMatcher(rules)

    @staticmethod
    def create_file_collector(config: OrganizeConfig) -> FileCollector:
        """
        Create configured FileCollector

        Args:
            config: Configuration containing collection preferences

        Returns:
            Configured FileCollector instance
        """
        return FileCollector(include_hidden=config.include_hidden)

    @staticmethod
    def create_execution_strategy(config: OrganizeConfig) -> ExecutionStrategy:
        """
        Create appropriate execution strategy based on configuration

        Args:
            config: Configuration determining strategy type

        Returns:
            Appropriate ExecutionStrategy instance
        """
        if config.execution_mode == ExecutionMode.DRY_RUN:
            return DryRunStrategy()
        elif config.execution_mode == ExecutionMode.AUTOMATIC:
            return AutomaticStrategy(
                always_delete=config.always_delete, never_delete=config.never_delete
            )
        elif config.execution_mode == ExecutionMode.INTERACTIVE:
            return InteractiveStrategy()
        else:
            # This should not happen with proper enum usage
            raise ValueError(f"Unknown execution mode: {config.execution_mode}")

    @staticmethod
    def _load_rules(rules_file: str) -> Rules:
        """
        Load rules from YAML file

        Args:
            rules_file: Path to rules file

        Returns:
            Loaded rules list or None if loading failed
        """
        try:
            with open(rules_file, encoding="utf-8") as f:
                rules = yaml.safe_load(f)

            if not isinstance(rules, list):
                logger.error(f"Rules file {rules_file} must contain a list")
                return None

            return rules

        except yaml.YAMLError as e:
            logger.error(f"YAML error in rules file {rules_file}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading rules file {rules_file}: {e}")
            return None
